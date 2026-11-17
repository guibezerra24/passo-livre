# Databricks notebook source
# MAGIC %md
# MAGIC # Passo Livre - Bronze, Prata e Ouro
# MAGIC Guilherme Rezende Bezerra RM 98508 | Gustavo Brisqui RM 97969 | Matheus Brisqui RM 97892
# MAGIC Execute no Databricks Free Edition. As evidências reais ficam em bigdata/evidencias/databricks.
# MAGIC Envie os arquivos para /Volumes/workspace/passo_livre/chegada/{ibge,clima,sp156,sptrans}.
# MAGIC O primeiro lote foi enviado pela CLI oficial com OAuth; a interface bloqueou controle automatizado.
# MAGIC Para a evidência de upload manual pedida no briefing, registre o envio do segundo lote pelo Catalog Explorer.
# MAGIC Execute com lote 1; guarde contagens. Adicione lote 2 de OUTRO DIA DE COLETA; execute; repita sem upload.

# COMMAND ----------
import json
from pyspark.sql import functions as F, Window

CATALOG = 'workspace'
SCHEMA = 'passo_livre'
BASE = f'{CATALOG}.{SCHEMA}'
VOLUME = f'/Volumes/{CATALOG}/{SCHEMA}/chegada'
spark.sql(f'CREATE SCHEMA IF NOT EXISTS {BASE}')
spark.sql(f'CREATE VOLUME IF NOT EXISTS {BASE}.chegada')
spark.sql(f'CREATE VOLUME IF NOT EXISTS {BASE}.exportacao')
spark.sql(f'CREATE TABLE IF NOT EXISTS {BASE}.bronze (payload STRING, arquivo_origem STRING) USING DELTA')
for source in ['ibge', 'clima', 'sp156']:
    dbutils.fs.mkdirs(f'{VOLUME}/{source}')

# COMMAND ----------
# Pare aqui na primeira execução e crie as pastas e faça o upload no Catalog Explorer.
# Os arquivos contêm uma linha JSON por registro, sem JSON multilinha.
before = spark.table(f'{BASE}.bronze').count()
for source in ['ibge', 'clima', 'sp156']:
    spark.sql(f"""
      COPY INTO {BASE}.bronze
      FROM (SELECT value AS payload, _metadata.file_path AS arquivo_origem FROM '{VOLUME}/{source}')
      FILEFORMAT = TEXT
      PATTERN = '*.jsonl'
    """)
after = spark.table(f'{BASE}.bronze').count()
display(spark.createDataFrame([(before, after, after-before)], ['bronze_antes', 'bronze_depois', 'linhas_novas']))
audit = spark.createDataFrame([(before,after,after-before)], ['bronze_antes','bronze_depois','linhas_novas']).withColumn('executado_em',F.current_timestamp())
audit.write.mode('append').saveAsTable(f'{BASE}.auditoria_bronze')
display(spark.table(f'{BASE}.auditoria_bronze').orderBy('executado_em'))

# COMMAND ----------
bronze = spark.table(f'{BASE}.bronze')
def records(source, fields):
    return (bronze.where(F.get_json_object('payload','$.fonte')==source)
            .select(*[F.get_json_object('payload',f'$.registro.{field}').alias(field) for field in fields],
                    F.to_timestamp(F.get_json_object('payload','$.coletado_em')).alias('coletado_em'), 'arquivo_origem'))

districts = records('ibge',['distrito_id','distrito','distrito_chave','municipio_id']).dropDuplicates(['distrito_id'])
districts.createOrReplaceTempView('distritos_lote')
spark.sql(f'CREATE OR REPLACE TABLE {BASE}.dim_distrito AS SELECT distrito_id, distrito, distrito_chave, municipio_id FROM distritos_lote')
weather = records('clima',['data','chuva_mm','temperatura_max_c','escala'])
weather = (weather.withColumn('data',F.to_date('data'))
           .withColumn('chuva_mm',F.expr('try_cast(chuva_mm as double)'))
           .withColumn('temperatura_max_c',F.expr('try_cast(temperatura_max_c as double)')))
w = Window.partitionBy('data').orderBy(F.desc('coletado_em'),F.desc('arquivo_origem'))
weather = weather.withColumn('_rn',F.row_number().over(w)).where('_rn=1').drop('_rn','arquivo_origem')
weather.write.mode('overwrite').option('overwriteSchema','true').saveAsTable(f'{BASE}.prata_clima')

# COMMAND ----------
fields=['ocorrencia_id','abertura','finalizacao','servico','assunto','status_original','distrito_chave','latitude','longitude','origem','ponto_id']
df=records('sp156',fields)
df=(df.withColumn('finalizacao_texto',F.col('finalizacao'))
    .withColumn('abertura',F.to_date(F.try_to_timestamp('abertura',F.lit('dd/MM/yyyy'))))
    .withColumn('finalizacao',F.to_date(F.try_to_timestamp('finalizacao',F.lit('dd/MM/yyyy'))))
    .withColumn('latitude',F.expr('try_cast(latitude as double)'))
    .withColumn('longitude',F.expr('try_cast(longitude as double)'))
    .join(districts.select('distrito_chave','distrito_id'),'distrito_chave','left'))
# Regras independentes: um registro pode violar mais de uma; não somar como total de rejeitados.
rules={
    'id_ausente': F.col('ocorrencia_id').isNull() | (F.length('ocorrencia_id')!=64),
    'abertura_invalida': F.col('abertura').isNull(),
    'finalizacao_invalida': F.col('finalizacao_texto').isNotNull() & (F.trim('finalizacao_texto')!='') & F.col('finalizacao').isNull(),
    'distrito_desconhecido': F.col('distrito_id').isNull(),
    'coordenada_invalida': F.col('latitude').isNull() | F.col('longitude').isNull() | ~F.col('latitude').between(-24,-23) | ~F.col('longitude').between(-47,-46),
    'cronologia_invalida': F.col('finalizacao').isNotNull() & (F.col('finalizacao')<F.col('abertura')),
}
for name, invalid in rules.items():
    df=df.withColumn(name,F.coalesce(invalid,F.lit(True)))
bad=F.lit(False)
for name in rules: bad=bad | F.col(name)
quality=df.agg(*[F.sum(F.col(name).cast('int')).alias(name) for name in rules],F.count('*').alias('avaliados'),F.sum(bad.cast('int')).alias('rejeitados_distintos'))
display(quality)
quality.withColumn('executado_em',F.current_timestamp()).write.mode('append').saveAsTable(f'{BASE}.auditoria_qualidade')
df.where(bad).write.mode('overwrite').option('overwriteSchema','true').saveAsTable(f'{BASE}.quarentena')
valid=df.where(~bad).drop(*rules.keys(),'finalizacao_texto')
w=Window.partitionBy('ocorrencia_id').orderBy(F.desc('coletado_em'),F.desc('arquivo_origem'))
valid=valid.withColumn('_rn',F.row_number().over(w)).where('_rn=1').drop('_rn')
valid.createOrReplaceTempView('ocorrencias_validas')
spark.sql(f'CREATE TABLE IF NOT EXISTS {BASE}.prata_ocorrencias AS SELECT * FROM ocorrencias_validas WHERE 1=0')
spark.sql(f"""MERGE INTO {BASE}.prata_ocorrencias AS alvo USING ocorrencias_validas AS novo
ON alvo.ocorrencia_id=novo.ocorrencia_id
WHEN MATCHED AND novo.coletado_em >= alvo.coletado_em THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *""")
display(spark.table(f'{BASE}.prata_ocorrencias').groupBy('distrito_id').count())

# COMMAND ----------
# Grão: uma solicitação pública por chave técnica da publicação, não um obstáculo único.
# Sem token/GTFS/georreferenciamento validado, ponto_id permanece nulo. Não inventar associação.
spark.sql(f"""CREATE OR REPLACE TABLE {BASE}.dim_servico AS
SELECT sha2(servico,256) AS servico_id, servico, min(assunto) AS assunto FROM {BASE}.prata_ocorrencias GROUP BY servico""")
spark.sql(f"""CREATE OR REPLACE TABLE {BASE}.dim_data AS
SELECT DISTINCT abertura AS data, year(abertura) AS ano, month(abertura) AS mes,
dayofmonth(abertura) AS dia FROM {BASE}.prata_ocorrencias""")
spark.sql(f"""CREATE OR REPLACE TABLE {BASE}.fato_ocorrencias AS
SELECT o.ocorrencia_id, o.distrito_id, sha2(o.servico,256) AS servico_id,
o.abertura AS data, o.finalizacao, o.status_original, o.ponto_id,
round(o.latitude,3) AS latitude_aproximada, round(o.longitude,3) AS longitude_aproximada,
CASE WHEN lower(o.status_original) IN ('finalizada','finalizado') THEN 1 ELSE 0 END AS finalizada,
datediff(o.finalizacao,o.abertura) AS dias_ate_finalizacao,
c.chuva_mm, c.temperatura_max_c, o.origem, o.coletado_em
FROM {BASE}.prata_ocorrencias o LEFT JOIN {BASE}.prata_clima c ON o.abertura=c.data""")
# Sem nome, CPF, telefone, endereço, número ou CEP. Coordenadas arredondadas ~100m:
# não podem orientar desvio exato na calçada. Números de RM são só autoria acadêmica.
display(spark.table(f'{BASE}.fato_ocorrencias').limit(20))

# COMMAND ----------
# Cinco consultas obrigatórias com resultado exibido. Texto de interpretação em docs/BIG_DATA.md.
queries={
 'q1_distritos':f'SELECT d.distrito, count(*) AS solicitacoes FROM {BASE}.fato_ocorrencias f JOIN {BASE}.dim_distrito d USING(distrito_id) GROUP BY d.distrito ORDER BY solicitacoes DESC',
 'q2_servicos':f'SELECT s.servico,count(*) AS solicitacoes FROM {BASE}.fato_ocorrencias f JOIN {BASE}.dim_servico s USING(servico_id) GROUP BY s.servico ORDER BY solicitacoes DESC',
 'q3_impacto':f'SELECT d.distrito,count(*) AS solicitacoes,round(100.0*avg(finalizada),2) AS percentual_finalizadas,round(avg(CASE WHEN finalizada=1 THEN dias_ate_finalizacao END),2) AS media_dias_finalizadas FROM {BASE}.fato_ocorrencias f JOIN {BASE}.dim_distrito d USING(distrito_id) GROUP BY d.distrito ORDER BY solicitacoes DESC',
 'q4_chuva':f"SELECT CASE WHEN chuva_mm IS NULL THEN 'sem_dado' WHEN chuva_mm>=10 THEN '10mm_ou_mais' ELSE 'menos_10mm' END AS faixa_chuva,count(*) AS solicitacoes FROM {BASE}.fato_ocorrencias GROUP BY 1",
 'q5_abertas':f"SELECT d.distrito,count(*) AS solicitacoes_nao_finalizadas FROM {BASE}.fato_ocorrencias f JOIN {BASE}.dim_distrito d USING(distrito_id) WHERE lower(status_original) IN ('aberta','aberto','em andamento') GROUP BY d.distrito ORDER BY solicitacoes_nao_finalizadas DESC",
}
for name,sql in queries.items():
    print(name)
    result=spark.sql(sql)
    display(result)
    result.coalesce(1).write.mode('overwrite').json(f'/Volumes/{CATALOG}/{SCHEMA}/exportacao/{name}')

# COMMAND ----------
# Contrato do produto: exportação REAL da Ouro para baixar no Catalog Explorer.
product=spark.sql(f"""SELECT f.ocorrencia_id,d.distrito,s.servico,f.data,f.status_original,
 f.latitude_aproximada,f.longitude_aproximada,f.chuva_mm,f.origem,f.coletado_em
 FROM {BASE}.fato_ocorrencias f JOIN {BASE}.dim_distrito d USING(distrito_id)
 JOIN {BASE}.dim_servico s USING(servico_id)""")
product.coalesce(1).write.mode('overwrite').json(f'/Volumes/{CATALOG}/{SCHEMA}/exportacao/mvp')
print('Baixe part-*.json de exportacao/mvp. Execute python -m bigdata.import_gold CAMINHO no projeto local.')

# COMMAND ----------
# Evidência persistente de cada execução, inclusive repetição sem novos arquivos.
counts = {name: spark.table(f'{BASE}.{name}').count() for name in [
    'bronze', 'prata_ocorrencias', 'fato_ocorrencias', 'dim_distrito',
    'dim_servico', 'dim_data', 'quarentena', 'prata_clima']}
counts['bronze_antes'] = before
counts['bronze_depois'] = after
counts['linhas_novas'] = after - before
summary = spark.createDataFrame([counts]).withColumn('executado_em', F.current_timestamp())
summary.write.mode('append').saveAsTable(f'{BASE}.auditoria_execucoes')
display(summary)
for name in ['auditoria_bronze', 'auditoria_qualidade', 'auditoria_execucoes']:
    spark.table(f'{BASE}.{name}').coalesce(1).write.mode('overwrite').json(
        f'/Volumes/{CATALOG}/{SCHEMA}/exportacao/{name}')
dbutils.notebook.exit(json.dumps(counts))
