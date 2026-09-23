"""Minimal FastAPI proxy for an A2A agent (supporting both Local Mode and Deployed Agent Runtime).

The browser talks ONLY to this proxy (same origin, no CORS, no GCP creds in the
browser). The proxy returns replies as structured parts the chat UI knows how to show:

  * {"kind": "text", "text": ...}  -> a normal chat bubble
  * {"kind": "a2ui", "data": ...}  -> one A2UI message (beginRendering /
    surfaceUpdate); static/index.html renders these as a card.

Modes:
  1. Local Mode (default when AGENT_ENGINE_RESOURCE_NAME is not set):
     Executes the local ADK agent and extracts text and A2UI cards.
  2. Cloud A2A Mode (when AGENT_ENGINE_RESOURCE_NAME is set):
     Authenticates with ADC and proxies requests via A2A protocol to Agent Runtime.

Run:
  uv run python frontend/main.py                 # -> http://localhost:8080
"""

import json
import os
import re
import uuid

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# Try importing A2A client types for Cloud Deployed Mode
try:
    import google.auth
    import google.auth.transport.requests
    from a2a.client import ClientConfig, ClientFactory
    from a2a.types import (
        AgentCard,
        Message,
        Part,
        Role,
        TaskArtifactUpdateEvent,
        TransportProtocol,
    )
    try:
        from a2a.types import FilePart, TextPart
    except ImportError:
        FilePart = None
        TextPart = None
except ImportError:
    pass

RESOURCE = os.environ.get("AGENT_ENGINE_RESOURCE_NAME")
AGENT_DIRECTORY = os.environ.get("AGENT_DIRECTORY", "app")

_A2UI_MIME = "application/json+a2ui"
_contexts: dict[str, str] = {}
_card = None

if RESOURCE:
    LOCATION = RESOURCE.split("/locations/")[1].split("/")[0]
    A2A_BASE = (
        f"https://{LOCATION}-aiplatform.googleapis.com/reasoningEngines/v1/"
        f"{RESOURCE}/api/a2a/{AGENT_DIRECTORY}"
    )
    A2A_CARD_URL = f"{A2A_BASE}/.well-known/agent-card.json"
    _creds, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    def _auth_headers() -> dict[str, str]:
        _creds.refresh(google.auth.transport.requests.Request())
        return {
            "Authorization": f"Bearer {_creds.token}",
            "Content-Type": "application/json",
        }
else:
    from dotenv import load_dotenv
    load_dotenv()
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types
    from app.agent import root_agent, app as adk_app

    _local_runner = Runner(
        app=adk_app,
        session_service=InMemorySessionService(),
        auto_create_session=True,
    )


app = FastAPI()


@app.exception_handler(Exception)
async def _json_errors(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={
            "parts": [{"kind": "text", "text": f"Error: {type(exc).__name__}: {exc}"}]
        },
    )


async def _get_card(client: httpx.AsyncClient):
    global _card
    if _card is None:
        resp = await client.get(A2A_CARD_URL)
        resp.raise_for_status()
        card = AgentCard(**resp.json())
        card.url = A2A_BASE
        _card = card
    return _card


def _extract_parts(parts: list) -> list[dict]:
    out: list[dict] = []
    for p in parts:
        root = getattr(p, "root", p)
        if TextPart and isinstance(root, TextPart) and getattr(root, "text", None):
            out.append({"kind": "text", "text": root.text})
        elif getattr(root, "data", None) is not None:
            meta = getattr(root, "metadata", None) or {}
            mime = meta.get("mimeType") if isinstance(meta, dict) else None
            if mime == _A2UI_MIME:
                out.append({"kind": "a2ui", "data": root.data})
        elif FilePart and isinstance(root, FilePart):
            uri = getattr(getattr(root, "file", None), "uri", None)
            if uri:
                out.append({"kind": "text", "text": uri})
    return out


@app.post("/chat")
async def chat(req: Request):
    body = await req.json()
    message = body.get("message", "")
    user_id = body.get("user_id") or "web-user"
    parts: list[dict] = []

    if not RESOURCE:
        # Local Mode: query the ADK Runner directly
        session_id = _contexts.get(user_id)
        if not session_id:
            session_id = str(uuid.uuid4())
            _contexts[user_id] = session_id

        msg = types.Content(role="user", parts=[types.Part.from_text(text=message)])
        async for event in _local_runner.run_async(
            user_id=user_id, session_id=session_id, new_message=msg
        ):
            if event.content and event.content.parts:
                for p in event.content.parts:
                    if p.text:
                        parts.append({"kind": "text", "text": p.text})
                    elif p.inline_data:
                        try:
                            data_str = p.inline_data.data.decode("utf-8")
                            match = re.search(r"<a2a_datapart_json>(.*?)</a2a_datapart_json>", data_str, re.DOTALL)
                            if match:
                                obj = json.loads(match.group(1))
                                parts.append({"kind": "a2ui", "data": obj.get("data")})
                        except Exception:
                            pass
    else:
        # Cloud A2A Mode
        async with httpx.AsyncClient(headers=_auth_headers(), timeout=120) as client:
            card = await _get_card(client)
            factory = ClientFactory(
                ClientConfig(
                    supported_transports=[
                        TransportProtocol.jsonrpc,
                        TransportProtocol.http_json,
                    ],
                    httpx_client=client,
                )
            )
            a2a_client = factory.create(card)

            msg = Message(
                message_id=str(uuid.uuid4()),
                role=Role.user,
                parts=[Part(root=TextPart(text=message))] if TextPart else [Part(text=message)],
                context_id=_contexts.get(user_id),
            )

            last_task = None
            got_artifact_update = False
            async for event in a2a_client.send_message(msg):
                if not isinstance(event, tuple):
                    continue
                task, update = event
                if task is not None:
                    last_task = task
                    if getattr(task, "context_id", None):
                        _contexts[user_id] = task.context_id
                if isinstance(update, TaskArtifactUpdateEvent):
                    got_artifact_update = True
                    parts.extend(_extract_parts(update.artifact.parts))

            if not got_artifact_update and last_task is not None:
                for artifact in getattr(last_task, "artifacts", None) or []:
                    parts.extend(_extract_parts(artifact.parts))

    if not parts:
        parts = [{"kind": "text", "text": "(The agent didn't return a reply.)"}]
    return JSONResponse({"parts": parts})


# Serve the chat UI (works whether launched from project root or frontend dir)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    print(f"Starting GreenThumb chat server on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
