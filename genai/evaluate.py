"""Avaliação reproduzível. Métricas automáticas são proxies, não juiz semântico."""
import argparse
import json
import platform
import re
import statistics
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from genai.engine import ROOT, Retriever, answer

OUT = ROOT / 'genai/avaliacao'


def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')


def cases(name):
    return json.loads((OUT / (name + '.json')).read_text(encoding='utf-8'))


def calibrate():
    retriever = Retriever()
    dev = cases('validacao')
    scored = [(x, retriever.search(x['pergunta'])) for x in dev]
    trials = []
    for t in [0.05, 0.08, 0.10, 0.12, 0.15, 0.18, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45]:
        positives = [int(ds[0]['score'] >= t) for c, ds in scored if c['fontes']]
        negatives = [int(ds[0]['score'] < t) for c, ds in scored if not c['fontes']]
        score = (statistics.mean(positives) + statistics.mean(negatives)) / 2
        trials.append({'threshold': t, 'balanced_accuracy_validacao': score})
    best = max(trials, key=lambda r: (r['balanced_accuracy_validacao'], -r['threshold']))
    result = {**best, 'method': 'Maior acurácia balanceada em validação; empate prefere menor limiar para preservar cobertura. Teste não participa do cálculo. Versão 2 exploratória após diagnóstico do piloto.', 'trials': trials,
              'scores': [{'id': c['id'], 'score': ds[0]['score'], 'answerable': bool(c['fontes'])} for c, ds in scored]}
    (OUT / 'limiar.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def retrieval_metrics():
    r = Retriever()
    rows = []
    for c in cases('teste'):
        if c['fontes']:
            found = [d['id'] for d in r.search(c['pergunta'])]
            rows.append({'id': c['id'], 'recall@1': len(set(found[:1]) & set(c['fontes'])) / len(c['fontes']), 'recall@3': len(set(found) & set(c['fontes'])) / len(c['fontes']), 'recuperados': found})
    result = {'n': len(rows), 'recall@1': statistics.mean(x['recall@1'] for x in rows), 'recall@3': statistics.mean(x['recall@3'] for x in rows), 'rows': rows}
    (OUT / 'busca.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def grade(c, result):
    a = result['answer']
    expected_refusal = not c['fontes']
    refused = a['status'] == 'nao_consta'
    keywords = all(any(norm(term) in norm(a['resposta']) for term in alternatives) for alternatives in c['conceitos'])
    citation_hit = bool(set(a['fontes']) & set(c['fontes']))
    return {'acerto_proxy': (refused if expected_refusal else (not refused and keywords)),
            'recusa_esperada': expected_refusal, 'recusou': refused,
            'citacao_correta': (not refused and citation_hit) if not expected_refusal else (refused and not a['fontes']),
            'resposta_indevida_fora_base': expected_refusal and not refused,
            'conceitos_presentes': keywords}


def run():
    calibrate()
    retrieval_metrics()
    r = Retriever()
    output = OUT / 'respostas.jsonl'
    if output.exists():
        import shutil
        pilot=OUT/'piloto'
        pilot.mkdir(exist_ok=True)
        for name in ['respostas.jsonl','placar.json','erros_reais.json']:
            if (OUT/name).exists(): shutil.copy2(OUT/name,pilot/name)
    output.write_text('', encoding='utf-8')
    rows = []
    for mode in ['sem_contexto', 'rag', 'agente']:
        for c in cases('teste'):
            result = answer(c['pergunta'], mode, r)
            row = {'id': c['id'], 'modo': mode, 'pergunta': c['pergunta'], 'gabarito': c, **result, 'metricas': grade(c, result)}
            rows.append(row)
            with output.open('a', encoding='utf-8') as f:
                f.write(json.dumps(row, ensure_ascii=False) + '\n')
            print(mode, c['id'], row['metricas']['acerto_proxy'], flush=True)
    scoreboard = []
    for mode in ['sem_contexto', 'rag', 'agente']:
        sub = [x for x in rows if x['modo'] == mode]
        outside = [x for x in sub if x['metricas']['recusa_esperada']]
        scoreboard.append({'modo': mode, 'n': len(sub),
                          'acerto_proxy': statistics.mean(x['metricas']['acerto_proxy'] for x in sub),
                          'contrato_valido_primeira_geracao': statistics.mean(x['valid_json'] for x in sub if x['llm_called']) if any(x['llm_called'] for x in sub) else None,
                          'citacao_correta': statistics.mean(x['metricas']['citacao_correta'] for x in sub),
                          'resposta_indevida_fora_base': statistics.mean(x['metricas']['resposta_indevida_fora_base'] for x in outside),
                          'latencia_media_s': statistics.mean(x['seconds'] for x in sub),
                          'perguntas_com_llm': sum(x['llm_called'] for x in sub),
                          'chamadas_llm': sum(len(x.get('attempts',[])) for x in sub)})
    (OUT / 'placar.json').write_text(json.dumps({'executado_em_utc': datetime.now(timezone.utc).isoformat(), 'python': platform.python_version(), 'limite': 'Acerto por conceitos e resposta indevida fora da base são proxies. Citação válida não prova fundamentação semântica.', 'configuracoes': scoreboard}, ensure_ascii=False, indent=2), encoding='utf-8')
    errors = [x for x in rows if not x['metricas']['acerto_proxy'] or not x['metricas']['citacao_correta'] or not x['valid_json']]
    (OUT / 'erros_reais.json').write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--retrieval-only', action='store_true')
    args = p.parse_args()
    if args.retrieval_only:
        print(calibrate())
        print(retrieval_metrics())
    else:
        run()
