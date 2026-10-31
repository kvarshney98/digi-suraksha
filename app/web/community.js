function textFor(value) {
  return typeof value === 'string' ? value : value?.[lang] || value?.en || value?.hi || '';
}
function safeLink(value) {
  try { const u = new URL(value); return u.protocol === 'https:' ? esc(u.href) : '#'; }
  catch { return '#'; }
}
function checkField(key) {
  return `<label class="check"><input type="checkbox" id="${key}" name="${key}"><span>${t(key)}</span></label>`;
}
function inputField(key, type='text', extra='') {
  return label(key, `<input id="${key}" name="${key}" type="${type}" ${extra}>`);
}
let incidentKey = crypto.randomUUID();
let incidentFiles = [];
let storedFiles = [];
let pinMatches = [];
let stateChoices = [];

function responseView() {
  return head('responseTitle','responseIntro') + `<div class="layout"><section class="panel">
    <form id="incidentForm">
      ${label('description','<textarea id="description" name="description" minlength="5" maxlength="10000" required></textarea>')}
      ${label('outcome',`<select id="outcome" name="outcome">${['attempt','money','credentials'].map(k=>`<option value="${k}">${t(k)}</option>`).join('')}</select>`)}
      <p class="fine">${t('dateTimeHelp')}</p>
      <div class="row"><div>${inputField('date','date','required')}${checkField('date_unknown')}</div>
      <div>${inputField('time','time','required')}${checkField('time_unknown')}${checkField('time_approximate')}</div></div>
      <fieldset><legend>${t('locationTitle')}</legend>
        ${inputField('pincode','text','inputmode="numeric" pattern="[1-9][0-9]{5}" maxlength="6"')}
        <button type="button" class="secondary" id="pinLookup">${t('lookupPin')}</button>
        <p class="fine">${t('pinDisclosure')}</p><div id="pinStatus" role="status"></div>
        <div id="pinChoices"></div>
        <div class="row">${label('state',`<select id="state" name="state"><option value="">${t('select')}</option></select>`)}${inputField('city','text','maxlength="100"')}</div>
        ${inputField('locality','text','maxlength="150"')}
      </fieldset>
      <fieldset><legend>${t('senderTitle')}</legend>
        ${inputField('sender_phone','tel','maxlength="30"')}${inputField('sender_email','email','maxlength="254"')}
        <p class="fine">${t('senderNote')}</p><p id="phoneHint" role="status" class="fine"></p>
      </fieldset>
      ${inputField('amount','text','maxlength="40"')}${inputField('reference','text','maxlength="150"')}
      ${label('evidence','<textarea id="evidence" name="evidence" maxlength="2000"></textarea>')}
      ${label('attachments','<input id="attachments" type="file" multiple accept=".png,.jpg,.jpeg,.webp,.pdf,.txt,.eml">')}
      <p class="fine">${t('attachmentHelp')}</p><div id="selectedFiles" role="status"></div>
      ${inputField('acknowledgement','text','maxlength="150"')}
      ${checkField('save')}
      <div class="actions"><button type="submit">${t('generate')} →</button><button type="button" class="secondary" id="newIncident">${t('newIncident')}</button></div>
      <div id="incidentStatus" role="status"></div>
    </form></section>
    <aside class="panel"><h2>${t('history')}</h2><div id="history"></div><a href="/privacy">${t('privacyLink')}</a></aside>
    </div><section id="drafts" aria-live="polite"></section>`;
}
function syncUnknowns() {
  for (const key of ['date','time']) {
    const unknown=$('#'+key+'_unknown').checked;
    $('#'+key).disabled=unknown;
    $('#'+key).required=!unknown;
    if (unknown) $('#'+key).value='';
  }
  $('#time_approximate').disabled=$('#time_unknown').checked;
  if ($('#time_unknown').checked) $('#time_approximate').checked=false;
}
function incidentValues(saveOverride) {
  const form=$('#incidentForm');
  const values=Object.fromEntries(new FormData(form));
  for (const key of ['save','date_unknown','time_unknown','time_approximate']) values[key]=$('#'+key).checked;
  values.date=$('#date').value;
  values.time=$('#time').value;
  values.language=lang;
  values.record_id=incidentKey;
  if (saveOverride !== undefined) values.save=saveOverride;
  return values;
}
function selectedFileList() {
  $('#selectedFiles').innerHTML=incidentFiles.map((f,index)=>`<div class="file-item"><span>${esc(f.name)} · ${Math.ceil(f.size/1024)} KB</span><button type="button" class="secondary" data-remove-file="${index}">${t('delete')}</button></div>`).join('');
  document.querySelectorAll('[data-remove-file]').forEach(b=>b.onclick=()=>{incidentFiles.splice(Number(b.dataset.removeFile),1);selectedFileList();});
}
function draftAttachments(result) {
  const area=$('#draftAttachments');
  if (!area) return;
  const files=result.attachments||[];
  area.innerHTML=files.length?`<h3>${t('attachments')}</h3><ul>${files.map(f=>`<li>${esc(f.name)}${result.id?` · <a href="/api/incidents/${encodeURIComponent(result.id)}/attachments/${encodeURIComponent(f.id)}">${t('downloadAttachment')}</a>`:''}</li>`).join('')}</ul>${!result.id?`<p class="fine">${t('unsavedFiles')}</p>`:''}`:'';
}
async function loadHistory() {
  const records=await api('/api/incidents');
  $('#history').innerHTML=records.length?records.map(r=>`<div class="history-item"><small>${esc(r.created.slice(0,10))}</small><p>${esc(r.description.slice(0,100))}</p><button class="secondary" data-open="${esc(r.id)}">${t('open')}</button><button class="secondary" data-delete="${esc(r.id)}">${t('delete')}</button></div>`).join(''):`<p class="sub">${t('empty')}</p>`;
  document.querySelectorAll('[data-delete]').forEach(b=>b.onclick=async()=>{
    try {
      await api('/api/incidents/'+b.dataset.delete,{method:'DELETE'});
      if (incidentKey===b.dataset.delete) { incidentKey=crypto.randomUUID(); storedFiles=[]; $('#drafts').innerHTML=''; lastDraft=null; }
      await loadHistory();
    } catch(e) { toast(e.message); }
  });
  document.querySelectorAll('[data-open]').forEach(b=>b.onclick=async()=>{
    const r=records.find(r=>r.id===b.dataset.open);
    incidentKey=r.id; incidentFiles=[];storedFiles=r.attachments||[];
    for (const key of ['description','outcome','amount','reference','evidence','acknowledgement','pincode','state','city','locality','sender_phone','sender_email']) $('#'+key).value=r[key]||'';
    $('#date').value=(r.date||'').slice(0,10);
    $('#time').value=r.time||(r.date?.includes('T')?r.date.slice(11,16):'');
    $('#date_unknown').checked=r.date_unknown ?? !$('#date').value;
    $('#time_unknown').checked=r.time_unknown ?? !$('#time').value;
    $('#time_approximate').checked=!!r.time_approximate;
    $('#save').checked=true;
    syncUnknowns();selectedFileList();
    showDraft(r);
    // Translate a historical draft without saving it again or incrementing counters.
    if(r.language!==lang) {
      try { const translated=await api('/api/incidents',json(incidentValues(false))); translated.id=r.id; showDraft(translated); }
      catch(e) { toast(e.message); }
    }
  });
}
async function initResponse() {
  if (!stateChoices.length) stateChoices=await api('/api/locations/states');
  $('#state').innerHTML=`<option value="">${t('select')}</option>`+stateChoices.map(s=>`<option value="${esc(s.value)}">${esc(textFor(s.name))}</option>`).join('');
  for (const k of ['date_unknown','time_unknown']) $('#'+k).onchange=syncUnknowns;
  syncUnknowns();selectedFileList();
  const phoneHint=()=>{
    const phone=$('#sender_phone').value.replace(/[ ()-]/g,'').replace(/^00/,'+');
    $('#phoneHint').textContent=phone.startsWith('+91')?t('indianNumber'):(phone.startsWith('+')||phone.startsWith('00'))?t('internationalNumber'):'';
  };
  $('#sender_phone').oninput=phoneHint;
  $('#attachments').onchange=e=>{
    const selected=[...e.target.files];
    if(storedFiles.length+incidentFiles.length+selected.length>3||storedFiles.reduce((n,f)=>n+f.size,0)+[...incidentFiles,...selected].reduce((n,f)=>n+f.size,0)>5*1024*1024) toast(t('attachmentLimit'));
    else incidentFiles.push(...selected);
    e.target.value='';selectedFileList();
  };
  $('#pinLookup').onclick=async()=>{
    const pin=$('#pincode').value.trim();
    if(!/^[1-9][0-9]{5}$/.test(pin)) {$('#pincode').reportValidity();$('#pinStatus').textContent=t('pinInvalid');return;}
    const button=$('#pinLookup');button.disabled=true;$('#pinStatus').textContent=t('pinBusy');$('#pinChoices').innerHTML='';
    try {
      const result=await api('/api/locations/'+pin);
      if($('#pincode').value.trim()!==pin)return;
      pinMatches=result.locations;
      $('#pinStatus').textContent=pinMatches.length?'':t('pinNone');
      if(pinMatches.length){
        $('#pinChoices').innerHTML=label('chooseLocality',`<select id="chooseLocality"><option value="">${t('select')}</option>${pinMatches.map((m,i)=>`<option value="${i}">${esc(m.locality)} — ${esc(m.city)}, ${esc(m.state)}</option>`).join('')}</select>`);
        $('#chooseLocality').onchange=e=>{
          if(e.target.value==='')return;
          const item=pinMatches[Number(e.target.value)];
          const canonical=stateChoices.find(s=>s.value.toLowerCase()===item.state.toLowerCase());
          $('#state').value=canonical?.value||'';$('#city').value=item.city;$('#locality').value=item.locality;
        };
      }
    }catch(e){$('#pinStatus').textContent=e.message;}
    finally{button.disabled=false;}
  };
  $('#pincode').oninput=()=>{$('#pinChoices').innerHTML='';$('#pinStatus').textContent='';pinMatches=[];};
  $('#newIncident').onclick=()=>{
    $('#incidentForm').reset();incidentKey=crypto.randomUUID();incidentFiles=[];storedFiles=[];lastDraft=null;
    $('#drafts').innerHTML='';$('#incidentStatus').textContent='';$('#phoneHint').textContent='';$('#pinChoices').innerHTML='';$('#pinStatus').textContent='';syncUnknowns();selectedFileList();
  };
  $('#incidentForm').onsubmit=async event=>{
    event.preventDefault();const button=event.submitter;button.disabled=true;
    try{
      const form=new FormData();form.append('payload',JSON.stringify(incidentValues()));incidentFiles.forEach(file=>form.append('files',file));
      const result=await api('/api/incidents/prepare',{method:'POST',body:form});
      if(result.id){incidentKey=result.id;storedFiles=result.attachments||[];incidentFiles=[];selectedFileList();}
      showDraft(result);await loadHistory();$('#incidentStatus').textContent='';
    }catch(e){$('#incidentStatus').textContent=e.message;}
    finally{button.disabled=false;}
  };
  await loadHistory();
}
async function loadCounters() {
  try {
    const counts=await api('/api/stats');
    if(!$('#incidentCounters'))return;
    $('#incidentCounters').innerHTML=`<div><strong>${counts.today.toLocaleString(lang==='hi'?'hi-IN':'en-IN')}</strong> ${t('recordedToday')}</div><div><strong>${counts.total.toLocaleString(lang==='hi'?'hi-IN':'en-IN')}</strong> ${t('recordedTotal')}</div><small>${t('counterNote')}</small>`;
  } catch {if($('#incidentCounters'))$('#incidentCounters').textContent=t('counterUnavailable');}
}
async function bankSection() {
  const banks=await api('/api/banks');
  const slot=$('#bankSection');if(!slot)return;
  slot.innerHTML=`<h2>${t('bankTitle')}</h2><p>${t('bankIntro')}</p>${label('bankSelect',`<select id="bankSelect"><option value="">${t('select')}</option>${banks.map(b=>`<option value="${esc(b.id)}">${esc(textFor(b.name))} · ${esc(textFor(b.country))}</option>`).join('')}</select>`)}<div id="bankContact" aria-live="polite"></div><p class="fine">${t('bankNote')}</p>`;
  $('#bankSelect').onchange=e=>{
    const bank=banks.find(b=>b.id===e.target.value);
    $('#bankContact').innerHTML=bank?`<h3>${esc(textFor(bank.name))}</h3><p>${esc(textFor(bank.purpose))}</p><div class="actions"><a class="button" href="tel:${esc(bank.phone)}">${t('bankCall')}: ${esc(bank.phone)}</a><a class="button secondary" href="${safeLink(bank.url)}" target="_blank" rel="noopener noreferrer">${t('bankWebsite')} ↗</a></div><small>${t('verified')}: ${esc(bank.last_verified)} · <a href="${safeLink(bank.source)}" target="_blank" rel="noopener noreferrer">${t('source')}</a></small>`:'';
  };
}
function videoLinks(item) {
  const videos=[...(item.videos||[]),...(item.video_channel?[item.video_channel]:[])];
  return videos.length?`<h3>${t('watchVideos')}</h3><ul>${videos.map(v=>`<li><a href="${safeLink(v.url)}" target="_blank" rel="noopener noreferrer">${esc(textFor(v.title))} ↗</a></li>`).join('')}</ul><p class="fine">${t('videoInternet')}</p>`:'';
}
function advisoryUploadView() {
  return `<details class="panel upload-panel"><summary>${t('uploadAdvisory')}</summary><p>${t('advisoryIntro')}</p><form id="advisoryForm">
    ${inputField('advisoryTitle','text','required minlength="3" maxlength="150"')}
    ${label('advisoryLanguage',`<select id="advisoryLanguage"><option value="en">English</option><option value="hi">हिन्दी</option></select>`)}
    ${['looks','signs','action','avoid','after'].map(k=>label('advisory_'+k,`<textarea id="advisory_${k}" maxlength="${k==='looks'?3000:2000}" ${k==='looks'?'required minlength="10"':''}></textarea>`)).join('')}
    ${inputField('advisorySource','url','required maxlength="1000" pattern="https://.*"')}
    ${label('advisoryFile','<input id="advisoryFile" type="file" accept=".pdf,.txt,.png,.jpg,.jpeg,.webp">')}
    <button>${t('submitAdvisory')}</button><p id="advisoryStatus" role="status"></p>
  </form></details><details class="panel upload-panel"><summary>${t('reviewTitle')}</summary><p class="fine">${t('reviewIntro')}</p><div id="reviewQueue"></div></details>`;
}
async function refreshQueue() {
  const entries=await api('/api/advisories/review');
  $('#reviewQueue').innerHTML=entries.length?entries.map(a=>`<article class="review-item"><span class="badge">${t(a.status)}</span><h3>${esc(a.title)}</h3><p>${esc(a.looks)}</p><dl>${['signs','action','avoid','after'].filter(k=>a[k]).map(k=>`<dt>${t(k)}</dt><dd>${esc(a[k])}</dd>`).join('')}</dl><a href="${safeLink(a.source)}" target="_blank" rel="noopener noreferrer">${t('uploadSource')} ↗</a>${a.attachment_name?`<p><a href="/api/advisories/${encodeURIComponent(a.id)}/attachment">${t('downloadAttachment')}: ${esc(a.attachment_name)}</a></p>`:''}${a.status==='pending'?`<label class="check"><input type="checkbox" id="review-${esc(a.id)}"><span>${t('reviewed')}</span></label><button data-publish="${esc(a.id)}">${t('publish')}</button>`:''}<button class="secondary" data-remove-advisory="${esc(a.id)}">${t('delete')}</button></article>`).join(''):`<p>${t('noQueue')}</p>`;
  document.querySelectorAll('[data-publish]').forEach(b=>b.onclick=async()=>{
    if(!document.getElementById('review-'+b.dataset.publish).checked){toast(t('reviewed'));return;}
    try{await api('/api/advisories/'+b.dataset.publish+'/publish',json({reviewed:true}));await refreshAdvisoryLibrary();await refreshQueue();}catch(e){toast(e.message);}
  });
  document.querySelectorAll('[data-remove-advisory]').forEach(b=>b.onclick=async()=>{
    try{await api('/api/advisories/'+b.dataset.removeAdvisory,{method:'DELETE'});await refreshAdvisoryLibrary();await refreshQueue();}catch(e){toast(e.message);}
  });
}
let advisoryRows=[];
function drawAdvisoryLibrary() {
  const query=$('#search').value.toLowerCase();
  const rows=advisoryRows.filter(a=>JSON.stringify(a).toLowerCase().includes(query));
  $('#advisories').innerHTML=rows.length?rows.map((a,index)=>`<article class="card"><span class="number">${String(index+1).padStart(2,'0')} /</span>${a.uploaded?`<p class="fine">${t('localUpload')}: ${a.language==='hi'?'हिन्दी':'English'}</p>`:''}<h2>${esc(textFor(a.title))}</h2><p>${esc(textFor(a.looks))}</p><details><summary>${t('learn')}</summary><dl>${['signs','action','avoid','after'].filter(k=>textFor(a[k])).map(k=>`<dt>${t(k)}</dt><dd>${esc(textFor(a[k]))}</dd>`).join('')}</dl>${videoLinks(a)}${a.source?`<p><a href="${safeLink(a.source)}" target="_blank" rel="noopener noreferrer">${t('uploadSource')}</a></p>`:''}${a.attachment_url?`<p><a href="${esc(a.attachment_url)}">${t('downloadAttachment')}: ${esc(a.attachment_name)}</a></p>`:''}<a href="/reporting">${t('reporting')} →</a></details></article>`).join(''):`<p>${t('noResults')}</p>`;
}
async function refreshAdvisoryLibrary(){advisoryRows=await api('/api/advisories');drawAdvisoryLibrary();}
async function awarenessView() {
  $('#main').innerHTML=head('awarenessTitle','awarenessIntro')+label('search','<input class="search" id="search" type="search">')+'<div class="advisories" id="advisories"></div>'+advisoryUploadView();
  $('#search').oninput=drawAdvisoryLibrary;
  $('#advisoryLanguage').value=lang;
  $('#advisoryForm').onsubmit=async event=>{
    event.preventDefault();const button=event.submitter;button.disabled=true;
    try{
      const payload={language:$('#advisoryLanguage').value,title:$('#advisoryTitle').value,source:$('#advisorySource').value};
      for(const key of ['looks','signs','action','avoid','after'])payload[key]=$('#advisory_'+key).value;
      const form=new FormData();form.append('payload',JSON.stringify(payload));const file=$('#advisoryFile').files[0];
      if(file){if(file.size>5*1024*1024)throw Error(t('fileError'));form.append('file',file);}
      await api('/api/advisories/upload',{method:'POST',body:form});event.target.reset();$('#advisoryStatus').textContent=t('advisorySubmitted');await refreshQueue();
    }catch(e){$('#advisoryStatus').textContent=e.message;}
    finally{button.disabled=false;}
  };
  await refreshAdvisoryLibrary();await refreshQueue();
}

setInterval(()=>{if(location.pathname==='/'&&!document.hidden)loadCounters();},30000);
