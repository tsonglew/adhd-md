"""Separate configured path, observed loading, tool requests, and outcome."""
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parent
for p in sorted(ROOT.glob('*/metadata.json')):
 d=p.parent;m=json.loads(p.read_text());calls=json.loads((d/'tool-calls.json').read_text())
 local=[];commands=[];level_calls=[]
 for i,c in enumerate(calls):
  encoded=json.dumps(c,ensure_ascii=False)
  if 'SKILL.md' in encoded and ('/'+m['run_id']+'/workspace/' in encoded or re.search(r'(?<![/\w])\.(agents|claude|codex)/skills/adhd-md',encoded)):local.append(i)
  params=c.get('input',{});cmd=c.get('command') or (params.get('command','') if isinstance(params,dict) else '')
  if isinstance(cmd,str) and re.search(r'adhd_md\.py\s+(audit|report|verify|fmt)\b',cmd):
   commands.append(i)
   for match in re.finditer(r'adhd_md\.py\s+(audit|report)\s+([^;\n]+)',cmd):
    if '--help' in match[2]:continue
    level=re.search(r'--level(?:=|\s+)([123])',match[2])
    level_calls.append({'command_index':i,'operation':match[1],'level':level[1] if level else 'implicit/indirect; inspect command'})
 observation={'discovery':'Task context explicitly supplies local snapshot path; this is not an automatic-discovery-only test.','loading':'local SKILL.md reference observed in tool trace' if local else 'not confirmed from captured tool trace','local_skill_tool_indices':local,'tool_execution':'local audit/report/verify command requests observed; raw logs retain results' if commands else 'not confirmed from captured trace','checker_tool_indices':commands,'audit_report_levels':level_calls,'expected_level':3 if m['level']=='deep' else 2,'runtime_exit':m['exit_code'],'output_exists':m['output_exists'],'final_machine_checks':'independent harness ran against frozen source and output' if m['output_exists'] else 'no output to verify','note':'CLI exit, loading, tool requests and output validity are distinct. Missing trace evidence is not counted as success.'}
 (d/'host-observation.json').write_text(json.dumps(observation,ensure_ascii=False,indent=2)+'\n')
 if m['host'] in ('codex','claude') and not local:print('Loading trace requires review:',d.name)
 for call in level_calls:
  if call['level'] not in (str(observation['expected_level']),'implicit/indirect; inspect command'):print('Unexpected level:',d.name,call)
