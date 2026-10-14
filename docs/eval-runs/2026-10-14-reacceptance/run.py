"""Run the active regression subset; archived plan.json retains the original matrix."""
import argparse, concurrent.futures, hashlib, importlib.util, json, pathlib, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[3]
DEST=pathlib.Path(__file__).resolve().parent
BASE=pathlib.Path('/tmp/adhd-reacceptance-20261014')
def active_cases():
 suite=json.loads((ROOT/'docs/eval-corpus/active-suite.json').read_text())
 cases=suite['active_cases']
 excluded=suite['excluded_cases']
 known={f'H{i:02}' for i in range(1,13)}
 if len(cases)!=len(set(cases)) or set(cases)&set(excluded) or set(cases)|set(excluded)!=known:
  raise ValueError('Active and excluded cases must partition H01–H12')
 return cases
def hashes(root):
 return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def job(host,case,repeat):
 if case.startswith('H') and case not in active_cases():
  raise ValueError(f'{case} is excluded from the current acceptance suite')
 spec=importlib.util.spec_from_file_location('harness',ROOT/'docs/eval-runs/2026-10-14/run-harness.py')
 h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
 h.ROOT=ROOT;h.BASE=BASE
 if case.startswith('R'):
  h.CORPUS=ROOT/'docs/eval-corpus/repair-validation'
  h.CASES={'R01':dict(id='R01',file='content.md',language='en',document_type='runbook',scope='content',level='deep',constraints='Preserve factual guards and layout style; judge rule decisions must respect scope.'),'R02':dict(id='R02',file='format.md',language='zh',document_type='reference',scope='format',level='deep',constraints='Preserve punctuation, literals, comment and inclusive threshold.')}
  h.TEMPLATES={('en','content'):'Use the local adhd-md skill to improve {input}, scope=content, level=deep. Preserve the original layout style and all information. Write {output}. Report checks and judge-rule decisions.',('zh','format'):'用本地 adhd-md skill 优化 {input}，scope=format，level=deep。保留所有原字、标点和信息，写到 {output}。报告校验及需判断规则的结论。'}
 expected=json.loads((DEST/'skill-snapshot.json').read_text())
 assert hashes(ROOT/'skill')==expected,'Skill changed before execution'
 h.run(host,case,repeat,600)
 folder=BASE/f'{host}-{case}-r{repeat}'
 actual=hashes(folder/'workspace/.agents/skills/adhd-md')
 write(folder/'actual-skill-snapshot.json',actual)
 meta=json.loads((folder/'metadata.json').read_text())
 meta.update(skill_snapshot_matches=actual==expected,source_skill_unchanged=hashes(ROOT/'skill')==expected,provenance='Uncommitted working tree: skill-snapshot.json is authoritative; HEAD alone does not describe the tested version.')
 write(folder/'metadata.json',meta)
def main():
 p=argparse.ArgumentParser();p.add_argument('--job',nargs=3);p.add_argument('--workers',type=int,default=6);p.add_argument('--plan',action='store_true');args=p.parse_args()
 if args.job:return job(args.job[0],args.job[1],int(args.job[2]))
 jobs=[(host,case,r) for case in active_cases() for r in range(1,4 if case in ('H03','H06','H09','H12') else 2) for host in ('codex','claude')]
 jobs += [(host,'R01',1) for host in ('codex','claude')]
 jobs += [(host,'H01',1) for host in ('cursor','gemini','opencode','grok')]
 if args.plan:
  print(json.dumps({'jobs':jobs,'suite':'docs/eval-corpus/active-suite.json'},ensure_ascii=False,indent=2));return
 BASE.mkdir(exist_ok=False)
 write(DEST/'skill-snapshot.json',hashes(ROOT/'skill'))
 (DEST/'source.patch').write_bytes(subprocess.check_output(['git','diff','--','skill/'],cwd=ROOT))
 write(DEST/'plan.json',{'jobs':jobs,'workers':args.workers,'timeout_seconds':600,'corpus_kind':'regression, previously used for tuning','review':'preannotated constraints + coordinator review, not human signoff','no_tuning_during_run':True})
 def launch(j):
  r=subprocess.run([sys.executable,__file__,'--job',j[0],j[1],str(j[2])],cwd=ROOT,capture_output=True,text=True)
  print(r.stdout.strip() or json.dumps({'job':j,'exit':r.returncode,'stderr':r.stderr[-1000:]}),flush=True)
  if r.returncode:write(DEST/('-'.join(map(str,j))+'-runner-error.json'),{'exit':r.returncode,'stderr':r.stderr})
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:list(pool.map(launch,jobs))
 assert hashes(ROOT/'skill')==json.loads((DEST/'skill-snapshot.json').read_text())
if __name__=='__main__':main()
