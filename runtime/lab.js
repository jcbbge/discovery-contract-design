/* Synthetic lab client. Only textContent is used for server-provided strings. */
'use strict';
const $ = id => document.getElementById(id);
const el = (tag, text, className) => {
  const item = document.createElement(tag);
  if (text !== undefined) item.textContent = String(text);
  if (className) item.className = className;
  return item;
};
const settled = status => status === 'satisfied' || status === 'satisfied_by_rule';
const labels = {pending: 'Pending', in_progress: 'In progress', blocked: 'Blocked', failed: 'Failed', satisfied: 'Satisfied', satisfied_by_rule: 'By rule'};
const label = status => labels[status] || String(status || 'Pending');
const text = value => value == null ? '—' : String(value);
const fmt = value => { try { return JSON.stringify(value, null, 2); } catch { return '—'; } };
const API = '/lab/api/runs';
let run = null;
let runList = [];
let stage = '';
let markerId = '';
let position = 0;
let playing = null;
let busy = false;
let generation = 0;

function feedback(message, error = false) {
  const box = $('feedback'); box.hidden = !message;
  box.textContent = message || '';
  box.classList.toggle('error', error);
}
async function request(path, method = 'GET', data) {
  const response = await fetch(path, {
    method, cache: 'no-store',
    ...(method === 'GET' ? {} : {headers: {'Content-Type': 'application/json', 'X-Pipeline-Lab': '1'}, body: JSON.stringify(data || {})})
  });
  let result;
  try { result = await response.json(); } catch { throw new Error(`Invalid server response (${response.status})`); }
  if (!response.ok) throw new Error(result?.error || `Request failed (${response.status})`);
  return result;
}
async function mutation(action, success) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('button').forEach(button => { if (!button.disabled) { button.disabled = true; button.dataset.labBusy = '1'; } });
  feedback('Recording in the isolated lab ledger…');
  try {
    await action();
    feedback(success);
  } catch (error) {
    feedback(`Not recorded: ${error.message}`, true);
  } finally {
    document.querySelectorAll('button[data-lab-busy]').forEach(button => { button.disabled = false; delete button.dataset.labBusy; });
    busy = false;
  }
}
function stop() { if (playing) clearInterval(playing); playing = null; $('play').textContent = 'Play'; $('play').setAttribute('aria-label', 'Play timeline'); }
function setRun(data) {
  const previous = run?.run;
  run = data;
  if (previous !== data.run) { stage = ''; markerId = ''; $('marker-search').value = ''; stop(); }
  if (!data.markers?.some(marker => marker.id === markerId)) markerId = data.markers?.[0]?.id || '';
  position = data.events?.length || 0;
  render(true);
}
function clearRun() {
  stop(); run = null; stage = ''; markerId = ''; position = 0;
  for (const id of ['run-panel', 'timeline-panel', 'markers-panel', 'activity-panel', 'tools']) $(id).hidden = true;
  $('stages').replaceChildren(el('p', 'Create or select a synthetic run.', 'hint'));
}
async function refreshList(preferred) {
  const list = await request(API);
  runList = list;
  const selector = $('runs');
  const choice = preferred !== undefined ? preferred : run?.run || selector.value;
  selector.replaceChildren(el('option', 'Select a run…'));
  selector.firstChild.value = '';
  for (const entry of list) {
    const option = el('option', `${entry.scenario || 'synthetic'} · ${entry.id}`);
    option.value = entry.id; selector.append(option);
  }
  selector.value = list.some(item => item.id === choice) ? choice : '';
  if (!selector.value) clearRun();
  else if (run?.run !== selector.value) await loadRun(selector.value);
}
async function loadRun(id) {
  const ticket = ++generation;
  if (!id) { clearRun(); return; }
  const data = await request(`${API}/${encodeURIComponent(id)}`);
  if (ticket === generation && $('runs').value === id) { setRun(data); feedback(''); }
}
function preserveFocus(container, keyAttribute, draw) {
  const active = document.activeElement;
  const key = container.contains(active) ? active.getAttribute(keyAttribute) : null;
  draw();
  if (key !== null) [...container.querySelectorAll('button')].find(button => button.getAttribute(keyAttribute) === key)?.focus({preventScroll: true});
}
function renderStages() {
  const host = $('stages');
  const statuses = replayStatuses();
  preserveFocus(host, 'data-stage', () => {
    host.replaceChildren();
    for (const item of [{id: '', name: 'All stages'}, ...run.stages]) {
      const markers = item.id ? run.markers.filter(marker => marker.stage === item.id) : run.markers;
      const button = el('button', undefined, 'stage-button'); button.type = 'button';
      button.dataset.stage = item.id; button.setAttribute('aria-pressed', String(stage === item.id));
      button.append(el('span', item.id || 'ALL', 'stage-id'), el('span', item.name, 'stage-name'), el('span', `${markers.filter(m => settled(statuses.get(m.id))).length}/${markers.length}`, 'count'));
      button.addEventListener('click', () => { stage = item.id; renderStages(); renderMarkers(); });
      host.append(button);
    }
  });
}
function replayStatuses() {
  const statuses = new Map(run.markers.map(marker => [marker.id, 'pending']));
  for (const event of run.events.slice(0, position)) {
    if (['marker', 'marker_revision'].includes(event.kind) && statuses.has(event.marker)) statuses.set(event.marker, event.payload?.status || 'pending');
  }
  return statuses;
}
function renderMarkers() {
  const host = $('markers');
  const query = $('marker-search').value.trim().toLocaleLowerCase();
  const statuses = replayStatuses();
  const shown = run.markers.filter(m => (!stage || m.stage === stage) && (!query || `${m.id} ${m.requirement}`.toLocaleLowerCase().includes(query)));
  $('marker-total').textContent = `${shown.length} of ${run.markers.length}`;
  preserveFocus(host, 'data-marker', () => {
    host.replaceChildren();
    for (const marker of shown) {
      const button = el('button', undefined, 'marker-row'); button.type = 'button'; button.dataset.marker = marker.id;
      button.setAttribute('aria-pressed', String(markerId === marker.id));
      button.setAttribute('aria-label', `${marker.id}: ${marker.requirement}. ${label(statuses.get(marker.id))}. Inspect marker`);
      button.append(el('span', marker.id, 'mono'), el('span', marker.requirement, 'title'), el('span', label(statuses.get(marker.id)), 'pill ' + statuses.get(marker.id)));
      button.addEventListener('click', () => { markerId = marker.id; renderMarkers(); renderInspector(); });
      host.append(button);
    }
    if (!shown.length) host.append(el('p', 'No markers match. Try another stage or search.', 'hint'));
  });
}
function renderInspector() {
  const marker = run.markers.find(m => m.id === markerId);
  if (!marker) return;
  const title = $('inspector-title'); title.replaceChildren(el('strong', marker.id + ' · '), document.createTextNode(marker.requirement));
  $('inspector-current').textContent = `Current: ${label(marker.status)} · ${marker.evidence?.length || 0} pointer(s). ${marker.updated ? 'Updated ' + marker.updated : 'Never updated.'}`;
  $('mark-status').value = marker.status;
  $('mark-value').value = marker.value == null ? '' : fmt(marker.value);
  $('mark-evidence').value = Array.isArray(marker.evidence) ? marker.evidence.join('\n') : '';
  $('mark-revise').checked = settled(marker.status);
  $('mark-fields').disabled = false;
  $('trace-form').dataset.marker = marker.id;
}
function renderState() {
  $('run-id').textContent = run.run;
  $('run-mode').textContent = `SYNTHETIC · ${run.mode || 'lab'}`;
  const current = position === run.events.length;
  const statuses = current ? new Map(run.markers.map(m => [m.id, m.status])) : replayStatuses();
  const done = [...statuses.values()].filter(settled).length;
  $('progress-count').textContent = `${done} / ${run.progress.total}`;
  $('progress-percent').textContent = `${(100 * done / (run.progress.total || 1)).toFixed(1)}% ${current ? 'current' : 'at event'}`;
  $('meter').setAttribute('aria-valuemax', String(run.progress.total));
  $('meter').setAttribute('aria-valuenow', String(done));
  $('meter').firstElementChild.style.width = `${Math.min(100, 100 * done / (run.progress.total || 1))}%`;
  const gates = $('gates'); gates.replaceChildren();
  $('gate-context').textContent = current ? 'Gate checks · current' : `Gate checks · at event ${position}`;
  for (const [name, liveGate] of Object.entries(run.gates || {})) {
    const required = run.gate_requirements?.[name];
    // A missing definition must not be replaced with the current verdict during replay.
    if (!current && !Array.isArray(required)) {
      gates.append(el('div', `${name.replaceAll('_', ' ')} · replay unavailable (gate requirements not provided)`, 'gate'));
      continue;
    }
    const missing = current ? liveGate.missing : required.filter(id => !settled(statuses.get(id)));
    const ready = current ? liveGate.ready : missing.length === 0;
    const row = el('div', undefined, 'gate');
    row.append(el('span', name.replaceAll('_', ' ') + (ready ? '' : ` · ${missing.length} missing: ${missing.slice(0, 5).join(', ')}${missing.length > 5 ? '…' : ''}`)), el('span', ready ? 'Ready' : 'Blocked', 'pill ' + (ready ? 'ready' : 'blocked')));
    gates.append(row);
  }
  const metrics = $('metrics'); metrics.replaceChildren();
  const values = Object.values(run.telemetry || {});
  if (!values.length) metrics.append(el('p', 'No measurements yet. Unknown ≠ zero.', 'event-readout'));
  for (const metric of values) {
    const row = el('div', undefined, 'metric-row');
    row.append(el('strong', `${metric.name.replaceAll('_', ' ')} · ${metric.percent == null ? 'Unknown' : metric.percent + '%'}`),
      el('small', `${metric.numerator}/${metric.denominator} ${text(metric.denominator_label)} · ${text(metric.method)}`),
      el('small', `Pointer: ${Array.isArray(metric.evidence) ? metric.evidence.join(', ') : text(metric.evidence)}`));
    metrics.append(row);
  }
  $('branch-summary').textContent = run.options?.deep_comb ? 'Deep-comb route · confirmation gate active' : 'Standard synthetic route · deep-comb off';
  $('branch-value').checked = Boolean(run.options?.deep_comb);
}
function renderTimeline() {
  const events = run.events || [];
  position = Math.max(0, Math.min(position, events.length));
  $('scrub').max = String(events.length); $('scrub').value = String(position);
  $('timeline-label').textContent = `${position} / ${events.length} events`;
  const event = events[position - 1];
  const readout = $('event-readout'); readout.replaceChildren();
  if (event) {
    readout.append(el('strong', `#${event.seq} · ${event.kind.replaceAll('_', ' ')} · ${event.marker || 'run'}`),
      el('span', `${event.at || 'time unknown'} · ${event.kind === 'operation' ? `${text(event.payload?.operation)} → ${text(event.payload?.result)}` : event.kind === 'marker' || event.kind === 'marker_revision' ? label(event.payload?.status) : event.kind === 'measurement' ? text(event.payload?.name) : 'Recorded event'}`));
    // Show the full, bounded synthetic metadata so replay is an inspectable trace,
    // not merely a sequence counter. Use textContent, never interpreted HTML.
    if (event.kind === 'operation') {
      for (const [name, value] of [['input', event.payload?.args], ['prescribed operation', event.payload?.operation],
          ['return', event.payload?.returned], ['result', event.payload?.result], ['evidence', event.payload?.evidence]]) {
        readout.append(el('pre', `${name} → ${fmt(value)}`, 'trace-detail'));
      }
    } else if (['marker', 'marker_revision', 'measurement'].includes(event.kind)) {
      readout.append(el('pre', fmt(event.payload), 'trace-detail'));
    }
  } else readout.textContent = 'Before the first recorded event · no marker claims yet.';
  $('previous').disabled = position === 0; $('next').disabled = position === events.length; $('latest').disabled = position === events.length;
}
function seek(next) { if (!run) return; position = Math.max(0, Math.min(run.events.length, next)); renderTimeline(); renderState(); renderStages(); renderMarkers(); }
function renderActivity() {
  const host = $('activity'); host.replaceChildren();
  for (const event of [...run.events].reverse()) {
    const button = el('button', undefined, 'trace-entry'); button.type = 'button';
    button.setAttribute('aria-label', `Replay event ${event.seq}: ${event.kind} ${event.marker || ''}`);
    button.append(el('span', `#${event.seq} · ${event.kind.replaceAll('_', ' ')}`), document.createTextNode(` · ${event.marker || 'run'} · ${event.kind === 'operation' ? text(event.payload?.operation) + ' → ' + text(event.payload?.result) : event.kind === 'measurement' ? text(event.payload?.name) : event.kind === 'marker' || event.kind === 'marker_revision' ? label(event.payload?.status) : text(event.at)}`));
    button.addEventListener('click', () => { stop(); seek(run.events.indexOf(event) + 1); $('scrub').focus(); });
    host.append(button);
  }
}
function render(updateInspector = false) {
  for (const id of ['run-panel', 'timeline-panel', 'markers-panel', 'activity-panel', 'tools']) $(id).hidden = false;
  renderStages(); renderTimeline(); renderState(); renderMarkers(); renderActivity();
  if (updateInspector) renderInspector();
}
function parsedJSON(id, fallback) {
  const value = $(id).value.trim();
  if (!value) return fallback;
  try { return JSON.parse(value); } catch { throw new Error(`${$(id).labels?.[0]?.textContent || id} must be valid JSON`); }
}
const pointers = id => $(id).value.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
async function writeRun(operation, body, success) {
  if (!run) return;
  const id = run.run;
  await mutation(async () => {
    const data = await request(`${API}/${encodeURIComponent(id)}/${operation}`, 'POST', body());
    if (run?.run === id) setRun(data);
  }, success);
}
$('create').addEventListener('click', () => mutation(async () => {
  const data = await request(API, 'POST', {scenario: $('scenario').value});
  await refreshList(data.run);
  setRun(data);
}, 'Synthetic scenario created. Select markers to explore the contract.'));
$('runs').addEventListener('change', async e => {
  const id = e.target.value;
  if (!id) { clearRun(); feedback(''); return; }
  try { await loadRun(id); } catch (error) { clearRun(); feedback(`Unable to load run: ${error.message}`, true); }
});
$('reset').addEventListener('click', () => {
  if (!runList.length) { feedback('Sandbox is already empty.'); return; }
  if (!confirm(`Delete all ${runList.length} synthetic lab runs? This cannot be undone.`)) return;
  mutation(async () => {
    await request('/lab/api/reset', 'POST', {});
    ++generation; await refreshList('');
  }, 'Sandbox reset. All synthetic runs deleted.');
});
$('delete-run').addEventListener('click', () => {
  if (!run || !confirm(`Delete synthetic run ${run.run}?`)) return;
  mutation(async () => { await request(`${API}/${encodeURIComponent(run.run)}/reset`, 'POST', {}); ++generation; await refreshList(''); }, 'Synthetic run deleted.');
});
$('marker-search').addEventListener('input', () => { if (run) renderMarkers(); });
$('mark-form').addEventListener('submit', event => {
  event.preventDefault();
  writeRun('mark', () => ({marker: markerId, status: $('mark-status').value,
    value: parsedJSON('mark-value', null), evidence: pointers('mark-evidence'), revise: $('mark-revise').checked}), 'Marker claim recorded. Gates and replay updated.');
});
$('branch-apply').addEventListener('click', async () => {
  await writeRun('configure', () => ({key: 'deep_comb', value: $('branch-value').checked}), 'Deep-comb route recorded.');
  if (run) $('branch-value').checked = Boolean(run.options?.deep_comb);
});
$('trace-form').addEventListener('submit', event => {
  event.preventDefault();
  writeRun('trace', () => ({marker: markerId, operation: $('trace-operation').value.trim(), result: $('trace-result').value.trim(),
    inputs: parsedJSON('trace-inputs', {}), outputs: parsedJSON('trace-outputs', {}), evidence: pointers('trace-evidence'), actor: 'lab'}), 'Operation trace appended.');
});
$('metric-form').addEventListener('submit', event => {
  event.preventDefault();
  writeRun('measure', () => ({name: $('metric-name').value.trim(), numerator: Number($('metric-numerator').value),
    denominator: Number($('metric-denominator').value), denominator_label: $('metric-label').value.trim(),
    method: $('metric-method').value.trim(), evidence: $('metric-evidence').value.trim(), actor: 'lab'}), 'Evidence measurement recorded separately from progress.');
});
$('scrub').addEventListener('input', () => { stop(); seek(Number($('scrub').value)); });
$('previous').addEventListener('click', () => { stop(); seek(position - 1); });
$('next').addEventListener('click', () => { stop(); seek(position + 1); });
$('latest').addEventListener('click', () => { stop(); seek(run.events.length); });
$('play').addEventListener('click', () => {
  if (playing) { stop(); return; }
  if (position === run.events.length) seek(0);
  $('play').textContent = 'Pause'; $('play').setAttribute('aria-label', 'Pause timeline');
  playing = setInterval(() => { if (position >= run.events.length) stop(); else seek(position + 1); }, 850);
});
refreshList().catch(error => { clearRun(); feedback(`Lab unavailable: ${error.message}`, true); });
