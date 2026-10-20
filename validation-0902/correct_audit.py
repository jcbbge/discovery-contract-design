#!/usr/bin/env python3
"""Append-only corrections of evidence-audit findings; preserve earlier self-reports."""
import copy,json,os,subprocess
RUN='mw-discovery-0902-live-v2'
ARC='/home/jrg/projects/infinity/arc/'
T='/home/jrg/projects/infinity/discovery/transcripts/0902_weekly_nathaniel.segmented.md'
SESSION='/home/jrg/.pi/agent/sessions/--home-jrg--/2026-10-20T04-30-27-653Z_01a15793-3544-77f5-b15a-46f1714c7278.jsonl:353'
EARLIER=SESSION.rsplit(':',1)[0]+':347'

def cite(s,p):return {'summary':s,'pointer':p}
def a(p,line):return ARC+p+':'+str(line)
def state():return {m['id']:m for m in json.loads(subprocess.check_output(['pipeline-observer','status',RUN,'--json'],text=True))['markers']}
def revise(mid,changed,more):
    old=state()[mid]
    value=copy.deepcopy(old['value']);value.update(changed)
    evidence=list(dict.fromkeys(old['evidence']+more))
    if old['value']==value and evidence==old['evidence']: print(mid,'already corrected');return
    args=['pipeline-observer','mark',RUN,mid,'--status',old['status'],'--value',json.dumps(value),'--revise']
    for ref in evidence:args.extend(['--evidence',ref])
    subprocess.run(args,check=True)

revise('A02',{'basis':'Ground was presented in this sitting before v2 creation; earlier v1 source exposure and missing pre-read declarations were not erased. This is a LIVE retrospective re-observation, not a fresh blind evaluation.','earlier_run':'mw-discovery-0902-validation','prior_source_exposure':True,'ground_presentation':EARLIER},[EARLIER])
for mid in ('C08','C09','C12'):
    revise(mid,{'presentation_ref':SESSION,'presentation_at':'2026-10-20T07:23:49.238Z','recording_order':'User-facing synthesis preceded recording of C11; earlier trace events 22-24 preceded marker event 28, not the actual spoken synthesis.'},[SESSION])
revise('C05',{'temporal_scope':'September 2 source is a historical intake; September 15/29 decisions and October work are later/current Ground constraints, not settled at that meeting.','meeting_basis':cite('Selection and pack-list questions raised in meeting',T+':203'),'subsequent_constraint':cite('Selected options compose required items under later accepted ADR',a('docs/decisions/2026-09-15-a-choice-option-composes.md',37))},[T+':203',a('docs/decisions/2026-09-15-a-choice-option-composes.md',3)])
c06=state()['C06']['value']
contr=copy.deepcopy(c06['contradictions'])
contr[0]['summary']='HISTORICAL CHANGE: September 2 walkthrough lacked collection choices; subsequent current source renders controls. Not a contradiction in current code or proof of live Galley membership.'
revise('C06',{'contradictions':contr,'gap':cite('Readiness code warns, rather than refusing confirmation; remaining diagrams and actual migration require separate owner and artifact verification',a('apps/web/src/routes/buildCanvas.readiness.ts',6)), 'gap_references':[T+':369',a('.madewell/stock/food-diagrams.md',5),a('.madewell/stock/bento-cutover-in-one-week.md',22)],'temporal_scope':'Current source-code mechanisms versus historical meeting and later open cards; not a production acceptance test.'},[T+':369',a('apps/api/src/lib/contracts/tables.ts',348),a('.madewell/stock/food-diagrams.md',5)])
revise('C11',{'actual':cite('Arc source implements collection group materialization; separate UI choice controls and pack projection exist. Live owner data and authoring are unverified.',a('apps/api/src/routes/builds-items.ts',321)),'material_refs':[a('apps/web/src/routes/GalleyPackageRows.tsx',116),a('apps/api/src/lib/contracts/tables.ts',348)],'meeting_basis':cite('Meeting asks to put requirements on selected variants, then pack them',T+':203'),'temporal_scope':'0902 asks are historical; September ADRs bind current Ground, not the meeting itself'},[T+':203',a('apps/web/src/routes/GalleyPackageRows.tsx',116),a('apps/api/src/lib/contracts/tables.ts',348)])
revise('D03',{'participants':['Nathaniel (filename only; no identified turn)','Josh (addressed, turn unverified)','Maggie (addressed, turn unverified)'],'speaker_labels':False},[T+':49',T+':105'])
revise('D04',{'off_stage':['Mimi (named)','Rosie (named)','Kate (named)'],'mentioned_groups':['dispatch','sales'],'attribution':'No speaker turns labeled; roles not inferred from naming alone'},[T+':9',T+':147',T+':297',T+':347'])
print('Correction events appended; previous records remain available in event history.')
