from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Iterable


STEP_LABELS = {
    1: 'Baixar anexos do e-mail',
    2: 'Normalizar',
    3: 'Consolidar',
    4: 'Gerar DOCX base',
    5: 'Gerar sermão',
    6: 'Gerar HTMLs',
    7: 'Gerar PDFs',
    8: 'Publicar',
    9: 'Pipeline completo',
}


def generate_browse_html(
    sermon_rows: Iterable[dict],
    output_path: Path,
    title: str = 'Browse de Sermões',
    article_rows: Iterable[dict] | None = None,
    browse_meta: dict | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    datasets_json = json.dumps(
        {
            'sermoes_formatados': list(sermon_rows),
            'artigos_sem_sermao': list(article_rows or []),
        },
        ensure_ascii=False,
    )
    meta_json = json.dumps(browse_meta or {}, ensure_ascii=False)
    step_labels_json = json.dumps(STEP_LABELS, ensure_ascii=False)
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
    .context-chip {{ display: inline-block; margin: 0 0 10px; padding: 4px 10px; border-radius: 999px; background: #e7eef8; color: #0f4c81; font-size: 12px; font-weight: 700; }}
    .context-switch {{ display:flex; gap:8px; margin: 8px 0 10px; flex-wrap:wrap; }}
    .ctx-btn {{ padding: 8px 12px; border-radius: 999px; border: 1px solid #0f4c81; background:#fff; color:#0f4c81; cursor:pointer; font-weight:700; }}
    .ctx-btn.active {{ background:#0f4c81; color:#fff; }}
    .toolbar {{ display: grid; grid-template-columns: 2fr 1fr 1fr 1fr 1fr auto auto auto auto auto; gap: 8px; margin: 12px 0 10px; position: sticky; top: 0; background: #f6f8fb; z-index: 12; padding: 6px 0; }}
    .table-wrap {{ max-height: calc(100vh - 280px); overflow: auto; border-radius: 12px; box-shadow: 0 0 0 1px #e6edf5 inset; }}
    .ops-panel {{ display:none; margin: 6px 0 16px; padding: 12px; background:#fff; border:1px solid #d7e0ea; border-radius:12px; }}
    .ops-top {{ display:grid; grid-template-columns: 1.3fr 1fr; gap: 12px; align-items:start; }}
    .ops-legend {{ font-size: 12px; color:#374151; line-height:1.55; }}
    .ops-hint {{ font-size: 12px; color:#4b5563; margin-top: 6px; }}
    .paths-hint {{ font-size: 12px; color:#4b5563; margin-top: 10px; }}
    .paths-hint .mono {{ display:block; margin-top:3px; }}
    input, select, button {{ padding: 10px 12px; border-radius: 10px; border: 1px solid #cfd8e3; }}
    button {{ cursor: pointer; background: #0f4c81; color: white; border: none; }}
    button.secondary {{ background: #fff; color: #0f4c81; border: 1px solid #0f4c81; }}
    button.warn {{ background: #8a4b08; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; }}
    th, td {{ border-bottom: 1px solid #edf2f7; padding: 10px 8px; text-align: left; vertical-align: top; font-size: 13px; }}
    th {{ position: sticky; top: 0; background: #eef4fb; cursor: pointer; user-select: none; z-index: 5; }}
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
    .muted {{ color:#6b7280; }}
  </style>
</head>
<body>
  <h1>{escape(title)}</h1>
  <div class=\"context-switch\">
    <button id=\"ctxSermoes\" class=\"ctx-btn active\">Sermões formatados</button>
    <button id=\"ctxArtigos\" class=\"ctx-btn\">Artigos sem sermão</button>
  </div>
  <div class=\"context-chip\" id=\"contextChip\">Contexto atual: sermões formatados</div>
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
  <div id=\"opsPanel\" class=\"ops-panel\">
    <div class=\"ops-top\">
      <div>
        <label for=\"operationSpec\"><strong>Operação (artigos)</strong></label>
        <input id=\"operationSpec\" placeholder=\"Ex.: 5 | 3-7 | 1,5,6,7,8\" />
        <div id=\"operationHint\" class=\"ops-hint\">Aceita etapa única, faixa ou lista. Ex.: <span class=\"mono\">5</span>, <span class=\"mono\">3-7</span>, <span class=\"mono\">1,5,6,7,8</span>.</div>
        <div class=\"paths-hint\" id=\"pathsHint\"></div>
      </div>
      <div class=\"ops-legend\" id=\"opsLegend\"></div>
    </div>
  </div>
  <div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th data-key=\"pick\" class=\"sortable\">Sel.</th>
        <th data-key=\"titulo\" class=\"sortable\">Título</th>
        <th data-key=\"serie\" class=\"sortable\">Série</th>
        <th data-key=\"autor\" class=\"sortable\">Autor</th>
        <th data-key=\"status_manifest\" class=\"sortable\">Status manifest</th>
        <th data-key=\"ultimo_status_execucao\" class=\"sortable\">Status execução</th>
        <th data-key=\"publicado\" class=\"sortable\" id=\"hdrPublicado\">Publicado</th>
        <th data-key=\"completo_ok\" class=\"sortable\" id=\"hdrCompleto\">Completo</th>
        <th data-key=\"alterado_desde_ultima_execucao\" class=\"sortable\" id=\"hdrAlterado\">Alterado</th>
        <th id=\"hdrArtefatos\">Artefatos</th>
        <th id=\"hdrMetadados\">Metadados</th>
        <th data-key=\"pasta_relativa\" class=\"sortable\" id=\"hdrPasta\">Pasta</th>
      </tr>
    </thead>
    <tbody id=\"tbody\"></tbody>
  </table>
  </div>
<script>
const datasets = {datasets_json};
const browseMeta = {meta_json};
const stepLabels = {step_labels_json};
let currentContext = 'sermoes_formatados';
let currentSort = {{ key: 'titulo', dir: 1 }};
const selectedByContext = {{
  sermoes_formatados: new Set(),
  artigos_sem_sermao: new Set(),
}};
const opSpecByContext = {{ artigos_sem_sermao: '' }};
let lastFilteredIds = [];

const contextMeta = {{
  sermoes_formatados: {{
    label: 'sermões formatados',
    summaryExtraLabel: 'Match BD visíveis',
    headers: {{ publicado: 'Publicado', completo: 'Completo', alterado: 'Alterado', artefatos: 'Artefatos' }},
  }},
  artigos_sem_sermao: {{
    label: 'artigos sem sermão',
    summaryExtraLabel: 'Pendentes visíveis',
    headers: {{ publicado: 'Visível', completo: 'Sermão', alterado: 'Alterado', artefatos: 'Ação/insumos' }},
  }},
}};

function rows() {{ return datasets[currentContext] || []; }}
function selectedIds() {{ return selectedByContext[currentContext]; }}
function uniq(values) {{ return [...new Set(values.filter(Boolean))].sort((a,b) => String(a).localeCompare(String(b), 'pt-BR')); }}
function text(v) {{ return String(v ?? ''); }}
function boolLabel(v) {{ return v ? 'sim' : 'NÃO'; }}
function klass(v) {{ return v ? 'ok' : 'bad'; }}
function boolSort(v) {{ return v ? '1' : '0'; }}
function artifactLabel(label, ok) {{ return ok ? label.toLowerCase() : label.toUpperCase(); }}

function parseOperationSpec(raw) {{
  const spec = String(raw || '').trim();
  if (!spec) return {{ raw: '', normalized: '', steps: [], labels: [], valid: true, error: '' }};
  const tokens = spec.split(',').map(t => t.trim()).filter(Boolean);
  const steps = [];
  try {{
    tokens.forEach(tok => {{
      if (tok.includes('-')) {{
        const parts = tok.split('-').map(p => p.trim()).filter(Boolean);
        if (parts.length !== 2) throw new Error(`Faixa inválida: ${{tok}}`);
        let a = parseInt(parts[0], 10);
        let b = parseInt(parts[1], 10);
        if (Number.isNaN(a) || Number.isNaN(b)) throw new Error(`Faixa inválida: ${{tok}}`);
        if (a > b) [a, b] = [b, a];
        if (a < 1 || b > 9) throw new Error(`Faixa fora do intervalo 1-9: ${{tok}}`);
        for (let i = a; i <= b; i += 1) steps.push(i);
      }} else {{
        const n = parseInt(tok, 10);
        if (Number.isNaN(n) || n < 1 || n > 9) throw new Error(`Etapa fora do intervalo 1-9: ${{tok}}`);
        steps.push(n);
      }}
    }});
  }} catch (err) {{
    return {{ raw: spec, normalized: '', steps: [], labels: [], valid: false, error: err.message || String(err) }};
  }}
  const uniqSorted = [...new Set(steps)].sort((a,b) => a - b);
  return {{
    raw: spec,
    normalized: uniqSorted.join(','),
    steps: uniqSorted,
    labels: uniqSorted.map(s => `${{s}}. ${{stepLabels[String(s)] || ''}}`),
    valid: true,
    error: ''
  }};
}}

function fillSelect(id, values, emptyLabel) {{
  const sel = document.getElementById(id);
  const current = sel.value;
  sel.innerHTML = '';
  const opt0 = document.createElement('option');
  opt0.value = '';
  opt0.textContent = emptyLabel;
  sel.appendChild(opt0);
  values.forEach(v => {{
    const opt = document.createElement('option');
    opt.value = v; opt.textContent = v; sel.appendChild(opt);
  }});
  if (values.includes(current)) sel.value = current;
}}

function refreshFilters() {{
  const data = rows();
  fillSelect('serie', uniq(data.map(r => r.serie)), 'Todas as séries');
  fillSelect('autor', uniq(data.map(r => r.autor)), 'Todos os autores');
  fillSelect('statusManifest', uniq(data.map(r => r.status_manifest)), 'Status manifest');
  fillSelect('statusExec', uniq(data.map(r => r.ultimo_status_execucao)), 'Status execução');
}}

function resetFilters() {{
  document.getElementById('search').value = '';
  ['serie','autor','statusManifest','statusExec'].forEach(id => document.getElementById(id).value = '');
}}

function rowMatches(r) {{
  const q = document.getElementById('search').value.trim().toLowerCase();
  const serie = document.getElementById('serie').value;
  const autor = document.getElementById('autor').value;
  const sm = document.getElementById('statusManifest').value;
  const se = document.getElementById('statusExec').value;
  const hay = [r.titulo, r.rotulo_curto, r.slug_previsto, r.serie, r.autor, r.pasta_origem, r.pasta_relativa, r.id_base, r.observacoes, r.artigo_slug, r.artigo_titulo, r.workspace_source_types, r.etapa_atual].join(' ').toLowerCase();
  return (!q || hay.includes(q))
    && (!serie || r.serie === serie)
    && (!autor || r.autor === autor)
    && (!sm || r.status_manifest === sm)
    && (!se || r.ultimo_status_execucao === se);
}}

function getSortValue(r, key) {{
  if (key === 'pick') return selectedIds().has(r.id_base) ? '1' : '0';
  if (key === 'publicado' || key === 'completo_ok' || key === 'alterado_desde_ultima_execucao') return boolSort(r[key]);
  return text(r[key]);
}}

function buildArtifacts(r) {{
  if (currentContext === 'artigos_sem_sermao') {{
    const bits = [];
    const spec = r.operacao_recomendada || '';
    bits.push(`<div><span class=\"bad\">GERAR</span> <span class=\"mono\">${{spec || '1-8'}}</span></div>`);
    if (r.workspace_docx_path) bits.push(`<div><span class=\"ok\">docx</span></div>`);
    if (r.workspace_html_path) bits.push(`<div><span class=\"ok\">html</span></div>`);
    if (r.workspace_pdf_path) bits.push(`<div><span class=\"ok\">pdf</span></div>`);
    if (!r.workspace_docx_path && !r.workspace_html_path && !r.workspace_pdf_path) bits.push(`<div><span class=\"bad\">SEM INSUMOS</span></div>`);
    return `<div class=\"artifact-list\">${{bits.join('')}}</div>`;
  }}
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

function secondaryLabel(r) {{
  const label = String(r.rotulo_curto || '').trim();
  const title = String(r.titulo || '').trim();
  if (!label || label === title) return '';
  return `<div class=\"mono\">${{label}}</div>`;
}}

function buildMetadata(r) {{
  if (currentContext === 'artigos_sem_sermao') {{
    return `
      <div><strong>Artigo ID:</strong> <span class=\"mono\">${{r.artigo_id || ''}}</span></div>
      <div><strong>Slug:</strong> <span class=\"mono\">${{r.artigo_slug || ''}}</span></div>
      <div class=\"small\"><strong>Etapa atual:</strong> ${{r.etapa_atual || ''}}</div>
      <div class=\"small\"><strong>Operação sugerida:</strong> <span class=\"mono\">${{r.operacao_recomendada || '1-8'}}</span></div>
      <div class=\"small\"><strong>Fontes locais:</strong> ${{r.workspace_source_types || 'nenhuma'}}</div>
      <div class=\"small\"><strong>Media:</strong> <span class=\"mono\">${{r.destino_media_rel || ''}}</span></div>
      <div class=\"small\"><strong>Obs:</strong> ${{r.observacoes || ''}}</div>`;
  }}
  const bdInfo = r.artigo_id
    ? `<div class=\"small\"><strong>BD:</strong> Artigo #${{r.artigo_id}} (${{r.bd_match_kind || 'match'}})</div>`
    : `<div class=\"small\"><strong>BD:</strong> sem match de Artigo</div>`;
  return `
    <div><strong>Slug:</strong> <span class=\"mono\">${{r.slug_previsto || ''}}</span></div>
    <div><strong>Rótulo:</strong> <span class=\"mono\">${{r.rotulo_curto || ''}}</span></div>
    <div class=\"small\"><strong>Nome sugerido:</strong> <span class=\"mono\">${{r.nome_arquivo_canonico || ''}}</span></div>
    <div class=\"small\"><strong>ID base:</strong> <span class=\"mono\">${{r.id_base || ''}}</span></div>
    <div class=\"small\"><strong>Fontes:</strong> T=${{r.fonte_titulo || ''}} | S=${{r.fonte_serie || ''}} | A=${{r.fonte_autor || ''}}</div>
    ${{bdInfo}}
    <div class=\"small\"><strong>Artigo:</strong> <span class=\"mono\">${{r.artigo_slug || ''}}</span> — ${{r.artigo_titulo || ''}}</div>
    <div class=\"small\"><strong>Media:</strong> <span class=\"mono\">${{r.destino_media_rel || ''}}</span></div>
    <div class=\"small\"><strong>Obs:</strong> ${{r.observacoes || ''}}</div>`;
}}

function updateSummary(filtered) {{
  const data = rows();
  const visibleSelected = filtered.filter(r => selectedIds().has(r.id_base)).length;
  const extra = currentContext === 'sermoes_formatados'
    ? filtered.filter(r => r.artigo_id).length
    : filtered.length;
  document.getElementById('summary').textContent =
    `Itens: ${{data.length}} | Visíveis: ${{filtered.length}} | Selecionados totais: ${{selectedIds().size}} | Selecionados visíveis: ${{visibleSelected}} | ${{contextMeta[currentContext].summaryExtraLabel}}: ${{extra}}`;
}}

function updateSortHeaders() {{
  document.querySelectorAll('th[data-key]').forEach(th => {{
    th.classList.remove('sorted-asc', 'sorted-desc');
    if (th.getAttribute('data-key') === currentSort.key) {{
      th.classList.add(currentSort.dir === 1 ? 'sorted-asc' : 'sorted-desc');
    }}
  }});
}}

function renderOpsPanel() {{
  const panel = document.getElementById('opsPanel');
  const input = document.getElementById('operationSpec');
  const hint = document.getElementById('operationHint');
  const paths = document.getElementById('pathsHint');
  const legend = document.getElementById('opsLegend');
  if (currentContext !== 'artigos_sem_sermao') {{
    panel.style.display = 'none';
    return;
  }}
  panel.style.display = 'block';
  input.value = opSpecByContext.artigos_sem_sermao || '';
  const plan = parseOperationSpec(input.value);
  if (!input.value) {{
    hint.innerHTML = 'Aceita etapa única, faixa ou lista. Ex.: <span class=\"mono\">5</span>, <span class=\"mono\">3-7</span>, <span class=\"mono\">1,5,6,7,8</span>.';
  }} else if (plan.valid) {{
    hint.innerHTML = `Plano interpretado: <span class=\"mono\">${{plan.normalized}}</span><br>${{plan.labels.join('<br>')}}`;
  }} else {{
    hint.innerHTML = `<span class=\"bad\">${{plan.error}}</span>`;
  }}
  legend.innerHTML = Object.keys(stepLabels).sort((a,b)=>Number(a)-Number(b)).map(k => `<div><span class=\"mono\">${{k}}</span>. ${{stepLabels[k]}}</div>`).join('');
  const parts = [];
  if (browseMeta.input_dir_artigos) parts.push(`<strong>InputDirArtigos</strong><span class=\"mono\">${{browseMeta.input_dir_artigos}}</span>`);
  if (browseMeta.workspace_artigos) parts.push(`<strong>WorkspaceArtigos</strong><span class=\"mono\">${{browseMeta.workspace_artigos}}</span>`);
  paths.innerHTML = parts.join('');
}}

function applyContextUi() {{
  document.getElementById('contextChip').textContent = `Contexto atual: ${{contextMeta[currentContext].label}}`;
  document.getElementById('ctxSermoes').classList.toggle('active', currentContext === 'sermoes_formatados');
  document.getElementById('ctxArtigos').classList.toggle('active', currentContext === 'artigos_sem_sermao');
  document.getElementById('hdrPublicado').textContent = contextMeta[currentContext].headers.publicado;
  document.getElementById('hdrCompleto').textContent = contextMeta[currentContext].headers.completo;
  document.getElementById('hdrAlterado').textContent = contextMeta[currentContext].headers.alterado;
  document.getElementById('hdrArtefatos').textContent = contextMeta[currentContext].headers.artefatos;
  renderOpsPanel();
}}

function render() {{
  const data = rows();
  const filtered = data.filter(rowMatches).sort((a,b) => {{
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
      <td><input type=\"checkbox\" class=\"pick\" data-id=\"${{r.id_base}}\" ${{selectedIds().has(r.id_base) ? 'checked' : ''}}></td>
      <td><div><strong>${{r.titulo || ''}}</strong></div>${{secondaryLabel(r)}}</td>
      <td><span class=\"tag\">${{r.serie || ''}}</span></td>
      <td>${{r.autor || ''}}</td>
      <td>${{r.status_manifest || ''}}</td>
      <td>${{r.ultimo_status_execucao || ''}}</td>
      <td class=\"${{klass(r.publicado)}}\">${{boolLabel(r.publicado)}}</td>
      <td class=\"${{klass(r.completo_ok)}}\">${{boolLabel(r.completo_ok)}}</td>
      <td class=\"${{klass(r.alterado_desde_ultima_execucao)}}\">${{boolLabel(r.alterado_desde_ultima_execucao)}}</td>
      <td class=\"mono nowrap\">${{buildArtifacts(r)}}</td>
      <td>${{buildMetadata(r)}}</td>
      <td class=\"mono\">${{r.pasta_relativa || r.pasta_origem || '.'}}</td>
    `;
    tbody.appendChild(tr);
  }});
  updateSummary(filtered);
  updateSortHeaders();
}}

function applyToVisible(fn) {{
  const visibleSet = new Set(lastFilteredIds);
  rows().forEach(r => {{ if (visibleSet.has(r.id_base)) fn(r.id_base); }});
  render();
}}

function switchContext(nextContext) {{
  currentContext = nextContext;
  resetFilters();
  refreshFilters();
  applyContextUi();
  render();
}}

document.querySelectorAll('input,select').forEach(el => {{
  if (el.id !== 'operationSpec') el.addEventListener('input', render);
}});
document.querySelectorAll('th[data-key]').forEach(th => th.addEventListener('click', () => {{
  const key = th.getAttribute('data-key');
  currentSort = {{ key, dir: currentSort.key === key ? currentSort.dir * -1 : 1 }};
  render();
}}));
document.getElementById('selectVisible').addEventListener('click', () => applyToVisible(id => selectedIds().add(id)));
document.getElementById('unselectVisible').addEventListener('click', () => applyToVisible(id => selectedIds().delete(id)));
document.getElementById('invertVisible').addEventListener('click', () => applyToVisible(id => selectedIds().has(id) ? selectedIds().delete(id) : selectedIds().add(id)));
document.getElementById('clearAll').addEventListener('click', () => {{ selectedIds().clear(); render(); }});
document.getElementById('operationSpec').addEventListener('input', e => {{ opSpecByContext.artigos_sem_sermao = e.target.value; renderOpsPanel(); }});
document.getElementById('download').addEventListener('click', () => {{
  const plan = currentContext === 'artigos_sem_sermao' ? parseOperationSpec(opSpecByContext.artigos_sem_sermao) : {{ raw:'', normalized:'', steps:[], labels:[], valid:true, error:'' }};
  const payload = {{
    created_at: new Date().toISOString(),
    current_context: currentContext,
    selected_ids: [...selectedIds()],
    operation_spec: plan.raw,
    operation_plan: {{ normalized: plan.normalized, steps: plan.steps, labels: plan.labels, valid: plan.valid, error: plan.error }},
    browse_meta: browseMeta,
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
    if (e.target.checked) selectedIds().add(id); else selectedIds().delete(id);
    render();
  }}
}});
document.getElementById('ctxSermoes').addEventListener('click', () => switchContext('sermoes_formatados'));
document.getElementById('ctxArtigos').addEventListener('click', () => switchContext('artigos_sem_sermao'));
applyContextUi();
refreshFilters();
render();
</script>
</body>
</html>"""
    output_path.write_text(html, encoding='utf-8')
