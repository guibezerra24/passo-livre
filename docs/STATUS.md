# Estado da entrega - 18/11/2026

## Big Data: execução final concluída

- Três fontes externas reais: SP156, IBGE e Open-Meteo; coletas em 17 e 18/11, com manifestos, datas e hashes conferidos.
- Airflow 3: DAG diário, coletas paralelas e verificação final; Graph/Grid reais salvos. SPTrans opcional sem token, não coletada.
- Lote 1 enviado por CLI oficial; lote 2 enviado manualmente pelo integrante. Os três arquivos remotos do lote 2 foram baixados e seus hashes coincidiram com os originais locais.
- Databricks: segundo lote carregado com sucesso. Bronze 60.653 → 121.306. Reexecução sem upload: 121.306 → 121.306, zero novas linhas.
- Prata e fato Ouro: 60.366 solicitações válidas; 96 distritos, 20 serviços e 91 datas. Seis regras e MERGE executados.
- Quarentena: 200 versões de linhas, correspondentes às mesmas 100 solicitações inválidas repetidas nos dois lotes. As contagens de regras se sobrepõem.
- Cinco consultas executadas e resultados exportados. Ouro importada no app; painel público atualizado para a coleta de 18/11.
- [PDF final](Passo_Livre_Big_Data_FINAL.pdf), [GitHub público](https://github.com/guibezerra24/passo-livre) e [painel](https://guibezerra24.github.io/passo-livre/).

## GenAI

Implementação local e avaliação concluídas: Qwen2.5 1.5B, base com 11 trechos, 16 perguntas em três configurações, recall, placar e análise de erros. O vídeo solicitado ao grupo ainda não foi recebido nesta conversa. Não afirmar entrega de GenAI sem vincular a gravação e submeter no Teams.

## Ação do grupo

Entregar o PDF final de Big Data no Teams da disciplina, por um integrante, até 19/11/2026 às 23h55. A submissão ao Teams não foi realizada pelo assistente. Manter GitHub e painel públicos durante a correção.

## Limites e diferença em relação ao briefing

- A rubrica pede upload pela interface. O lote 1 usou CLI oficial/OAuth; o lote 2 foi manual pela interface. Isso está explicitado no PDF.
- Agendamento depende do computador ligado. Em 18/11, a execução de 9h começou às 11h41 após iniciar o ambiente. Notificação em log, sem canal externo.
- Recorte histórico de abril a junho de 2026; a coleta diária não significa novos registros a cada dia.
- Chave por UUID do recurso e posição da linha: o CSV original manteve o mesmo hash entre os dois dias, mas republicações reordenadas exigem reconciliação.
- Status finalizado não garante remoção física; mapa aproximado não garante segurança de trajetos. Não há abertura automática de chamados.
- Assistente local, sem modelo em execução no GitHub Pages. Não houve LoRA; a especialização usa a alternativa agente.
