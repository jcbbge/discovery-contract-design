#!/usr/bin/env python3
"""Idempotent, cited declarations for the 0902 live validation. Never writes Arc.

Run after Ground was presented to the user. If interrupted, rerun: only still-pending
markers are recorded. This is an audit recipe, NOT evidence that a source claim is true.
"""
import json
import subprocess
from pathlib import Path

RUN='mw-discovery-0902-live-v2'
CLI='pipeline-observer'
ARC='/home/jrg/projects/infinity/arc/'
TRANS='/home/jrg/projects/infinity/discovery/transcripts/0902_weekly_nathaniel.segmented.md'

def call(*args):
    p=subprocess.run([CLI,*args],capture_output=True,text=True)
    if p.returncode: raise RuntimeError(f'{args}: {p.stderr}')
    print(p.stdout.strip())

def snapshot():
    return json.loads(subprocess.check_output([CLI,'status',RUN,'--json'],text=True))

def mark(id,value,evidence,status='satisfied'):
    cur=next(m for m in snapshot()['markers'] if m['id']==id)
    if cur['status'] in ('satisfied','satisfied_by_rule'):
        if cur['value']!=value: raise RuntimeError(f'{id}: existing settlement differs; inspect and --revise deliberately')
        print(id,'already settled');return
    call('mark',RUN,id,'--status',status,'--value',json.dumps(value),*[x for p in evidence for x in ('--evidence',p)])

def cite(summary,pointer):return {'summary':summary,'pointer':pointer}
def a(rel,line):return ARC+rel+':'+line

def row(rel,line,what,relevance,summary):
    return {'path':rel,'what':what,'relevance':relevance,'summary':summary,'pointer':a(rel,line)}

# Run mode, Ground/rack dispositions A01–A03 were declared separately, prior to
# resuming this v2 run. This validation is explicitly LIVE, not a blind evaluation.
mark('N01',{'live_conversation':False,'basis':'supplied archived transcript'},[TRANS+':1'])
for mid in ('N02','N03'):
    mark(mid,{'rule':'supplied artifact, not live conversation'},[a('.madewell/skills/discovery.md','335')],'satisfied_by_rule')
mark('B01',{'path':ARC+'.madewell/stock/','inventory':'read current rack, not a per-candidate duplicate check'},[a('.madewell/stock/galley-collection-members-in-arc.md','6'),a('.madewell/stock/0930-discovery-handoff.md','1')])
mark('B02',{'path':ARC+'.madewell/DECISIONS.md','read':True,'adr_index':'current'},[a('.madewell/DECISIONS.md','7')])
mark('B03',{'path':ARC+'PRODUCT.md','pointer_file':ARC+'.madewell/PRODUCT.md','read':True},[a('.madewell/PRODUCT.md','6'),a('PRODUCT.md','39')])
mark('L01',{'paired':False,'basis':'T26 is prior analysis consulted as live historical context and duplicate check, not a designated paired primary source'},[a('.madewell/skills/discovery.md','51')])
mark('B04',{'rule':'no paired artifact','designation':'no designated paired primary artifact; historical T26 and ADRs consulted as context'},[a('.madewell/skills/discovery.md','55')],'satisfied_by_rule')

mark('C01',{'applicability':'live','ground':'on','protocol':ARC+'.madewell/ground/PROTOCOL.md'},[a('.madewell/ground/PROTOCOL.md','1')])
mark('C02',{'roots':ARC+'.madewell/ground/ROOTS.md','external_owner_register':'template_only','named_external_owners':['Galley','HubSpot','dispatch','Bento']},[a('.madewell/ground/ROOTS.md','10'),a('.madewell/ground/ROOTS.md','23')])
mark('C03',{'present':['.madewell/DECISIONS.md','.madewell/PRODUCT.md','.madewell/stock/','.madewell/bench/','.madewell/finished/','.madewell/jig/','AGENTS.md','MADEWELL.md','.madewell/SPEC.md','docs/','PRODUCT.md','discovery/transcripts/0902_weekly_nathaniel.segmented.md'],'root_missing':[],'scope':'preflight paths, not proof of implementation'},[a('.madewell/ground/ROOTS.md','10'),a('.madewell/ground/PROTOCOL.md','53')])
mark('C04',{'nouns':['Galley collections/recipes','venue-fee rentals','stage/bistro selections','quantity rules','diagrams/pack lists','readiness','HubSpot deal','dispatch clock','employee files','Bento migration'],'owner_by_value':{'Galley memberships':'Galley: NOT READ','HubSpot deal values':'HubSpot: NOT READ','dispatch timing':'dispatch: NOT READ','Bento payment records':'Bento: NOT READ','Arc authored operational slots':'Arc current code, live data unverified'}},[a('.madewell/ground/PROTOCOL.md','72'),a('docs/decisions/2026-08-23-arc-dispatch-boundary.md','30')])

corpus=[
 row('.madewell/DECISIONS.md','7','decision index','governing rulings','Later accepted ADRs supersede old implementation interpretations'),
 row('.madewell/PRODUCT.md','6','identity pointer','product vision','Points to Arc root PRODUCT.md'),
 row('PRODUCT.md','39','product identity','Bento replacement and build','Build is core to Arc operating model'),
 row('.madewell/SPEC.md','15','work position law','no duplicate board','Position is path; stock is sole work ledger'),
 row('MADEWELL.md','1','protocol entry','discipline','Made Well operates via the current-depth protocol'),
 row('.madewell/jig/README.md','1','implementation discipline','boundary','Jig is implement/verify; Discovery only ideates'),
 row('.madewell/finished/experience-package-context.md','12','finished scoped display','duplicate guard','Finished display does not prove paid parentage'),
 row('.madewell/stock/required-vs-bundled-composition.md','11','legacy stock','selection design history','Older waits must be tested against later ADRs'),
 row('.madewell/stock/paid-package-membership-data-model-plan.md','6','current stock','paid add-on unresolved','Paid membership relationship is still waiting on a decision'),
 row('docs/decisions/2026-09-15-a-choice-option-composes.md','37','accepted ADR','stage/bistro rules','Selected choice composes required children'),
 row('docs/decisions/2026-09-29-galley-product-groups-read-as-choices.md','7','accepted ADR','collection choices','Multi-group exception supersedes narrower earlier rule'),
 row('docs/decisions/2026-09-15-unresolved-quantity-never-blocks-an-add.md','65','accepted ADR','quantity','Unresolved count remains NULL rather than refusing add'),
 row('docs/decisions/2026-08-23-arc-dispatch-boundary.md','30','accepted ADR','clock ownership','Arc projects pack; dispatch owns delivery clock'),
 row('.madewell/stock/bento-cutover-in-one-week.md','7','later migration stock','outdates source schedule','Manual rebuild and payment checks, go-live week unknown'),
 row('.madewell/stock/catalog-composition-coverage-signal.md','6','readiness stock','missing composition','A request for a signal, not evidence it shipped'),
 row('docs/platform/ARCHITECTURE.md','20','data ownership law','actual write paths','Owner/mirror/write/echo/guard declared before integration claims'),
]
mark('C05',{'corpus':corpus,
 'locked_decisions':[
 cite('Selected options compose required children',a('docs/decisions/2026-09-15-a-choice-option-composes.md','37')),
 cite('Unresolved guest-dependent quantities remain NULL',a('docs/decisions/2026-09-15-unresolved-quantity-never-blocks-an-add.md','65')),
 cite('Arc owns pack projection; dispatch owns truck timing',a('docs/decisions/2026-08-23-arc-dispatch-boundary.md','30')),
 cite('Galley food slots remain Galley-owned',a('docs/decisions/2026-09-15-galley-collection-owns-arc-slots.md','10')),
 cite('Position lives in stock, not in observer ledger',a('docs/decisions/2026-09-11-one-ledger.md','28'))],
 'open_questions':[
 cite('Paid package membership model still open',a('.madewell/stock/paid-package-membership-data-model-plan.md','6')),
 cite('Which specific stock cards are superseded by current implementation?',a('.madewell/stock/required-vs-bundled-composition.md','11')),
 cite('When and by what evidence is Bento cut over?',a('.madewell/stock/bento-cutover-in-one-week.md','22')),
 cite('External owner current values not read',a('.madewell/ground/ROOTS.md','23'))],
 'synthesis':cite('The sale must preserve operational choices, physical components, owner rules and readiness without treating dated notes as deployed code',a('docs/decisions/2026-09-15-a-choice-option-composes.md','37'))},[a('.madewell/ground/PICTURE.md','18'),a('docs/decisions/2026-09-15-a-choice-option-composes.md','37')])

surfaces=[
 ('apps/api/src/routes/builds-items.ts',[321,365],'BUILT','Collection group-line and operational-slot materialization visible; live Galley membership unknown'),
 ('apps/web/src/routes/GalleyPackageRows.tsx',[116,151],'BUILT','Collection child rows and choice controls visible; owner values unknown'),
 ('apps/api/src/lib/catalog-slot-rules.ts',[65,82],'PARTIAL','Selection mechanics exist; authored venue and stage components not verified'),
 ('apps/api/src/lib/catalog-slot-rules.ts',[238,310],'PARTIAL','Quantity modes exist; authored factors and case rounding unverified'),
 ('apps/api/src/lib/contracts/tables.ts',[348,399],'PARTIAL','Money-free pack-list projection exists; diagrams and complete readiness unknown'),
 ('apps/web/src/routes/buildCanvas.readiness.ts',[6,28],'PARTIAL','Readiness currently warns but does not refuse confirmation'),
 ('apps/api/src/routes/catalog-media.ts',[87,101],'PARTIAL','Authenticated catalog media routes; not proof of employee-file authorization'),
 ('packages/db/src/schema/deals.ts',[50,55],'PARTIAL','Bento URL field is not a migrated event or reconciled payment'),
]
mark('C06',{'surfaces':[{'path':ARC+p,'lines':ln,'verdict':ver,'summary':summ,'pointer':a(p,str(ln[0]))} for p,ln,ver,summ in surfaces],
 'gap':cite('Source asks for reliable live choices, composition, diagrams and migration; code provides mechanisms, owner data and production acceptance unverified',a('apps/web/src/routes/buildCanvas.readiness.ts','6')),
 'contradictions':[cite('Meeting called Galley collection choices unfinished, code now renders choice controls',a('apps/web/src/routes/GalleyPackageRows.tsx','116')),
 cite('Readiness warning allows continuation; do not call it a hard go-live gate',a('apps/web/src/routes/buildCanvas.readiness.ts','6'))]},[a('.madewell/ground/PICTURE.md','34'),a('apps/api/src/routes/builds-items.ts','321')])
mark('C07',{'owners_not_read':['Galley','HubSpot','dispatch','Bento'],'Arc_mirrors_are_not_external_truth':True,'claims':'Live external values left UNKNOWN'},[a('docs/decisions/2026-09-15-galley-collection-owns-arc-slots.md','129'),a('docs/decisions/2026-08-23-arc-dispatch-boundary.md','30')])
for mid,operation in [('C08','present_corpus_picture'),('C09','present_material_picture'),('C12','present_decision_ready_ground_picture')]:
    call('trace',RUN,mid,operation,'--inputs',json.dumps({'sources':['Ground PICTURE.md','0902 segmented','current Arc docs and code']}),'--outputs',json.dumps({'presented':True,'Arc_writes':False,'external_owners_unverified':True}),'--result','presented in user-facing Ground picture; no Ground file written','--evidence',a('.madewell/ground/PICTURE.md','18'))
mark('C08',{'presented':True,'shape':'corpus table, locked decisions, questions and synthesis presented to user; no Ground file written'},['C08:present_corpus_picture',a('.madewell/ground/PICTURE.md','18')])
mark('C09',{'presented':True,'shape':'material table, verdicts, gaps, contradictions and owner limits presented to user'},['C09:present_material_picture',a('.madewell/ground/PICTURE.md','34')])
mark('C10',{'mechanism':'other hands','reason':'seven high-density topics plus extensive current rack, ADRs and code exceed one context with room left to act','scope':'two read-only Ground halves; synthesis and presentation by main session'},[a('.madewell/ground/PROTOCOL.md','133')])
mark('C11',{'required':cite('Intelligible sold choices must retain physical components and Galley-owned rules',a('docs/decisions/2026-09-15-a-choice-option-composes.md','37')),
 'actual':cite('Arc implements group choices and pack projection; authoring, owner data and go-live acceptance not established',a('apps/api/src/routes/builds-items.ts','321')),
 'locked_decisions':[cite('Choice composes required items',a('docs/decisions/2026-09-15-a-choice-option-composes.md','37')),cite('Arc pack commitment, dispatch clock',a('docs/decisions/2026-08-23-arc-dispatch-boundary.md','30'))],
 'open_decisions':[dict(cite('Paid package membership model',a('.madewell/stock/paid-package-membership-data-model-plan.md','6')),owner='lead'),dict(cite('Live Galley member/food readiness',a('docs/decisions/2026-09-15-galley-collection-owns-arc-slots.md','129')),owner='external'),dict(cite('Bento payments and cutoff evidence',a('.madewell/stock/bento-cutover-in-one-week.md','22')),owner='external')],
 'next_move':cite('Check candidate against current ADR and code before racking; verify external owner and live behavior before declaring done',a('.madewell/ground/PROTOCOL.md','143'))},[a('.madewell/ground/PICTURE.md','46'),a('apps/web/src/routes/buildCanvas.readiness.ts','6')])
mark('C12',{'presented':True,'read_only':True,'boundary':'no Arc changes during Ground; stop at decision-ready picture'},['C12:present_decision_ready_ground_picture',a('.madewell/ground/PROTOCOL.md','143')])

# Only classify what the primary source supports. Names and year are not invented.
mark('D01',{'source_type':'meeting transcript','path':TRANS,'segments':216},[TRANS+':1'])
mark('D02',{'date':'unknown year, September 2 indicated by filename; not established in body','analysis_date':'separate from event date'},[TRANS+':1'])
mark('D03',{'participants':['Nathaniel (filename; turn attribution unverified)','Josh (addressed in audio; turn attribution unverified)','Maggie (addressed and apparently joins; turn attribution unverified)'],'speaker_labels':False},[TRANS+':105',TRANS+':9'])
mark('D04',{'off_stage':['Rosie','Mimi','Kate','dispatch','sales'], 'attribution':'names and roles inferred where unlabeled'},[TRANS+':139',TRANS+':67',TRANS+':343'])
mark('D05',{'maturity':'mixed','basis':'execution/status claims plus planning and ideation, not implementation verification'},[TRANS+':115',TRANS+':317'])
mark('D06',{'per_section':[{'segments':'1-68','maturity':'EXECUTION / PLANNING','basis':'reported builder status and constraints'},{'segments':'69-80','maturity':'PLANNING','basis':'review and recipe ownership discussion'},{'segments':'81-146','maturity':'IDEATION / PLANNING','basis':'venue, variants and quantity alternatives'},{'segments':'147-216','maturity':'PLANNING / IDEATION','basis':'proposed milestones, migration and diagrams'}],'FIELD':'not FIELD: internal product/work discussion, not unmediated customer work'},[TRANS+':1',TRANS+':317',a('.madewell/skills/discovery.md','72')])
mark('D07',{'density':'HIGH','basis':'seven distinct subjects across 216 stable segments; no false line-count trigger'},[TRANS+':1',TRANS+':433'])
mark('E01',{'topic_count':7,'topics':[{'id':i,'segments':span,'label':label} for i,span,label in [
(1,'1-16','Galley collections, feedback authority'),(2,'17-36','onboarding, HubSpot dependencies, security'),(3,'37-68','dispatch, inventory and builder choice visibility'),(4,'69-80','recipe review and food-owner boundaries'),(5,'81-146','venue fees, variants and quantity rules'),(6,'147-180','pack lists and migration'),(7,'181-216','diagrams, readiness and documents')]]},[TRANS+':1',TRANS+':161',TRANS+':363'])
call('configure',RUN,'deep_comb','true')
mark('E02',{'route':'deep-comb','trigger':'HIGH density + 7 distinct non-serial topics; no override'},[a('.madewell/skills/discovery.md','110'),TRANS+':1'])
mark('E03',{'address_space':'216 numbered consecutive sections','committed_source':TRANS,'original':'/home/jrg/projects/infinity/discovery/transcripts/0902_weekly_nathaniel.md','integrity':'normalized content matches original; see source-independent inspection; not independent corroboration'},[TRANS+':1'])
call('mark',RUN,'E04','--status','blocked','--value',json.dumps({'reason':'Seven-slice topic map presented to person; explicit confirmation not received','confirmed':False}),'--evidence',a('.madewell/skills/discovery.md','115'))
print('PRE-FANOUT STOP: E04 remains BLOCKED; no parallel slice analysis without explicit person confirmation.')
