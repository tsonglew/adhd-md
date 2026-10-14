"""Supporting checks; semantic and judge reviews remain explicit per-run records."""
from pathlib import Path
import difflib,json,re
DEST=Path(__file__).resolve().parent

def plain(text):
 stash=[]
 def protect(m):
  stash.append(m.group(0));return '\x00'+str(len(stash)-1)+'\x00'
 text=re.sub(r'^```[^\n]*\n.*?^```[^\n]*$',protect,text,flags=re.M|re.S)
 text=re.sub(r'`[^`\n]+`',protect,text)
 text=re.sub(r'^#{1,6} +','',text,flags=re.M)
 text=re.sub(r'^---[ \t]*$', '', text, flags=re.M)
 text=re.sub(r'^([ \t]*)[-*+] +',r'\1',text,flags=re.M)
 text=re.sub(r'^> ?', '', text, flags=re.M)
 text=re.sub(r'^[ \t]*\[[ xX]\] +', '', text, flags=re.M)
 text=text.replace('**','')
 text=re.sub(r'\s+','',text)
 for i,value in enumerate(stash):text=text.replace('\x00'+str(i)+'\x00',value)
 return text

rows=[]
for p in sorted(DEST.glob('*/metadata.json')):
 d=p.parent;m=json.loads(p.read_text())
 row={k:m.get(k) for k in ('run_id','host','id','repeat','scope','level','exit_code','timed_out','output_exists','input_unchanged','skill_snapshot_matches','source_skill_unchanged')}
 if m['output_exists']:
  a=json.loads((d/'audit-after.json').read_text());v=json.loads((d/'verify.json').read_text())
  original=(d/'input.md').read_text();output=(d/'output.md').read_text()
  row.update(verify=v['status'],score=a['score']['total'],x=a['score']['x_deduct'],byte_identical=original==output)
  if m['scope']=='format':row['visible_sequence_equal']=plain(original)==plain(output)
  (d/'candidate.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),output.splitlines(True),fromfile='input.md',tofile='output.md')))
  report=(d/'assistant-messages.md').read_text()
  for extra in list(d.glob('output*.md'))+list((d/'model-artifacts').rglob('*.md'))+list((d/'model-artifacts').rglob('*.txt')):
   if extra.name!='output.md':report+='\n'+extra.read_text()
  ids=a['coverage']['rule_ids']['judge_only']
  row['judge_ids_not_mentioned']=[i for i in ids if not re.search(r'\b'+i+r'\b',report)]
  calls=json.loads((d/'tool-calls.json').read_text())
  cmds=[]
  for c in calls:
   params=c.get('input',{})
   cmd=c.get('command') or (params.get('command','') if isinstance(params,dict) else '')
   if isinstance(cmd,str) and 'adhd_md.py' in cmd and re.search(r'\b(audit|report)\b',cmd):cmds.append(cmd)
  row['audit_report_commands']=cmds
  row['machine_gate']=v['status']=='pass' and a['score']['x_deduct']==0
  row['review_note']='Rule ID mentions and visible-sequence equality are supporting checks, not semantic proof.'
 rows.append(row)
(DEST/'summary.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
for r in rows:print(r['run_id'],r.get('verify','no output'),'X='+str(r.get('x')), 'same='+str(r.get('visible_sequence_equal')), 'missing_judge='+str(r.get('judge_ids_not_mentioned')))
