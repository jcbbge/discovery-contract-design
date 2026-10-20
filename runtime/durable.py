#!/usr/bin/env python3
"""Local contract runner: pinned definition, append-only audit, fixed progress, read-only UI."""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote, parse_qs

HOME = Path(os.environ.get('PIPELINE_HOME', str(Path.home() / '.local/state/pipeline-observer'))).expanduser()
DEFAULT = Path(__file__).resolve().parent / 'contracts/made-well-discovery-v2.json'
SETTLED = {'satisfied', 'satisfied_by_rule'}
STATUSES = SETTLED | {'pending', 'in_progress', 'blocked', 'failed'}

def now(): return datetime.now(timezone.utc).isoformat()
def canonical(obj): return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
def fail(message): raise ValueError(message)

def connect():
    HOME.mkdir(parents=True, exist_ok=True, mode=0o700)
    db = sqlite3.connect(HOME / 'runs.sqlite', timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA busy_timeout=10000')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, contract TEXT NOT NULL, digest TEXT NOT NULL,
      input_ref TEXT NOT NULL, mode TEXT NOT NULL, options TEXT NOT NULL, created TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS markers (run_id TEXT NOT NULL, marker TEXT NOT NULL, status TEXT NOT NULL,
      value TEXT, evidence TEXT NOT NULL DEFAULT '[]', updated TEXT NOT NULL,
      PRIMARY KEY(run_id,marker), FOREIGN KEY(run_id) REFERENCES runs(id));
    CREATE TABLE IF NOT EXISTS events (seq INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL,
      at TEXT NOT NULL, kind TEXT NOT NULL, marker TEXT, payload TEXT NOT NULL);
    ''')
    return db

def contract_for(db, run_id):
    row = db.execute('SELECT * FROM runs WHERE id=?', (run_id,)).fetchone()
    if not row: fail(f'unknown run: {run_id}')
    doc = json.loads(row['contract'])
    if hashlib.sha256(row['contract'].encode()).hexdigest() != row['digest']:
        fail('stored contract digest mismatch')
    return row, doc

def state(db, run_id, with_events=True):
    row, doc = contract_for(db, run_id)
    found = {m['marker']: dict(m) for m in db.execute('SELECT * FROM markers WHERE run_id=?', (run_id,))}
    markers = []
    for m in doc['markers']:
        r = found.get(m['id'])
        markers.append({**m, 'status': r['status'] if r else 'pending',
                        'value': json.loads(r['value']) if r and r['value'] else None,
                        'evidence': json.loads(r['evidence']) if r else [],
                        'updated': r['updated'] if r else None})
    done = sum(m['status'] in SETTLED for m in markers)
    assert len(markers) == doc['progress']['denominator']
    statuses = {m['id']: m['status'] for m in markers}
    gates = {name: {'ready': all(statuses[k] in SETTLED for k in keys),
                    'missing': [k for k in keys if statuses[k] not in SETTLED]}
             for name, keys in doc['gates'].items()}
    result = {'run': row['id'], 'input_ref': row['input_ref'], 'mode': row['mode'],
              'options': json.loads(row['options']), 'created': row['created'],
              'contract_id': doc['id'], 'contract_version': doc['version'], 'contract_digest': row['digest'],
              'progress': {'done': done, 'total': len(markers), 'percent': round(done * 100 / len(markers), 1)},
              'stages': doc['stages'], 'markers': markers, 'gates': gates}
    if with_events:
        result['events'] = [{'seq': e['seq'], 'at': e['at'], 'kind': e['kind'], 'marker': e['marker'],
                             'payload': json.loads(e['payload'])} for e in db.execute(
                                 'SELECT * FROM events WHERE run_id=? ORDER BY seq', (run_id,))]
    measures = {}
    for e in db.execute("SELECT * FROM events WHERE run_id=? AND kind='measurement' ORDER BY seq", (run_id,)):
        data = json.loads(e['payload'])
        measures[data['name']] = {**data, 'at': e['at'], 'seq': e['seq']}
    result['telemetry'] = measures
    return result

def event(db, run_id, kind, marker=None, payload=None):
    db.execute('INSERT INTO events(run_id,at,kind,marker,payload) VALUES (?,?,?,?,?)',
               (run_id, now(), kind, marker, canonical(payload or {})))

def verify_source_snapshot(doc):
    """Require a matching on-disk file-byte snapshot for new v2 runs, before creating state."""
    if doc.get('schema') == 'pipeline-contract/v1' and doc.get('version') == 1:
        print('warning: v1 has legacy, incomplete provenance; source hashes are not checked for new runs', file=sys.stderr)
        return
    if doc.get('schema') != 'pipeline-contract/v2' or doc.get('version') != 2:
        fail('unsupported contract schema/version')
    hashes = doc.get('source_hashes')
    if not isinstance(hashes, dict) or len(hashes) != 6:
        fail('v2 requires the six-file source snapshot (five governing files and marker inventory)')
    for name, expected in hashes.items():
        if not isinstance(name, str) or not Path(name).is_absolute() or not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
            fail('invalid v2 source snapshot entry')
        try:
            actual = hashlib.sha256(Path(name).read_bytes()).hexdigest()
        except OSError as exc:
            fail(f'v2 source snapshot unavailable: {name}: {exc}')
        if actual != expected:
            fail(f'v2 source snapshot SHA256 mismatch: {name}; create a new contract version from reviewed sources')

def initialize(args):
    doc = json.loads(Path(args.contract).read_text())
    verify_source_snapshot(doc)
    ids = [m['id'] for m in doc['markers']]
    if len(ids) != len(set(ids)) or len(ids) != doc['progress']['denominator']: fail('invalid contract marker set')
    if args.mode == 'blind' and (args.paired_answer_key or args.paired and not args.paired_primary):
        fail('blind paired source must be declared primary and not an answer key')
    run_id = args.id or str(uuid.uuid4())
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,123}', run_id): fail('invalid run ID')
    opts = {'paired': args.paired, 'deep_comb': args.deep_comb, 'prd': args.prd,
            'live_conversation': args.live_conversation, 'trade': args.trade,
            'in_flight': args.in_flight, 'paired_primary': args.paired_primary}
    c = canonical(doc)
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('INSERT INTO runs VALUES (?,?,?,?,?,?,?)',
                   (run_id, c, hashlib.sha256(c.encode()).hexdigest(), args.input_ref, args.mode, canonical(opts), now()))
        event(db, run_id, 'run_created', payload={'input_ref': args.input_ref, 'mode': args.mode,
                                                 'options': opts, 'contract_version': doc['version']})
        # The CLI records the declared mode before examining source, not the unverified rack or Ground result.
        db.execute('INSERT INTO markers VALUES (?,?,?,?,?,?)',
                   (run_id, 'A01', 'satisfied', canonical({'mode': args.mode}), canonical(['A01:declaration']), now()))
        event(db, run_id, 'marker', 'A01', {'status': 'satisfied', 'value': {'mode': args.mode}, 'evidence': ['A01:declaration']})
    print(f'{run_id}: declared {args.mode}, 1/{len(ids)}; use mark for Ground and rack declarations')

def configure(args):
    dependency = {'paired': ('B04','L01','L02','L03','L04'), 'deep_comb': ('E02','E03','E04','E05','E06'),
                  'prd': ('I01','I02','I03','I04','I05'), 'trade': ('F07',),
                  'in_flight': ('J05',), 'live_conversation': ('N01','N02','N03')}
    if args.key not in dependency: fail('unknown option; choose one of '+', '.join(dependency))
    value = args.value == 'true'
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row,_ = contract_for(db,args.run)
        current = json.loads(row['options'])
        if current[args.key] == value: print('no change'); return
        done = {r['marker'] for r in db.execute('SELECT marker FROM markers WHERE run_id=? AND status IN (?,?)',
                                                (args.run,*SETTLED))}
        if done.intersection(dependency[args.key]):
            fail('option already used by settled markers: '+', '.join(sorted(done.intersection(dependency[args.key]))))
        if args.key == 'paired' and value and row['mode']=='blind' and not current.get('paired_primary'):
            fail('blind paired input must be explicitly certified as a permitted primary source')
        current[args.key]=value
        db.execute('UPDATE runs SET options=? WHERE id=?',(canonical(current),args.run))
        event(db,args.run,'option_changed',payload={'key':args.key,'from':not value,'to':value})
    print(f'{args.run} {args.key}={value}')

def allowed_bypass(marker, row, opts):
    if marker.startswith('C') and row['mode'] == 'blind': return 'blind: Ground prohibited'
    if marker in {'B01', 'B02', 'B03'} and row['mode'] == 'blind': return 'blind: answer-key context withheld'
    if marker == 'B04' and not opts['paired']: return 'no paired artifact'
    if marker in {'E03','E04','E05','E06'} and not opts['deep_comb']: return 'single-pass or cross-artifact route'
    if marker == 'F07' and not opts['trade']: return 'no loaded trade'
    if marker in {'I02','I03','I04','I05'} and not opts['prd']: return 'not a PRD/compression document'
    if marker in {'L02','L03','L04'} and not opts['paired']: return 'no paired artifact'
    if marker == 'J05' and not opts['in_flight']: return 'no in-flight finding'
    if marker in {'N02','N03'} and not opts['live_conversation']: return 'supplied artifact, not live conversation'
    if marker in {'M04','M05'} and opts.get('operator_unavailable'): return 'operator unavailable; no ruling to capture'
    return None

# Evidence is an address, not a substitute for the corpus. Never persist an unaddressable
# assertion as a settled marker. A01 points to its start declaration, before source read.
POINTER = re.compile(r'^(?:[^\s:#]+(?:/[^\s:#]+)*)(?::[1-9][0-9]*(?:-[1-9][0-9]*)?|#[A-Za-z0-9._/-]+)$')
MARKER_POINTER = re.compile(r'^[A-Z][0-9]{2}:[A-Za-z0-9._/-]+$')

def pointer(p):
    return isinstance(p, str) and len(p) <= 256 and bool(POINTER.fullmatch(p) or MARKER_POINTER.fullmatch(p))

def require_pointer(p, label):
    if not pointer(p): fail(f'{label} needs a checkable file:line, file#anchor or marker:record pointer (not raw material)')

def text(p, label):
    if not isinstance(p, str) or not p.strip() or len(p) > 256: fail(f'{label} needs a short nonempty string')

def citation(p, label):
    if not isinstance(p, dict): fail(f'{label} needs a structured citation')
    text(p.get('summary'), label+'.summary')
    require_pointer(p.get('pointer'), label+'.pointer')

def ledger(value, marker):
    if not isinstance(value, dict): fail(f'{marker} needs a structured Ground ledger')
    if marker == 'C05':
        entries = value.get('corpus')
        if not isinstance(entries, list) or not entries: fail('C05 needs corpus table rows')
        for entry in entries:
            if not isinstance(entry, dict): fail('C05 corpus row must be an object')
            for field in ('path','what','relevance','summary'): text(entry.get(field), 'C05.'+field)
            require_pointer(entry.get('pointer'), 'C05 corpus row')
        for field in ('locked_decisions','open_questions'):
            entries = value.get(field)
            if not isinstance(entries, list): fail('C05 needs '+field+' list (empty if none)')
            for entry in entries:
                if not isinstance(entry, dict): fail('C05 '+field+' entry must be an object')
                text(entry.get('summary'), 'C05 '+field)
                if field == 'open_questions' and entry.get('pointer') == 'UNKNOWN': continue
                require_pointer(entry.get('pointer'), 'C05 '+field)
        citation(value.get('synthesis'), 'C05 synthesis')
    elif marker == 'C06':
        entries = value.get('surfaces')
        if not isinstance(entries, list) or not entries: fail('C06 needs material surface rows (explicit NET-NEW if absent)')
        for entry in entries:
            if not isinstance(entry, dict): fail('C06 surface must be an object')
            for field in ('path','summary'): text(entry.get(field), 'C06.'+field)
            if entry.get('verdict') not in ('BUILT','PARTIAL','NET-NEW'): fail('C06 needs typed surface verdict')
            if entry['verdict']=='NET-NEW':
                if entry.get('lines') is not None: fail('C06 NET-NEW has no material line range; cite search result')
            else:
                if not isinstance(entry.get('lines'), list) or len(entry['lines']) != 2 or any(type(n) is not int or n < 1 for n in entry['lines']):
                    fail('C06 needs [first,last] line range for existing surface')
                if entry['lines'][0] > entry['lines'][1]: fail('C06 line range reversed')
            require_pointer(entry.get('pointer'), 'C06 surface')
        citation(value.get('gap'), 'C06 gap')
        entries = value.get('contradictions')
        if not isinstance(entries, list): fail('C06 needs contradictions list (empty if none)')
        for entry in entries: citation(entry, 'C06 contradiction')
    else:
        for field in ('required','actual','next_move'): citation(value.get(field), 'C11 '+field)
        for field in ('locked_decisions','open_decisions'):
            entries=value.get(field)
            if not isinstance(entries,list): fail('C11 needs '+field+' list (empty if none)')
            for entry in entries:
                citation(entry, 'C11 '+field)
                if field == 'open_decisions' and entry.get('owner') not in ('lead','external'):
                    fail('C11 open decision needs lead or external owner')

def validate_candidates(value):
    if not isinstance(value, dict) or not isinstance(value.get('candidates'), list):
        fail('J03 needs candidates array (empty when none)')
    seen=set()
    for candidate in value['candidates']:
        if not isinstance(candidate,dict): fail('J03 candidate must be an object')
        for field in ('id','lens','finding'): text(candidate.get(field), 'J03 '+field)
        if candidate['id'] in seen: fail('J03 duplicate candidate ID')
        seen.add(candidate['id'])
        if candidate.get('disposition') not in ('rack','decision','release'):
            fail('J03 disposition must be rack, decision or release')
        require_pointer(candidate.get('evidence'), 'J03 evidence')
        attribution=candidate.get('attribution')
        if not isinstance(attribution,dict) or attribution.get('kind') not in ('stated','inferred'):
            fail('J03 attribution needs stated/inferred kind')
        if attribution['kind']=='inferred': text(attribution.get('qualification'), 'J03 inferred attribution qualification')

def classification(db, run, marker, field, expected):
    record=db.execute('SELECT status,value FROM markers WHERE run_id=? AND marker=?',(run,marker)).fetchone()
    if not record or record['status'] not in SETTLED or not record['value'] or json.loads(record['value']).get(field) != expected:
        fail(f'bypass requires settled {marker} classification {field}={expected!r}')

def validate_bypass_context(db, run, marker, row, opts):
    if marker.startswith('C') or marker in ('B01','B02','B03'):
        classification(db,run,'A01','mode','blind')
    elif marker == 'B04' or marker in ('L02','L03','L04'):
        classification(db,run,'L01','paired',False)
    elif marker in ('E03','E04','E05','E06'):
        route = 'cross-artifact' if opts['paired'] else 'single-pass'
        classification(db,run,'E02','route',route)
    elif marker in ('I02','I03','I04','I05'):
        classification(db,run,'I01','prd',False)
    elif marker == 'J05': classification(db,run,'J01','in_flight',False)
    elif marker in ('N02','N03'): classification(db,run,'N01','live_conversation',False)

def review_value(value):
    if not isinstance(value,dict) or value.get('review') not in ('confirmed','unavailable'):
        fail('M03 requires review confirmed or unavailable; waiting is not settled')
    request=value.get('request')
    if not isinstance(request,dict) or request.get('question') != 'Does that match what you meant?':
        fail('M03 needs explicit review request with canonical question')
    times=[]
    for label, entry in (('request',request), ('reply' if value['review']=='confirmed' else 'open_question',
                          value.get('reply') if value['review']=='confirmed' else value.get('open_question'))):
        if not isinstance(entry,dict): fail('M03 needs '+label+' record')
        try:
            stamp=datetime.fromisoformat(entry['at'])
            if stamp.tzinfo is None or stamp.utcoffset() is None: raise ValueError()
            times.append(stamp)
        except (ValueError,TypeError,KeyError): fail('M03 '+label+' needs ISO timestamp with timezone')
        require_pointer(entry.get('pointer'), 'M03 '+label)
    if times[1] < times[0]: fail('M03 reply/open question cannot precede request')
    if value['review']=='unavailable' and value.get('reply'): fail('M03 unavailable cannot contain a reply')

def update(args):
    if args.status not in STATUSES: fail('invalid status')
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        row, doc = contract_for(db, args.run)
        ids = {m['id'] for m in doc['markers']}
        if args.marker not in ids: fail(f'unknown marker: {args.marker}')
        opts = json.loads(row['options'])
        review = db.execute("SELECT value FROM markers WHERE run_id=? AND marker='M03'", (args.run,)).fetchone()
        opts['operator_unavailable'] = bool(review and review['value'] and json.loads(review['value']).get('review') == 'unavailable')
        prior = db.execute('SELECT status FROM markers WHERE run_id=? AND marker=?', (args.run,args.marker)).fetchone()
        if prior and prior['status'] in SETTLED and not args.revise:
            fail('settled marker is immutable; --revise appends a correction event')
        evidence = args.evidence or []
        value = json.loads(args.value) if args.value else None
        if args.status in SETTLED:
            if not evidence: fail('settled marker needs --evidence pointer')
            for p in evidence: require_pointer(p, 'settlement evidence')
        if args.status == 'satisfied_by_rule':
            rule = allowed_bypass(args.marker, row, opts)
            if not rule: fail('no contract-authorized bypass for this marker and run options')
            if not isinstance(value, dict) or value.get('rule') != rule:
                fail(f'bypass must provide --value JSON with exact rule: {rule}')
            validate_bypass_context(db, args.run, args.marker, row, opts)
            if args.marker == 'F07' and value.get('trade_loaded') is not False:
                fail('F07 bypass must classify trade_loaded=false')
        if args.status == 'satisfied' and args.marker in ('A02','A03'):
            if not isinstance(value,dict): fail('A02/A03 needs mode disposition')
            if args.marker == 'A02' and value.get('ground') != ('on' if row['mode']=='live' else 'skipped (blind)'):
                fail('A02 Ground declaration must agree with run mode')
            if args.marker == 'A03':
                rack=value.get('rack')
                if rack not in ('loaded','not loaded') or (row['mode']=='blind' and rack!='not loaded') or (rack=='not loaded' and not value.get('reason')):
                    fail('A03 rack declaration must agree with mode; not loaded needs reason')
        if args.status == 'satisfied' and args.marker.startswith('C') and row['mode'] == 'blind':
            fail('blind run cannot perform Ground')
        if args.status == 'satisfied' and args.marker in {'B01','B02','B03'} and row['mode'] == 'blind':
            fail('blind run cannot read withheld context')
        if args.status == 'satisfied' and args.marker in ('E02','I01','L01','N01','J01'):
            field,expected={'E02':('route','deep-comb' if opts['deep_comb'] else 'cross-artifact' if opts['paired'] else 'single-pass'),
                'I01':('prd',opts['prd']),'L01':('paired',opts['paired']),
                'N01':('live_conversation',opts['live_conversation']),'J01':('in_flight',opts['in_flight'])}[args.marker]
            if not isinstance(value,dict) or value.get(field) != expected:
                fail(f'{args.marker} requires {field}={expected!r} consistent with run options')
        if args.status == 'satisfied' and args.marker in ('C05','C06','C11'):
            ledger(value,args.marker)
        if args.status == 'satisfied' and args.marker == 'J03': validate_candidates(value)
        if args.marker == 'M07' and args.status == 'satisfied':
            current = state(db, args.run, False)
            if not current['gates']['publish']['ready']:
                fail('publish gate blocked: '+','.join(current['gates']['publish']['missing']))
            review = next(m for m in current['markers'] if m['id']=='M03')['value']
            if not review or review.get('review') not in ('confirmed','unavailable'):
                fail('M03 must record review confirmed or operator unavailable')
            if review['review'] == 'unavailable':
                if not isinstance(value,dict): fail('operator unavailable: M07 must cite open_question')
                require_pointer(value.get('open_question'), 'M07 open_question')
        if args.marker == 'M03' and args.status == 'satisfied':
            review_value(value)
            completed = {m['id']:m['status'] for m in state(db,args.run,False)['markers']}
            if completed['M01'] not in SETTLED or completed['M02'] not in SETTLED:
                fail('draft and reflection must precede review')
        if args.marker == 'H02' and args.status == 'satisfied':
            m = {x['id']: x for x in state(db,args.run,False)['markers']}
            if m['M03']['status'] not in SETTLED: fail('One Thing destination requires review/unavailability decision')
            if not isinstance(value,dict) or value.get('destination') not in ('PRODUCT.md','DECISIONS.md','stock'):
                fail('H02 requires a final authorized destination')
        at = now()
        db.execute('INSERT INTO markers VALUES (?,?,?,?,?,?) ON CONFLICT(run_id,marker) DO UPDATE SET status=excluded.status,value=excluded.value,evidence=excluded.evidence,updated=excluded.updated',
                   (args.run,args.marker,args.status,canonical(value) if value is not None else None,canonical(evidence),at))
        event(db,args.run,'marker_revision' if prior and args.revise else 'marker',args.marker,
              {'status':args.status,'value':value,'evidence':evidence,'prior':prior['status'] if prior else None})
    print(f'{args.run} {args.marker}: {args.status}')

# Traces are bounded metadata, never raw captures. Reject before any event is written.
FORBIDDEN_TRACE_KEY = re.compile(r'(?:body|transcript|content|text|secret|password|token|credential|authorization|api[_-]?key)',re.I)
def safe_trace_shape(obj):
    budget=[0]
    def walk(v, depth):
        budget[0]+=1
        if budget[0]>100 or depth>5: fail('trace metadata too large; use source pointers')
        if isinstance(v,dict):
            if len(v)>30: fail('trace object too wide; use source pointers')
            for k,item in v.items():
                if not isinstance(k,str) or len(k)>64 or FORBIDDEN_TRACE_KEY.search(k):
                    fail('trace contains forbidden raw/secret field; use source pointers')
                walk(item,depth+1)
        elif isinstance(v,list):
            if len(v)>30: fail('trace array too wide; use source pointers')
            for item in v: walk(item,depth+1)
        elif isinstance(v,str):
            if len(v)>256: fail('trace string too long; use source pointers, not raw material')
        elif v is not None and type(v) not in (int,float,bool): fail('invalid trace scalar')
    if not isinstance(obj,dict): fail('trace inputs and outputs must be JSON objects of metadata; use source pointers')
    walk(obj,0)
    if len(canonical(obj).encode())>4096: fail('trace metadata too large; use source pointers')

def trace(args):
    inputs=json.loads(args.inputs); outputs=json.loads(args.outputs)
    for obj in (inputs,outputs): safe_trace_shape(obj)
    for label, val in (('operation',args.operation),('result',args.result),('actor',args.actor)):
        text(val,'trace '+label)
    for p in args.evidence or []: require_pointer(p,'trace evidence')
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        _,doc=contract_for(db,args.run)
        if args.marker not in {m['id'] for m in doc['markers']}: fail('unknown marker')
        event(db,args.run,'operation',args.marker,{'operation':args.operation,'args':inputs,
              'returned':outputs,'result':args.result,'evidence':args.evidence or [],'actor':args.actor})
    print(f'{args.run} {args.marker}: traced {args.operation}')

def measure(args):
    if args.numerator < 0 or args.denominator < 0 or args.numerator > args.denominator:
        fail('require 0 <= numerator <= denominator; use denominator 0 for empty population')
    if not re.fullmatch('[a-z][a-z0-9_]{1,63}',args.name): fail('invalid metric name')
    with connect() as db:
        db.execute('BEGIN IMMEDIATE'); contract_for(db,args.run)
        event(db,args.run,'measurement',payload={
            'name':args.name,'numerator':args.numerator,'denominator':args.denominator,
            'denominator_label':args.denominator_label,'percent':round(100*args.numerator/args.denominator,1) if args.denominator else None,
            'method':args.method,'evidence':args.evidence,'actor':args.actor})
    print(f'{args.run} {args.name}: {args.numerator}/{args.denominator}; not workflow progress')

def summary(args):
    with connect() as db:
        if args.run:
            s=state(db,args.run, args.events)
            if args.json: print(json.dumps(s,indent=2)); return
            print(f"{s['run']} {s['contract_id']} v{s['contract_version']} {s['progress']['done']}/{s['progress']['total']} ({s['progress']['percent']}%) mode={s['mode']}")
            for stage in s['stages']:
                subset=[m for m in s['markers'] if m['stage']==stage['id']]
                count=sum(m['status'] in SETTLED for m in subset)
                print(f"  {stage['id']} {stage['name']}: {count}/{len(subset)}")
                if args.detail:
                    for m in subset: print(f"    {m['id']} [{m['status']}] {m['requirement']}")
            for gate,v in s['gates'].items():
                if not v['ready']: print(f"  gate {gate}: blocked ({', '.join(v['missing'])})")
            for key,m in s['telemetry'].items():
                print(f"  metric {key}: {m['numerator']}/{m['denominator']} {m['denominator_label']} ({m['percent'] if m['percent'] is not None else 'n/a'}%) evidence={m['evidence']}")
            if args.events:
                for e in s['events']:
                    print(f"  #{e['seq']} {e['at']} {e['kind']} {e['marker'] or ''} {canonical(e['payload'])}")
        else:
            rows=db.execute('SELECT id FROM runs ORDER BY created DESC').fetchall()
            for r in rows:
                s=state(db,r['id'],False)
                print(f"{s['run']} {s['progress']['done']}/{s['progress']['total']} ({s['progress']['percent']}%) {s['input_ref']}")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=urlparse(self.path).path
        if path == '/lab/' or path == '/lab/app.js' or path.startswith('/lab/api/'):
            from lab_server import handle
            return handle(self, 'GET', path)
        if path in ('/', '/app.js'):
            filename = 'index.html' if path == '/' else 'app.js'
            body=(Path(__file__).parent/filename).read_bytes()
            self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8' if path=='/' else 'application/javascript; charset=utf-8')
        elif path in ('/fonts/Geist-Regular.ttf', '/fonts/Geist-Medium.ttf', '/fonts/Geist-Bold.ttf'):
            body = (Path(__file__).parent / path.lstrip('/')).read_bytes()
            self.send_response(200); self.send_header('Content-Type', 'font/ttf')
        elif path=='/api/runs':
            with connect() as db:
                body=json.dumps([{'id':r['id'],'input_ref':r['input_ref']} for r in db.execute('SELECT id,input_ref FROM runs ORDER BY created DESC')]).encode()
            self.send_response(200);self.send_header('Content-Type','application/json')
        elif path.startswith('/api/runs/') and path.endswith('/source'):
            name = unquote(path[len('/api/runs/'):-len('/source')])
            query = parse_qs(urlparse(self.path).query)
            try:
                line_text = query.get('line', [''])[0]
                if not re.fullmatch(r'[1-9][0-9]{0,4}', line_text): raise ValueError('invalid line')
                line = int(line_text)
                with connect() as db: run = state(db, name, False)
                source = Path(run['input_ref']).resolve(strict=True)
                corpus = (Path.home() / 'projects/infinity/discovery/transcripts').resolve()
                if corpus not in source.parents or not source.name.endswith('.segmented.md'):
                    raise ValueError('source not available for preview')
                j03 = next((m for m in run['markers'] if m['id'] == 'J03'), {})
                candidates = (j03.get('value') or {}).get('candidates', [])
                if not any(c.get('evidence') == f'{source}:{line}' for c in candidates):
                    raise ValueError('not a recorded candidate source pointer')
                if source.stat().st_size > 2_000_000: raise ValueError('source too large')
                lines = source.read_text(encoding='utf-8').splitlines()
                if line > len(lines): raise ValueError('line out of range')
                snippets = [{'line': n, 'text': lines[n-1][:1600]} for n in range(max(1,line-2),min(len(lines),line+2)+1)]
                body = json.dumps({'pointer': f'{source}:{line}', 'lines': snippets}).encode()
            except (ValueError, OSError, UnicodeError, TypeError):
                self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type','application/json')
        elif path.startswith('/api/runs/'):
            name=unquote(path[len('/api/runs/'):])
            try:
                with connect() as db: body=json.dumps(state(db,name)).encode()
            except ValueError:
                self.send_error(404);return
            self.send_response(200);self.send_header('Content-Type','application/json')
        else: self.send_error(404);return
        self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'")
        self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def do_POST(self):
        path=urlparse(self.path).path
        if path.startswith('/lab/api/'):
            from lab_server import handle
            return handle(self, 'POST', path)
        self.send_error(404)
    def log_message(self,*args): pass

def main():
    p=argparse.ArgumentParser(description='Fixed-contract work ledger (never stores raw transcripts)')
    commands=p.add_subparsers(dest='command',required=True)
    c=commands.add_parser('start');c.add_argument('input_ref');c.add_argument('--id');c.add_argument('--contract',default=str(DEFAULT));c.add_argument('--mode',choices=['live','blind'],required=True)
    for flag in ('paired','paired-answer-key','paired-primary','deep-comb','prd','live-conversation','trade','in-flight'):
        c.add_argument('--'+flag,action='store_true',dest=flag.replace('-','_'))
    c.set_defaults(func=initialize)
    c=commands.add_parser('configure');c.add_argument('run');c.add_argument('key');c.add_argument('value',choices=['true','false']);c.set_defaults(func=configure)
    c=commands.add_parser('mark');c.add_argument('run');c.add_argument('marker');c.add_argument('--status',choices=sorted(STATUSES),required=True);c.add_argument('--value',help='JSON value');c.add_argument('--evidence',action='append');c.add_argument('--revise',action='store_true');c.set_defaults(func=update)
    c=commands.add_parser('trace');c.add_argument('run');c.add_argument('marker');c.add_argument('operation');c.add_argument('--inputs',default='{}');c.add_argument('--outputs',default='{}');c.add_argument('--result',required=True);c.add_argument('--evidence',action='append');c.add_argument('--actor',default='agent');c.set_defaults(func=trace)
    c=commands.add_parser('measure');c.add_argument('run');c.add_argument('name');c.add_argument('numerator',type=int);c.add_argument('denominator',type=int);c.add_argument('--denominator-label',required=True);c.add_argument('--method',required=True);c.add_argument('--evidence',required=True);c.add_argument('--actor',default='agent');c.set_defaults(func=measure)
    c=commands.add_parser('status');c.add_argument('run',nargs='?');c.add_argument('--detail',action='store_true');c.add_argument('--events',action='store_true');c.add_argument('--json',action='store_true');c.set_defaults(func=summary)
    c=commands.add_parser('serve');c.add_argument('--port',type=int,default=8787);c.set_defaults(func=lambda a: (print(f'Open http://127.0.0.1:{a.port}/',flush=True),ThreadingHTTPServer(('127.0.0.1',a.port),Handler).serve_forever()))
    a=p.parse_args()
    try: a.func(a)
    except (ValueError,sqlite3.IntegrityError,json.JSONDecodeError) as e:
        print(f'error: {e}',file=sys.stderr);sys.exit(2)
if __name__=='__main__': main()
