"""Contrato compacto do painel, compartilhado pela API e pela publicação estática."""
from collections import Counter


def build_dashboard(data):
    if data.get('proveniencia') != 'IMPORTACAO_DECLARADA_DATABRICKS':
        raise ValueError('O painel exige exportação real do Databricks.')
    rows = data['registros']
    districts = sorted({r['distrito'] for r in rows})
    services = sorted({r['servico'] for r in rows})
    statuses = sorted({r['status_original'] for r in rows})
    di, si, sti = ({v: i for i, v in enumerate(values)} for values in (districts, services, statuses))
    dates = [r['data'] for r in rows]
    collected = sorted({r['coletado_em'] for r in rows})
    return {
        'versao': 1, 'proveniencia': data['proveniencia'],
        'sha256_exportacao': data['sha256_arquivo'],
        'periodo': {'inicio': min(dates), 'fim': max(dates)},
        'coletas': collected,
        'distritos': districts, 'servicos': services, 'situacoes': statuses,
        'campos': ['distrito_indice','servico_indice','data','situacao_indice','latitude_aproximada','longitude_aproximada'],
        'registros': [[di[r['distrito']], si[r['servico']], r['data'], sti[r['status_original']],
                       r['latitude_aproximada'], r['longitude_aproximada']] for r in rows],
        'total': len(rows), 'contagens_status': dict(Counter(r['status_original'] for r in rows)),
        'aviso': 'Dados históricos e coordenadas aproximadas. Não certificam rotas acessíveis. Finalização administrativa não comprova remoção física.',
    }
