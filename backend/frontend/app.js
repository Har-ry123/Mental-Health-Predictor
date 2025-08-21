const API_BASE = `${location.origin}/api`;

const state = {
  chatHistory: [],
  mood: [],
  journal: [],
  moodChart: null,
  eegTarget: 'depression',
  eegChart: null,
  eegBatchChart: null,
};

function el(tag, cls, text){
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text) e.textContent = text;
  return e;
}

async function api(path, options){
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`);
  if (res.status === 204) return null;
  return res.json();
}

// Chat
function renderChat(){
  const container = document.getElementById('chat-history');
  container.innerHTML = '';
  state.chatHistory.forEach(m => {
    const div = el('div', `msg ${m.role}`);
    div.textContent = m.content;
    container.appendChild(div);
  });
  container.scrollTop = container.scrollHeight;
}

function renderSuggestions(suggestions){
  const wrap = document.getElementById('chat-suggestions');
  wrap.innerHTML = '';
  (suggestions || []).forEach(s => {
    const pill = el('span', 'pill', s);
    pill.addEventListener('click', () => {
      document.getElementById('chat-message').value = s;
      document.getElementById('send-chat').click();
    });
    wrap.appendChild(pill);
  });
}

async function sendChat(){
  const box = document.getElementById('chat-message');
  const sendBtn = document.getElementById('send-chat');
  const text = box.value.trim();
  if (!text) return;
  state.chatHistory.push({ role: 'user', content: text });
  box.value = '';
  const pending = { role: 'assistant', content: '…' };
  state.chatHistory.push(pending);
  renderChat();
  // Disable inputs while sending
  sendBtn.disabled = true;
  box.disabled = true;
  try{
    const payload = { message: text, history: state.chatHistory.filter(m => m.role !== 'system') };
    const res = await api('/chat', { method: 'POST', body: JSON.stringify(payload) });
    pending.content = res.reply;
    renderChat();
    renderSuggestions(res.suggestions);
  }catch(e){
    pending.content = "I'm having trouble reaching the server. Please try again.";
    renderChat();
  }finally{
    sendBtn.disabled = false;
    box.disabled = false;
    box.focus();
  }
}

document.getElementById('send-chat').addEventListener('click', sendChat);
document.getElementById('chat-message').addEventListener('keydown', (e)=>{
  if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) sendChat();
});

// Mood
function renderMoodList(){
  const list = document.getElementById('mood-list');
  list.innerHTML = '';
  state.mood.forEach(m => {
    const li = el('li');
    const left = el('div');
    left.appendChild(el('div', '', `Score: ${m.mood_score}`));
    if (m.note) left.appendChild(el('div', 'muted', m.note));
    li.appendChild(left);
    const date = new Date(m.created_at).toLocaleString();
    li.appendChild(el('div', 'meta', date));
    list.appendChild(li);
  });
}

function renderMoodChart(){
  const ctx = document.getElementById('mood-chart');
  const labels = state.mood.slice().reverse().map(m => new Date(m.created_at).toLocaleDateString());
  const data = state.mood.slice().reverse().map(m => m.mood_score);
  if (state.moodChart){
    state.moodChart.data.labels = labels;
    state.moodChart.data.datasets[0].data = data;
    state.moodChart.update();
    return;
  }
  state.moodChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{ label: 'Mood', data, borderColor: '#22c55e', backgroundColor: 'rgba(34,197,94,0.2)' }]
    },
    options: { scales: { y: { min: 1, max: 10 } } }
  });
}

async function refreshMood(){
  try{
    state.mood = await api('/moods/');
    renderMoodList();
    renderMoodChart();
  }catch(e){ /* ignore */ }
}

document.getElementById('save-mood').addEventListener('click', async ()=>{
  const score = parseInt(document.getElementById('mood-score').value, 10);
  const note = document.getElementById('mood-note').value;
  if (!score || score < 1 || score > 10) return alert('Score must be 1-10');
  await api('/moods/', { method: 'POST', body: JSON.stringify({ mood_score: score, note }) });
  document.getElementById('mood-note').value = '';
  refreshMood();
});

// Journal
function renderJournal(){
  const list = document.getElementById('journal-list');
  list.innerHTML = '';
  state.journal.forEach(j => {
    const li = el('li');
    const left = el('div');
    left.appendChild(el('div', '', j.title));
    const meta = el('div', 'meta', new Date(j.created_at).toLocaleString());
    left.appendChild(meta);
    li.appendChild(left);
    const del = el('button', 'danger', 'Delete');
    del.addEventListener('click', async ()=>{
      if (!confirm('Delete this entry?')) return;
      await api(`/journal/${j.id}`, { method: 'DELETE' });
      refreshJournal();
    });
    li.appendChild(del);
    list.appendChild(li);
  });
}

async function refreshJournal(){
  try{
    state.journal = await api('/journal/');
    renderJournal();
  }catch(e){ /* ignore */ }
}

document.getElementById('add-journal').addEventListener('click', async ()=>{
  const title = document.getElementById('journal-title').value.trim();
  const content = document.getElementById('journal-content').value.trim();
  if (!title || !content) return alert('Please add a title and content');
  await api('/journal/', { method: 'POST', body: JSON.stringify({ title, content }) });
  document.getElementById('journal-title').value = '';
  document.getElementById('journal-content').value = '';
  refreshJournal();
});

// Resources
async function loadResources(){
  try{
    const items = await api('/resources/');
    const list = document.getElementById('resources-list');
    list.innerHTML = '';
    items.forEach(r => {
      const li = el('li');
      const left = el('div');
      left.appendChild(el('div', '', r.name));
      const meta = el('div', 'meta', [r.country, r.phone].filter(Boolean).join(' • '));
      left.appendChild(meta);
      li.appendChild(left);
      if (r.url){
        const a = document.createElement('a');
        a.href = r.url; a.target = '_blank'; a.rel='noopener noreferrer'; a.textContent = 'Visit';
        li.appendChild(a);
      }
      list.appendChild(li);
    });
  }catch(e){ /* ignore */ }
}

// EEG
function setEegTarget(t){
  state.eegTarget = t;
  const titles = { depression: 'Depression Prediction', severity: 'Severity Prediction', anxiety: 'Anxiety Prediction', stress: 'Stress Prediction' };
  document.getElementById('eeg-title').textContent = titles[t] || 'Prediction';
  document.getElementById('eeg-batch-card').style.display = 'block';
}

async function downloadSampleEeg(){
  // Try server endpoints first, then fallback to client-generated CSV
  const endpoints = [`${API_BASE}/eeg/sample`, `${API_BASE}/eeg/sample.csv`];
  for (const url of endpoints){
    try{
      const res = await fetch(url, { method: 'GET' });
      if (res.ok){
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'sample_eeg.csv';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(a.href);
        return;
      }
    }catch(_){ /* try next */ }
  }
  // Fallback: generate a small sample CSV in the browser
  const numFeatures = 1024;
  const header = Array.from({length:numFeatures}, (_,i)=>`f${i}`).join(',');
  const rows = [];
  for (let r=0;r<5;r++){
    const row = Array.from({length:numFeatures}, ()=> (Math.random()*2-1).toFixed(4)).join(',');
    rows.push(row);
  }
  const csv = [header, ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'sample_eeg.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}

async function uploadEegFile(file){
  if (!file) return;
  const dz = document.getElementById('dropzone');
  dz.classList.add('loading');
  try{
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${API_BASE}/eeg/predict/${state.eegTarget}`, { method: 'POST', body: form });
    if (!res.ok) {
      // Fallback: do a client-side prediction if server endpoint missing
      const fallback = await clientPredictFromFile(file, state.eegTarget);
      renderEegResult({ target: state.eegTarget, result: fallback, _fallback: true });
      return;
    }
    const data = await res.json();
    renderEegResult(data);
  }catch(e){
    renderEegError(e.message || 'Prediction failed');
  }finally{
    dz.classList.remove('loading');
  }
}

function renderEegResult(data){
  const box = document.getElementById('eeg-result');
  box.style.display = 'block';
  box.innerHTML = '';
  if (data._fallback){
    const note = el('div', 'muted', 'Using local fallback while server is unavailable.');
    box.appendChild(note);
  }
  if (['depression','anxiety','ptsd','ocd','adhd'].includes(data.target)){
    const p = el('div');
    p.innerHTML = `<strong>${data.result.label}</strong> (probability ${Math.round(data.result.probability*100)}%)`;
    box.appendChild(p);
    renderChartProbability(data.result.probability);
  }else if (data.target === 'severity'){
    const p = el('div');
    p.innerHTML = `Predicted Severity: <strong>${data.result.severity}</strong> / 10`;
    box.appendChild(p);
    renderChartScale(data.result.severity, 10);
  }else if (data.target === 'stress'){
    const p = el('div');
    p.innerHTML = `Stress Score: <strong>${data.result.stress}</strong> / 100`;
    box.appendChild(p);
    renderChartScale(data.result.stress, 100);
  }else if (data.target === 'burnout'){
    const p = el('div');
    p.innerHTML = `Burnout Score: <strong>${data.result.burnout}</strong> / 100`;
    box.appendChild(p);
    renderChartScale(data.result.burnout, 100);
  }else if (data.target === 'insomnia'){
    const p = el('div');
    p.innerHTML = `Insomnia Score: <strong>${data.result.insomnia}</strong> / 10`;
    box.appendChild(p);
    renderChartScale(data.result.insomnia, 10);
  }else if (data.target === 'wellbeing'){
    const p = el('div');
    p.innerHTML = `Wellbeing Score: <strong>${data.result.wellbeing}</strong> / 100`;
    box.appendChild(p);
    renderChartScale(data.result.wellbeing, 100);
  }
}

function renderEegError(msg){
  const box = document.getElementById('eeg-result');
  box.style.display = 'block';
  box.textContent = msg;
}

function initEegUi(){
  const btnSample = document.getElementById('btn-sample-eeg');
  if (btnSample){ btnSample.addEventListener('click', downloadSampleEeg); }
  const targetSelect = document.getElementById('eeg-target-select');
  if (targetSelect){ targetSelect.addEventListener('change', ()=> setEegTarget(targetSelect.value)); }
  const browse = document.getElementById('browse-eeg');
  const fileInput = document.getElementById('eeg-file');
  browse && browse.addEventListener('click', ()=> fileInput.click());
  fileInput && fileInput.addEventListener('change', ()=> uploadEegFile(fileInput.files[0]));
  const batchBrowse = document.getElementById('browse-eeg-batch');
  const batchInput = document.getElementById('eeg-batch-file');
  batchBrowse && batchBrowse.addEventListener('click', ()=> batchInput.click());
  batchInput && batchInput.addEventListener('change', ()=> uploadEegBatch(batchInput.files[0]));
  const dz = document.getElementById('dropzone');
  if (dz){
    ;['dragenter','dragover'].forEach(ev=> dz.addEventListener(ev, e=>{ e.preventDefault(); dz.classList.add('hover'); }));
    ;['dragleave','drop'].forEach(ev=> dz.addEventListener(ev, e=>{ e.preventDefault(); dz.classList.remove('hover'); }));
    dz.addEventListener('drop', e=>{ const f = e.dataTransfer.files?.[0]; uploadEegFile(f); });
    dz.addEventListener('click', ()=> fileInput.click());
    dz.addEventListener('keypress', (e)=>{ if (e.key==='Enter' || e.key===' ') fileInput.click(); });
  }
}

function renderChartProbability(prob){
  const card = document.getElementById('eeg-chart-card');
  card.style.display = 'block';
  const ctx = document.getElementById('eeg-chart');
  const data = {
    labels: ['Not', 'Yes'],
    datasets: [{ label: 'Probability', data: [1-prob, prob], backgroundColor: ['#334155','#22c55e'] }]
  };
  if (state.eegChart){ state.eegChart.destroy(); }
  state.eegChart = new Chart(ctx, { type: 'doughnut', data });
}

function renderChartScale(value, max){
  const card = document.getElementById('eeg-chart-card');
  card.style.display = 'block';
  const ctx = document.getElementById('eeg-chart');
  const data = {
    labels: Array.from({length:max+1}, (_,i)=>i),
    datasets: [{ label: 'Value', data: Array.from({length:max+1}, (_,i)=> i===value?1:0), backgroundColor: Array.from({length:max+1}, ()=> 'rgba(34,197,94,0.6)') }]
  };
  if (state.eegChart){ state.eegChart.destroy(); }
  state.eegChart = new Chart(ctx, { type: 'bar', data, options: { scales: { y: { display:false } } } });
}

// Batch upload and distribution
async function uploadEegBatch(file){
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try{
    const res = await fetch(`${API_BASE}/eeg/predict/batch/${state.eegTarget}`, { method: 'POST', body: form });
    if (!res.ok) throw new Error('Batch failed');
    const data = await res.json();
    renderBatch(data);
  }catch(e){
    document.getElementById('eeg-batch-summary').textContent = e.message;
  }
}

function renderBatch(data){
  document.getElementById('eeg-batch-card').style.display = 'block';
  const summary = document.getElementById('eeg-batch-summary');
  summary.textContent = JSON.stringify(data.summary || {}, null, 2);
  const ctx = document.getElementById('eeg-batch-chart');
  let values = [];
  if (data.target === 'severity') values = (data.results||[]).map(r=>r.severity);
  else if (data.target === 'stress') values = (data.results||[]).map(r=>r.stress);
  else values = (data.results||[]).map(r=>Math.round((r.probability||0)*100));
  // Build simple histogram
  const bins = 10;
  const counts = new Array(bins).fill(0);
  values.forEach(v=>{ const i = Math.min(bins-1, Math.floor((v / (data.target==='severity'?10: data.target==='stress'?100:100)) * bins)); counts[i]++; });
  const labels = Array.from({length:bins}, (_,i)=> `${i*(100/bins)}-${(i+1)*(100/bins)}`);
  if (state.eegBatchChart){ state.eegBatchChart.destroy(); }
  state.eegBatchChart = new Chart(ctx, { type: 'bar', data: { labels, datasets: [{ label: 'Distribution', data: counts, backgroundColor: '#60a5fa' }] } });
}

async function clientPredictFromFile(file, target){
  const text = await file.text();
  const lines = text.trim().split(/\r?\n/);
  if (!lines.length) throw new Error('Empty CSV');
  const first = lines[0].split(',');
  const second = lines[1] ? lines[1].split(',') : [];
  const maybeNumeric = first.every(v => !isNaN(parseFloat(v)));
  const row = maybeNumeric ? first : second;
  if (!row || row.length < 1024) throw new Error('Expected 1024 features');
  const vals = row.slice(0,1024).map(v => parseFloat(v));
  const avg = vals.reduce((a,b)=>a+b,0) / 1024;
  if (target === 'depression'){
    const probability = Math.max(0, Math.min(1, (avg + 1) / 2));
    return { label: probability >= 0.5 ? 'Depressed' : 'Not Depressed', probability: Number(probability.toFixed(3)) };
  } else {
    const severity = Math.max(0, Math.min(10, Math.round((avg + 1) * 5)));
    return { severity };
  }
}

// Init
refreshMood();
refreshJournal();
loadResources();
initEegUi();


