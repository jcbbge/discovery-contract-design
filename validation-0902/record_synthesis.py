#!/usr/bin/env python3
"""Record read-only synthesis/draft into LIVE run; NEVER publish or imply a reply."""
import json,subprocess
from pathlib import Path
RUN='mw-discovery-0902-live-v2'
HERE=Path(__file__).resolve().parent
WORK=str(HERE/'SYNTHESIS.md')
T='/home/jrg/projects/infinity/discovery/transcripts/0902_weekly_nathaniel.segmented.md'
ARC='/home/jrg/projects/infinity/arc/'
SLICES=Path('/home/jrg/.pi/durable-subagents/w/01M5CSS7VZP2Z3B4KSQ0W1SJRA/x')
SYN=Path('/home/jrg/.pi/durable-subagents/w/01M5CSY4AZPJ7Q8R7NCAPRNDKN/x/tasks%3A0@1/session.jsonl')

def call(*args):
    r=subprocess.run(['pipeline-observer',*args],capture_output=True,text=True)
    if r.returncode:raise RuntimeError(f'{args[:4]}: {r.stderr}')
    print(r.stdout.strip())

def state():return json.loads(subprocess.check_output(['pipeline-observer','status',RUN,'--json'],text=True))

def mark(mid,value,refs,status='satisfied'):
    old=next(m for m in state()['markers'] if m['id']==mid)
    if old['status'] in ('satisfied','satisfied_by_rule'):
        if old['value']!=value:raise RuntimeError(f'{mid} already settled differently; use deliberate --revise')
        print(mid,'already recorded');return
    a=['mark',RUN,mid,'--status',status,'--value',json.dumps(value)]
    for p in refs:a.extend(['--evidence',p])
    call(*a)

def c(i):return {'id':f'X{i:02d}','lens':LENSES[i-1],'finding':FINDINGS[i-1],
                 'disposition':DISPOSITIONS[i-1], 'evidence':T+':'+str(LINES[i-1]),
                 'attribution':{'kind':'inferred','qualification':QUALS[i-1]}}

result_lines=[15,21,19,23,23,22,18]
refs=[str(SLICES/f'slice{i}@1/session.jsonl')+':'+str(n) for i,n in enumerate(result_lines,1)]
for i,ref in enumerate(refs,1):
    # The seven readers' final results already exist; avoid replaying tool operations.
    if not any(e['kind']=='operation' and e['marker']=='E05' and e['payload'].get('args',{}).get('slice')==i for e in state().get('events',[])):
        # status --json omits events; use --events for idempotence
        events=json.loads(subprocess.check_output(['pipeline-observer','status',RUN,'--json','--events'],text=True))['events']
        if any(e['kind']=='operation' and e['marker']=='E05' and e['payload'].get('args',{}).get('slice')==i for e in events):continue
        call('trace',RUN,'E05','read_isolated_topic_slice','--inputs',json.dumps({'slice':i,'scope':'E01:topic_map'}),'--outputs',json.dumps({'reader_result':ref,'ran':True}),'--result','read-only source-bounded slice completed; not an approved finding','--evidence',ref)
mark('E05',{'slices_completed':7,'isolated':True,'reader_refs':refs,'scope':'Only own § ranges and canonical lens rubric; no Arc writes'},refs)
mark('E06',{'synthesis_ref':WORK+':16','through_line':'Commitment fidelity across client choice, owner data, operational readiness and fulfillment','alignments':['choice composition decided','dispatch-clock owner decided'],'discrepancies':['old collection visibility vs later source code','readiness warning vs complete preparation','0902 migration plan vs later manual cutover'],'crosscuts_not_minted_as_new_stock':True},[WORK+':16',str(SYN)+':35',T+':203'])
call('measure',RUN,'topic_slices_read','7','7','--denominator-label','confirmed transcript topic slices','--method','bounded isolated reader results linked by durable session pointers','--evidence',WORK+':3')

lens_data={
 'F01':('Substance',{'friction_count':12,'examples':['collection visibility changed since 0902','venue fee inclusions need acceptance','stage/bistro parts and guest quantity need real-data checks','sold item missing setup needs handoff'],'source':'historical statements, not current code verdict'},[WORK+':9',T+':203',T+':371']),
 'F02':('People',{'actors':['Maggie','Josh','Mimi','Trong','Rosie'],'roles':'meeting-described, not confirmed by individuals','vocabulary':['required items','bundle','collection','diagram','pack list','ready for Rosie'],'speaker_labels':False},[WORK+':10',T+':147']),
 'F03':('Process',{'actual_and_proposed':'venue configuration; recipe reviewer sequence; event/pack exception handoffs','unknown':'live task completion and owner acceptance','shadow_work':'staff manual assembly and arithmetic'},[WORK+':11',T+':295']),
 'F04':('Gap',{'questions':['live owner collection membership','venue/stage/bistro authored data','employee files permissions','Bento reconciliation and go-live','post-confirmation readiness owner'],'unknown_external':['Galley','HubSpot','dispatch','Bento']},[WORK+':12',T+':379']),
 'F05':('Subtext',{'rubric':'human meeting, mixed maturity','observations':['bistro model revised mid-discussion','unlimited venue described alongside editable initial quantity','retired policy corrected from cannot to should-not'],'attribution':'all turns unlabeled; no silence means approval'},[WORK+':13',T+':241']),
 'F06':('Meta',{'signal':'preserve source owner, maturity, operational layer and verification point','boundary':'no duplicate rack work from old T26; process feedback remains separate from product stock'},[WORK+':14',ARC+'.madewell/skills/discovery.md:190'])}
for id,(_,value,evidence) in lens_data.items():mark(id,value,evidence)
mark('F07',{'rule':'no loaded trade','trade_loaded':False},[ARC+'.madewell/AGENTS.md:15'],'satisfied_by_rule')
mark('I01',{'prd':False,'reason':'source is an archived meeting transcript, not a PRD or compressed blueprint'},[T+':1'])
for mid in ('I02','I03','I04','I05'):
    mark(mid,{'rule':'not a PRD/compression document'},[ARC+'.madewell/skills/discovery.md:206'],'satisfied_by_rule')
for mid in ('L02','L03','L04'):
    mark(mid,{'rule':'no paired artifact'},[ARC+'.madewell/skills/discovery.md:306'],'satisfied_by_rule')
mark('H01',{'finding':'Once an already-sold item remains operationally incomplete after nonblocking confirmation, accountable exception owner, deadline and verified resolution are missing.','tentative':True,'distinct_from_existing':'existing coverage-signal card names detection but not full post-confirmation exception lifecycle'},[WORK+':40',T+':379',ARC+'apps/web/src/routes/buildCanvas.readiness.ts:6'])

LENSES=['People','Process','Gap','Substance','Substance','Substance','Process','Substance','Substance','Process','Gap']
FINDINGS=[
 'Listening to employees and verifying build requirements are different acts needing a defined verifier and scope.',
 'HubSpot-dependent and allegedly independent onboarding and portal work need distinct pause and restart criteria.',
 'Employee-file protection is stated without a demonstrated access-control review.',
 'A stage or bistro choice should resolve its physical variant and shared components for packing.',
 'A venue fee should preserve editable inclusions and correct non-extra-charge goods.',
 'Guest and rack quantities need authored factors and acceptance at boundary cases.',
 'Recipe import needs distinct reviewer handoffs and top-level versus shared-recipe identities.',
 'A sold item missing a diagram or required items should reach its accountable operations owner.',
 'Editable venue prefill requires a specific owner-supplied HubSpot mapping.',
 'The September 2 Bento calendar is a historical proposal, not an approved migration schedule.',
 'Split-truck timing belongs to Dispatch rather than one inferred HubSpot delivery field.']
DISPOSITIONS=['decision','rack','release','rack','rack','rack','decision','rack','rack','release','release']
LINES=[9,37,69,203,175,261,145,371,101,321,85]
QUALS=[
 'Speaker identity inferred; verification distinction inferred from spoken guidance.',
 'Speaker inferred; forecasts stated, actual dependencies not verified.',
 'Speaker inferred; concern stated, no breach or control failure demonstrated.',
 'Speaker inferred; proposed behavior stated, authored data and shortages unverified.',
 'Speaker inferred; design intent stated, per-venue behavior unverified.',
 'Speaker inferred; examples stated, no universal factor or successful production proof.',
 'Speaker inferred; sequence reported, actual status labels and Galley owner unverified.',
 'Speaker inferred; concern stated, alert mechanism and owner unsettled.',
 'Speaker inferred; possible prefill stated, mapping and live HubSpot not read.',
 'Speaker inferred; milestones stated as proposal, year and approval unestablished.',
 'Speaker inferred; ownership direction stated, dispatch live system not read.']
candidates=[c(i) for i in range(1,12)]
call('configure',RUN,'in_flight','true')
mark('J01',{'closed':True,'candidate_count':11,'candidate_ids':[x['id'] for x in candidates],'lens_refs':[WORK+':9',WORK+':24'],'in_flight':True,'basis':'historical intake; live verified code/ADRs make some existing work in-flight'},[WORK+':24',ARC+'docs/admin/SPEC-slot-member-quantity-rules.md:1'])
mark('J02',{'routed':{x['id']:x['disposition'] for x in candidates},'named_releases':['X03 Arc feature/security verdict','X10 obsolete cutoff date','X11 duplicate dispatch ownership ADR'],'rack_means':'existing piece update proposal, never new duplicate'},[WORK+':24',WORK+':42'])
mark('J03',{'candidates':candidates,'attribution_policy':'speaker turns unlabeled; proposed dispositions pending domain operator review'},[WORK+':24',T+':1'])
call('mark',RUN,'J04','--status','in_progress','--value',json.dumps({'draft_duplicate_check':'2026-10-20 ~14:04 UTC, all 11 checked against cited addresses in SYNTHESIS.md; fresh per-candidate check still REQUIRED immediately before any Arc write'}),'--evidence',WORK+':36')
call('mark',RUN,'J05','--status','in_progress','--value',json.dumps({'reason':'in-flight existing stock/ADRs identified; verdict must precede any new racking','ref':ARC+'docs/admin/SPEC-slot-member-quantity-rules.md:1'}),'--evidence',ARC+'docs/admin/SPEC-slot-member-quantity-rules.md:1')
mark('J06',{'corpus':T,'proposal':'If a transcript-derived stock update is approved, use a title + source path only; no source body'},[WORK+':3',ARC+'.madewell/skills/discovery.md:218'])
mark('K01',{'named':['commitment fidelity','post-confirmation readiness exception','mirror versus owner','variant versus physical constituents'],'scope':'draft names; do not assert accepted taxonomy'},[WORK+':16'])
call('mark',RUN,'K02','--status','in_progress','--value',json.dumps({'proposed_questions':['Who owns the post-confirmation incomplete-item exception?','Who verifies employee-sourced build guidance?','What are culinary approval labels?'],'actual_Decisions_or_Product_write':False}),'--evidence',WORK+':42')
call('mark',RUN,'K03','--status','in_progress','--value',json.dumps({'proposed_closures':['dispatch clock belongs to dispatch, per locked ADR'],'actual_Decisions_or_Product_write':False}),'--evidence',ARC+'docs/decisions/2026-08-23-arc-dispatch-boundary.md:30')
# M01 and M02 remain in_progress: a written observer draft is not a reflection
# delivered to the domain operator or an operator-facing Step 5 presentation.
call('mark',RUN,'M03','--status','blocked','--value',json.dumps({'reason':'domain operator has not been shown the final draft or asked to verify interpretation; no reply. Sandbox demo user is not automatically Nathaniel or Galley owner.'}),'--evidence',WORK+':42')
print('STOP: draft recorded; no Arc writes, no operator approval, no publication. J04/J05/K02/K03 and M03+ remain open.')
