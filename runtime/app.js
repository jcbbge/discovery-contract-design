(() => {
'use strict';
const $ = id => document.getElementById(id);
const settled = status => status === 'satisfied' || status === 'satisfied_by_rule';
const text = value => value == null ? 'Not recorded' : String(value);
const json = value => JSON.stringify(value, null, 2);
let selected = '', fingerprint = '', busy = false;
function el(tag, content, className) { const node = document.createElement(tag); if (className) node.className = className; if (content != null) node.textContent = text(content); return node; }
function details(className, label, key) { const node = el('details', null, className); node.dataset.key = key; node.append(el('summary', label)); return node; }
function pointer(parent, value) {
  const values = Array.isArray(value) ? value : [value];
  for (const item of values.filter(Boolean)) {
    const line = el('div'); line.append(el('span', item, 'pointer'));
    const copy = el('button', 'Copy pointer', 'copy'); copy.type = 'button';
    copy.setAttribute('aria-label', `Copy evidence pointer ${item}`);
    copy.addEventListener('click', async () => { try { await navigator.clipboard.writeText(item); copy.textContent = 'Copied'; setTimeout(() => copy.textContent = 'Copy pointer', 1500); } catch { copy.textContent = 'Copy unavailable'; } });
    line.append(copy); parent.append(line);
  }
}
function eventDetail(event) {
  const payload = event.payload || {};
  const node = details('trace', `${event.kind === 'operation' ? 'Operation' : 'Recorded change'} · ${event.kind === 'operation' ? text(payload.operation) : event.kind} · ${event.at || 'time unknown'}`, `event-${event.seq}`);
  const body = el('div', null, 'fields');
  if (event.kind === 'operation') {
    for (const [label, value] of [['Input and arguments', payload.args], ['Operation', payload.operation], ['Return', payload.returned], ['Result', payload.result], ['Evidence', payload.evidence]]) {
      const row = el('div'); row.append(el('b', `${label}: `), el('span', typeof value === 'object' ? json(value) : text(value))); body.append(row);
    }
  }
  const raw = details('record', 'Inspect recorded event', `raw-${event.seq}`);
  raw.append(el('pre', json(event))); body.append(raw); node.append(body); return node;
}
function renderCandidates(run) {
  const marker = run.markers.find(item => item.id === 'J03');
  const candidates = Array.isArray(marker?.value?.candidates) ? marker.value.candidates : [];
  const produced = settled(marker?.status) && Array.isArray(marker?.value?.candidates);
  const count = candidates.length;
  const sourceName = run.input_ref.split('/').at(-1);
  $('run-title').textContent = sourceName.replace(/\.segmented\.md$|\.md$/i, '').replaceAll('_', ' ').replace(/\bnathaniel\b/i, 'Nathaniel');
  $('source').textContent = `Input artifact · ${sourceName}`;
  $('fresh').textContent = run.events.length ? `Latest record ${new Date(run.events.at(-1).at).toLocaleString()}` : 'No events yet';
  $('lead').textContent = produced ? 'The numbered output of this recorded Discovery run.' : 'Candidate output has not been recorded for this run.';
  const outcome = $('outcome'); outcome.replaceChildren();
  const topline = el('div', null, 'topline');
  const answer = el('div', null, 'answer');
  answer.append(el('span', produced ? `${count} ` : 'Awaiting ', 'number'), el('span', produced ? `candidate work item${count === 1 ? '' : 's'} produced` : 'candidate list'));
  topline.append(answer); outcome.append(topline);
  outcome.append(el('p', produced ? 'Output recorded. These are candidates, not approved or selected work.' : 'The observer cannot yet say Discovery produced a candidate list.', 'sub'));
  const flow = el('div', null, 'flow'); flow.append(el('span', 'Artifact', 'thing'), el('span', '→', 'arrow'), el('span', 'Discovery', 'thing'), el('span', '→', 'arrow'), el('span', produced ? 'Candidate list' : 'Output pending', 'thing final')); outcome.append(flow);
  $('candidate-count').textContent = produced ? `${count} recorded · original order` : 'Not recorded';
  const list = $('candidates'); list.replaceChildren();
  if (!produced) { list.append(el('p', 'No candidate list has been recorded for this run. This is not a claim that Discovery found nothing.', 'empty')); return; }
  if (!count) { list.append(el('p', 'Discovery recorded zero candidate work items.', 'empty')); return; }
  candidates.forEach((candidate, index) => {
    const item = details('candidate', null, `candidate-${index}`);
    const summary = item.firstElementChild; summary.className = 'candidate-summary';
    summary.append(el('span', `${index + 1}.`, 'num'), el('span', candidate.finding || 'Untitled candidate', 'finding'), el('span', '›', 'chevron'));
    const body = el('div', null, 'candidate-body');
    body.append(el('p', `Recorded as ${text(candidate.id)} · ${text(candidate.lens)} lens. This is a proposed work candidate, not an approved or selected task.`));
    body.append(el('p', 'Source pointer:')); pointer(body, candidate.evidence);
    const sourceLine = typeof candidate.evidence === 'string' && candidate.evidence.startsWith(`${run.input_ref}:`)
      ? candidate.evidence.slice(run.input_ref.length + 1) : '';
    if (/^[1-9][0-9]{0,4}$/.test(sourceLine)) {
      const view = el('button', 'Read source passage', 'copy'); view.type = 'button';
      const passage = el('div', null, 'source-preview');
      view.addEventListener('click', async () => {
        view.disabled = true;
        try {
          const response = await fetchJSON(`/api/runs/${encodeURIComponent(run.run)}/source?line=${sourceLine}`);
          passage.replaceChildren(el('pre', response.lines.map(line => `${line.line}: ${line.text}`).join('\n')));
          view.textContent = 'Source passage shown';
        } catch { passage.replaceChildren(el('p', 'Source passage unavailable. Use the recorded pointer to check the source directly.', 'note')); view.disabled = false; }
      });
      body.append(view, passage);
    }
    if (candidate.attribution) body.append(el('p', `Attribution: ${text(candidate.attribution.kind)}. ${text(candidate.attribution.qualification)}`));
    const record = details('record', 'Inspect exact candidate record and its J03 ledger event', `candidate-record-${index}`);
    record.append(el('pre', json(candidate)));
    const j03 = run.events.filter(e => e.marker === 'J03');
    for (const event of j03) record.append(eventDetail(event));
    body.append(record); item.append(body); list.append(item);
  });
}
function renderSteps(run) {
  const list = $('steps'); list.replaceChildren();
  const stages = run.stages || [];
  $('context').firstElementChild.textContent = `How did it get here? · ${run.progress.done}/${run.progress.total} steps recorded`;
  $('context-note').textContent = `Run ${run.run} · Input ${run.input_ref}. Recorded claims: ${run.progress.done}/${run.progress.total} fixed markers. A checked marker is an agent-reported claim, not independent verification. Open any stage and step for evidence and operation records.`;
  for (const stage of stages) {
    const markers = run.markers.filter(marker => marker.stage === stage.id);
    const done = markers.filter(marker => settled(marker.status)).length;
    const item = details('step', null, `stage-${stage.id}`);
    const summary = item.firstElementChild; summary.className = 'step-summary';
    summary.append(el('span', '›', 'chevron'), el('span', stage.name, 'name'), el('span', `${done}/${markers.length} recorded`, 'count'));
    const body = el('div', null, 'step-body');
    if (done < markers.length) body.append(el('p', 'Some steps here are not settled. Candidate output and subsequent protocol review are distinct.', 'stage-note'));
    for (const marker of markers) {
      const row = details('marker', null, `marker-${marker.id}`);
      const heading = row.firstElementChild;
      heading.append(el('span', `${marker.id} · ${marker.requirement}`, 'marker-title'), el('span', ` — ${marker.status.replaceAll('_', ' ')}`, 'marker-status'));
      const detail = el('div', null, 'marker-detail');
      detail.append(el('p', 'Reported value', 'label'), el('pre', json(marker.value)));
      detail.append(el('p', 'Evidence pointers', 'label')); if (marker.evidence?.length) pointer(detail, marker.evidence); else detail.append(el('p', 'No evidence pointer recorded.', 'note'));
      const events = run.events.filter(event => event.marker === marker.id);
      detail.append(el('p', `Recorded events (${events.length})`, 'label'));
      events.forEach(event => detail.append(eventDetail(event)));
      row.append(detail); body.append(row);
    }
    item.append(body); list.append(item);
  }
  const measurements = $('measure-list'); measurements.replaceChildren();
  const measures = Object.values(run.telemetry || {});
  if (!measures.length) measurements.append(el('p', 'No measurements recorded.', 'note'));
  for (const m of measures) {
    const dl = el('dl'); dl.append(el('dt', `${m.name.replaceAll('_', ' ')}: ${m.numerator} of ${m.denominator} ${m.denominator_label}`));
    dl.append(el('dd', `Method: ${m.method}. Evidence: ${text(m.evidence)}. Recorded ${m.at}. This is telemetry, not step completion.`)); measurements.append(dl);
  }
}
function opened() { return new Set([...document.querySelectorAll('details[open][data-key]')].map(x => x.dataset.key)); }
function restore(keys) { for (const node of document.querySelectorAll('details[data-key]')) if (keys.has(node.dataset.key)) node.open = true; }
async function fetchJSON(path) { const response = await fetch(path, {cache:'no-store'}); if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`); return response.json(); }
async function refresh(force = false) {
  if (!selected || busy) return; busy = true;
  try {
    const run = await fetchJSON(`/api/runs/${encodeURIComponent(selected)}`);
    const stamp = `${run.events.length}:${run.events.at(-1)?.seq || 0}:${run.progress.done}:${run.markers.find(m => m.id === 'J03')?.status}`;
    if (force || fingerprint !== stamp) {
      const keys = opened(); renderCandidates(run); renderSteps(run); restore(keys); fingerprint = stamp;
    }
    $('updated').textContent = `Checked ${new Date().toLocaleTimeString()}.`;
    $('error').hidden = true;
  } catch (error) { $('error').textContent = `Could not read the run. ${error.message}`; $('error').hidden = false; }
  finally { busy = false; }
}
async function init() {
  try {
    const runs = await fetchJSON('/api/runs'); const select = $('runs'); select.replaceChildren();
    if (!runs.length) { select.append(el('option', 'No runs recorded')); $('run-title').textContent = 'No Discovery runs recorded'; $('outcome').replaceChildren(el('p', 'When the existing Discovery workflow records a run, its candidates and execution trail appear here.')); return; }
    runs.forEach(r => { const option = el('option', r.id); option.value = r.id; select.append(option); });
    const requested = new URLSearchParams(location.search).get('run');
    selected = runs.some(r => r.id === requested) ? requested : (runs.find(r => r.id === 'mw-discovery-0902-live-v2') || runs[0]).id;
    select.value = selected; select.disabled = false;
    select.addEventListener('change', () => { selected = select.value; fingerprint = ''; history.replaceState(null, '', `?run=${encodeURIComponent(selected)}`); refresh(true); });
    await refresh(true); setInterval(() => refresh(), 6000);
  } catch (error) { $('error').textContent = `Could not list recorded runs. ${error.message}`; $('error').hidden = false; $('run-title').textContent = 'Discovery unavailable'; }
}
init();
})();
