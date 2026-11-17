# Estado da entrega - 17/11/2026

## Executado e comprovado

- Repositório local com autoria e ficha técnica.
- Ollama local + Qwen2.5 1.5B. Experimento de 16 perguntas em três configurações, base com 11 trechos, limiar calibrado, recall@1 e @3, placar, respostas salvas e cinco erros analisados.
- Avaliação assistida identificou limitações que a métrica automática não captura. O relatório registra tanto os ganhos quanto as falhas.
- API FastAPI testada localmente: assistente, leitura de dados e indicadores.
- Coleta real de SP156, IBGE e Open-Meteo em 17/11/2026.
- Airflow 3 executado com sucesso, cinco tarefas e prints reais de Graph/Grid. A tarefa opcional SPTrans terminou com retorno `nao_configurada`, não coletou dados sem token.
- Pré-validação local de qualidade e cinco consultas SQL. Reexecução local preserva 60.366 registros distintos. Isso não substitui validação Databricks.
- Databricks executado em 17/11: Bronze com 60.653 linhas (60.466 SP156 + 96 IBGE + 91 clima), Prata/Ouro com 60.366 solicitações e quarentena com 100. Três dimensões e cinco consultas executadas; saídas HTML, JSON e auditorias em `bigdata/evidencias/databricks`.
- Exportação real da Ouro baixada e importada para a API local. Primeiro lote enviado pela CLI oficial com OAuth, devido ao bloqueio de controle automático da interface. Registrar o upload do segundo lote pelo Catalog Explorer para a evidência manual do briefing.
- Repetição sem novos arquivos executada com sucesso: Bronze 60.653 → 60.653, incremento zero; Prata/Ouro 60.366 → 60.366. Isso comprova repetição do primeiro lote, não substitui a prova após o segundo dia.

## Falta antes de entregar

| Pendência | Ação |
|---|---|
| Segundo dia de coleta | Manter Docker e computador ligados para o DAG ou executar em 18/11. Conferir com `python -m bigdata.check_collection_days`. Duas execuções no mesmo dia não bastam. |
| Databricks | Primeiro lote concluído. Enviar segundo lote de outro dia e repetir; repetir sem novos arquivos. |
| Evidência Bronze/Prata/Ouro | Salvar contagens das três execuções, qualidade, tabelas e resultados das cinco consultas no Databricks. |
| App do grupo | Ouro real já importada na API local. Integrar endpoints e fotografar tela consumindo dados; conectar assistente e mostrar as fontes. |
| GitHub público | Publicar repositório; inserir URL no README e relatórios. |
| Vídeo GenAI | Gravar demonstração, comparar configurações e explicar erros e limites; adicionar link. |
| PDF Big Data final | Substituir status pendentes por evidências reais, adicionar links e remover a indicação de preliminar somente após completar. |
| Cadastro SPTrans | Opcional para as fontes mínimas; necessário para adicionar paradas/consulta Olho Vivo conforme escopo original. |
| NBR 9050 | Opcional para o corpus inicial; requer edição licenciada antes de incorporar conteúdo normativo. |

## O que não afirmar

- Que a coleta começou dia 13: ela começou dia 17.
- Que duas datas históricas consultadas hoje são dois dias de coleta.
- Que a repetição do primeiro lote comprova dois dias de coleta: o segundo dia ainda está pendente.
- Que foi realizado LoRA ou treinamento de pesos: foi implementada a alternativa agente.
- Que o agente superou o RAG: a métrica por conceitos empatou e a revisão semântica encontrou falhas em ambos.
- Que SP156 representa todos os obstáculos, que status finalizado significa remoção, ou que o mapa garante segurança de trajetos.
- Que houve publicação em GitHub, deploy público ou abertura automática de chamado municipal.

## Prazo

O briefing informa entrega em 19/11/2026 às 23h55. Não exige iniciar dia 13. Dois dias de coleta, 17 e 18, ainda permitem cumprir o requisito, desde que ambas sejam executadas e comprovadas. Não há promessa de execução futura se o computador estiver desligado.
