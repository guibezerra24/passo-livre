"""Contrato de integração com o MVP; execução local em loopback por padrão."""
import hmac
import json
import os
import threading
from functools import lru_cache
from pathlib import Path
from typing import Literal

import requests
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from genai.engine import ROOT, Retriever, answer
from api.dashboard import build_dashboard

app=FastAPI(title='Passo Livre - GenAI e Dados',version='1.0.0',description='Assistente documental e contrato de leitura da Ouro. Dados históricos não certificam rotas acessíveis.')
lock=threading.Lock()


def auth(authorization: str | None=Header(default=None)):
    token=os.getenv('API_TOKEN','')
    if token and not hmac.compare_digest(authorization or '', 'Bearer '+token):
        raise HTTPException(401,'Token inválido')


class Question(BaseModel):
    pergunta: str=Field(min_length=4,max_length=1000)
    modo: Literal['sem_contexto','rag','agente']='agente'


@lru_cache(maxsize=1)
def retriever(): return Retriever()


@app.get('/health')
def health(): return {'status':'ok','produto':'Passo Livre','versao':'1.0.0'}


@app.post('/v1/assistente',dependencies=[Depends(auth)])
def assistant(body:Question):
    if not lock.acquire(blocking=False): raise HTTPException(429,'Assistente ocupado; tente novamente.')
    try:
        result=answer(body.pergunta,body.modo,retriever())
        result['fontes_detalhadas']=[{'id':d['id'],'titulo':d['titulo'],'url':d['url']} for d in retriever().docs if d['id'] in result['answer']['fontes']]
        # Raw prompts and model traces stay in evaluation artifacts, not public responses.
        return {k:result[k] for k in ['answer','fontes_detalhadas','seconds','llm_called']}
    except requests.RequestException:
        raise HTTPException(503,'Modelo local indisponível. Verifique Ollama e o modelo configurado.') from None
    finally: lock.release()


def dataset(preview=False):
    path=ROOT/'bigdata/exportacao'/('preview_local.json' if preview else 'ouro_mvp.json')
    if not path.exists():
        raise HTTPException(503,'Exportação não disponível. Execute a coleta e pré-validação local ou importe a Ouro do Databricks.')
    return json.loads(path.read_text(encoding='utf-8'))


@app.get('/v1/ocorrencias',dependencies=[Depends(auth)])
def occurrences(distrito:str|None=None,limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0),preview:bool=False):
    data=dataset(preview)
    rows=data['registros']
    if distrito: rows=[r for r in rows if r['distrito'].casefold()==distrito.casefold()]
    return {'proveniencia':data['proveniencia'],'total':len(rows),'offset':offset,'registros':rows[offset:offset+limit],
            'aviso':'Dados históricos; localização aproximada; não validam rota acessível atual.'}


@app.get('/v1/indicadores',dependencies=[Depends(auth)])
def indicators(preview:bool=False):
    data=dataset(preview)
    rows=data['registros']
    finished=sum(str(r['status_original']).casefold() in ['finalizada','finalizado'] for r in rows)
    return {'proveniencia':data['proveniencia'],'solicitacoes':len(rows),'finalizadas':finished,
            'percentual_finalizadas':round(100*finished/len(rows),2) if rows else None,
            'interpretacao':'Finalização administrativa não comprova remoção física do obstáculo.'}


@app.get('/v1/painel', dependencies=[Depends(auth)])
def dashboard():
    return build_dashboard(dataset())


@app.get('/config.json')
def frontend_config():
    return {'modo':'local', 'dados':'v1/painel', 'assistente':'v1/assistente'}


@app.get('/')
def frontend():
    return FileResponse(ROOT/'web/index.html')


app.mount('/assets', StaticFiles(directory=ROOT/'web/assets', check_dir=False), name='assets')
