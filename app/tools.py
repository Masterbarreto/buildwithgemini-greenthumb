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

"""Tools for GreenThumb Botanicals agent."""

import os
from typing import Any, Dict, List, Optional
from google.cloud import firestore

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-12e2994a59cd")
if PROJECT_ID.isdigit() or not PROJECT_ID:
    PROJECT_ID = "qwiklabs-gcp-03-12e2994a59cd"

# Initialize Firestore Client
db = firestore.Client(project=PROJECT_ID)


def list_plants(
    pet_friendly_only: Optional[bool] = None,
    max_price: Optional[float] = None,
    light_filter: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Consulta o catálogo de plantas da estufa no Firestore com filtros opcionais.

    Args:
        pet_friendly_only: Se True, retorna apenas plantas seguras e não tóxicas para cães e gatos.
        max_price: Valor máximo em Reais (R$) para filtrar plantas acessíveis.
        light_filter: Filtro por luminosidade (ex: 'sombra', 'pouca luz', 'indireta', 'sol pleno').

    Returns:
        Uma lista de plantas disponíveis com informações botânicas, fotos, cuidados e preços.
    """
    collection_ref = db.collection("plants")
    query = collection_ref

    if pet_friendly_only is not None:
        query = query.where("pet_friendly", "==", pet_friendly_only)

    docs = query.stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        if max_price is not None and data.get("price_brl", 0) > max_price:
            continue
        if light_filter:
            req = data.get("light_requirement", "").lower()
            if light_filter.lower() not in req:
                continue
        results.append(data)

    return results


def get_plant_details(plant_id: str) -> Dict[str, Any]:
    """Obtém os detalhes completos de uma planta específica pelo ID (ex: 'zamioculca', 'costela-de-adao').

    Args:
        plant_id: Identificador único da planta (slug ou id).

    Returns:
        Dicionário com detalhes botânicos, ficha técnica de cultivo e informações de estoque.
    """
    doc_ref = db.collection("plants").document(plant_id.lower().strip())
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()

    # Fallback: search by name
    all_docs = db.collection("plants").stream()
    for d in all_docs:
        data = d.to_dict()
        if plant_id.lower() in data.get("name", "").lower():
            return data

    return {"error": f"Planta com identificador '{plant_id}' não encontrada no catálogo."}


def calculate_watering_schedule(
    plant_category: str,
    pot_volume_liters: float,
    room_temperature_celsius: float = 24.0,
) -> Dict[str, Any]:
    """Calcula a recomendação de rega (frequência em dias e volume de água em ml) com base no vaso e ambiente.

    Args:
        plant_category: Tipo ou categoria da planta (ex: 'suculenta', 'folhagem tropical', 'samambaia', 'purificadora').
        pot_volume_liters: Volume aproximado do vaso em litros (ex: 2.5, 5.0).
        room_temperature_celsius: Temperatura média do ambiente em graus Celsius (°C).

    Returns:
        Recomendação calculada contendo intervalo de rega sugerido (dias), volume de água (ml) e dicas de drenagem.
    """
    category = plant_category.lower()

    # Base days by category
    if "suculenta" in category or "cacto" in category or "zamioculca" in category:
        base_days = 15
        water_ratio = 0.15  # 15% do volume do vaso
    elif "samambaia" in category or "maranta" in category:
        base_days = 3
        water_ratio = 0.25  # 25% do volume do vaso
    elif "purificadora" in category or "sansevieria" in category or "espada" in category:
        base_days = 12
        water_ratio = 0.18
    else:
        # Padrão folhagens tropicais
        base_days = 7
        water_ratio = 0.20

    # Ajuste por temperatura
    if room_temperature_celsius >= 30.0:
        base_days = max(2, base_days - 2)
        water_ratio += 0.05
    elif room_temperature_celsius <= 18.0:
        base_days += 3
        water_ratio -= 0.03

    volume_ml = round(pot_volume_liters * 1000 * water_ratio)
    interval_days = round(base_days)

    return {
        "plant_category": plant_category,
        "pot_volume_liters": pot_volume_liters,
        "room_temperature_celsius": room_temperature_celsius,
        "recommended_interval_days": interval_days,
        "recommended_water_volume_ml": volume_ml,
        "care_tips": "Regue uniformemente o substrato até sair água pelos furos de drenagem. Nunca deixe água acumulada no pratinho para evitar apodrecimento das raízes."
    }


def record_care_log(
    user_id: str,
    plant_name: str,
    action: str,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Registra uma ação de cuidado botânico realizada pelo usuário (ex: 'Rega', 'Adubação', 'Poda').

    Args:
        user_id: Identificador do usuário ou jardineiro.
        plant_name: Nome da planta cuidada.
        action: Ação realizada (ex: 'Rega realizada', 'Fertilização com NPK 10-10-10', 'Troca de vaso').
        notes: Observações adicionais do usuário (ex: 'Folha nova brotando', 'Solo estava bem seco').

    Returns:
        Confirmação do registro salvo no Firestore.
    """
    log_data = {
        "user_id": user_id,
        "plant_name": plant_name,
        "action": action,
        "notes": notes or "",
        "timestamp": firestore.SERVER_TIMESTAMP,
    }
    doc_ref = db.collection("care_logs").document()
    doc_ref.set(log_data)

    return {
        "status": "success",
        "log_id": doc_ref.id,
        "message": f"Registro de '{action}' para a planta '{plant_name}' salvo com sucesso!",
    }
