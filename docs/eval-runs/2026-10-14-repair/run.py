"""Run frozen repair cases using the historical CLI harness, retaining actual snapshot hashes."""
import hashlib, importlib.util, json, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('harness', ROOT/'docs/eval-runs/2026-10-14/run-harness.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
h.ROOT = ROOT
h.BASE = pathlib.Path('/tmp/adhd-repair-validation')
h.BASE.mkdir(exist_ok=True)
h.CORPUS = ROOT/'docs/eval-corpus/repair-validation'
h.CASES = {
 'R01': dict(id='R01',file='content.md',language='en',document_type='runbook',scope='content',level='deep',constraints='Preserve facts, guards and layout.'),
 'R02': dict(id='R02',file='format.md',language='zh',document_type='reference',scope='format',level='deep',constraints='Preserve all original punctuation and characters.'),
}
h.TEMPLATES = {
 ('en','content'): 'Use the local adhd-md skill to improve {input}, scope=content, level=deep. Preserve the original layout style and all information. Write {output}. Report checks and judge-rule decisions.',
 ('zh','format'): '用本地 adhd-md skill 优化 {input}，scope=format，level=deep。保留所有原字、标点和信息，写到 {output}。报告校验及需判断规则的结论。',
}
repeat = int(sys.argv[3]) if len(sys.argv)>3 else 1
for case in ([sys.argv[2]] if len(sys.argv)>2 else h.CASES):
 h.run(sys.argv[1],case,repeat,600)
 folder=h.BASE/f'{sys.argv[1]}-{case}-r{repeat}'
 snapshot=folder/'workspace/.agents/skills/adhd-md'
 manifest = {str(p.relative_to(snapshot)):h.digest(p) for p in sorted(snapshot.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc'}
 h.save(folder/'actual-skill-snapshot.json',manifest)
