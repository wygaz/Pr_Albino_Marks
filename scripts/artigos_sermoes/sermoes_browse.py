from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Iterable


STEP_LABELS = {
    1: "Extrair artigos",
    2: "Preparar ambiente operacional",
    3: "Gerar prompts de imagem [Artigos]",
    4: "Gerar imagens [Artigos]",
    5: "Gerar PDFs de artigos [Artigos]",
    6: "Publicar artigos [Artigos]",
    7: "Gerar relatorio tecnico [Sermoes]",
    8: "Gerar sermao [Sermoes]",
    9: "Exportar formatos [Sermoes]",
    10: "Pipeline completo [Sermoes] (roda 6,7,8,9 e 11)",
    11: "Republicar artefatos existentes [Sermoes]",
}


HTML_TEMPLATE = """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE__</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 8px; background: #f6f8fb; color: #1f2937; }
    h1 { margin: 0; font-size: 18px; }
    .topbar { position:sticky; top:0; z-index:20; background:#f6f8fb; padding-bottom:4px; }
    .top { display:flex; justify-content:space-between; gap:6px; flex-wrap:wrap; margin-bottom:3px; align-items:flex-start; }
    .sw, .acts, .mini { display:flex; gap:5px; flex-wrap:wrap; align-items:center; }
    .actcol { display:flex; flex-direction:column; align-items:flex-end; gap:4px; position:relative; }
    .colsbox { min-width: 620px; }
    .ctx { padding:5px 9px; border-radius:999px; border:1px solid #0f4c81; background:#fff; color:#0f4c81; cursor:pointer; font-weight:700; }
    .ctx.a { background:#0f4c81; color:#fff; }
    button { cursor:pointer; background:#0f4c81; color:#fff; border:none; border-radius:10px; padding:6px 9px; }
    button.s { background:#fff; color:#0f4c81; border:1px solid #0f4c81; }
    button.w { background:#8a4b08; }
    input, select { padding:6px 8px; border-radius:10px; border:1px solid #cfd8e3; min-width:0; }
    .chip { display:inline-block; margin:0 0 4px; padding:3px 9px; border-radius:999px; background:#e7eef8; color:#0f4c81; font-size:12px; font-weight:700; }
    .summary, .small { font-size:11px; color:#6b7280; }
    .ops { display:block; margin:3px 0 4px; padding:4px 6px; background:#fff; border:1px solid #d7e0ea; border-radius:12px; }
    .opsg { display:grid; grid-template-columns:minmax(0,2fr) minmax(300px,1fr); gap:8px; align-items:start; }
    .toolbar { display:grid; grid-template-columns:1fr; gap:5px; margin:4px 0 5px; align-items:center; }
    .filters { display:grid; grid-template-columns:repeat(5, minmax(120px,1fr)); gap:5px; }
    .search { position:relative; }
    .search span { position:absolute; left:9px; top:50%; transform:translateY(-50%); font-size:12px; color:#6b7280; }
    .search input { padding-left:28px; width:100%; }
    .box { border:1px solid #dbe4ee; background:#fbfdff; border-radius:10px; padding:5px; }
    .pills { display:flex; gap:5px; flex-wrap:wrap; min-height:24px; }
    .pill { display:inline-flex; gap:6px; align-items:center; padding:3px 8px; border-radius:999px; background:#e7eef8; color:#0f4c81; font-size:12px; }
    details summary { cursor:pointer; font-size:12px; color:#0f4c81; font-weight:700; list-style:none; }
    details summary::-webkit-details-marker { display:none; }
    details .grid { display:grid; grid-template-columns:repeat(5,minmax(90px,1fr)); gap:4px 8px; padding-top:4px; }
    .wrap { max-height:calc(100vh - 145px); overflow:auto; border-radius:12px; box-shadow:0 0 0 1px #e6edf5 inset; background:#fff; }
    table { width:100%; border-collapse:collapse; background:#fff; }
    th, td { border-bottom:1px solid #edf2f7; padding:6px 5px; text-align:left; vertical-align:top; font-size:11px; }
    th { position:sticky; top:0; background:#eef4fb; cursor:pointer; user-select:none; z-index:5; }
    th.sort::after { content:' ↕'; color:#6b7280; }
    th.a::after { content:' ↑'; color:#0f4c81; }
    th.d::after { content:' ↓'; color:#0f4c81; }
    th.n { width:32px; min-width:32px; text-align:center; padding:3px 2px; }
    th.n .v { writing-mode:vertical-rl; transform:rotate(180deg); white-space:nowrap; }
    .c { text-align:center; }
    .ok { color:#0b7a2f; font-weight:700; }
    .bad { color:#9b1c1c; font-weight:800; text-transform:uppercase; }
    .tag { display:inline-block; padding:2px 8px; border-radius:999px; background:#eef4fb; }
    .mono { font-family:Consolas,monospace; font-size:11px; }
    .art div { margin-bottom:2px; white-space:nowrap; }
    .hide { display:none; }
    .flyout { position:absolute; top:36px; right:0; z-index:30; background:#fff; border:1px solid #dbe4ee; border-radius:10px; box-shadow:0 10px 30px rgba(15,76,129,.12); padding:6px 8px; }
    .flyout summary { display:inline-block; padding:4px 8px; border-radius:10px; border:1px solid #0f4c81; background:#fff; color:#0f4c81; }
    .flyout[open] summary { margin-bottom:4px; }
    @media (max-width:1360px) { .filters { grid-template-columns:repeat(3,minmax(180px,1fr)); } details .grid { grid-template-columns:repeat(3,minmax(110px,1fr)); } .colsbox { min-width: 420px; } }
    @media (max-width:1100px) { .toolbar { grid-template-columns:1fr 1fr; } .filters { display:grid; grid-template-columns:1fr 1fr; } .opsg { grid-template-columns:1fr; } details .grid { grid-template-columns:repeat(2,minmax(110px,1fr)); } .colsbox { min-width: 280px; } .wrap { max-height:calc(100vh - 210px); } }
  </style>
</head>
<body>
<div class="topbar">
<div class="top"><h1>__TITLE__</h1><div class="actcol"><div class="acts"><button id="rf" class="s">Atualizar</button><button id="sv">Selecionar visiveis</button><button id="dv" class="s">Desmarcar visiveis</button><button id="iv" class="s">Inverter visiveis</button><button id="cl" class="s">Limpar selecao</button><button id="dl" class="w">Salvar selecao JSON</button><button id="ex" class="w">Executar steps</button></div><details class="small colsbox flyout"><summary>Colunas e paths</summary><div class="grid" style="padding-top:4px"><label><input type="checkbox" data-col-toggle="serie" checked> Serie</label><label><input type="checkbox" data-col-toggle="autor" checked> Autor</label><label><input type="checkbox" data-col-toggle="status_manifest" checked> Status manifest</label><label><input type="checkbox" data-col-toggle="status_exec" checked> Status execucao</label><label><input type="checkbox" data-col-toggle="publicado" checked> Publicado</label><label><input type="checkbox" data-col-toggle="bd_docx" checked> BD DOCX</label><label><input type="checkbox" data-col-toggle="bd_pdf" checked> BD PDF</label><label><input type="checkbox" data-col-toggle="bd_img" checked> BD IMG</label><label><input type="checkbox" data-col-toggle="completo" checked> Sermao</label><label><input type="checkbox" data-col-toggle="alterado" checked> Alterado</label><label><input type="checkbox" data-col-toggle="artefatos" checked> Artefatos</label><label><input type="checkbox" data-col-toggle="metadados" checked> Metadados</label><label><input type="checkbox" data-col-toggle="pasta" checked> Pasta</label></div><div class="small" id="paths" style="margin-top:4px"></div></details></div></div>
<div class="sw"><button id="cs" class="ctx a">Sermoes formatados</button><button id="ca" class="ctx">Artigos sem sermao</button></div>
<div class="mini"><div class="chip" id="chip">Contexto atual: sermoes formatados</div><div class="chip" id="selinfo">Selecionados: 0 de 0</div></div><div class="summary" id="sum"></div>
<div id="ops" class="ops"><div class="opsg"><div>
<div class="box"><div class="mini"><label for="sp"><strong>Steps</strong></label><select id="sp"></select><button id="add">Adicionar</button><button id="clr" class="s">Limpar</button></div><div class="pills" id="pills"></div><div class="small" id="hint">Escolha os steps pelo dropdown.</div></div>
</div><div id="kindsBox"><div class="box"><div><strong>Tipos de publicacao</strong></div><div class="mini" style="margin-top:4px"><label><input type="checkbox" id="all"> ALL</label><label><input type="checkbox" id="docx"> DOCX</label><label><input type="checkbox" id="pdf"> PDF</label><label><input type="checkbox" id="img"> IMG</label></div></div></div></div></div>
<div class="toolbar"><div class="search"><span>🔎</span><input id="q" placeholder="Buscar por titulo, slug, serie, autor, pasta ou id_base"></div><div class="filters"><select id="serie"><option value="">Todas as series</option></select><select id="autor"><option value="">Todos os autores</option></select><select id="sm"><option value="">Status manifest</option></select><select id="se"><option value="">Status execucao</option></select><select id="pend"><option value="">Pendencias</option><option value="any">Qualquer pendencia</option><option value="docx">Falta DOCX no BD</option><option value="pdf">Falta PDF no BD</option><option value="img">Falta imagem no BD</option></select></div></div>
</div>
<div class="wrap"><table><thead><tr><th data-key="pick" class="n"><input type="checkbox" id="allv" title="Selecionar ou desmarcar visiveis"></th><th data-key="titulo" class="sort" data-col="titulo">Titulo</th><th data-key="serie" class="sort" data-col="serie">Serie</th><th data-key="autor" class="sort" data-col="autor">Autor</th><th data-key="status_manifest" class="sort" data-col="status_manifest">Status manifest</th><th data-key="ultimo_status_execucao" class="sort" data-col="status_exec">Status execucao</th><th data-key="publicado" class="sort n" data-col="publicado" id="hp"><span class="v">Publicado</span></th><th data-key="publicado_docx" class="sort n" data-col="bd_docx" id="hd"><span class="v">BD DOCX</span></th><th data-key="publicado_pdf" class="sort n" data-col="bd_pdf" id="hf"><span class="v">BD PDF</span></th><th data-key="publicado_img" class="sort n" data-col="bd_img" id="hi"><span class="v">BD IMG</span></th><th data-key="completo_ok" class="sort n" data-col="completo" id="hc"><span class="v">Completo</span></th><th data-key="alterado_desde_ultima_execucao" class="sort n" data-col="alterado" id="ha"><span class="v">Alterado</span></th><th data-col="artefatos" id="har">Artefatos</th><th data-col="metadados" id="hmd">Metadados</th><th data-key="pasta_relativa" class="sort" data-col="pasta">Pasta</th></tr></thead><tbody id="tb"></tbody></table></div>
<script>
const helperBase=window.location.origin;
const ds=__DATASETS__,meta=__META__,stepLabels=__STEP_LABELS__,defaultSelectionPath=__DEFAULT_SELECTION_PATH__;
let ctx='sermoes_formatados',sort={key:'titulo',dir:1},last=[];
const sel={sermoes_formatados:new Set(),artigos_sem_sermao:new Set()},steps={sermoes_formatados:[10],artigos_sem_sermao:[]},pk={sermoes_formatados:['all'],artigos_sem_sermao:['all']},cols={titulo:true,serie:true,autor:true,status_manifest:true,status_exec:true,publicado:true,bd_docx:true,bd_pdf:true,bd_img:true,completo:true,alterado:true,artefatos:true,metadados:true,pasta:true};
let activeJobPoll=null;
const cm={sermoes_formatados:{label:'sermoes formatados',extra:'Match BD visiveis',heads:{publicado:'Publicado',completo:'Completo',alterado:'Alterado',artefatos:'Artefatos'}},artigos_sem_sermao:{label:'artigos sem sermao',extra:'Pendentes visiveis',heads:{publicado:'Publicado',completo:'Sermao',alterado:'Alterado',artefatos:'Acao/insumos'}}};
const allowedSteps={sermoes_formatados:[9,10,11],artigos_sem_sermao:[1,2,3,4,5,6,7,8,9,10,11]};
const rows=()=>ds[ctx]||[],picked=()=>sel[ctx],text=v=>String(v??''),bool=v=>v?'sim':'nao',klass=v=>v?'ok':'bad',boolSort=v=>v?'1':'0';
function uniq(a){return [...new Set(a.filter(Boolean))].sort((x,y)=>String(x).localeCompare(String(y),'pt-BR'));}
function plan(raw){const s=String(raw||'').trim();if(!s)return{raw:'',normalized:'',steps:[],labels:[],valid:true,error:''};const t=s.split(',').map(x=>x.trim()).filter(Boolean),st=[];try{t.forEach(tok=>{if(tok.includes('-')){let p=tok.split('-').map(x=>x.trim()).filter(Boolean);if(p.length!==2)throw new Error(`Faixa invalida: ${tok}`);let a=parseInt(p[0],10),b=parseInt(p[1],10);if(Number.isNaN(a)||Number.isNaN(b))throw new Error(`Faixa invalida: ${tok}`);if(a>b)[a,b]=[b,a];if(a<1||b>11)throw new Error(`Faixa fora do intervalo 1-11: ${tok}`);for(let i=a;i<=b;i++)st.push(i);}else{let n=parseInt(tok,10);if(Number.isNaN(n)||n<1||n>11)throw new Error(`Etapa fora do intervalo 1-11: ${tok}`);st.push(n);}});}catch(e){return{raw:s,normalized:'',steps:[],labels:[],valid:false,error:e.message||String(e)};}const u=[...new Set(st)].sort((a,b)=>a-b);return{raw:s,normalized:u.join(','),steps:u,labels:u.map(n=>`${n}. ${stepLabels[String(n)]||''}`),valid:true,error:''};}
function curPlan(context){return plan(((steps[context]||[]).sort((a,b)=>a-b)).join(','));}
function getKinds(){if(document.getElementById('all').checked)return['all'];const r=[];if(document.getElementById('docx').checked)r.push('docx');if(document.getElementById('pdf').checked)r.push('pdf');if(document.getElementById('img').checked)r.push('img');return r.length?r:['all'];}
function articlePlan(r){const done=r.publicado_docx&&r.publicado_pdf&&r.publicado_img;if(done)return{label:'OK',kind:'ok'};const op=(r.operacao_recomendada||'').trim();if(op)return{label:op,kind:'bad'};return{label:'1-6',kind:'bad'};}
function fill(id,vals,empty){const s=document.getElementById(id),cur=s.value;s.innerHTML='';const o=document.createElement('option');o.value='';o.textContent=empty;s.appendChild(o);vals.forEach(v=>{const x=document.createElement('option');x.value=v;x.textContent=v;s.appendChild(x);});if(vals.includes(cur))s.value=cur;}
function refresh(){const d=rows();fill('serie',uniq(d.map(r=>r.serie)),'Todas as series');fill('autor',uniq(d.map(r=>r.autor)),'Todos os autores');fill('sm',uniq(d.map(r=>r.status_manifest)),'Status manifest');fill('se',uniq(d.map(r=>r.ultimo_status_execucao)),'Status execucao');}
function match(r){const q=document.getElementById('q').value.trim().toLowerCase(),serie=document.getElementById('serie').value,autor=document.getElementById('autor').value,sm=document.getElementById('sm').value,se=document.getElementById('se').value,p=document.getElementById('pend').value;const hay=[r.titulo,r.rotulo_curto,r.slug_previsto,r.serie,r.autor,r.pasta_origem,r.pasta_relativa,r.id_base,r.observacoes,r.artigo_slug,r.artigo_titulo,r.workspace_source_types,r.etapa_atual].join(' ').toLowerCase();let pok=true;if(ctx==='artigos_sem_sermao'){if(p==='any')pok=!(r.publicado_docx&&r.publicado_pdf&&r.publicado_img);else if(p==='docx')pok=!r.publicado_docx;else if(p==='pdf')pok=!r.publicado_pdf;else if(p==='img')pok=!r.publicado_img;}return(!q||hay.includes(q))&&(!serie||r.serie===serie)&&(!autor||r.autor===autor)&&(!sm||r.status_manifest===sm)&&(!se||r.ultimo_status_execucao===se)&&pok;}
function gsv(r,k){if(k==='pick')return picked().has(r.id_base)?'1':'0';if(['publicado','publicado_docx','publicado_pdf','publicado_img','completo_ok','alterado_desde_ultima_execucao'].includes(k))return boolSort(r[k]);return text(r[k]);}
function articleSortValue(r){return text(r.pasta_relativa||r.workspace_docx_path||r.titulo);}
function arts(r){if(ctx==='artigos_sem_sermao'){const b=[],pl=articlePlan(r);b.push(`<div><span class="${pl.kind}">${pl.label==='OK'?'OK':'GERAR'}</span> <span class="mono">${pl.label}</span></div>`);if(r.workspace_docx_path)b.push('<div><span class="ok">docx</span></div>');if(r.workspace_pdf_path)b.push('<div><span class="ok">pdf</span></div>');if(r.workspace_image_path)b.push('<div><span class="ok">img</span></div>');if(!r.workspace_docx_path&&!r.workspace_pdf_path&&!r.workspace_image_path)b.push('<div><span class="bad">SEM INSUMOS</span></div>');return `<div class="art">${b.join('')}</div>`;}return `<div class="art"><div><span class="${klass(r.html_a4_ok)}">${r.html_a4_ok?'a4 html':'A4 HTML'}</span></div><div><span class="${klass(r.html_a5_ok)}">${r.html_a5_ok?'a5 html':'A5 HTML'}</span></div><div><span class="${klass(r.html_tablet_ok)}">${r.html_tablet_ok?'tablet html':'TABLET HTML'}</span></div><div><span class="${klass(r.docx_a4_ok)}">${r.docx_a4_ok?'docx a4':'DOCX A4'}</span></div><div><span class="${klass(r.pdf_a4_ok)}">${r.pdf_a4_ok?'pdf a4':'PDF A4'}</span></div></div>`;}
function metaBox(r){if(ctx==='artigos_sem_sermao'){const pl=articlePlan(r);return `<div><strong>Artigo ID:</strong> <span class="mono">${r.artigo_id||''}</span></div><div><strong>Slug:</strong> <span class="mono">${r.artigo_slug||''}</span></div><div class="small"><strong>Etapa atual:</strong> ${r.etapa_atual||''}</div><div class="small"><strong>Operacao sugerida:</strong> <span class="mono">${pl.label}</span></div><div class="small"><strong>Tipo sugerido:</strong> <span class="mono">${r.publish_kind_recomendado||'all'}</span></div><div class="small"><strong>Obs:</strong> ${r.observacoes||''}</div>`;}const bd=r.artigo_id?`<div class="small"><strong>BD:</strong> Artigo #${r.artigo_id}</div>`:`<div class="small"><strong>BD:</strong> sem match</div>`;return `<div><strong>Slug:</strong> <span class="mono">${r.slug_previsto||''}</span></div>${bd}`;}
function updSum(f){const d=rows(),vs=f.filter(r=>picked().has(r.id_base)).length,extra=ctx==='sermoes_formatados'?f.filter(r=>r.artigo_id).length:f.filter(r=>!(r.publicado_docx&&r.publicado_pdf&&r.publicado_img)).length;document.getElementById('selinfo').textContent=`Selecionados: ${picked().size} de ${d.length}`;document.getElementById('sum').textContent=`Itens: ${d.length} | Visiveis: ${f.length} | Selecionados visiveis: ${vs} | ${cm[ctx].extra}: ${extra}`;}
function hdrs(){document.querySelectorAll('th[data-key]').forEach(th=>{th.classList.remove('a','d');if(th.getAttribute('data-key')===sort.key)th.classList.add(sort.dir===1?'a':'d');});}
function syncAll(){const t=last.length,s=last.filter(id=>picked().has(id)).length,h=document.getElementById('allv');h.checked=t>0&&s===t;h.indeterminate=s>0&&s<t;}
function applyCols(){document.querySelectorAll('[data-col]').forEach(el=>{el.classList.toggle('hide',!cols[el.getAttribute('data-col')]);});}
function syncKinds(){const ks=new Set(pk[ctx]||['all']);document.getElementById('all').checked=ks.has('all');document.getElementById('docx').checked=ks.has('all')||ks.has('docx');document.getElementById('pdf').checked=ks.has('all')||ks.has('pdf');document.getElementById('img').checked=ks.has('all')||ks.has('img');}
function syncStepOptions(){const sp=document.getElementById('sp');const allowed=allowedSteps[ctx]||[];sp.innerHTML='<option value="">Step...</option>'+allowed.map(k=>`<option value="${k}">${k}. ${stepLabels[String(k)]}</option>`).join('');}
function syncSteps(){const h=document.getElementById('pills');h.innerHTML='';const st=[...(steps[ctx]||[])].sort((a,b)=>a-b);st.forEach(n=>{const removable=(allowedSteps[ctx]||[]).length>1;const x=removable?` <button type="button" class="s" data-rm="${n}" style="padding:0 6px;border-radius:999px;">x</button>`:'';const p=document.createElement('span');p.className='pill';p.innerHTML=`${n}. ${stepLabels[String(n)]}${x}`;h.appendChild(p);});const p=curPlan(ctx);document.getElementById('hint').innerHTML=st.length?`Plano: <span class="mono">${p.normalized}</span><br>${p.labels.join('<br>')}`:'Escolha os steps pelo dropdown.';}
function buildSelectionPayload(){const p=curPlan(ctx);return{created_at:new Date().toISOString(),current_context:ctx,selected_ids:[...picked()],publish_kinds:ctx==='artigos_sem_sermao'?(pk[ctx]||['all']):['all'],operation_spec:p.raw,operation_plan:{normalized:p.normalized,steps:p.steps,labels:p.labels,valid:p.valid,error:p.error},browse_meta:meta,filters:{search:document.getElementById('q').value,serie:document.getElementById('serie').value,autor:document.getElementById('autor').value,status_manifest:document.getElementById('sm').value,status_execucao:document.getElementById('se').value,pending_filter:document.getElementById('pend').value},save_path:defaultSelectionPath};}
function ops(){document.getElementById('ops').style.display='block';syncStepOptions();syncSteps();document.getElementById('kindsBox').style.display=ctx==='artigos_sem_sermao'?'':'none';syncKinds();const parts=[];if(ctx==='sermoes_formatados'&&meta.input_dir)parts.push(`<strong>InputDirSermoes</strong><br><span class="mono">${meta.input_dir}</span>`);if(meta.input_dir_artigos)parts.push(`<strong>InputDirArtigos</strong><br><span class="mono">${meta.input_dir_artigos}</span>`);if(meta.workspace_artigos)parts.push(`<strong>WorkspaceArtigos</strong><br><span class="mono">${meta.workspace_artigos}</span>`);parts.push(`<strong>SelectionFile</strong><br><span class="mono">${defaultSelectionPath}</span>`);document.getElementById('paths').innerHTML=parts.join('<br>');}
function ui(){document.getElementById('chip').textContent=`Contexto atual: ${cm[ctx].label}`;document.getElementById('cs').classList.toggle('a',ctx==='sermoes_formatados');document.getElementById('ca').classList.toggle('a',ctx==='artigos_sem_sermao');document.getElementById('hp').innerHTML=`<span class="v">${cm[ctx].heads.publicado}</span>`;document.getElementById('hc').innerHTML=`<span class="v">${cm[ctx].heads.completo}</span>`;document.getElementById('ha').innerHTML=`<span class="v">${cm[ctx].heads.alterado}</span>`;document.getElementById('har').textContent=cm[ctx].heads.artefatos;document.getElementById('pend').style.display=ctx==='artigos_sem_sermao'?'':'none';['hd','hf','hi'].forEach(id=>document.getElementById(id).style.display=ctx==='artigos_sem_sermao'?'':'none');ops();}
function render(){const d=rows(),f=d.filter(match).sort((a,b)=>{if(ctx==='artigos_sem_sermao'){const ap=picked().has(a.id_base)?0:1,bp=picked().has(b.id_base)?0:1;if(ap!==bp)return ap-bp;}const av=(ctx==='artigos_sem_sermao'&&sort.key==='pasta_relativa')?articleSortValue(a):gsv(a,sort.key);const bv=(ctx==='artigos_sem_sermao'&&sort.key==='pasta_relativa')?articleSortValue(b):gsv(b,sort.key);return av.localeCompare(bv,'pt-BR')*sort.dir;});last=f.map(r=>r.id_base);const tb=document.getElementById('tb');tb.innerHTML='';f.forEach(r=>{const tr=document.createElement('tr');tr.innerHTML=`<td class="c"><input type="checkbox" class="pick" data-id="${r.id_base}" ${picked().has(r.id_base)?'checked':''}></td><td data-col="titulo"><div><strong>${r.titulo||''}</strong></div>${(r.rotulo_curto&&r.rotulo_curto!==r.titulo)?`<div class="mono">${r.rotulo_curto}</div>`:''}</td><td data-col="serie"><span class="tag">${r.serie||''}</span></td><td data-col="autor">${r.autor||''}</td><td data-col="status_manifest">${r.status_manifest||''}</td><td data-col="status_exec">${r.ultimo_status_execucao||''}</td><td data-col="publicado" class="c ${klass(r.publicado)}">${bool(r.publicado)}</td><td data-col="bd_docx" class="c ${klass(r.publicado_docx)}">${ctx==='artigos_sem_sermao'?bool(r.publicado_docx):''}</td><td data-col="bd_pdf" class="c ${klass(r.publicado_pdf)}">${ctx==='artigos_sem_sermao'?bool(r.publicado_pdf):''}</td><td data-col="bd_img" class="c ${klass(r.publicado_img)}">${ctx==='artigos_sem_sermao'?bool(r.publicado_img):''}</td><td data-col="completo" class="c ${klass(r.completo_ok)}">${bool(r.completo_ok)}</td><td data-col="alterado" class="c ${klass(r.alterado_desde_ultima_execucao)}">${bool(r.alterado_desde_ultima_execucao)}</td><td data-col="artefatos" class="mono">${arts(r)}</td><td data-col="metadados">${metaBox(r)}</td><td data-col="pasta" class="mono">${r.pasta_relativa||r.pasta_origem||'.'}</td>`;tb.appendChild(tr);});updSum(f);hdrs();syncAll();applyCols();}
function act(fn){const vis=new Set(last);rows().forEach(r=>{if(vis.has(r.id_base))fn(r.id_base);});render();}
function sw(next){ctx=next;sort=ctx==='artigos_sem_sermao'?{key:'pasta_relativa',dir:1}:{key:'titulo',dir:1};['q','serie','autor','sm','se','pend'].forEach(id=>{const e=document.getElementById(id);if(e)e.value='';});refresh();ui();render();}
document.querySelectorAll('th[data-key]').forEach(th=>th.addEventListener('click',()=>{const k=th.getAttribute('data-key');if(k==='pick')return;sort={key:k,dir:sort.key===k?sort.dir*-1:1};render();}));
['q','serie','autor','sm','se','pend'].forEach(id=>{const e=document.getElementById(id);if(e){e.addEventListener('input',render);e.addEventListener('change',render);}});
document.querySelectorAll('[data-col-toggle]').forEach(e=>e.addEventListener('change',ev=>{cols[ev.target.getAttribute('data-col-toggle')]=ev.target.checked;applyCols();}));
document.getElementById('sv').addEventListener('click',()=>act(id=>picked().add(id)));document.getElementById('dv').addEventListener('click',()=>act(id=>picked().delete(id)));document.getElementById('iv').addEventListener('click',()=>act(id=>picked().has(id)?picked().delete(id):picked().add(id)));document.getElementById('cl').addEventListener('click',()=>{picked().clear();render();});
document.getElementById('rf').addEventListener('click',async()=>{const btn=document.getElementById('rf');const old=btn.textContent;btn.disabled=true;btn.textContent='Atualizando...';try{const res=await fetch(`${helperBase}/refresh`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({browse_meta:meta})});const data=await res.json();if(!res.ok||!data.ok)throw new Error(data.error||'Falha ao atualizar');location.reload();}catch(err){alert('Falha ao atualizar o Browse. Verifique se o helper local esta rodando.');btn.disabled=false;btn.textContent=old;return;}});
document.getElementById('allv').addEventListener('click',e=>{e.stopPropagation();const t=last.length,s=last.filter(id=>picked().has(id)).length,all=!(t>0&&s===t);if(all)act(id=>picked().add(id));else act(id=>picked().delete(id));});
document.getElementById('add').addEventListener('click',()=>{const n=parseInt(document.getElementById('sp').value||'',10);if(Number.isNaN(n))return;const allowed=allowedSteps[ctx]||[];if(!allowed.includes(n))return;if(allowed.length===1){steps[ctx]=[n];}else if(!steps[ctx].includes(n)){steps[ctx].push(n);}ops();});
document.getElementById('clr').addEventListener('click',()=>{steps[ctx]=(allowedSteps[ctx]||[]).length===1?[allowedSteps[ctx][0]]:[];ops();});
document.addEventListener('click',e=>{const rm=e.target.getAttribute('data-rm');if(rm){steps[ctx]=steps[ctx].filter(n=>n!==parseInt(rm,10));ops();}});
['all','docx','pdf','img'].forEach(id=>document.getElementById(id).addEventListener('change',ev=>{if(id==='all'&&ev.target.checked)pk[ctx]=['all'];else{if(id!=='all'&&ev.target.checked)document.getElementById('all').checked=false;pk[ctx]=getKinds();}syncKinds();}));
document.getElementById('dl').addEventListener('click',async()=>{const payload=buildSelectionPayload();try{const res=await fetch(`${helperBase}/save-selection`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await res.json();if(!res.ok||!data.ok)throw new Error(data.error||'Falha ao salvar');alert(`Selecao salva em:\\n${data.path||defaultSelectionPath}`);return;}catch(err){const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='selecionados_atual.json';a.click();alert(`Helper indisponivel. JSON baixado manualmente.\\nCaminho padrao esperado: ${defaultSelectionPath}`);}});
async function pollJob(jobId, btn, old){if(activeJobPoll)clearInterval(activeJobPoll);const hint=document.getElementById('hint');hint.innerHTML=`Executando no Helper... <span class="mono">${jobId}</span>`;activeJobPoll=setInterval(async()=>{try{const res=await fetch(`${helperBase}/job-status/${jobId}`);const data=await res.json();if(!res.ok||!data.ok)throw new Error(data.error||'Falha ao consultar status');const status=data.status||'running';btn.textContent=status==='running'?'Executando...':old;if(status==='running'){const tail=((data.stdout||'')+(data.stderr?`\\n${data.stderr}`:'')).trim();if(tail)hint.innerHTML=`Execucao em andamento.<br><span class="mono">${tail.slice(-500)}</span>`;return;}clearInterval(activeJobPoll);activeJobPoll=null;if(status==='completed'){alert(`Execucao concluida.\\n\\n${(data.stdout||'').trim()||'Sem saida resumida.'}`);location.reload();return;}throw new Error(((data.stdout||'')+(data.stderr?`\\n${data.stderr}`:'')).trim()||'Falha ao executar');}catch(err){clearInterval(activeJobPoll);activeJobPoll=null;btn.disabled=false;btn.textContent=old;alert(`Falha ao executar os steps pelo Browse.\\n\\n${err.message||err}`);}},2000);}
document.getElementById('ex').addEventListener('click',async()=>{const payload=buildSelectionPayload();if(!payload.selected_ids.length){alert('Nenhum item selecionado.');return;}if(!(payload.operation_plan&&payload.operation_plan.steps&&payload.operation_plan.steps.length)){alert('Nenhum step selecionado.');return;}const btn=document.getElementById('ex');const old=btn.textContent;btn.disabled=true;btn.textContent='Executando...';try{const res=await fetch(`${helperBase}/execute`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const data=await res.json();if(!res.ok||!data.ok)throw new Error((data.stdout||data.stderr||data.error||'Falha ao executar').trim());await pollJob(data.job_id,btn,old);}catch(err){btn.disabled=false;btn.textContent=old;alert(`Falha ao executar os steps pelo Browse.\\n\\n${err.message||err}`);return;}});
document.addEventListener('change',e=>{if(e.target.classList.contains('pick')){const id=e.target.dataset.id;if(e.target.checked)picked().add(id);else picked().delete(id);render();}});
document.getElementById('cs').addEventListener('click',()=>sw('sermoes_formatados'));document.getElementById('ca').addEventListener('click',()=>sw('artigos_sem_sermao'));
ui();refresh();render();
</script></body></html>"""


def generate_browse_html(
    sermon_rows: Iterable[dict],
    output_path: Path,
    title: str = "Browse de Sermoes",
    article_rows: Iterable[dict] | None = None,
    browse_meta: dict | None = None,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html = (
        HTML_TEMPLATE
        .replace("__TITLE__", escape(title))
        .replace(
            "__DATASETS__",
            json.dumps(
                {
                    "sermoes_formatados": list(sermon_rows),
                    "artigos_sem_sermao": list(article_rows or []),
                },
                ensure_ascii=False,
            ),
        )
        .replace("__META__", json.dumps(browse_meta or {}, ensure_ascii=False))
        .replace("__STEP_LABELS__", json.dumps(STEP_LABELS, ensure_ascii=False))
        .replace(
            "__DEFAULT_SELECTION_PATH__",
            json.dumps(str(Path("Apenas_Local") / "operacional" / "Jason-CSV" / "selecionados_atual.json"), ensure_ascii=False),
        )
    )
    output_path.write_text(html, encoding="utf-8")
