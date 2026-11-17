"""Gera a fotografia pública da Ouro. Não inclui tokens, endereços ou modelo local."""
import json
from pathlib import Path
from api.dashboard import build_dashboard

ROOT = Path(__file__).resolve().parents[1]

def main():
    data = json.loads((ROOT/'bigdata/exportacao/ouro_mvp.json').read_text(encoding='utf-8'))
    dashboard = build_dashboard(data)
    out = ROOT/'web/data/painel.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dashboard,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'Painel público: {dashboard["total"]} registros reais, {out.stat().st_size} bytes.')

if __name__ == '__main__': main()
