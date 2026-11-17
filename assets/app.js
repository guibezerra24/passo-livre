'use strict';
const $ = id => document.getElementById(id);
const number = value => new Intl.NumberFormat('pt-BR').format(value);
const date = value => new Intl.DateTimeFormat('pt-BR', {timeZone:'UTC'}).format(new Date(value.length===10 ? value+'T12:00:00Z' : value));
const normalized = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const state = {config:null,data:null,rows:[],filtered:[],page:0,size:12,map:null,layer:null,selected:null,accessKey:'',loading:false,searchTimer:null};
function element(tag,text,className){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;}
function headers(){return state.accessKey?{Authorization:'Bearer '+state.accessKey}:{};}
function category(status){const value=normalized(status);return value==='finalizada'||value==='finalizado'?'done':value==='cancelada'||value==='cancelado'?'cancel':'open';}
function color(row){return {done:'#247866',cancel:'#7a8791',open:'#ca7a39'}[category(row.status)];}
function setError(message){$('load-error-text').textContent=message;$('load-error').hidden=false;$('source-badge').textContent='Dados indisponíveis';}

async function load(){
  if(state.loading)return;state.loading=true;$('load-error').hidden=true;$('results').setAttribute('aria-busy','true');
  try{
    const configResponse=await fetch('./config.json',{cache:'no-store'});if(!configResponse.ok)throw new Error('Não foi possível abrir a configuração do painel.');
    state.config=await configResponse.json();configureAssistant();
    const response=await fetch(state.config.dados,{headers:headers(),cache:'no-store'});
    if(response.status===401){$('auth-box').hidden=false;throw new Error('Esta instalação exige uma chave de acesso. Informe a chave abaixo para carregar os dados.');}
    if(!response.ok)throw new Error('Os dados ainda não estão disponíveis nesta instalação. Tente novamente em alguns instantes.');
    const data=await response.json();
    if(data.versao!==1||!Array.isArray(data.registros)||data.proveniencia!=='IMPORTACAO_DECLARADA_DATABRICKS')throw new Error('A origem dos dados não pôde ser confirmada.');
    state.data=data;
    state.rows=data.registros.map((r,index)=>({index,district:data.distritos[r[0]],service:data.servicos[r[1]],day:r[2],status:data.situacoes[r[3]],lat:r[4],lon:r[5]}));
    state.rows.sort((a,b)=>b.day.localeCompare(a.day)||a.index-b.index);
    $('total').textContent=number(data.total);$('district-count').textContent=number(data.distritos.length);
    const open=state.rows.filter(r=>['aberto','aberta','em andamento'].includes(r.status.toLowerCase())).length;
    const finished=state.rows.filter(r=>category(r.status)==='done').length;
    $('open-count').textContent=number(open);$('finished-rate').textContent=new Intl.NumberFormat('pt-BR',{style:'percent',maximumFractionDigits:1}).format(finished/data.total);
    const chosen=$('district').value;$('district').replaceChildren(new Option('Todos os distritos',''));data.distritos.forEach(d=>$('district').add(new Option(d,d)));$('district').value=chosen;
    const last=data.coletas[data.coletas.length-1];
    $('source-badge').textContent='SP156 · coleta '+date(last);
    $('period').textContent='Solicitações: '+date(data.periodo.inicio)+' a '+date(data.periodo.fim)+'. Coleta: '+date(last)+'.';
    $('auth-box').hidden=true;initializeMap();applyFilters();
  }catch(error){setError(error.message||'Falha de conexão. Tente novamente.');$('results').replaceChildren(element('p','Não foi possível carregar as solicitações.','empty'));$('result-count').textContent='Indisponível';$('map-count').textContent='O mapa será preenchido quando os dados estiverem disponíveis.';}
  finally{state.loading=false;$('results').setAttribute('aria-busy','false');}
}

function initializeMap(){
  if(state.map)return;
  if(!window.L){$('map').replaceChildren(element('p','O mapa não pôde ser carregado. Você pode consultar todos os registros na lista ao lado.','map-fallback'));return;}
  $('map').replaceChildren();
  state.map=L.map('map',{scrollWheelZoom:false,preferCanvas:true}).setView([-23.57,-46.63],10);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'}).addTo(state.map);
  state.layer=L.layerGroup().addTo(state.map);
}
function applyFilters(){
  if(!state.data)return;
  const query=normalized($('search').value.trim()),district=$('district').value,status=$('status').value;
  state.filtered=state.rows.filter(r=>(!district||r.district===district)&&(!query||normalized(r.service).includes(query))&&(!status||({abertas:category(r.status)==='open',finalizadas:category(r.status)==='done',canceladas:category(r.status)==='cancel'})[status]));
  state.page=0;state.selected=null;renderResults();renderMap(true);
}
function renderResults(){
  const total=state.filtered.length,pages=Math.max(1,Math.ceil(total/state.size));
  $('result-count').textContent=number(total)+' resultado'+(total===1?'':'s');$('results').replaceChildren();
  const rows=state.filtered.slice(state.page*state.size,(state.page+1)*state.size);
  if(!rows.length)$('results').append(element('p','Nenhuma solicitação encontrada. Experimente outro serviço ou limpe os filtros.','empty'));
  rows.forEach(row=>{
    const button=element('button',undefined,'result-card'+(state.selected===row.index?' selected':''));button.type='button';button.dataset.record=String(row.index);button.setAttribute('aria-pressed',String(state.selected===row.index));
    button.setAttribute('aria-label',row.service+', '+row.district+', '+row.status+', '+date(row.day)+'. Ver no mapa.');
    const top=element('div',undefined,'result-top');top.append(element('span',row.district),element('span',row.status,'badge '+category(row.status)));
    const meta=element('div',undefined,'result-meta');meta.append(element('span',date(row.day)),element('span','Ver no mapa ↗'));
    button.append(top,element('strong',row.service),meta);button.addEventListener('click',()=>selectRow(row));$('results').append(button);
  });
  $('page-label').textContent=total?'Página '+number(state.page+1)+' de '+number(pages):'Sem resultados';
  $('previous').disabled=state.page===0;$('next').disabled=state.page+1>=pages;$('results').scrollTop=0;
}
function popup(row){const box=element('div');box.append(element('strong',row.service),element('p',row.district+' · '+row.status+'\nAbertura: '+date(row.day)),element('p','Localização aproximada. Não indica uma rota acessível.'));return box;}
function marker(row){return L.circleMarker([row.lat,row.lon],{radius:5,color:'#ffffff',weight:1,fillColor:color(row),fillOpacity:.85}).bindPopup(popup(row));}
function renderMap(fit=false){
  const points=state.filtered.filter(r=>Number.isFinite(r.lat)&&Number.isFinite(r.lon)).slice(0,300);
  $('map-count').textContent=points.length?number(points.length)+' de '+number(state.filtered.length)+' registros no mapa · coordenadas aproximadas · todos os resultados na lista':'Nenhum ponto para os filtros selecionados.';
  if(!state.map)return;state.layer.clearLayers();points.forEach(row=>marker(row).addTo(state.layer));
  if(fit&&points.length)state.map.fitBounds(points.map(r=>[r.lat,r.lon]),{padding:[24,24],maxZoom:13,animate:false});
}
function selectRow(row){
  state.selected=row.index;
  document.querySelectorAll('.result-card').forEach(button=>{const selected=button.dataset.record===String(row.index);button.classList.toggle('selected',selected);button.setAttribute('aria-pressed',String(selected));});
  if(!state.map)return;
  renderMap();marker(row).setStyle({radius:9,color:'#173c33',weight:3}).addTo(state.layer).openPopup();state.map.setView([row.lat,row.lon],15,{animate:false});
  $('map-count').textContent='Registro selecionado: '+row.district+' · localização aproximada.';
}
function configureAssistant(){
  const available=Boolean(state.config.assistente);
  $('assistant-label').textContent=available?'Assistente local disponível':'Assistente disponível na instalação local';
  $('assistant-notice').textContent=available?'Consulte a base documental. O assistente pode levar alguns instantes para responder.':'Nesta versão pública, você pode explorar os dados. Para fazer perguntas ao assistente, abra o app local do projeto, com o modelo instalado no computador. O roteiro está no repositório.';
  $('question').disabled=!available;$('ask').disabled=!available;document.querySelectorAll('[data-question]').forEach(button=>button.disabled=!available);
  if(!available)$('question').placeholder='A consulta ao assistente funciona no app local.';
}
async function ask(event){
  event.preventDefault();if(!state.config?.assistente)return;
  $('ask').disabled=true;$('question').disabled=true;$('answer').hidden=false;$('answer').replaceChildren(element('p','Consultando a base e conferindo as fontes…'));
  try{
    const response=await fetch(state.config.assistente,{method:'POST',headers:{'Content-Type':'application/json',...headers()},body:JSON.stringify({pergunta:$('question').value,modo:'agente'}),signal:AbortSignal.timeout(540000)});
    if(!response.ok){const messages={401:'A consulta exige uma chave de acesso válida nesta instalação.',429:'O assistente está respondendo outra pergunta. Aguarde e tente novamente.',503:'O assistente local está indisponível. Verifique se o Ollama está aberto.'};throw new Error(messages[response.status]||'Não foi possível concluir a consulta. Tente novamente.');}
    const result=await response.json();$('answer').replaceChildren(element('strong',result.answer.status==='nao_consta'?'Não consta na base':'Resposta com fontes'),element('p',result.answer.resposta));
    for(const source of result.fontes_detalhadas||[]){const url=new URL(source.url,location.href);if(!['https:','http:'].includes(url.protocol))continue;const link=element('a',source.titulo+' ↗');link.href=url.href;link.target='_blank';link.rel='noopener noreferrer';$('answer').append(link);}
  }catch(error){$('answer').replaceChildren(element('p',error.name==='TimeoutError'?'A consulta demorou mais que o esperado. Tente novamente.':error.message));}
  finally{$('ask').disabled=false;$('question').disabled=false;}
}
$('filters').addEventListener('submit',event=>event.preventDefault());
$('search').addEventListener('input',()=>{clearTimeout(state.searchTimer);state.searchTimer=setTimeout(applyFilters,180);});
['district','status'].forEach(id=>$(id).addEventListener('change',applyFilters));
$('clear').addEventListener('click',()=>{$('filters').reset();clearTimeout(state.searchTimer);applyFilters();});
$('previous').addEventListener('click',()=>{state.page--;renderResults();});$('next').addEventListener('click',()=>{state.page++;renderResults();});
$('reset-map').addEventListener('click',()=>renderMap(true));$('retry').addEventListener('click',load);
$('connect').addEventListener('click',()=>{state.accessKey=$('access-key').value;$('access-key').value='';load();});
document.querySelectorAll('[data-question]').forEach(button=>button.addEventListener('click',()=>{$('question').value=button.dataset.question;$('question').focus();}));
$('question-form').addEventListener('submit',ask);
load();
