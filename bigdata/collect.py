"""Coletas reais, timestamp de relógio, arquivos imutáveis e manifesto SHA-256."""
import argparse
import csv
import hashlib
import io
import json
import os
import re
import tempfile
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(os.environ.get('PASSO_ROOT') or Path(__file__).resolve().parents[1])
CKAN = 'https://dados.prefeitura.sp.gov.br/api/3/action/package_show?id=dados-do-sp156'
IBGE = 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios/3550308/distritos'


def normalize(s):
    return re.sub(r'\s+', ' ', ''.join(c for c in unicodedata.normalize('NFD', str(s).lower()) if unicodedata.category(c) != 'Mn')).strip()


def session():
    s = requests.Session()
    s.headers['User-Agent'] = 'PassoLivre-Academic/1.0'
    s.mount('https://', HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))
    return s


def stamp():
    return datetime.now(timezone.utc).isoformat()


def save(source, records, meta):
    collected = stamp()
    batch = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder = ROOT / 'bigdata/chegada' / source
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{source}_{batch}.jsonl'
    rows = [{'fonte': source, 'coletado_em': collected, 'lote_id': batch, 'registro': row} for row in records]
    content = ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)
    path.write_text(content, encoding='utf-8')
    manifest = {**meta, 'fonte': source, 'coletado_em_utc': collected, 'lote_id': batch,
                'linhas': len(rows), 'arquivo': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'data_coleta_nao_e_data_referencia': True}
    evidence = ROOT / 'bigdata/evidencias/coletas'
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / f'{source}_{batch}.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    # Sanitized samples only, no street number, CEP, person identifier or raw text.
    samples = ROOT / 'bigdata/amostras'
    samples.mkdir(parents=True, exist_ok=True)
    (samples / f'{source}.jsonl').write_text(''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in rows[:20]), encoding='utf-8')
    return manifest


def collect_ibge():
    r = session().get(IBGE, timeout=60)
    r.raise_for_status()
    rows = [{'distrito_id': str(x['id']), 'distrito': x['nome'], 'distrito_chave': normalize(x['nome']), 'municipio_id': str(x['municipio']['id'])} for x in r.json()]
    return save('ibge', rows, {'url': IBGE, 'licenca': 'Dados públicos IBGE; atribuição à fonte', 'papel': 'Cadastro territorial; não fornece população PCD nesta consulta'})


def collect_weather():
    url = 'https://archive-api.open-meteo.com/v1/archive'
    params = {'latitude': -23.5505, 'longitude': -46.6333, 'start_date': '2026-04-01', 'end_date': '2026-06-30',
              'daily': 'temperature_2m_max,precipitation_sum', 'timezone': 'America/Sao_Paulo'}
    r = session().get(url, params=params, timeout=90)
    r.raise_for_status()
    data = r.json()['daily']
    rows = [{'data': d, 'chuva_mm': data['precipitation_sum'][i], 'temperatura_max_c': data['temperature_2m_max'][i], 'escala': 'municipal_reanalise'} for i,d in enumerate(data['time'])]
    return save('clima', rows, {'url': r.url, 'licenca': 'CC BY 4.0 - Open-Meteo', 'papel': 'Contexto meteorológico agregado; não é chuva medida em cada calçada'})


def collect_sp156():
    s = session()
    response = s.get(CKAN, timeout=60)
    response.raise_for_status()
    package = response.json()['result']
    candidates = [r for r in package['resources'] if r['id'] == '368eb32d-ef25-4441-be8f-fce0146575a1' and r['format'].upper() == 'CSV']
    if len(candidates) != 1:
        raise RuntimeError('Recurso SP156 2º TRI 2026 mudou; conferir catálogo CKAN antes de continuar.')
    resource = candidates[0]
    cache = ROOT / 'bigdata/cache'
    cache.mkdir(parents=True, exist_ok=True)
    # Always fetch anew: a second-day collection must actually contact the source.
    raw = cache / 'sp156_download.csv'
    with s.get(resource['url'], stream=True, timeout=120) as res:
        res.raise_for_status()
        with raw.open('wb') as f:
            for chunk in res.iter_content(1024 * 1024):
                f.write(chunk)
    raw_hash = hashlib.sha256(raw.read_bytes()).hexdigest()
    encoding = 'utf-8-sig'
    try:
        raw.read_bytes().decode(encoding)
    except UnicodeDecodeError:
        encoding = 'cp1252'
    rows=[]
    scanned=0
    with raw.open(encoding=encoding, newline='') as f:
        reader=csv.DictReader(f, delimiter=';')
        for original in reader:
            scanned+=1
            row={normalize(k):v.strip() if v else '' for k,v in original.items() if k}
            subject=normalize(row.get('assunto',''))
            service=normalize(row.get('servico',''))
            if not any(t in subject+' '+service for t in ['calcad','rampa','acessibilidade','entulho','passeio publico']):
                continue
            # Public data has no stable protocol ID. Key within this fixed publication:
            # resource UUID + CSV row number. Preserves identical distinct requests.
            # Republishing/reordering requires full reconciliation; documented limit.
            key=hashlib.sha256(f"{resource['id']}:{scanned}".encode()).hexdigest()
            rows.append({'ocorrencia_id':key, 'linha_fonte':scanned, 'recurso_id':resource['id'],
                         'abertura':row.get('data de abertura'), 'finalizacao':row.get('data de finalizacao'),
                         'servico':row.get('servico'), 'assunto':row.get('assunto'), 'status_original':row.get('status'),
                         'distrito':row.get('distrito'), 'distrito_chave':normalize(row.get('distrito','')),
                         'latitude':row.get('latitude'), 'longitude':row.get('longitude'),
                         'origem':'SP156_PUBLICO', 'ponto_id':None})
    raw.unlink()  # Do not retain raw addresses locally or in Git.
    return save('sp156', rows, {'url':resource['url'], 'recurso_id':resource['id'], 'licenca':package.get('license_title'),
                'linhas_lidas':scanned, 'arquivo_original_sha256':raw_hash, 'encoding':encoding,
                'filtro':'assunto/serviço contém calcad, rampa, acessibilidade, entulho ou passeio publico; sem acentos',
                'periodo_referencia':'2026-04-01 a 2026-06-30', 'chave_limite':'UUID do recurso + posição da linha; não é protocolo. Reordenação de republicação exige reconciliação.'})


def collect_sptrans(token=None):
    token=token or os.getenv('SPTRANS_TOKEN')
    if not token:
        raise RuntimeError('SPTRANS_TOKEN ausente. Fonte opcional não executada.')
    s=session()
    base='https://api.olhovivo.sptrans.com.br/v2.1'
    # Never expose authentication URL or token in logs/errors.
    try:
        auth=s.post(base+'/Login/Autenticar',params={'token':token},timeout=45)
        if auth.status_code != 200 or auth.json() is not True:
            raise RuntimeError('Falha de autenticação SPTrans')
    except requests.RequestException:
        raise RuntimeError('Falha de conexão na autenticação SPTrans') from None
    r=s.get(base+'/Parada/Buscar',params={'termosBusca':os.getenv('SPTRANS_SEARCH','Paulista')},timeout=45)
    r.raise_for_status()
    rows=[{'ponto_id':str(x['cp']), 'nome':x['np'], 'latitude':x['py'], 'longitude':x['px']} for x in r.json()]
    return save('sptrans',rows,{'url':base+'/Parada/Buscar','cobertura':'Busca por termo; API documenta paradas de corredores, não todos os pontos','licenca':'Termos SPTrans; validar antes de redistribuir'})


def verify(manifests):
    for m in manifests:
        path=ROOT/m['arquivo']
        if m['linhas'] <= 0 or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=m['sha256']:
            raise RuntimeError('Arquivo ausente, vazio ou hash divergente: '+m['fonte'])
    return {'status':'ok','fontes':[m['fonte'] for m in manifests]}


if __name__=='__main__':
    from dotenv import load_dotenv
    load_dotenv(ROOT/'.env')
    p=argparse.ArgumentParser()
    p.add_argument('--source',choices=['all','ibge','clima','sp156','sptrans'],default='all')
    args=p.parse_args()
    funcs={'ibge':collect_ibge,'clima':collect_weather,'sp156':collect_sp156,'sptrans':collect_sptrans}
    selected=[funcs[k] for k in ['ibge','clima','sp156']] if args.source=='all' else [funcs[args.source]]
    with ThreadPoolExecutor(max_workers=3) as pool:
        manifests=list(pool.map(lambda f:f(),selected))
    print(json.dumps(verify(manifests),ensure_ascii=False))
    for m in manifests: print(m['fonte'],m['linhas'],m['coletado_em_utc'])
