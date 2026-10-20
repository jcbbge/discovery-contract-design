#!/usr/bin/env python3
"""Offline behavioral tests for fixed contract, trace, gates, recovery and HTTP projection."""
import json
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

BASE = Path(__file__).resolve().parent
CLI = BASE / 'durable.py'
CONTRACT = BASE / 'contracts/made-well-discovery-v1.json'
V2 = BASE / 'contracts/made-well-discovery-v2.json'

class DurableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.env = {**os.environ,'PIPELINE_HOME':self.tmp.name}
    def call(self,*args,ok=True):
        proc=subprocess.run([sys.executable,str(CLI),*args],env=self.env,text=True,capture_output=True)
        if ok: self.assertEqual(proc.returncode,0,proc.stderr)
        else: self.assertNotEqual(proc.returncode,0,proc.stdout)
        return proc
    def start(self,run='case',mode='live',*flags):
        self.call('start','corpus/example.md','--id',run,'--mode',mode,'--contract',str(CONTRACT),*flags)
        return self.data(run)
    def data(self,run='case',events=False):
        return json.loads(self.call('status',run,'--json',*(['--events'] if events else [])).stdout)
    def mark(self,run,marker,status='satisfied',value=None,evidence='corpus/example.md:12',ok=True):
        args=['mark',run,marker,'--status',status,'--evidence',evidence]
        if value is not None: args.extend(['--value',json.dumps(value)])
        return self.call(*args,ok=ok)
    @staticmethod
    def review(status):
        value={'review':status,'request':{'question':'Does that match what you meant?',
            'at':'2026-10-20T07:00:00+00:00','pointer':'corpus/review.md:1'}}
        if status=='confirmed': value['reply']={'at':'2026-10-20T07:01:00+00:00','pointer':'corpus/review.md:2'}
        else: value['open_question']={'at':'2026-10-20T07:01:00+00:00','pointer':'DECISIONS.md:12'}
        return value
    @staticmethod
    def fixture(mid):
        cite=lambda summary: {'summary':summary,'pointer':'corpus/example.md:12'}
        if mid=='A02': return {'ground':'on'}
        if mid=='A03': return {'rack':'loaded'}
        if mid=='E02': return {'route':'single-pass'}
        if mid=='I01': return {'prd':False}
        if mid=='L01': return {'paired':False}
        if mid=='N01': return {'live_conversation':False}
        if mid=='J01': return {'in_flight':False}
        if mid=='C05': return {'corpus':[{'path':'corpus/example.md','what':'intake',
            'relevance':'task source','summary':'synthetic evidence','pointer':'corpus/example.md:12'}],
            'locked_decisions':[], 'open_questions':[], 'synthesis':cite('written context')}
        if mid=='C06': return {'surfaces':[{'path':'corpus/example.md','lines':[12,15],
            'verdict':'PARTIAL','summary':'synthetic surface','pointer':'corpus/example.md:12'}],
            'gap':cite('work remains'),'contradictions':[]}
        if mid=='C11': return {'required':cite('required work'),'actual':cite('observed state'),
            'locked_decisions':[],'open_decisions':[],'next_move':cite('review next')}
        if mid=='J03': return {'candidates':[]}
        return {'observed':'test fixture'}
    def test_v2_default_source_snapshot_and_existing_v1_run(self):
        doc=json.loads(V2.read_text())
        self.assertEqual(doc['version'],2)
        self.assertNotIn('source_revision',doc)
        self.assertEqual(len(doc['source_hashes']),6)
        self.assertEqual(set(doc['source_hashes']), {
            str(BASE.parent/'MARKER_INVENTORY.md'),
            *(str(Path.home()/'projects/infinity/arc'/p) for p in (
                'AGENTS.md','.madewell/skills/discovery.md','.madewell/ground/PROTOCOL.md',
                '.madewell/ground/PICTURE.md','.madewell/ground/ROOTS.md'))})
        for name, digest in doc['source_hashes'].items():
            self.assertEqual(hashlib.sha256(Path(name).read_bytes()).hexdigest(),digest)
        legacy=self.call('start','corpus/example.md','--id','legacy','--mode','live',
                         '--contract',str(CONTRACT))
        self.assertIn('legacy, incomplete provenance',legacy.stderr)
        self.call('start','corpus/example.md','--id','new','--mode','live')
        self.assertEqual(self.data('legacy')['contract_version'],1)
        self.assertEqual(self.data('new')['contract_version'],2)
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'governing.md'; source.write_text('original')
            changed=json.loads(V2.read_text())
            original=next(iter(changed['source_hashes']))
            changed['source_hashes'][str(source)]=changed['source_hashes'].pop(original)
            custom=Path(tmp)/'contract.json'; custom.write_text(json.dumps(changed))
            refused=self.call('start','corpus/example.md','--id','stale','--mode','live',
                              '--contract',str(custom),ok=False)
            self.assertIn('source snapshot SHA256 mismatch',refused.stderr)
            self.assertNotIn('stale',self.call('status').stdout)
            source.unlink()
            refused=self.call('start','corpus/example.md','--id','missing','--mode','live',
                              '--contract',str(custom),ok=False)
            self.assertIn('source snapshot unavailable',refused.stderr)
        self.assertEqual(self.data('legacy')['contract_version'],1)

    def test_builder_guards_both_frozen_versions_without_writing_them(self):
        import build_contract
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            v1=root/'v1.json'; v1.write_bytes(CONTRACT.read_bytes())
            v2=root/'v2.json'; v2.write_bytes(V2.read_bytes())
            with patch.multiple(build_contract,V1=v1,OUTPUT=v2):
                build_contract.main()
                original=v2.read_bytes()
                with patch.object(build_contract,'SOURCES',list(reversed(build_contract.SOURCES))):
                    with self.assertRaisesRegex(SystemExit,'Refusing to change frozen v2'):
                        build_contract.main()
                self.assertEqual(v2.read_bytes(),original)
                v2.write_text('altered')
                with self.assertRaisesRegex(SystemExit,'Frozen v2 missing or changed'):
                    build_contract.main()
                v2.unlink()
                with self.assertRaisesRegex(SystemExit,'Frozen v2 missing or changed'):
                    build_contract.main()
                v2.write_bytes(original)
                v1.write_text('altered')
                with self.assertRaisesRegex(SystemExit,'Frozen v1 missing or changed'):
                    build_contract.main()

    def test_definition_fixed_count_and_pinned_snapshot(self):
        d=json.loads(CONTRACT.read_text());self.assertEqual(len(d['markers']),72)
        self.assertEqual(len({m['id'] for m in d['markers']}),72)
        s=self.start();self.assertEqual(s['progress'],{'done':1,'total':72,'percent':1.4})
        self.assertEqual(s['markers'][0]['id'],'A01')
        self.assertFalse(s['gates']['publish']['ready'])
        self.assertEqual(s['contract_version'],1)
    def test_blind_isolation_and_conditional_bypass(self):
        self.start(mode='blind')
        self.mark('case','C01',ok=False)
        self.mark('case','B01',ok=False)
        self.mark('case','C01','satisfied_by_rule',{'rule':'blind: Ground prohibited'})
        self.mark('case','B01','satisfied_by_rule',{'rule':'blind: answer-key context withheld'})
        self.assertEqual(self.data()['progress']['done'],3)
        self.call('start','corpus/example.md','--id','bad','--mode','blind','--paired','--paired-answer-key',ok=False)
    def test_fixed_branch_math_and_invalid_bypass(self):
        for name, flags in [('short',[]),('dense',['--deep-comb']),('paired',['--paired','--paired-primary'])]:
            self.start(name,'live',*flags)
            self.assertEqual(self.data(name)['progress']['total'],72)
        self.mark('short','E02',value={'route':'single-pass'})
        self.mark('short','E03','satisfied_by_rule',{'rule':'single-pass or cross-artifact route'})
        self.mark('dense','E03','satisfied_by_rule',{'rule':'single-pass or cross-artifact route'},ok=False)
        self.mark('paired','L02','satisfied_by_rule',{'rule':'no paired artifact'},ok=False)
        self.assertEqual(self.data('short')['progress']['done'],3)
    def test_branch_selection_after_classification_is_audited(self):
        self.start()
        self.mark('case','D05',value={'maturity':'IDEATION'})
        self.call('configure','case','deep_comb','true')
        self.assertTrue(self.data()['options']['deep_comb'])
        self.mark('case','E03','satisfied_by_rule',{'rule':'single-pass or cross-artifact route'},ok=False)
        self.mark('case','E02',value={'route':'deep-comb'})
        self.call('configure','case','deep_comb','false',ok=False)
        self.assertEqual(self.data()['progress']['total'],72)
    def test_review_and_publication_gates(self):
        self.start()
        self.mark('case','M03',value={'review':'confirmed'},ok=False)
        self.mark('case','M07',value={'output':'stock/example.md'},ok=False)
        self.mark('case','M01');self.mark('case','M02')
        self.mark('case','M03',value=self.review('unavailable'))
        self.mark('case','M04','satisfied_by_rule',{'rule':'operator unavailable; no ruling to capture'})
        self.mark('case','M07',value={'open_question':'DECISIONS.md:12'},ok=False)
        self.mark('case','H02',value={'destination':'stock'})
        self.mark('case','H02',value={'destination':'PRODUCT.md'},ok=False) # corrections must be explicit
        self.assertEqual(self.data()['progress']['done'],6)
    def test_metrics_do_not_change_progress_or_invent_denominators(self):
        self.start()
        self.call('measure','case','source_spans_read','8','10','--denominator-label','indexed source spans',
                  '--method','stable span inventory','--evidence','corpus/index.md#spans')
        self.assertEqual(self.data()['telemetry']['source_spans_read']['percent'],80)
        self.assertEqual(self.data()['progress']['done'],1)
        self.call('measure','case','source_spans_read','0','0','--denominator-label','indexed source spans',
                  '--method','not indexed','--evidence','corpus/index.md#unknown')
        self.assertIsNone(self.data()['telemetry']['source_spans_read']['percent'])
        self.call('measure','case','source_spans_read','11','10','--denominator-label','spans',
                  '--method','invalid','--evidence','none',ok=False)
    def test_trace_preserves_argument_return_and_retry_audit(self):
        self.start()
        self.call('trace','case','D01','classify_input','--inputs','{"source":"corpus/example.md"}',
                  '--outputs','{"type":"voice-note"}','--result','classified','--evidence','corpus/example.md#meta')
        self.mark('case','D01',value={'type':'voice-note'})
        self.call('mark','case','D01','--status','failed','--evidence','contradiction',ok=False)
        self.call('mark','case','D01','--status','failed','--evidence','contradiction','--revise')
        events=self.data(events=True)['events']
        self.assertEqual(next(e for e in events if e['kind']=='operation')['payload']['returned']['type'],'voice-note')
        self.assertEqual(events[-1]['kind'],'marker_revision')
        self.assertEqual(self.data()['progress']['done'],1)
    def test_full_fixed_contract_and_ui(self):
        import durable
        durable.HOME = Path(self.tmp.name)
        self.start('complete')
        # Paired applicability is needed to justify B04's early no-pair bypass.
        self.mark('complete','L01',value=self.fixture('L01'))
        for m in self.data('complete')['markers']:
            mid=m['id']
            if mid in ('A01','L01','M03','H02','M07','M08','M09','M10'): continue
            with durable.connect() as db:
                row,_=durable.contract_for(db,'complete')
                opts=json.loads(row['options'])
                rule=durable.allowed_bypass(mid,row,opts)
            if rule:
                self.mark('complete',mid,'satisfied_by_rule',{'rule':rule, **({'trade_loaded':False} if mid=='F07' else {})})
            else:
                self.mark('complete',mid,value=self.fixture(mid))
        self.mark('complete','M03',value=self.review('confirmed'))
        self.mark('complete','H02',value={'destination':'stock'})
        self.assertTrue(self.data('complete')['gates']['publish']['ready'])
        self.mark('complete','M07',value={'output':'stock/test.md'})
        for mid in ('M08','M09','M10'):
            self.mark('complete',mid,value={'observed':'test fixture'})
        self.assertEqual(self.data('complete')['progress'],{'done':72,'total':72,'percent':100.0})
        server=ThreadingHTTPServer(('127.0.0.1',0),durable.Handler)
        t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:
            root=f'http://127.0.0.1:{server.server_address[1]}'
            with urllib.request.urlopen(root+'/api/runs/complete') as response:
                projection=json.load(response)
            self.assertEqual(projection['progress']['percent'],100)
            with urllib.request.urlopen(root+'/app.js') as response:
                self.assertIn('function',response.read().decode())
            with urllib.request.urlopen(root) as response:
                self.assertIn('operation(args)',response.read().decode())
        finally:
            server.shutdown();server.server_close();t.join(timeout=2)
    def test_bypasses_need_branch_classification_not_just_default_flags(self):
        self.start()
        cases=[('E03',{'rule':'single-pass or cross-artifact route'},'E02',{'route':'single-pass'}),
               ('I02',{'rule':'not a PRD/compression document'},'I01',{'prd':False}),
               ('N02',{'rule':'supplied artifact, not live conversation'},'N01',{'live_conversation':False}),
               ('J05',{'rule':'no in-flight finding'},'J01',{'in_flight':False}),
               ('L02',{'rule':'no paired artifact'},'L01',{'paired':False}),
               ('B04',{'rule':'no paired artifact'},'L01',{'paired':False})]
        for mid,val,_,_ in cases: self.mark('case',mid,'satisfied_by_rule',val,ok=False)
        for _,_,classifier,val in cases:
            if self.data()['markers'][next(i for i,m in enumerate(self.data()['markers']) if m['id']==classifier)]['status']!='satisfied':
                self.mark('case',classifier,value=val)
        for mid,val,_,_ in cases: self.mark('case',mid,'satisfied_by_rule',val)
        self.mark('case','F07','satisfied_by_rule',{'rule':'no loaded trade'},ok=False)
        self.mark('case','F07','satisfied_by_rule',{'rule':'no loaded trade','trade_loaded':False})
        self.mark('case','A02',value={'ground':'skipped (blind)'},ok=False)
        self.mark('case','A03',value={'rack':'not loaded'},ok=False)
        self.mark('case','A02',value={'ground':'on'})
        self.start('blind','blind')
        self.mark('blind','A02',value={'ground':'on'},ok=False)
        self.mark('blind','A03',value={'rack':'not loaded'},ok=False)
        self.mark('blind','A03',value={'rack':'not loaded','reason':'evaluation excludes rack'})

    def test_trace_rejects_raw_and_secrets_atomically(self):
        self.start()
        for payload in ({'nested':{'transcript':'raw'}},{'body':'raw'}, {'secret':'x'},
                        {'a':'x'*257}, {'items':[{'key':i} for i in range(31)]}):
            self.call('trace','case','D01','read','--inputs',json.dumps(payload),
                      '--result','done',ok=False)
        self.call('trace','case','D01','read','--inputs','[]','--result','done',ok=False)
        self.call('trace','case','D01','read','--result','x'*257,ok=False)
        self.assertFalse(any(e['kind']=='operation' for e in self.data(events=True)['events']))
        self.call('trace','case','D01','read','--inputs','{"source":"corpus/example.md:12"}',
                  '--outputs','{"count":2}','--result','done')

    def test_review_requires_explicit_timestamped_request_and_reply_or_question(self):
        self.start()
        self.mark('case','M01');self.mark('case','M02')
        self.mark('case','M03',value={'review':'confirmed'},ok=False)
        v=self.review('confirmed')
        del v['reply'];self.mark('case','M03',value=v,ok=False)
        v=self.review('confirmed');v['request']['at']='yesterday'
        self.mark('case','M03',value=v,ok=False)
        v=self.review('unavailable');v['open_question']['pointer']='vague'
        self.mark('case','M03',value=v,ok=False)
        self.mark('case','M03',value=self.review('unavailable'))
        self.mark('case','M07',value={'open_question':'vague'},ok=False)

    def test_ground_ledgers_and_six_field_candidates(self):
        self.start()
        for mid in ('C05','C06','C11','J03'):
            self.mark('case',mid,value={'observed':'claim'},ok=False)
            value=self.fixture(mid)
            self.mark('case',mid,value=value)
        self.assertEqual(self.data()['progress']['done'],5)
        bad={'candidates':[{'id':'x','lens':'People','finding':'A gap exists.',
              'disposition':'rack','evidence':'corpus/example.md:12',
              'attribution':{'kind':'inferred'}}]}
        self.mark('case','J03',value=bad,ok=False) # no implicit overwrite
        self.call('mark','case','J03','--status','satisfied','--revise','--evidence',
                  'corpus/example.md:12','--value',json.dumps(bad),ok=False)
        bad['candidates'][0]['attribution']['qualification']='speaker uncertain'
        self.call('mark','case','J03','--status','satisfied','--revise','--evidence',
                  'corpus/example.md:12','--value',json.dumps(bad))
        self.mark('case','D05',value={'maturity':'IDEATION'},evidence='unsupported',ok=False)
        self.assertEqual(self.data()['progress']['done'],5)

    def test_no_count_change_on_live_conversation_and_prd(self):
        for run,flags in [('voice',['--live-conversation']),('prd',['--prd']),('both',['--prd','--trade'])]:
            self.start(run,'live',*flags)
            self.assertEqual(self.data(run)['progress']['total'],72)
        self.mark('prd','I02','satisfied_by_rule',{'rule':'not a PRD/compression document'},ok=False)
        self.mark('voice','N02','satisfied_by_rule',{'rule':'supplied artifact, not live conversation'},ok=False)

if __name__=='__main__': unittest.main()
