# Ficha Técnica do MVP - Passo Livre

| Campo | Definição |
|---|---|
| Produto | Passo Livre |
| Cidadão e território | Pessoas com deficiência, mobilidade reduzida e idosos em São Paulo/SP |
| Problema | Falta de informação organizada sobre barreiras em calçadas e no acesso a pontos de ônibus |
| Proposta de valor | Reunir relatos e dados públicos para acompanhar barreiras e oferecer orientação documental com fontes |
| Arquitetura | App do grupo → API FastAPI → assistente local Ollama + exportação da Ouro; Airflow → arquivos → upload manual → Databricks Bronze/Prata/Ouro |
| Dados executados | SP156 2º trimestre de 2026, distritos do IBGE, clima histórico Open-Meteo |
| Dados opcionais | SPTrans Olho Vivo: conector preparado; token ainda não disponível |
| IA | Qwen2.5 1.5B Q4_K_M local; TF-IDF; RAG; agente limitado com busca, validação e revisão |
| URL pública e GitHub | Ainda não publicados; o repositório desta entrega é local |
| Indicadores | Solicitações por distrito e serviço, percentual de finalização administrativa, tempo médio até finalização e cobertura da base |
| ODS propostos | 10 e 11: inclusão e mobilidade acessível; contribuição a validar com usuários |

## Integrantes

- Guilherme Rezende Bezerra - RM 98508
- Gustavo Brisqui - RM 97969
- Matheus Brisqui - RM 97892

## Limites comuns

Dados históricos de solicitações não certificam a existência atual de um obstáculo. Uma solicitação finalizada pode não significar problema resolvido. Ausência de relatos não comprova passagem livre. Não há cálculo de rotas acessíveis em tempo real neste módulo.

O dado SP156 não oferece protocolo estável no CSV selecionado. A chave técnica combina recurso e número da linha; reordenação na republicação exige reconciliação. As ocorrências não foram associadas a pontos de ônibus: isso depende de cadastro de pontos e validação geográfica. `ponto_id` permanece nulo.

A NBR 9050 não integra a base inicial. Uma cópia licenciada e sua edição precisam ser verificadas antes de incorporar valores normativos. Conteúdos legais são paráfrases com referência, não consultoria jurídica individual.

## Integração prevista com os colegas

O app consome `POST /v1/assistente`, `GET /v1/ocorrencias` e `GET /v1/indicadores`. Visão computacional, robô, RPA, hospedagem pública e pitch são componentes de outros integrantes; não estão implementados neste pacote.

Os endpoints de dados recusam servir uma suposta Ouro quando ela não foi importada. `preview=true` oferece explicitamente a pré-validação local, com a origem identificada na resposta.
