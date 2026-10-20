"""Opt-in localhost lab HTTP adapter; durable CLI validates all workflow writes."""
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import uuid
from pathlib import Path
from urllib.parse import unquote

import durable

LAB_HOME = Path.home() / '.local/state/pipeline-observer-lab'
CLI = Path(__file__).resolve().parent / 'durable.py'
SCENARIOS = ('empty', 'preflight', 'deep-comb-awaiting-confirmation', 'review-gate')
RUN_ID = re.compile(r'lab-[0-9a-f]{32}\Z')
# Pointers are explicitly synthetic; these are not claims that a corpus exists.
REF = 'lab/synthetic-fixture.md#simulation'
EVIDENCE = 'lab/synthetic-fixture.md#simulation'

class BadRequest(Exception):
    pass


def fields(obj, required, optional=()):
    if not isinstance(obj, dict) or not set(required) <= obj.keys() or obj.keys() - set(required) - set(optional):
        raise BadRequest('invalid fields; expected ' + ', '.join((*required, *optional)))


def metadata(obj):
    """Only bounded synthetic metadata; never accept capture/transcript payload fields."""
    count = [0]
    def walk(value, depth):
        count[0] += 1
        if count[0] > 100 or depth > 5:
            raise BadRequest('metadata too large')
        if isinstance(value, dict):
            if len(value) > 30: raise BadRequest('metadata too wide')
            for key, item in value.items():
                if not isinstance(key, str) or len(key) > 64 or durable.FORBIDDEN_TRACE_KEY.search(key):
                    raise BadRequest('raw or secret field forbidden')
                walk(item, depth + 1)
        elif isinstance(value, list):
            if len(value) > 30: raise BadRequest('metadata too wide')
            for item in value: walk(item, depth + 1)
        elif isinstance(value, str):
            if len(value) > 256: raise BadRequest('metadata string too long')
        elif type(value) is float and not math.isfinite(value):
            raise BadRequest('nonfinite metadata')
        elif value is not None and type(value) not in (int, float, bool):
            raise BadRequest('invalid metadata')
    walk(obj, 0)
    if len(durable.canonical(obj).encode()) > 4096: raise BadRequest('metadata too large')


def string(value, label, pointer=False):
    durable.text(value, label)
    if pointer: durable.require_pointer(value, label)
    return value


def lab_path():
    root = LAB_HOME.expanduser().absolute()
    productions = (durable.HOME.expanduser().resolve(),
                   (Path.home() / '.local/state/pipeline-observer').resolve())
    if root.is_symlink() or any((root / suffix).is_symlink() for suffix in
                                ('runs.sqlite', 'runs.sqlite-wal', 'runs.sqlite-shm')):
        raise BadRequest('lab storage symlink refused')
    real = root.resolve()
    for production in productions:
        if real == production or production in real.parents or real in production.parents:
            raise BadRequest('lab storage overlaps production')
        if (root / 'runs.sqlite').exists() and (production / 'runs.sqlite').exists() and (
                root / 'runs.sqlite').samefile(production / 'runs.sqlite'):
            raise BadRequest('lab database aliases production')
    return root


def cli(*argv):
    root = lab_path()
    env = dict(os.environ)
    env['PIPELINE_HOME'] = str(root)
    try:
        result = subprocess.run([sys.executable, str(CLI), *argv], env=env,
                                capture_output=True, text=True, timeout=15, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise BadRequest('lab CLI timed out')
    if result.returncode:
        raise BadRequest(result.stderr.strip()[:500] or 'lab CLI rejected operation')
    return result.stdout


def snapshot(run):
    if not RUN_ID.fullmatch(run): raise BadRequest('invalid lab run ID')
    root = lab_path()
    if not (root / 'runs.sqlite').exists(): raise BadRequest('unknown lab run')
    try:
        with sqlite3.connect(f'file:{root / "runs.sqlite"}?mode=ro', uri=True) as db:
            db.row_factory = sqlite3.Row
            result = durable.state(db, run)
            _, contract = durable.contract_for(db, run)
            result['gate_requirements'] = contract['gates']
            return result
    except (sqlite3.Error, ValueError, AssertionError) as exc:
        raise BadRequest('unknown or invalid lab run') from exc


def runs():
    root = lab_path()
    if not (root / 'runs.sqlite').exists(): return []
    with sqlite3.connect(f'file:{root / "runs.sqlite"}?mode=ro', uri=True) as db:
        return [{'id': row[0], 'scenario': next((e['payload']['scenario'] for e in snapshot(row[0])['events']
                 if e['kind'] == 'lab_scenario'), 'empty')} for row in db.execute(
                    "SELECT id FROM runs WHERE id LIKE 'lab-%' ORDER BY created DESC LIMIT 100") if RUN_ID.fullmatch(row[0])]


def mark(run, marker, status, value=None, evidence=None, revise=False):
    argv = ['mark', run, marker, '--status', status]
    if value is not None: argv += ['--value', durable.canonical(value)]
    for item in evidence or []: argv += ['--evidence', item]
    if revise: argv += ['--revise']
    cli(*argv)


def create(scenario):
    if scenario not in SCENARIOS: raise BadRequest('unknown scenario')
    run = 'lab-' + uuid.uuid4().hex
    flags = ['--deep-comb'] if scenario == 'deep-comb-awaiting-confirmation' else []
    cli('start', REF, '--id', run, '--mode', 'live', *flags)
    # Seed via the same validators as normal runs. Failed seeds leave a visible
    # incomplete lab run (never silently claim a successful scenario).
    if scenario != 'empty':
        mark(run, 'A02', 'satisfied', {'ground': 'on'}, [EVIDENCE])
        mark(run, 'A03', 'satisfied', {'rack': 'not loaded', 'reason': 'synthetic lab fixture'}, [EVIDENCE])
    if scenario == 'deep-comb-awaiting-confirmation':
        mark(run, 'E01', 'satisfied', {'topic_count': 7, 'topics': [
            {'id': index, 'label': f'Synthetic topic {index}', 'segments': f'{index}–{index+1}'}
            for index in range(1, 8)]}, [EVIDENCE])
        mark(run, 'E02', 'satisfied', {'route': 'deep-comb'}, [EVIDENCE])
        mark(run, 'E03', 'satisfied', {'simulation': 'synthetic stable slice addresses', 'pointer': EVIDENCE}, [EVIDENCE])
        mark(run, 'E04', 'blocked', {'simulation': 'topic map awaits human confirmation before fan-out'})
    if scenario == 'review-gate':
        for marker in ('M01', 'M02'):
            mark(run, marker, 'satisfied', {'simulation': 'synthetic draft'}, [EVIDENCE])
        mark(run, 'M03', 'pending', {'review': 'waiting'})
    # Scenario metadata is an append-only event in the lab DB, not a production event.
    with sqlite3.connect(lab_path() / 'runs.sqlite') as db:
        db.execute('BEGIN IMMEDIATE')
        durable.event(db, run, 'lab_scenario', payload={'scenario': scenario, 'fixture': REF})
    return snapshot(run)


def reset(run=None):
    root = lab_path()
    if run is not None and not RUN_ID.fullmatch(run): raise BadRequest('invalid lab run ID')
    if not (root / 'runs.sqlite').exists(): return {'deleted': 0}
    with sqlite3.connect(root / 'runs.sqlite', timeout=10) as db:
        db.execute('BEGIN IMMEDIATE')
        ids = [r[0] for r in db.execute('SELECT id FROM runs') if RUN_ID.fullmatch(r[0]) and (run is None or r[0] == run)]
        for rid in ids:
            db.execute('DELETE FROM events WHERE run_id=?', (rid,))
            db.execute('DELETE FROM markers WHERE run_id=?', (rid,))
            db.execute('DELETE FROM runs WHERE id=?', (rid,))
    return {'deleted': len(ids)}


def action(path, data):
    if path == '/lab/api/runs':
        fields(data, ('scenario',))
        return create(data['scenario'])
    if path == '/lab/api/reset':
        fields(data, ())
        return reset()
    parts = path.split('/')
    if len(parts) != 6 or parts[:4] != ['', 'lab', 'api', 'runs']:
        raise BadRequest('unknown lab operation')
    run = unquote(parts[4])
    snapshot(run)  # check ownership before any write
    operation = parts[5]
    if operation == 'reset':
        fields(data, ())
        return reset(run)
    if operation == 'configure':
        fields(data, ('key', 'value'))
        if data['key'] not in ('deep_comb', 'prd', 'in_flight', 'paired', 'trade', 'live_conversation') or type(data['value']) is not bool:
            raise BadRequest('invalid branch key or boolean value')
        cli('configure', run, data['key'], 'true' if data['value'] else 'false')
    elif operation == 'mark':
        fields(data, ('marker', 'status'), ('value', 'evidence', 'revise'))
        if not isinstance(data['marker'], str) or not re.fullmatch(r'[A-Z][0-9]{2}', data['marker']): raise BadRequest('invalid marker')
        if data['status'] not in durable.STATUSES: raise BadRequest('invalid status')
        value = data.get('value')
        metadata(value)
        evidence = data.get('evidence', [])
        if not isinstance(evidence, list) or len(evidence) > 8: raise BadRequest('invalid evidence')
        for item in evidence: string(item, 'evidence', True)
        if type(data.get('revise', False)) is not bool: raise BadRequest('invalid revise')
        mark(run, data['marker'], data['status'], value, evidence, data.get('revise', False))
    elif operation == 'trace':
        fields(data, ('marker', 'operation', 'result'), ('inputs', 'outputs', 'evidence', 'actor'))
        evidence = data.get('evidence', [])
        if not isinstance(evidence, list) or len(evidence) > 8: raise BadRequest('invalid evidence')
        for item in evidence: string(item, 'trace evidence', True)
        for key in ('inputs', 'outputs'):
            if not isinstance(data.get(key, {}), dict): raise BadRequest('trace metadata must be object')
            metadata(data.get(key, {}))
        for key in ('operation', 'result', 'actor'): string(data.get(key, 'lab' if key == 'actor' else None), key)
        if not isinstance(data['marker'], str) or not re.fullmatch(r'[A-Z][0-9]{2}', data['marker']): raise BadRequest('invalid marker')
        argv = ['trace', run, data['marker'], data['operation'], '--inputs', durable.canonical(data.get('inputs', {})),
                '--outputs', durable.canonical(data.get('outputs', {})), '--result', data['result'], '--actor', data.get('actor', 'lab')]
        for item in evidence: argv += ['--evidence', item]
        cli(*argv)
    elif operation == 'measure':
        fields(data, ('name', 'numerator', 'denominator', 'denominator_label', 'method', 'evidence'), ('actor',))
        if not isinstance(data['name'], str) or not re.fullmatch(r'[a-z][a-z0-9_]{1,63}', data['name']): raise BadRequest('invalid metric')
        for key in ('numerator', 'denominator'):
            if type(data[key]) is not int or not 0 <= data[key] <= 1000000: raise BadRequest('invalid count')
        if data['numerator'] > data['denominator']: raise BadRequest('numerator exceeds denominator')
        for key in ('denominator_label', 'method', 'actor'): string(data.get(key, 'lab' if key == 'actor' else None), key)
        string(data['evidence'], 'evidence', True)
        cli('measure', run, data['name'], str(data['numerator']), str(data['denominator']), '--denominator-label',
            data['denominator_label'], '--method', data['method'], '--evidence', data['evidence'], '--actor', data.get('actor', 'lab'))
    else:
        raise BadRequest('unknown lab operation')
    return snapshot(run)


def respond(handler, status, body, content_type='application/json; charset=utf-8'):
    if not isinstance(body, bytes): body = json.dumps(body).encode()
    handler.send_response(status)
    handler.send_header('Content-Type', content_type)
    handler.send_header('Content-Length', str(len(body)))
    handler.send_header('Cache-Control', 'no-store')
    handler.send_header('X-Content-Type-Options', 'nosniff')
    handler.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'")
    handler.end_headers()
    handler.wfile.write(body)


def handle(handler, method, path):
    try:
        host = handler.headers.get('Host', '')
        # SSH forwards preserve the browser's Host (e.g. 127.0.0.1:18787),
        # not the server's local port 8787. Accept only a literal loopback host.
        match = re.fullmatch(r'(?:127\.0\.0\.1|localhost):([1-9][0-9]{0,4})', host)
        if handler.server.server_address[0] != '127.0.0.1' or not match or int(match.group(1)) > 65535:
            return respond(handler, 403, {'error': 'lab requires localhost bind and host'})
        if method == 'GET':
            if path in ('/lab/', '/lab/app.js'):
                name = 'lab.html' if path == '/lab/' else 'lab.js'
                body = (CLI.parent / name).read_bytes()
                return respond(handler, 200, body, 'text/html; charset=utf-8' if path == '/lab/' else 'application/javascript; charset=utf-8')
            if path == '/lab/api/scenarios': return respond(handler, 200, list(SCENARIOS))
            if path == '/lab/api/runs': return respond(handler, 200, runs())
            if path.startswith('/lab/api/runs/') and RUN_ID.fullmatch(unquote(path[len('/lab/api/runs/') :])):
                return respond(handler, 200, snapshot(unquote(path[len('/lab/api/runs/') :])))
            return respond(handler, 404, {'error': 'not found'})
        if handler.headers.get('Origin') != 'http://' + host or handler.headers.get('X-Pipeline-Lab') != '1':
            return respond(handler, 403, {'error': 'same-origin lab header required'})
        if handler.headers.get('Content-Type', '').lower().split(';')[0].strip() != 'application/json':
            return respond(handler, 415, {'error': 'JSON required'})
        size = handler.headers.get('Content-Length', '')
        if not size.isdecimal() or not 0 < int(size) <= 16384:
            return respond(handler, 413, {'error': 'invalid JSON body size'})
        data = json.loads(handler.rfile.read(int(size)),
                          parse_constant=lambda _: (_ for _ in ()).throw(BadRequest('nonfinite JSON forbidden')))
        return respond(handler, 200, action(path, data))
    except (BadRequest, ValueError, TypeError, json.JSONDecodeError) as exc:
        return respond(handler, 400, {'error': str(exc)[:500]})
    except FileNotFoundError:
        return respond(handler, 404, {'error': 'lab UI not installed'})
    except sqlite3.Error:
        return respond(handler, 503, {'error': 'lab storage unavailable'})
