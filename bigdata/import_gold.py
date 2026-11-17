"""Importa a exportação real do Databricks para a API. Não aceita preview como Ouro."""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from bigdata.collect import ROOT


def run(path):
    source=Path(path)
    rows=[json.loads(line) for line in source.read_text(encoding='utf-8').splitlines() if line.strip()]
    required={'ocorrencia_id','distrito','servico','data','status_original','latitude_aproximada','longitude_aproximada','origem','coletado_em'}
    if not rows or any(not required<=set(x) for x in rows): raise ValueError('Exportação fora do contrato')
    # Import only expected public fields, dropping extra columns.
    allowed=required|{'chuva_mm'}
    rows=[{k:v for k,v in x.items() if k in allowed} for x in rows]
    out=ROOT/'bigdata/exportacao/ouro_mvp.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({'proveniencia':'IMPORTACAO_DECLARADA_DATABRICKS','sha256_arquivo':hashlib.sha256(source.read_bytes()).hexdigest(),
                              'importado_em':datetime.now(timezone.utc).isoformat(),'registros':rows},ensure_ascii=False),encoding='utf-8')
    print('Importados',len(rows),'registros. Preserve evidência da exportação no Databricks.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('arquivo');run(p.parse_args().arquivo)
