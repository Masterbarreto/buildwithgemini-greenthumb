# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""GreenThumb Botanicals - ADK Agent for Greenhouse & Plant Care."""

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from .a2ui_utils import a2ui_callback
from .tools import (
    calculate_watering_schedule,
    get_plant_details,
    list_plants,
    record_care_log,
)

MODEL = "gemini-2.5-flash"

# Geração de memórias persistentes após cada turno do agente
async def generate_memories_callback(callback_context: CallbackContext):
    """Envia a sessão ao Memory Bank para persistir fatos e preferências do usuário."""
    try:
        await callback_context.add_session_to_memory()
    except Exception:
        pass
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "Você é o GreenThumb, o assistente botânico e consultor inteligente da estufa 'GreenThumb Botanicals'. "
        "Você é especialista em botânica, plantas ornamentais de interior, purificação de ar e cuidados com a vegetação. "
        "Seu tom é acolhedor, profissional, encorajador e apaixonado por plantas. Responda em Português do Brasil.\n\n"
        "Suas Diretrizes Operacionais:\n"
        "1. MEMÓRIA: Lembre-se sempre das preferências informadas pelo usuário em conversas anteriores ou turnos passados "
        "(ex: se ele possui animais de estimação como gatos/cães, se mora em apartamento com pouca luz, se é iniciante, "
        "ou quais plantas ele já possui em casa). Personalize todas as recomendações com base nesse contexto.\n"
        "2. CONSULTA AO CATÁLOGO: Sempre que o usuário pedir recomendações de plantas para comprar ou conhecer, use a tool "
        "`list_plants` ou `get_plant_details` para consultar o inventário real no Firestore. Nunca invente plantas inexistentes no catálogo.\n"
        "3. CÁLCULO DE REGA: Quando o usuário tiver dúvidas de frequência ou volume de rega para um vaso ou ambiente específico, "
        "utilize a tool `calculate_watering_schedule`.\n"
        "4. REGISTRO DE CUIDADOS: Quando o usuário relatar que regou, adubou ou podou uma planta, ofereça ou utilize a tool "
        "`record_care_log` para registrar o histórico.\n"
        "5. APRESENTAÇÃO VISUAL (A2UI): Quando listar plantas recomendadas ou exibir detalhes de uma espécie, apresente os cards visuais A2UI."
    ),
    workflow_description=(
        "Analise o pedido do usuário. Se for uma conversa informal, responda de forma prestativa e calorosa em texto. "
        "Se o usuário pedir recomendações ou informações sobre espécies, use as tools apropriadas e, ao apresentar a lista "
        "ou ficha técnica, gere a interface visual A2UI estruturada."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the image_url field from list_plants or get_plant_details). "
        "Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        list_plants,
        get_plant_details,
        calculate_watering_schedule,
        record_care_log,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
