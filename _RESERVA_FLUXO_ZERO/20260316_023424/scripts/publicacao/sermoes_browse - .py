from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Iterable



def generate_browse_html(rows: Iterable[dict], output_path: Path, title: str = 'Browse de Sermões') -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows_json = json.dumps(list(rows), ensure_ascii=False)
    html = f"""<!doctype html>
<html lang=\"pt-BR\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{escape(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 18px; background: #f6f8fb; color: #1f2937; }}
    h1 {{ margin: 0 0 8px; font-size: 24px; }}
    .summary {{ margin: 8px 0 14px; font-size: 14px; }}
    .context {{ display: inline-block; margin: 0 0 10px; padding: 4px 10px; border-radius: 999px; background: #e7eef8; color: #0f4c81; font-size: 12px; font-weight: 700; }}
    .toolbar {{ display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr auto auto auto auto auto; gap: 8px; margin: 12px 0 16px; }}
    input, select, button {{ padding: 10px 12px; border-radius: 10px; border: 1px solid #cfd8e3; }}
    button {{ cursor: pointer; background: #0f4c81; color: white; border: none; }}
    button.secondary {{ background: #fff; color: #0f4c81; border: 1px solid #0f4c81; }}
    button.warn {{ background: #8a4b08; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; }}
    th, td {{ border-bottom: 1px solid #edf2f7; padding: 10px 8px; text-align: left; vertical-align: top; font-size: 13px; }}
    th {{ position: sticky; top: 0; background: #eef4fb; cursor: pointer; user-select: none; }}
    th.sortable::after {{ content: ' ↕'; color: #6b7280; font-weight: 400; }}
    th.sorted-asc::after {{ content: ' ↑'; color: #0f4c81; font-weight: 700; }}
    th.sorted-desc::after {{ content: ' ↓'; color: #0f4c81; font-weight: 700; }}
    tr:hover {{ background: #f9fbff; }}
    .ok {{ color: #0b7a2f; font-weight: 700; }}
    .bad {{ color: #9b1c1c; font-weight: 800; text-transform: uppercase; }}
    .tag {{ display: inline-block; padding: 2px 8px; border-radius: 999px; background: #eef4fb; }}
    .mono {{ font-family: Consolas, monospace; font-size: 12px; }}
    .small {{ color: #4b5563; font-size: 12px; }}
    .legend {{ margin: 6px 0 14px; color: #4b5563; font-size: 12px; }}
    .artifact-list div {{ margin-bottom: 2px; white-space: nowrap; }}
    .nowrap {{ white-space: nowrap; }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  <div class=\"context\">Contexto atual: sermões formatados</div>
  <div class=\"summary\" id=\"summary\"></div>
  <div class=\"legend\">Filtros cumulativos. Você pode filtrar por grupo e depois ajustar item a item manualmente. Clique nos títulos de coluna para ordenar.</div>
  <div class=\"toolbar\">
    <input id=\"search\" placeholder=\"Buscar por título, slug, série, autor, pasta ou id_base\">
    <select id=\"serie\"><option value=\"\">Todas as séries</option></select>
    <select id=\"autor\"><option value=\"\">Todos os autores</option></select>
    <select id=\"statusManifest\"><option value=\"\">Status manifest</option></select>
    <select id=\"statusExec\"><option value=\"\">Status execução</option></select>
    <button id=\"selectVisible\">Selecionar visíveis</button>
    <button id=\"unselectVisible\" class=\"secondary\">Desmarcar visíveis</button>
    <button id=\"invertVisible\" class=\"secondary\">Inverter visíveis</button>
    <button id=\"clearAll\" class=\"secondary\">Limpar seleção</button>
    <button id=\"download\" class=\"warn\">Baixar seleção JSON</button>
  </div>
  <table>
    <thead>
      <tr>
        <th data-key=\"pick\" class=\"sortable\">Sel.</th>
        <th data-key=\"titulo\" class=\"sortable\">Título</th>
        <th data-key=\"serie\" class=\"sortable\">Série</th>
        <th data-key=\"autor\" class=\"sortable\">Autor</th>
        <th data-key=\"status_manifest\" class=\"sortable\">Status manifest</th>
        <th data-key=\"ultimo_status_execucao\" class=\"sortable\">Status execução</th>
        <th data-key=\"publicado\" class=\"sortable\">Publicado</th>
        <th data-key=\"completo_ok\" class=\"sortable\">Completo</th>
        <th data-key=\"alterado_desde_ultima_execucao\" class=\"sortable\">Alterado</th>
        <th>Artefatos</th>
        <th>Metadados</th>
        <th data-key=\"pasta_relativa\" class=\"sortable\">Pasta</th>
      </tr>
    </thead>
    <tbody id=\"tbody\"></tbody>
  </table>
<script>
const rows = {rows_json};
let currentSort = {{ key: 'titulo', dir: 1 }};
const selectedIds = new Set();
let lastFilteredIds = [];

function uniq(values) {{
  return [...new Set(values.filter(Boolean))].sort((a,b) => String(a).localeCompare(String(b), 'pt-BR'));
}}
function text(v) {{ return String(v ?? ''); }}
function boolLabel(v) {{ return v ? 'sim' : 'NÃO'; }}
function klass(v) {{ return v ? 'ok' : 'bad'; }}
function boolSort(v) {{ return v ? '1' : '0'; }}
function artifactLabel(label, ok) {{ return ok ? label.toLowerCase() : label.toUpperCase(); }}

function fillSelect(id, values) {{
  const sel = document.getElementById(id);
  values.forEach(v => {{
    const opt = document.createElement('option');
    opt.value = v; opt.textContent = v; sel.appendChild(opt);
  }});
}}

fillSelect('serie', uniq(rows.map(r => r.serie)));
fillSelect('autor', uniq(rows.map(r => r.autor)));
fillSelect('statusManifest', uniq(rows.map(r => r.status_manifest)));
fillSelect('statusExec', uniq(rows.map(r => r.ultimo_status_execucao)));

function rowMatches(r) {{
  const q = document.getElementById('search').value.trim().toLowerCase();
  const serie = document.getElementById('serie').value;
  const autor = document.getElementById('autor').value;
  const sm = document.getElementById('statusManifest').value;
  const se = document.getElementById('statusExec').value;
  const hay = [r.titulo, r.rotulo_curto, r.slug_previsto, r.serie, r.autor, r.pasta_origem, r.pasta_relativa, r.id_base, r.observacoes, r.artigo_slug, r.artigo_titulo].join(' ').toLowerCase();
  return (!q || hay.includes(q))
    && (!serie || r.serie === serie)
    && (!autor || r.autor === autor)
    && (!sm || r.status_manifest === sm)
    && (!se || r.ultimo_status_execucao === se);
}}

function getSortValue(r, key) {{
  if (key === 'pick') return selectedIds.has(r.id_base) ? '1' : '0';
  if (key === 'publicado' || key === 'completo_ok' || key === 'alterado_desde_ultima_execucao') return boolSort(r[key]);
  return text(r[key]);
}}

function buildArtifacts(r) {{
  return `<div class=\"artifact-list\">`
    + `<div><span class=\"${{klass(r.html_a4_ok)}}\">${{artifactLabel('A4 HTML', r.html_a4_ok)}}</span></div>`
    + `<div><span class=\"${{klass(r.html_a5_ok)}}\">${{artifactLabel('A5 HTML', r.html_a5_ok)}}</span></div>`
    + `<div><span class=\"${{klass(r.html_tablet_ok)}}\">${{artifactLabel('Tablet HTML', r.html_tablet_ok)}}</span></div>`
    + `<div><span class=\"${{klass(r.docx_a4_ok)}}\">${{artifactLabel('DOCX A4', r.docx_a4_ok)}}</span></div>`
    + `<div><span class=\"${{klass(r.pdf_a4_ok)}}\">${{artifactLabel('PDF A4', r.pdf_a4_ok)}}</span></div>`
    + `<div><span class=\"${{klass(r.pdf_a5_ok)}}\">${{artifactLabel('PDF A5', r.pdf_a5_ok)}}</span></div>`
    + `<div><span class=\"${{klass(r.pdf_tablet_ok)}}\">${{artifactLabel('PDF Tablet', r.pdf_tablet_ok)}}</span></div>`
    + `</div>`;
}}

function buildMetadata(r) {{
  const bdInfo = r.artigo_id
    ? `<div class=\"small\"><strong>BD:</strong> Artigo #${{r.artigo_id}} (${{r.bd_match_kind || 'match'}}) | área→série | autor=${{r.artigo_visivel ? 'visível' : 'oculto'}} </div>`
    : `<div class=\"small\"><strong>BD:</strong> sem match de Artigo</div>`;
  return `
    <div><strong>Slug:</strong> <span class=\"mono\">${{r.slug_previsto || ''}}</span></div>
    <div><strong>Rótulo:</strong> <span class=\"mono\">${{r.rotulo_curto || ''}}</span></div>
    <div class=\"small\"><strong>ID base:</strong> <span class=\"mono\">${{r.id_base || ''}}</span></div>
    <div class=\"small\"><strong>Fontes:</strong> T=${{r.fonte_titulo || ''}} | S=${{r.fonte_serie || ''}} | A=${{r.fonte_autor || ''}}</div>
    ${{bdInfo}}
    <div class=\"small\"><strong>Artigo:</strong> <span class=\"mono\">${{r.artigo_slug || ''}}</span> — ${{r.artigo_titulo || ''}}</div>
    <div class=\"small\"><strong>Media:</strong> <span class=\"mono\">${{r.destino_media_rel || ''}}</span></div>
    <div class=\"small\"><strong>Obs:</strong> ${{r.observacoes || ''}}</div>`;
}}

function updateSummary(filtered) {{
  const visibleSelected = filtered.filter(r => selectedIds.has(r.id_base)).length;
  const bdMatched = filtered.filter(r => r.artigo_id).length;
  document.getElementById('summary').textContent =
    `Itens: ${{rows.length}} | Visíveis: ${{filtered.length}} | Selecionados totais: ${{selectedIds.size}} | Selecionados visíveis: ${{visibleSelected}} | Match BD visíveis: ${{bdMatched}}`;
}}

function updateSortHeaders() {{
  document.querySelectorAll('th[data-key]').forEach(th => {{
    th.classList.remove('sorted-asc', 'sorted-desc');
    if (th.getAttribute('data-key') === currentSort.key) {{
      th.classList.add(currentSort.dir === 1 ? 'sorted-asc' : 'sorted-desc');
    }}
  }});
}}

function render() {{
  const filtered = rows.filter(rowMatches).sort((a,b) => {{
    const va = getSortValue(a, currentSort.key);
    const vb = getSortValue(b, currentSort.key);
    return va.localeCompare(vb, 'pt-BR') * currentSort.dir;
  }});
  lastFilteredIds = filtered.map(r => r.id_base);
  const tbody = document.getElementById('tbody');
  tbody.innerHTML = '';
  filtered.forEach(r => {{
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type=\"checkbox\" class=\"pick\" data-id=\"${{r.id_base}}\" ${{selectedIds.has(r.id_base) ? 'checked' : ''}}></td>
      <td><div><strong>${{r.titulo || ''}}</strong></div><div class=\"mono\">${{r.rotulo_curto || r.id_base || ''}}</div></td>
      <td><span class=\"tag\">${{r.serie || ''}}</span></td>
      <td>${{r.autor || ''}}</td>
      <td>${{r.status_manifest || ''}}</td>
      <td>${{r.ultimo_status_execucao || ''}}</td>
      <td class=\"${{klass(r.publicado)}}\">${{boolLabel(r.publicado)}}</td>
      <td class=\"${{klass(r.completo_ok)}}\">${{boolLabel(r.completo_ok)}}</td>
      <td class=\"${{klass(r.alterado_desde_ultima_execucao)}}\">${{boolLabel(r.alterado_desde_ultima_execucao)}}</td>
      <td class=\"mono nowrap\">${{buildArtifacts(r)}}</td>
      <td>${{buildMetadata(r)}}</td>
      <td class=\"mono\">${{r.pasta_relativa || r.pasta_origem || ''}}</td>
    `;
    tbody.appendChild(tr);
  }});
  updateSummary(filtered);
  updateSortHeaders();
}}

function applyToVisible(fn) {{
  const visibleSet = new Set(lastFilteredIds);
  rows.forEach(r => {{ if (visibleSet.has(r.id_base)) fn(r.id_base); }});
  render();
}}

document.querySelectorAll('input,select').forEach(el => el.addEventListener('input', render));
document.querySelectorAll('th[data-key]').forEach(th => th.addEventListener('click', () => {{
  const key = th.getAttribute('data-key');
  currentSort = {{ key, dir: currentSort.key === key ? currentSort.dir * -1 : 1 }};
  render();
}}));
document.getElementById('selectVisible').addEventListener('click', () => applyToVisible(id => selectedIds.add(id)));
document.getElementById('unselectVisible').addEventListener('click', () => applyToVisible(id => selectedIds.delete(id)));
document.getElementById('invertVisible').addEventListener('click', () => applyToVisible(id => selectedIds.has(id) ? selectedIds.delete(id) : selectedIds.add(id)));
document.getElementById('clearAll').addEventListener('click', () => {{ selectedIds.clear(); render(); }});
document.getElementById('download').addEventListener('click', () => {{
  const payload = {{
    created_at: new Date().toISOString(),
    selected_ids: [...selectedIds],
    filters: {{
      search: document.getElementById('search').value,
      serie: document.getElementById('serie').value,
      autor: document.getElementById('autor').value,
      status_manifest: document.getElementById('statusManifest').value,
      status_execucao: document.getElementById('statusExec').value
    }}
  }};
  const blob = new Blob([JSON.stringify(payload, null, 2)], {{type: 'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'selecionados_atual.json';
  a.click();
}});
document.addEventListener('change', e => {{
  if (e.target.classList.contains('pick')) {{
    const id = e.target.dataset.id;
    if (e.target.checked) selectedIds.add(id); else selectedIds.delete(id);
    render();
  }}
}});
render();
</script>
</body>
</html>"""
    output_path.write_text(html, encoding='utf-8')
