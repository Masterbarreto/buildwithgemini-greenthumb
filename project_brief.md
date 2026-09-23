# My agent: GreenThumb Botanicals
One-liner: Um assistente inteligente de estufa e cuidados botânicos que ajuda entusiastas de jardinagem a escolher e cuidar de plantas com base em um catálogo interativo.

Tool coverage:
- Memory: Lembra quais plantas o usuário possui, o nível de luz do seu espaço, restrições (ex: animais de estimação) e histórico de cuidados/regas.
- Tools: Consulta de catálogo/inventário de plantas (Firestore), registro de cuidados e agendamento de rega, guia de cultivo botânico.
- Catalog/UI: Catálogo de plantas e espécies da estufa renderizado como cards visuais A2UI (foto, espécie, nível de luz, frequência de rega e preço).
- Image gen: Geração de imagens de plantas saudáveis, florescendo ou simulação de vasos no ambiente.
- Sandbox: Cálculo de ciclo ideal de rega/fertilização com base em dimensões de vaso e umidade/temperatura.

Core rails (everyone): memory, tools, eval, deploy, frontend
My stretch menu (pick later): A2UI, Firestore, RAG Engine, Image Gen
First eval question: "Quais plantas da sua estufa são seguras para gatos e exigem pouca rega?"
