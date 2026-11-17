"""Confere datas REAIS de coleta, sem aceitar data de referência como coleta."""
import json
from datetime import datetime,timedelta,timezone
from bigdata.collect import ROOT

def check():
    result={}
    for source in ['ibge','clima','sp156']:
        manifests=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'bigdata/evidencias/coletas').glob(source+'_*.json')]
        days=sorted({datetime.fromisoformat(m['coletado_em_utc']).astimezone(timezone(timedelta(hours=-3))).date().isoformat() for m in manifests})
        result[source]={'dias_coleta_sao_paulo':days,'minimo_dois_dias':len(days)>=2}
    return {'atende':all(x['minimo_dois_dias'] for x in result.values()),'fontes':result}

if __name__=='__main__':
    result=check()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    raise SystemExit(0 if result['atende'] else 2)
