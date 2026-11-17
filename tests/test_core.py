import json
import pytest
from fastapi.testclient import TestClient
from genai.engine import Answer,Retriever,validate_grounding
from bigdata.preview import clean
from api.main import app


def test_retrieval_and_unknown_citation():
    docs=Retriever().search('Quais dados devo informar na reclamação de um ônibus?')
    assert 'SPRECL' in [x['id'] for x in docs]
    assert validate_grounding({'status':'respondido','resposta':'teste','fontes':['INVENTADA']},docs)


def test_contract_rejects_wrong_status():
    with pytest.raises(ValueError): Answer(status='talvez',resposta='x',fontes=[])


def test_quality_and_no_personal_fields():
    raw={'coletado_em':'2026-11-17T00:00:00+00:00','registro':{'ocorrencia_id':'a'*64,'abertura':'01/04/2026','finalizacao':'02/04/2026','servico':'Calçada','status_original':'Finalizada','distrito_chave':'se','latitude':'-23.55','longitude':'-46.63','cpf':'nao_publicar'}}
    out,errors=clean(raw,{'se':{'distrito':'Sé','distrito_id':'355030885'}})
    assert not errors and 'cpf' not in out and out['dias']==1
    raw['registro']['latitude']='0'
    assert 'coordenada_invalida' in clean(raw,{'se':{'distrito':'Sé','distrito_id':'355030885'}})[1]
    raw['registro']['abertura']='data inválida'
    assert 'abertura_invalida' in clean(raw,{})[1]


def test_api_security_and_validation(monkeypatch):
    monkeypatch.setenv('API_TOKEN','teste-local')
    client=TestClient(app)
    assert client.get('/health').status_code==200
    assert client.get('/v1/indicadores').status_code==401
    assert client.post('/v1/assistente',headers={'Authorization':'Bearer teste-local'},json={'pergunta':'a','modo':'rag'}).status_code==422
    assert client.get('/v1/ocorrencias?limit=10000',headers={'Authorization':'Bearer teste-local'}).status_code==422


def test_agent_refuses_after_invalid_citations(monkeypatch):
    import genai.engine as engine
    calls=[]
    def fake_generate(messages):
        calls.append(messages)
        return json.dumps({'status':'respondido','resposta':'Afirmação sem fonte','fontes':['INVENTADA']}),{}
    monkeypatch.setattr(engine,'generate',fake_generate)
    result=engine.answer('Qual direito ao transporte a pessoa com mobilidade reduzida possui?','agente')
    assert len(calls)==2
    assert result['answer']['status']=='nao_consta'
    assert result['answer']['fontes']==[]


def test_grader_does_not_credit_citation_on_false_refusal():
    from genai.evaluate import grade
    case={'fontes':['LBI46'],'conceitos':[['igualdade']]}
    result={'answer':{'status':'nao_consta','resposta':'Não consta','fontes':['LBI46']}}
    assert not grade(case,result)['citacao_correta']
