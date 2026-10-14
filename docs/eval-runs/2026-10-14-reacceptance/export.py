"""Preserve completed model runs without rewriting the original evaluation."""
from pathlib import Path
import gzip, hashlib, json, shutil, tarfile
DEST=Path(__file__).resolve().parent
BASE=Path('/tmp/adhd-reacceptance-20261014')
(DEST/'raw').mkdir(exist_ok=True)
(DEST/'.gitignore').write_text('raw/\n')
for d in sorted(BASE.glob('*')):
 meta=json.loads((d/'metadata.json').read_text())
 if 'exit_code' not in meta: continue
 out=DEST/d.name;out.mkdir(exist_ok=True)
 shutil.copy2(d/'prompt.txt',out/'prompt.txt')
 for p in d.glob('*.json'):
  if p.name!='actual-skill-snapshot.json':shutil.copy2(p,out/p.name)
 for name in sorted({p.name for p in (d/'workspace').glob('output*') if p.is_file()} | {'input.md'}):
  p=d/'workspace'/name
  if p.exists():shutil.copy2(p,out/name)
 artifacts=out/'model-artifacts';artifacts.mkdir(exist_ok=True)
 for file in (d/'workspace').rglob('*'):
  relative=file.relative_to(d/'workspace')
  if relative.parts[0].startswith('.'):
   continue
  if file.is_file() and file.suffix in ('.md','.json','.txt','.diff') and str(relative) not in ('input.md','output.md','AGENTS.md','CLAUDE.md','GEMINI.md','prompt.txt'):
   target=artifacts/relative;target.parent.mkdir(parents=True,exist_ok=True)
   shutil.copy2(file,target)
 snapshot=d/'workspace/.agents/skills/adhd-md'
 manifest={str(p.relative_to(snapshot)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(snapshot.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
 (out/'actual-skill-snapshot.json').write_text(json.dumps(manifest,indent=2)+'\n')
 with tarfile.open(DEST/'raw'/f'{d.name}-skill.tar.gz','w:gz') as archive:archive.add(snapshot,arcname='skill')
 texts=[];calls=[];models=set()
 for line in (d/'stdout.jsonl').read_text().splitlines():
  try:e=json.loads(line)
  except ValueError:continue
  if isinstance(e.get('message'),dict) and e['message'].get('model'):models.add(e['message']['model'])
  if isinstance(e.get('model'),str):models.add(e['model'])
  if isinstance(e.get('modelUsage'),dict):models.update(e['modelUsage'])
  if e.get('type')=='item.completed':
   i=e.get('item',{})
   if i.get('type')=='agent_message':texts.append(i.get('text',''))
   elif i.get('type')=='command_execution':calls.append({'command':i.get('command'),'exit_code':i.get('exit_code')})
  if e.get('type')=='assistant':
   for b in e.get('message',{}).get('content',[]):
    if b.get('type')=='text':texts.append(b.get('text',''))
    elif b.get('type')=='tool_use':calls.append({'tool':b.get('name'),'input':b.get('input')})
  if e.get('type')=='result' and e.get('result'):texts.append(e['result'])
  if e.get('type')=='tool_call':calls.append({'tool':e.get('toolName'),'input':e.get('rawInput')})
 (out/'assistant-messages.md').write_text('\n\n'.join(texts)+'\n')
 (out/'response-models.json').write_text(json.dumps(sorted(models),indent=2)+'\n')
 (out/'tool-calls.json').write_text(json.dumps(calls,ensure_ascii=False,indent=2)+'\n')
 for name in ('stdout.jsonl','stderr.log'):
  with gzip.open(DEST/'raw'/f'{d.name}-{name}.gz','wb') as f:f.write((d/name).read_bytes())
 print(d.name,meta['exit_code'],meta.get('verify_exit'))
