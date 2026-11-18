# Passo Livre | GenAI e Big Data

Mapa colaborativo de barreiras em calçadas e pontos de ônibus para pessoas com deficiência, idosos e pessoas com mobilidade reduzida em São Paulo. Este repositório contém os módulos de **Generative AI for Engineering** e **Big Data Architecture & Data Integration** da GS 2026.2, FIAP 4ES.

**[Abrir painel público](https://guibezerra24.github.io/passo-livre/)** · **[Código no GitHub](https://github.com/guibezerra24/passo-livre)** · [Como executar o app local](docs/APP.md)

O painel mostra uma fotografia real da Ouro: **60.366 solicitações**, 96 distritos, coleta de **18/11/2026**. Big Data foi executado com coletas reais dos dias **17 e 18/11**, Bronze com **121.306 linhas** e reexecução sem incremento. A versão local integra o assistente com fontes; a versão pública não executa o modelo local. [Relatório final Big Data](docs/Passo_Livre_Big_Data_FINAL.pdf) · [Evidências do segundo lote](docs/LOTE2.md).

## Ficha Técnica

| Campo | Definição |
|---|---|
| Cidadão e território | Pessoas com deficiência, idosos e mobilidade reduzida; São Paulo/SP |
| Problema | Informação fragmentada sobre barreiras em calçadas e acesso ao transporte |
| Valor | Organizar relatos, acompanhar solicitações e orientar com fontes |
| Componentes | Airflow → Volume → Databricks → API; base documental → busca → LLM local → revisão |
| Fontes | SP156, IBGE, Open-Meteo; SPTrans opcional com token |
| IA | Qwen2.5 1.5B local; RAG e agente de busca/validação/revisão |
| URL e repositório público | [Painel](https://guibezerra24.github.io/passo-livre/) e [GitHub](https://github.com/guibezerra24/passo-livre) |
| Indicadores | Volume, finalização administrativa, tempo de atendimento e qualidade dos dados |
| ODS | 10 e 11, contribuição proposta a validar |

Detalhes e limites: [Ficha Técnica](docs/FICHA_TECNICA.md).

## Integrantes

- Guilherme Rezende Bezerra - RM 98508
- Gustavo Brisqui - RM 97969
- Matheus Brisqui - RM 97892

## Comece aqui

1. Leia [o estado da entrega](docs/STATUS.md).
2. Para IA: [relatório GenAI](docs/GENAI.md) e notebook com saídas em `genai/notebooks`.
3. Para dados: [roteiro Big Data](docs/BIG_DATA.md) e notebook Databricks em `bigdata/databricks`.
4. Os scripts usam dados reais e registram datas reais. Não há prints, notas, protocolos ou métricas inventados.

## Instalação local

Python 3.12 ou 3.13. Na pasta deste README:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Instale o [Ollama](https://ollama.com/download) e baixe o mesmo modelo da avaliação:

```powershell
ollama pull qwen2.5:1.5b
```

O modelo é executado localmente. Os pesos não estão no repositório. Variáveis: `OLLAMA_URL`, `OLLAMA_MODEL` e `API_TOKEN`. O experimento foi realizado com Qwen2.5 1.5B Q4_K_M, licença Apache 2.0. Não houve treinamento de pesos: a especialização usa a alternativa **agente** aceita na rubrica.

```powershell
.venv/Scripts/python.exe -m genai.evaluate --retrieval-only
.venv/Scripts/python.exe -m genai.evaluate
.venv/Scripts/python.exe -m bigdata.collect
.venv/Scripts/python.exe -m bigdata.preview
.venv/Scripts/python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000/` para usar o app e `http://127.0.0.1:8000/docs` para testar a API. Para a tela local usar a Ouro, importe a exportação real do Databricks. O painel público inclui uma fotografia minimizada já gerada. A consulta com `preview=true` nos endpoints antigos serve apenas para integração local e informa isso na resposta.

```powershell
.venv/Scripts/python.exe -m pytest -q
```

## Organização

```text
api/                    API do assistente e dados para o app
web/                    tela responsiva, mapa, filtros e fotografia pública
scripts/                geração da fotografia pública a partir da Ouro
genai/base/             trechos, fontes e licenças
genai/avaliacao/        validação, teste, respostas reais, placar e erros
genai/notebooks/        notebook com saídas salvas
bigdata/dags/           DAG Airflow 3
bigdata/databricks/     Bronze, Prata, Ouro e cinco consultas
bigdata/amostras/       amostras públicas minimizadas
bigdata/evidencias/     manifestos e pré-validação identificada
docs/                   ficha técnica, relatórios e pendências
tests/                  contrato, autenticação e qualidade
```

## Publicação e entrega

Repositório **público** em `guibezerra24/passo-livre`. A branch `main` contém os módulos e a branch `gh-pages` recebe apenas `web/`. Nunca envie `.env`, tokens, dados brutos pessoais, volumes, logs com credenciais ou os pesos do modelo. A pasta `bigdata/chegada` é local e ignorada pelo Git; envie-a manualmente ao Databricks. Os RM fazem parte da autoria exigida. Metadados privados do workspace Databricks ficam fora da publicação; auditorias numéricas e consultas estão disponíveis.

GenAI: link do GitHub no Teams, com notebook com saídas, base, testes, API, README e relatório no repositório. O briefing consultado não exige explicitamente vídeo nem fixa duração; uma gravação pode complementar a demonstração. Big Data: PDF final com evidências e GitHub no Teams. Prazo informado no briefing: **19/11/2026 às 23h55**. Manter links acessíveis durante a correção, por até uma semana após o encerramento.

O painel público é estático e deve ser atualizado após cada importação da Ouro; consulte [o roteiro de atualização](docs/APP.md). Não há abertura de chamados municipais nem emissão de rotas garantidas neste módulo.
