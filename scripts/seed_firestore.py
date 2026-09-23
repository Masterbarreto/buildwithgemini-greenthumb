import os
from google.cloud import firestore

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "qwiklabs-gcp-03-12e2994a59cd")
# Guarantee project string ID if numeric
if PROJECT_ID.isdigit() or not PROJECT_ID:
    PROJECT_ID = "qwiklabs-gcp-03-12e2994a59cd"

db = firestore.Client(project=PROJECT_ID)

PLANTS = [
    {
        "id": "zamioculca",
        "name": "Zamioculca (Planta ZZ)",
        "scientific_name": "Zamioculcas zamiifolia",
        "category": "Plantas de Interior",
        "light_requirement": "baixa a média luz indireta (tolera sombra)",
        "watering_frequency": "a cada 2 a 3 semanas (deixar solo secar completamente)",
        "pet_friendly": False,
        "price_brl": 65.00,
        "difficulty": "Muito Fácil (Ideal para iniciantes)",
        "stock": 14,
        "image_url": "https://images.unsplash.com/photo-1632207691143-643e2a9a9361?w=600&auto=format&fit=crop&q=80",
        "description": "Planta extremamente resistente e de folhas verdes reluzentes. Sobrevive a períodos de seca e ambientes com pouca luz natural."
    },
    {
        "id": "espada-sao-jorge",
        "name": "Espada-de-São-Jorge",
        "scientific_name": "Sansevieria trifasciata",
        "category": "Plantas Purificadoras",
        "light_requirement": "qualquer nível de luz (de sombra a sol pleno)",
        "watering_frequency": "a cada 2 semanas no verão, mensal no inverno",
        "pet_friendly": False,
        "price_brl": 45.00,
        "difficulty": "Muito Fácil",
        "stock": 20,
        "image_url": "https://images.unsplash.com/photo-1593482892290-f54927ae1bf6?w=600&auto=format&fit=crop&q=80",
        "description": "Conhecida por purificar o ar e converter CO2 em oxigênio durante a noite. Quase indestrutível."
    },
    {
        "id": "maranta-pena-pavao",
        "name": "Maranta-Pena-de-Pavão (Planta da Oração)",
        "scientific_name": "Maranta leuconeura",
        "category": "Folhagens Tropicais",
        "light_requirement": "luz indireta suave (evitar sol direto)",
        "watering_frequency": "2 vezes por semana (manter solo levemente úmido)",
        "pet_friendly": True,
        "price_brl": 55.00,
        "difficulty": "Médio",
        "stock": 8,
        "image_url": "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=600&auto=format&fit=crop&q=80",
        "description": "Folhas decorativas com desenhos exuberantes que se fecham verticalmente à noite como mãos em oração. 100% segura para cães e gatos!"
    },
    {
        "id": "samambaia-americana",
        "name": "Samambaia Americana",
        "scientific_name": "Nephrolepis exaltata",
        "category": "Plantas Pendentes",
        "light_requirement": "luz indireta filtrada e alta umidade",
        "watering_frequency": "2 a 3 vezes por semana (gosta de borrifadas nas folhas)",
        "pet_friendly": True,
        "price_brl": 49.90,
        "difficulty": "Fácil a Médio",
        "stock": 12,
        "image_url": "https://images.unsplash.com/photo-1596547609652-9cf5d8d76921?w=600&auto=format&fit=crop&q=80",
        "description": "Volumosa e elegante folhagem verde-clara, excelente para pendurar na sala ou varanda coberta. Não tóxica para pets."
    },
    {
        "id": "costela-de-adao",
        "name": "Costela-de-Adão",
        "scientific_name": "Monstera deliciosa",
        "category": "Destaque Tropical",
        "light_requirement": "luz indireta abundante a meia-sombra",
        "watering_frequency": "1 vez por semana (quando os primeiros centímetros de terra estiverem secos)",
        "pet_friendly": False,
        "price_brl": 110.00,
        "difficulty": "Fácil",
        "stock": 7,
        "image_url": "https://images.unsplash.com/photo-1617173944883-6ffbd35d584d?w=600&auto=format&fit=crop&q=80",
        "description": "Ícone do design botânico contemporâneo. Suas folhas recortadas e esculturais dão um toque de selva urbana a qualquer ambiente."
    },
    {
        "id": "peperomia-melancia",
        "name": "Peperômia Melancia",
        "scientific_name": "Peperomia argyreia",
        "category": "Plantas Compactas / Mesa",
        "light_requirement": "luz indireta média a brilhante",
        "watering_frequency": "1 vez a cada 7-10 dias (deixar secar parcialmente)",
        "pet_friendly": True,
        "price_brl": 38.00,
        "difficulty": "Fácil",
        "stock": 15,
        "image_url": "https://images.unsplash.com/photo-1622383563227-04401ab4e5ea?w=600&auto=format&fit=crop&q=80",
        "description": "Compacta e charmosa, com folhas que imitam a casca de uma melancia. Segura para todos os animais de estimação."
    }
]

print(f"Populando Firestore no projeto '{PROJECT_ID}'...")
collection_ref = db.collection("plants")
for plant in PLANTS:
    doc_id = plant["id"]
    collection_ref.document(doc_id).set(plant)
    print(f"✓ Planta adicionada: {plant['name']} ({doc_id})")

print("Seeding concluído com sucesso!")
