"""Isolated HTTP lab checks: source snapshot, validator failures, CSRF, DB separation."""
import hashlib
import json
import sqlite3
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import durable
import lab_server


class LabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.production = base / 'production'
        self.lab = base / 'lab'
        self.production.mkdir()
        self.production_db = self.production / 'runs.sqlite'
        # Sentinels expose accidental calls to durable.connect() from lab HTTP handling.
        self.production_db.write_bytes(b'production sentinel; never touch')
        self.before = hashlib.sha256(self.production_db.read_bytes()).hexdigest()
        p1 = patch.object(durable, 'HOME', self.production)
        p2 = patch.object(lab_server, 'LAB_HOME', self.lab)
        p1.start(); p2.start()
        self.addCleanup(p1.stop); self.addCleanup(p2.stop)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), durable.Handler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 2)
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = 'http://127.0.0.1:%d' % self.server.server_address[1]

    def request(self, path, data=None, headers=None, status=200):
        h = dict(headers or {})
        if data is not None:
            h.setdefault('Content-Type', 'application/json')
            h.setdefault('Origin', self.url)
            h.setdefault('X-Pipeline-Lab', '1')
        req = urllib.request.Request(self.url + path, data=None if data is None else json.dumps(data).encode(), headers=h)
        try:
            response = urllib.request.urlopen(req, timeout=20)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            body = response.read()
            self.assertEqual(response.status, status, body)
            return json.loads(body) if response.headers.get_content_type() == 'application/json' else body

    def test_scenarios_state_and_isolation(self):
        self.assertEqual(set(self.request('/lab/api/scenarios')), set(lab_server.SCENARIOS))
        self.assertEqual(self.request('/lab/api/runs'), [])
        for scenario in lab_server.SCENARIOS:
            s = self.request('/lab/api/runs', {'scenario': scenario})
            self.assertEqual(s['contract_version'], 2)
            self.assertEqual(s['progress']['total'], 72)
            self.assertEqual(s['input_ref'], lab_server.REF)
            self.assertTrue(s['events'][0]['kind'] == 'run_created')
            self.assertEqual(s['events'][-1]['payload']['scenario'], scenario)
            if scenario == 'deep-comb-awaiting-confirmation':
                self.assertTrue(s['options']['deep_comb'])
                self.assertEqual(next(m for m in s['markers'] if m['id'] == 'E04')['status'], 'blocked')
                self.assertEqual(s['gates']['deep_comb_fanout']['missing'], ['E04'])
                self.request('/lab/api/runs/' + s['run'] + '/mark', {
                    'marker': 'E04', 'status': 'satisfied', 'value': {'simulation': 'confirmed for lab'},
                    'evidence': [lab_server.EVIDENCE]})
                self.assertTrue(self.request('/lab/api/runs/' + s['run'])['gates']['deep_comb_fanout']['ready'])
            if scenario == 'review-gate':
                self.assertIn('M03', s['gates']['publish']['missing'])
            self.assertEqual(self.request('/lab/api/runs/' + s['run'])['run'], s['run'])
        self.assertEqual(len(self.request('/lab/api/runs')), 4)
        self.assertEqual(self.request('/lab/api/reset', {})['deleted'], 4)
        self.assertEqual(self.request('/lab/api/runs'), [])
        self.assertEqual(hashlib.sha256(self.production_db.read_bytes()).hexdigest(), self.before)
        self.assertEqual(list(self.production.iterdir()), [self.production_db])

    def test_mark_trace_metric_validation_and_csrf(self):
        run = self.request('/lab/api/runs', {'scenario': 'empty'})['run']
        base = '/lab/api/runs/' + run
        self.request(base + '/mark', {'marker': 'E03', 'status': 'satisfied_by_rule',
                     'value': {'rule': 'single-pass or cross-artifact route'}, 'evidence': [lab_server.EVIDENCE]}, status=400)
        self.request(base + '/mark', {'marker': 'E02', 'status': 'satisfied',
                     'value': {'route': 'single-pass'}, 'evidence': [lab_server.EVIDENCE]})
        self.request(base + '/mark', {'marker': 'E03', 'status': 'satisfied_by_rule',
                     'value': {'rule': 'single-pass or cross-artifact route'}, 'evidence': [lab_server.EVIDENCE]})
        self.request(base + '/mark', {'marker': 'E03', 'status': 'failed'}, status=400)
        self.request(base + '/mark', {'marker': 'E03', 'status': 'failed', 'revise': True})
        self.request(base + '/trace', {'marker': 'E03', 'operation': 'synthetic_pass', 'result': 'retry',
                   'inputs': {'pointer': lab_server.REF}, 'outputs': {'count': 1}})
        self.request(base + '/trace', {'marker': 'E03', 'operation': 'bad', 'result': 'bad',
                   'inputs': {'transcript_body': 'secret'}}, status=400)
        self.request(base + '/mark', {'marker': 'D01', 'status': 'satisfied',
                     'value': {'transcript': 'raw'}, 'evidence': [lab_server.EVIDENCE]}, status=400)
        self.request(base + '/measure', {'name': 'fixtures_seen', 'numerator': 3, 'denominator': 2,
                     'denominator_label': 'synthetic fixtures', 'method': 'counted',
                     'evidence': lab_server.EVIDENCE}, status=400)
        result = self.request(base + '/measure', {'name': 'fixtures_seen', 'numerator': 1, 'denominator': 2,
                   'denominator_label': 'synthetic fixtures', 'method': 'counted', 'evidence': lab_server.EVIDENCE})
        self.assertEqual(result['telemetry']['fixtures_seen']['percent'], 50)
        self.assertEqual(result['progress']['done'], 2)
        self.assertEqual(result['events'][-2]['kind'], 'operation')
        self.request(base + '/mark', {'marker': 'D01', 'status': 'satisfied', 'evidence': [lab_server.EVIDENCE]},
                     headers={'Origin': 'http://evil.example'}, status=403)
        self.request(base + '/mark', {'marker': 'D01', 'status': 'satisfied', 'evidence': [lab_server.EVIDENCE]},
                     headers={'X-Pipeline-Lab': 'wrong'}, status=403)
        self.request(base + '/mark', {'marker': 'D01', 'status': 'satisfied', 'evidence': [lab_server.EVIDENCE]},
                     headers={'Content-Type': 'text/plain'}, status=415)
        self.assertEqual(self.request(base + '/reset', {})['deleted'], 1)
        self.assertEqual(hashlib.sha256(self.production_db.read_bytes()).hexdigest(), self.before)

    def test_branch_configuration_obeys_classification_lock(self):
        run = self.request('/lab/api/runs', {'scenario': 'preflight'})['run']
        base = '/lab/api/runs/' + run
        s = self.request(base + '/configure', {'key': 'deep_comb', 'value': True})
        self.assertTrue(s['options']['deep_comb'])
        self.assertEqual(s['events'][-1]['kind'], 'option_changed')
        self.request(base + '/configure', {'key': 'deep_comb', 'value': 'true'}, status=400)
        self.request(base + '/mark', {'marker': 'E02', 'status': 'satisfied',
                     'value': {'route': 'deep-comb'}, 'evidence': [lab_server.EVIDENCE]})
        self.request(base + '/configure', {'key': 'deep_comb', 'value': False}, status=400)
        self.assertEqual(hashlib.sha256(self.production_db.read_bytes()).hexdigest(), self.before)

    def test_ssh_forward_host_and_origin(self):
        # Browser tunnel is on 18787 even though the server itself listens elsewhere.
        forwarded = {'Host': '127.0.0.1:18787', 'Origin': 'http://127.0.0.1:18787'}
        self.assertEqual(set(self.request('/lab/api/scenarios', headers=forwarded)), set(lab_server.SCENARIOS))
        created = self.request('/lab/api/runs', {'scenario': 'empty'}, headers=forwarded)
        self.assertEqual(created['progress']['total'], 72)
        self.request('/lab/api/runs', {'scenario': 'empty'},
                     headers={'Host': 'public.example:18787', 'Origin': 'http://public.example:18787'}, status=403)
        self.assertEqual(hashlib.sha256(self.production_db.read_bytes()).hexdigest(), self.before)

    def test_fail_closed_storage_alias_and_foreign_run(self):
        with patch.object(lab_server, 'LAB_HOME', self.production):
            self.request('/lab/api/runs', {'scenario': 'empty'}, status=400)
        self.request('/lab/api/runs/lab-' + '0' * 32, status=400)
        self.request('/lab/api/runs/not-a-lab-run/mark', {'marker': 'A01', 'status': 'failed'}, status=400)
        self.assertEqual(hashlib.sha256(self.production_db.read_bytes()).hexdigest(), self.before)


if __name__ == '__main__': unittest.main()
