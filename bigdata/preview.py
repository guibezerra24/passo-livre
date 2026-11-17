"""Pré-validação LOCAL. SQLite não substitui evidências de Airflow/Databricks."""
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from bigdata.collect import ROOT, normalize


def read_source(source):
    files=sorted((ROOT/'bigdata/chegada'/source).glob('*.jsonl'))
    if not files: raise RuntimeError('Coleta ausente: '+source)
    for file in files:
        for line in file.read_text(encoding='utf-8').splitlines():
            yield json.loads(line)


def parse_date(value):
    if not value: return None
    try: return datetime.strptime(value,'%d/%m/%Y').date().isoformat()
    except ValueError: return None


def clean(row,districts):
    r=row['registro']
    reasons=[]
    opened=parse_date(r.get('abertura'))
    closed=parse_date(r.get('finalizacao'))
    district=districts.get(r.get('distrito_chave'))
    try: lat,lon=float(r.get('latitude')),float(r.get('longitude'))
    except (TypeError,ValueError): lat,lon=None,None
    if not r.get('ocorrencia_id') or len(r['ocorrencia_id'])!=64: reasons.append('id_ausente')
    if not opened: reasons.append('abertura_invalida')
    if r.get('finalizacao') and not closed: reasons.append('finalizacao_invalida')
    if not district: reasons.append('distrito_desconhecido')
    if lat is None or lon is None or not (-24<=lat<=-23 and -47<=lon<=-46): reasons.append('coordenada_invalida')
    if closed and opened and closed<opened: reasons.append('cronologia_invalida')
    if reasons: return None,reasons
    return {'ocorrencia_id':r['ocorrencia_id'],'distrito':district['distrito'],'distrito_id':district['distrito_id'],
            'servico':r['servico'],'data':opened,'finalizacao':closed,'status_original':r['status_original'],
            'finalizada':int(normalize(r['status_original']) in ['finalizada','finalizado']),
            'dias':(datetime.fromisoformat(closed)-datetime.fromisoformat(opened)).days if closed else None,
            'latitude_aproximada':round(lat,3),'longitude_aproximada':round(lon,3),
            'origem':'SP156_PUBLICO','coletado_em':row['coletado_em']},[]


def run():
    districts={r['registro']['distrito_chave']:r['registro'] for r in read_source('ibge')}
    climate={r['registro']['data']:r['registro'] for r in read_source('clima')}
    valid={}
    counts=Counter({k:0 for k in ['id_ausente','abertura_invalida','finalizacao_invalida','distrito_desconhecido','coordenada_invalida','cronologia_invalida','avaliados','rejeitados_distintos']})
    for row in read_source('sp156'):
        counts['avaliados']+=1
        obj,errors=clean(row,districts)
        counts.update(errors)
        if errors:
            counts['rejeitados_distintos']+=1
        else:
            obj['chuva_mm']=climate.get(obj['data'],{}).get('chuva_mm')
            old=valid.get(obj['ocorrencia_id'])
            if old is None or obj['coletado_em']>=old['coletado_em']: valid[obj['ocorrencia_id']]=obj
    db=sqlite3.connect(':memory:')
    db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE fato(ocorrencia_id TEXT PRIMARY KEY,distrito TEXT,distrito_id TEXT,servico TEXT,data TEXT,finalizacao TEXT,status_original TEXT,finalizada INT,dias INT,latitude_aproximada REAL,longitude_aproximada REAL,origem TEXT,coletado_em TEXT,chuva_mm REAL)')
    cols=list(next(iter(valid.values())).keys())
    sql=f'INSERT OR REPLACE INTO fato ({",".join(cols)}) VALUES ({",".join("?" for _ in cols)})'
    db.executemany(sql,[[r[c] for c in cols] for r in valid.values()])
    n1=db.execute('SELECT count(*) FROM fato').fetchone()[0]
    db.executemany(sql,[[r[c] for c in cols] for r in valid.values()])
    n2=db.execute('SELECT count(*) FROM fato').fetchone()[0]
    queries={
       'q1_distritos':'SELECT distrito,count(*) AS solicitacoes FROM fato GROUP BY distrito ORDER BY solicitacoes DESC',
       'q2_servicos':'SELECT servico,count(*) AS solicitacoes FROM fato GROUP BY servico ORDER BY solicitacoes DESC',
       'q3_impacto':'SELECT distrito,count(*) AS solicitacoes,round(100.0*avg(finalizada),2) AS percentual_finalizadas,round(avg(CASE WHEN finalizada=1 THEN dias END),2) AS media_dias_finalizadas FROM fato GROUP BY distrito ORDER BY solicitacoes DESC',
       'q4_chuva':"SELECT CASE WHEN chuva_mm IS NULL THEN 'sem_dado' WHEN chuva_mm>=10 THEN '10mm_ou_mais' ELSE 'menos_10mm' END AS faixa_chuva,count(*) AS solicitacoes FROM fato GROUP BY 1",
       'q5_abertas':"SELECT distrito,count(*) AS solicitacoes_nao_finalizadas FROM fato WHERE lower(status_original) IN ('aberta','aberto','em andamento') GROUP BY distrito ORDER BY solicitacoes_nao_finalizadas DESC",
    }
    results={name:{'sql_local':query,'rows':[dict(r) for r in db.execute(query)]} for name,query in queries.items()}
    evid=ROOT/'bigdata/evidencias'
    evid.mkdir(parents=True,exist_ok=True)
    report={'ambiente':'PRE_VALIDACAO_LOCAL_SQLITE_NAO_DATABRICKS','executado_em':datetime.now(timezone.utc).isoformat(),
            'qualidade':dict(counts),'validos_distintos':len(valid),'idempotencia_local':{'antes':n1,'depois_reexecucao':n2},'consultas':results}
    (evid/'pre_validacao_local.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    export=ROOT/'bigdata/exportacao'
    export.mkdir(parents=True,exist_ok=True)
    (export/'preview_local.json').write_text(json.dumps({'proveniencia':'PRE_VALIDACAO_LOCAL_NAO_OURO_DATABRICKS','registros':list(valid.values())},ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='consultas'},ensure_ascii=False,indent=2))


if __name__=='__main__': run()
