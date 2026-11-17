from fastapi.testclient import TestClient
from api.dashboard import build_dashboard
from api.main import app


def sample():
    return {'proveniencia':'IMPORTACAO_DECLARADA_DATABRICKS','sha256_arquivo':'hash',
            'registros':[{'distrito':'Sé','servico':'Calçada','data':'2026-04-01','status_original':'Aberto',
                          'latitude_aproximada':-23.55,'longitude_aproximada':-46.63,'coletado_em':'2026-11-17T12:00:00Z',
                          'cpf':'nao_publicar','endereco':'nao_publicar'}]}


def test_dashboard_preserves_records_and_excludes_personal_fields():
    result=build_dashboard(sample())
    assert result['total']==1
    row=result['registros'][0]
    assert result['distritos'][row[0]]=='Sé'
    assert result['servicos'][row[1]]=='Calçada'
    assert row[4:]==[-23.55,-46.63]
    assert 'nao_publicar' not in str(result)
    assert result['contagens_status']=={'Aberto':1}


def test_dashboard_api_requires_auth_and_real_dataset(monkeypatch):
    monkeypatch.setenv('API_TOKEN','chave-teste')
    monkeypatch.setattr('api.main.dataset',lambda:sample())
    client=TestClient(app)
    assert client.get('/v1/painel').status_code==401
    result=client.get('/v1/painel',headers={'Authorization':'Bearer chave-teste'})
    assert result.status_code==200 and result.json()['total']==1
    assert client.get('/').status_code==200
    assert client.get('/config.json').json()['modo']=='local'
