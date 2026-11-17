# Roteiro de demonstração - GenAI e Big Data

## GenAI - roteiro sugerido (o enunciado consultado não fixa duração)

1. Apresentar integrantes, Passo Livre, cidadão beneficiado e mobilidade urbana.
2. Abrir a base: 11 trechos, fontes e licenças; explicar por que a NBR 9050 não foi incorporada.
3. Mostrar as três configurações usando o mesmo modelo local. Explicar que a especialização escolhida é agente, sem alteração de pesos.
4. Demonstrar no Swagger/app uma pergunta sobre os dados necessários para reclamar de ônibus; mostrar JSON e referências.
5. Perguntar uma informação ausente, como o protocolo de um relato não conectado à base. Mostrar recusa.
6. Abrir notebook: recall, limiar, placar e saídas reais. Explicar 37,5% vs. 81,25% por conceitos e 68,75% na revisão assistida mais estrita das configurações com contexto.
7. Mostrar cinco erros do relatório, com causa e proposta de correção. O agente não superou o RAG no teste; explicar o custo da revisão.
8. Mostrar API integrada ao app e README de reprodução. Encerrar com limites e próximos passos.

Não ler respostas de erro como se fossem orientações válidas. Mostrar a indicação de exemplo incorreto.

## Big Data - sequência para evidências

1. Airflow Graph e Grid com execução concluída; destacar tarefas paralelas e conferência final. SPTrans opcional sem token não equivale a coleta.
2. Abrir manifestos de dois dias de coleta diferentes e conferir hashes/contagens.
3. Mostrar Volume com primeiro lote e contagem Bronze inicial.
4. Adicionar segundo lote; executar notebook; mostrar aumento de linhas na Bronze.
5. Reexecutar sem novos arquivos; mostrar incremento zero.
6. Mostrar regras de qualidade, totais por regra e quarentena. Explicar a chave técnica e suas limitações.
7. Mostrar fato, dimensões e cinco consultas com interpretação.
8. Baixar exportação da Ouro, importar e mostrar o app consumindo-a sem o modo preview.
9. Mostrar PDF final e repositório público acessível em janela anônima.
