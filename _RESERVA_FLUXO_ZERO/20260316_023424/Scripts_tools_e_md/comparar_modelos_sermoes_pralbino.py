#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comparar modelos (A/B) para gerar sermões/sermonetes a partir do ZIP exportado do Pr. Albino Marks.

✅ Este script NÃO depende do banco de dados. Ele lê um ZIP que contenha:
- dataset_sermoes*.json (preferido), OU
- manifest.json / lista de artigos em JSON, e (se necessário) textos em .txt/.html.

Saída:
- out/<timestamp>/<model>/<slug>__sermao25.md
- out/<timestamp>/<model>/<slug>__sermonete15.md
- out/<timestamp>/relatorio.csv
- out/<timestamp>/relatorio.html
"""

import argparse, os, re, json, zipfile, math, datetime
from pathlib import Path

# ---- OpenAI client (API) ----
def get_openai_client():
    try:
        from openai import OpenAI
    except Exception as e:
        raise SystemExit("Instale a lib: pip install openai\nErro ao importar openai: %s" % e)
    return OpenAI()

def call_model(client, model: str, prompt: str, temperature: float = 0.3, max_output_tokens: int = 8000):
    """
    Usa Responses API (recomendado). Se falhar por incompatibilidade, tenta fallback.
    """
    try:
        resp = client.responses.create(
            model=model,
            input=prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        text = getattr(resp, "output_text", None)
        if text:
            return text
        out = []
        for item in getattr(resp, "output", []) or []:
            if getattr(item, "type", None) == "message":
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", None) == "output_text":
                        out.append(getattr(c, "text", ""))
        return "\n".join(out).strip()
    except Exception as e:
        # Secondary fallback (older style)
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role":"user","content":prompt}],
                temperature=temperature,
                max_tokens=max_output_tokens,
            )
            return resp.choices[0].message.content
        except Exception as e2:
            raise RuntimeError(f"Falha ao chamar modelo {model}: {e}\nFallback também falhou: {e2}")

# ---- Helpers: extraction and metrics ----
VERSE_RE = re.compile(r'\b(?:[1-3]\s*)?[A-Za-zÀ-ÿ]{2,}\s+\d{1,3}:\d{1,3}(?:[-–]\d{1,3})?\b')
ENGLISH_HINT_RE = re.compile(r"\b(challenge|mindset|insight|feedback|performance|coach|goal|targets?)\b", re.IGNORECASE)

def minutes_from_words(words: int, wpm: int) -> float:
    return words / float(wpm)

def trigram_repetition_ratio(text: str) -> float:
    words = re.findall(r"\w+", text.lower())
    if len(words) < 10:
        return 0.0
    trigrams = [" ".join(words[i:i+3]) for i in range(len(words)-2)]
    total = len(trigrams)
    uniq = len(set(trigrams))
    if total == 0:
        return 0.0
    return 1.0 - (uniq/total)

def _read_json_from_zip(z: zipfile.ZipFile, name: str):
    with z.open(name) as f:
        return json.loads(f.read().decode("utf-8"))

def load_articles_from_zip(zip_path: Path):
    """
    Localiza um dataset JSON dentro do ZIP.
    Preferência:
    - dataset_sermoes*.json (pacote heurístico/export com classificação)
    - manifest.json / artigos.json / dataset_artigos.json
    - qualquer json com campos 'titulo' e algum texto
    """
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()

        # 1) dataset_sermoes*.json (preferido)
        ds_candidates = [n for n in names if re.search(r"dataset_sermoes.*\.json$", n)]
        if ds_candidates:
            data = _read_json_from_zip(z, ds_candidates[0])
            articles = []
            for item in data:
                slug = item.get("slug") or str(item.get("id") or "sem-slug")
                titulo = item.get("titulo") or item.get("title") or slug
                area = item.get("area") or item.get("classificacao", {}).get("area") or item.get("classificacao", {}).get("area_sugerida")
                texto = item.get("texto") or item.get("texto_integral") or item.get("conteudo") or item.get("html") or ""
                articles.append({"slug": slug, "titulo": titulo, "area": area, "texto": texto, "raw": item})
            return articles

        # 2) manifest.json
        manifest_candidates = [n for n in names if n.endswith("manifest.json")]
        if manifest_candidates:
            data = _read_json_from_zip(z, manifest_candidates[0])
            items = data.get("artigos", data if isinstance(data, list) else [])
            articles = []
            for it in items:
                slug = it.get("slug") or it.get("id") or it.get("arquivo_base") or "sem-slug"
                titulo = it.get("titulo") or slug
                area = it.get("area") or it.get("classificacao", {}).get("area") or it.get("area_sugerida")
                texto = it.get("texto") or it.get("texto_integral") or it.get("conteudo") or ""
                articles.append({"slug": slug, "titulo": titulo, "area": area, "texto": texto, "raw": it})
            if articles:
                return articles

        # 3) qualquer json parecido
        json_candidates = [n for n in names if n.lower().endswith(".json")]
        for n in json_candidates:
            try:
                data = _read_json_from_zip(z, n)
            except Exception:
                continue
            if isinstance(data, list) and data:
                sample = data[0]
                if isinstance(sample, dict) and ("titulo" in sample or "title" in sample):
                    text_key = None
                    for k in ["texto", "texto_integral", "conteudo", "content", "html", "body"]:
                        if k in sample:
                            text_key = k
                            break
                    if text_key:
                        articles = []
                        for it in data:
                            slug = it.get("slug") or str(it.get("id") or "sem-slug")
                            titulo = it.get("titulo") or it.get("title") or slug
                            area = it.get("area") or it.get("classificacao", {}).get("area") or it.get("area_sugerida")
                            texto = it.get(text_key) or ""
                            articles.append({"slug": slug, "titulo": titulo, "area": area, "texto": texto, "raw": it})
                        return articles

    raise SystemExit("Não encontrei dataset de artigos/sermões dentro do ZIP informado.")

def pick_sample_by_area(articles, per_area: int):
    by_area = {}
    for a in articles:
        area = a.get("area") or "SEM_AREA"
        by_area.setdefault(area, []).append(a)
    picked = []
    for area, items in sorted(by_area.items(), key=lambda x: x[0].lower()):
        picked.extend(items[:per_area])
    return picked

def build_outline_and_anchors(text: str, max_outline: int = 8, max_anchors: int = 10):
    """
    OUTLINE: primeiros parágrafos resumidos.
    ÂNCORAS: frases do artigo com tamanho "pregável" (60-220 chars).
    """
    sents = re.split(r"(?<=[\.\!\?])\s+", (text or "").strip())
    anchors = []
    for s in sents:
        s_clean = re.sub(r"\s+", " ", s).strip()
        if 60 <= len(s_clean) <= 220:
            anchors.append(s_clean)
        if len(anchors) >= max_anchors:
            break

    paras = [p.strip() for p in re.split(r"\n\s*\n", (text or "").strip()) if p.strip()]
    outline = []
    for p in paras[:max_outline]:
        p_one = re.sub(r"\s+", " ", p)
        outline.append(p_one[:160] + ("..." if len(p_one) > 160 else ""))
    return outline, anchors

def build_thesis(titulo: str, outline) -> str:
    # Preferir algo já vindo do texto (outline[0]); fallback: título.
    if outline:
        return outline[0]
    return f"Tema central: {titulo}"

def prompt_blindado_v1(titulo, area, minutes_target: int, wpm: int, tese: str, textos_biblicos, outline, anchors, max_complemento: int = 2):
    words_target = int(minutes_target * wpm)
    # Segurança: evitar lista enorme
    textos_biblicos = list(dict.fromkeys([t.strip() for t in (textos_biblicos or []) if t.strip()]))[:20]
    outline = (outline or [])[:8]
    anchors = (anchors or [])[:10]

    return f"""
Você é um assistente pastoral que prepara sermões FIÉIS ao conteúdo fornecido.

IDIOMA: escreva 100% em Português do Brasil. É PROIBIDO usar palavras/expressões em inglês (ex.: challenge, mindset, insight, feedback, performance, coach, goal). Se houver risco, reescreva.

OBJETIVO
Gerar um sermão com linguagem clara, pastoral, e totalmente ancorado no ARTIGO e nos TEXTOS BÍBLICOS fornecidos.

REGRAS DE FIDELIDADE (obrigatórias)
1) NÃO invente doutrinas, fatos históricos, citações ou afirmações que não estejam no ARTIGO.
2) Textos bíblicos: use SOMENTE os que estão em "TEXTOS_BIBLICOS_DO_ARTIGO".
   - Se precisar acrescentar algum texto bíblico por necessidade de conclusão/apelo, coloque numa seção separada chamada "COMPLEMENTO (fora do artigo)" e limite a no máximo {max_complemento} textos.
3) Inclua no sermão pelo menos 6 “ÂNCORAS DO ARTIGO” (frases curtas exatamente como aparecem no ARTIGO).
   - Marque cada âncora com o símbolo: ⛓️
4) Se algum ponto do sermão for inferência ou aplicação que não está explícita no artigo, rotule como: (Aplicação pastoral).
5) Não repita ideias com palavras diferentes só para “encher”. Seja objetivo.
6) Meta de duração: ~{minutes_target} minutos (~{words_target} palavras, {wpm} palavras/min).

FORMATO OBRIGATÓRIO DE SAÍDA
1) TÍTULO
2) ABERTURA (1 parágrafo)
3) TEXTO BASE (apenas referência, sem copiar o versículo inteiro)
4) ORAÇÃO INICIAL (3–5 linhas)
5) INTRODUÇÃO (1–2 parágrafos)
6) ESBOÇO (3 a 5 pontos principais)
   - cada ponto com: (a) explicação fiel ao artigo, (b) 1 âncora ⛓️, (c) 1 referência bíblica do artigo
7) ILUSTRAÇÃO (opcional) — somente se o artigo contiver alguma imagem/ilustração/analogias; se não houver, escreva “(Sem ilustração no artigo)”.
8) APLICAÇÕES PRÁTICAS (3 a 6 itens) — podem ser (Aplicação pastoral), mas coerentes.
9) APELO FINAL (1 parágrafo)
10) ORAÇÃO FINAL (5–8 linhas)
11) CHECKLIST DE FIDELIDADE
   - [ ] Tese corresponde ao artigo
   - [ ] Usei apenas textos bíblicos do artigo (ou marquei complemento)
   - [ ] Usei pelo menos 6 âncoras ⛓️
   - [ ] Sem palavras em inglês
   - [ ] Sem extrapolações doutrinárias indevidas

DADOS PARA PRODUÇÃO

ARTIGO
Título: {titulo}
Área: {area}

TEMA/TESE DO ARTIGO:
{tese}

TEXTOS_BIBLICOS_DO_ARTIGO:
{", ".join(textos_biblicos) if textos_biblicos else "(nenhum detectado automaticamente — se citar qualquer referência, marque como COMPLEMENTO)"}

ÂNCORAS_DO_ARTIGO (frases exatas — use no corpo do sermão):
- """ + "\n- ".join(anchors) + """

RESUMO ESTRUTURADO DO ARTIGO (pontos principais):
- """ + "\n- ".join(outline) + """

Gere agora o sermão no formato obrigatório.
""".strip()

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def write_text(path: Path, content: str):
    path.write_text(content, encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip-export", required=True, help="Caminho do ZIP exportado (ou pacote heurístico) contendo dataset_sermoes*.json")
    ap.add_argument("--out", required=True, help="Pasta de saída")
    ap.add_argument("--amostra-por-area", type=int, default=1, help="Quantos artigos por área (para teste rápido)")
    ap.add_argument("--models", default="gpt-4o-mini,gpt-4.1-mini,gpt-5-mini", help="Lista de modelos separados por vírgula")
    ap.add_argument("--wpm", type=int, default=130, help="Palavras por minuto (estimativa)")
    ap.add_argument("--temperature", type=float, default=0.3)
    args = ap.parse_args()

    zip_path = Path(args.zip_export)
    out_root = Path(args.out)

    articles = load_articles_from_zip(zip_path)
    sample = pick_sample_by_area(articles, args.amostra_por_area)

    if not sample:
        raise SystemExit("A amostra ficou vazia.")

    client = get_openai_client()
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = out_root / f"ab_test_{ts}"
    ensure_dir(out_dir)

    rows = []

    for art in sample:
        slug = (art.get("slug") or "sem-slug").strip()
        titulo = (art.get("titulo") or slug).strip()
        area = (art.get("area") or "SEM_AREA").strip()
        texto = art.get("texto") or ""

        verses = sorted(set(VERSE_RE.findall(texto)))
        outline, anchors = build_outline_and_anchors(texto, max_outline=8, max_anchors=10)
        tese = build_thesis(titulo, outline)

        for kind, minutes_target, max_out_tokens in [
            ("sermao25", 25, 9000),
            ("sermonete15", 15, 6500),
        ]:
            prompt = prompt_blindado_v1(
                titulo=titulo,
                area=area,
                minutes_target=minutes_target,
                wpm=args.wpm,
                tese=tese,
                textos_biblicos=verses,
                outline=outline,
                anchors=anchors,
            )

            for model in models:
                model_dir = out_dir / model
                ensure_dir(model_dir)

                out_file = model_dir / f"{slug}__{kind}.md"

                try:
                    text_out = call_model(
                        client,
                        model=model,
                        prompt=prompt,
                        temperature=args.temperature,
                        max_output_tokens=max_out_tokens,
                    )
                except Exception as e:
                    # Se um modelo não estiver disponível, registra e pula
                    err = str(e)
                    write_text(out_file, f"# ERRO ao gerar com {model}\n\n{err}\n")
                    rows.append({
                        "slug": slug, "area": area, "titulo": titulo, "tipo": kind, "model": model,
                        "status": "ERRO", "erro": err[:500],
                        "words": 0, "minutes_est": 0.0,
                        "trigram_rep": None, "english_hint": None,
                        "verses_detected_in_output": 0,
                    })
                    continue

                write_text(out_file, text_out)

                words = len(re.findall(r"\w+", text_out))
                minutes_est = minutes_from_words(words, args.wpm)
                trig = trigram_repetition_ratio(text_out)
                english_hint = bool(ENGLISH_HINT_RE.search(text_out))
                verses_out = len(set(VERSE_RE.findall(text_out)))

                rows.append({
                    "slug": slug,
                    "area": area,
                    "titulo": titulo,
                    "tipo": kind,
                    "model": model,
                    "status": "OK",
                    "erro": "",
                    "words": words,
                    "minutes_est": round(minutes_est, 2),
                    "trigram_rep": round(trig, 4),
                    "english_hint": english_hint,
                    "verses_detected_in_output": verses_out,
                })

    # relatório
    try:
        import pandas as pd
        df = pd.DataFrame(rows)
        df.to_csv(out_dir / "relatorio.csv", index=False, encoding="utf-8-sig")
        # html simples
        html = df.to_html(index=False)
        (out_dir / "relatorio.html").write_text(html, encoding="utf-8")
    except Exception:
        # sem pandas, faz csv manual
        import csv
        keys = list(rows[0].keys()) if rows else []
        with open(out_dir / "relatorio.csv", "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        (out_dir / "relatorio.html").write_text("Instale pandas para gerar HTML mais bonito.", encoding="utf-8")

    print(f"[OK] Saída em: {out_dir}")
    print("[DICA] Compare os .md lado a lado e veja relatorio.csv/relatorio.html")

if __name__ == "__main__":
    main()
