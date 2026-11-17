# App Passo Livre

## Dois modos de execução

- **Local:** FastAPI serve a tela e os dados reais da Ouro em `GET /v1/painel`; `POST /v1/assistente` usa Ollama local. A interface não envia perguntas a um provedor de LLM remoto.
- **Público:** GitHub Pages serve a mesma tela com uma fotografia minimizada da Ouro em `web/data/painel.json`. O assistente fica explicitamente indisponível nessa versão; nenhum endpoint do computador é exposto.

Publicação prevista: https://guibezerra24.github.io/passo-livre/ . Código: https://github.com/guibezerra24/passo-livre . A confirmação da publicação está em STATUS.md.

## Abrir localmente

Na raiz do repositório, com as dependências instaladas e a exportação Ouro importada:

```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8001
```

Abra http://127.0.0.1:8001 . Para o assistente, mantenha Ollama em execução com `qwen2.5:1.5b`. Se `API_TOKEN` estiver configurado, a tela pede a chave. Ela fica em memória da aba, sem armazenamento persistente.

## Recursos

Mapa OpenStreetMap/Leaflet, filtros combinados por distrito/situação/serviço, busca sem distinção de acentos, lista paginada, seleção do registro no mapa, estado vazio, falhas de conexão, indicadores globais e seção de fontes. A lista oferece os mesmos dados sem depender da interação com o mapa. A interface adapta-se a celular e computador, usa rótulos e foco visível; isso não equivale a certificação de acessibilidade.

O mapa exibe os primeiros 300 registros do filtro (abertura mais recente primeiro); a lista permite percorrer todos. Coordenadas aproximadas podem coincidir. A contagem mede solicitações administrativas, não obstáculos únicos. Não há criação de relatos ou cálculo de rota neste módulo.

## Atualizar após o segundo lote

1. Executar o notebook Databricks após o upload do segundo dia e baixar a nova Ouro.
2. Importar: `python -m bigdata.import_gold CAMINHO_DO_PART_JSON`.
3. Gerar a fotografia pública: `python -m scripts.build_public`.
4. Verificar localmente os dados e a data exibida. Executar `python -m pytest -q`.
5. Registrar as alterações e publicar `main`; executar `git subtree push --prefix web origin gh-pages`.

A fotografia pública contém somente índices de distrito/serviço/situação, data de abertura e coordenadas arredondadas. Mantém o SHA-256 da exportação de origem. Não inclui nome, contato, endereço, número, CEP, textos livres ou credenciais.

Leaflet 1.9.4 está incluído em `web/assets/vendor`, com licença BSD-2-Clause. Os mapas-base vêm de OpenStreetMap, com atribuição visível e dependência de conexão. As fontes de dados e licenças estão em BIG_DATA.md.
