import argparse, datetime, hashlib, json, os, pathlib, platform, re, shutil, signal, subprocess, time
ROOT = pathlib.Path('/Users/liucong03/Documents/adhd-md')
BASE = pathlib.Path('/tmp/adhd-eval-20261014')
CORPUS = ROOT / 'docs/eval-corpus/held-out'
MANIFEST = (CORPUS / 'manifest.md').read_text()
CASES = {}
for line in MANIFEST.splitlines():
    if re.match(r'\| H\d\d \|', line):
        cells = [c.strip() for c in line.strip('|').split('|')]
        scope, level = cells[3].split(' / ')
        CASES[cells[0]] = dict(id=cells[0], file=cells[1].strip('`'), language=cells[2].split(' / ')[0], document_type=cells[2].split(' / ')[1], scope=scope, level=level, constraints=cells[5])
TEMPLATES = {}
for title, body in re.findall(r'^### (.+)\n\n> (.+)$', MANIFEST, re.M):
    language, scope = title.split(' · ')
    TEMPLATES[('zh' if language == '中文' else 'en', scope)] = body

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def command(host, prompt):
    return {
        'codex': ['codex', 'exec', '-s', 'workspace-write', '--skip-git-repo-check', '--json', '--ephemeral', prompt],
        'claude': ['claude', '-p', '--output-format', 'stream-json', '--verbose', '--permission-mode', 'acceptEdits', '--allowedTools', 'Read,Write,Edit,Glob,Grep,Bash(python3 *),Bash(git status *),Bash(git -C *),Bash(cat *),Bash(ls *),Bash(cp *)', '--', prompt],
        'grok': ['grok', '--prompt-file', 'prompt.txt', '--output-format', 'streaming-json', '--permission-mode', 'acceptEdits', '--no-subagents', '--allow', 'Bash(python3 *)', '--allow', 'Bash(ls *)', '--allow', 'Bash(cat *)', '--allow', 'Bash(git *)', '--allow', 'Bash(find *)', '--allow', 'Bash(head *)', '--max-turns', '60'],
        'gemini': ['gemini', '-p', prompt, '--output-format', 'stream-json', '--approval-mode', 'auto_edit', '--allowed-tools', 'run_shell_command(python3),run_shell_command(git status),run_shell_command(cat),run_shell_command(ls)'],
        'cursor': ['cursor-agent', '-p', '--output-format', 'stream-json', '--sandbox', 'enabled', prompt],
        'opencode': ['opencode', 'run', '--format', 'json', prompt],
    }[host]

def run(host, case_id, repeat, timeout):
    case = CASES[case_id]
    run_id = f'{host}-{case_id}-r{repeat}'
    folder = BASE / run_id
    folder.mkdir(exist_ok=False)
    work = folder / 'workspace'
    work.mkdir()
    shutil.copy2(CORPUS / case['file'], work / 'input.md')
    skill = work / '.agents/skills/adhd-md'
    shutil.copytree(ROOT / 'skill', skill, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for hostdir in ('.codex', '.claude', '.grok', '.gemini', '.cursor', '.opencode'):
        dest = work / hostdir / 'skills/adhd-md'
        dest.parent.mkdir(parents=True)
        dest.symlink_to('../../.agents/skills/adhd-md')
    context = f"# Frozen evaluation case {case_id}\n\nLanguage: {case['language']}\nDocument type: {case['document_type']}\nscope={case['scope']}\nlevel={case['level']}\n\nThe adhd-md skill snapshot is at `.agents/skills/adhd-md/SKILL.md`.\n"
    (work / 'AGENTS.md').write_text(context)
    (work / 'CLAUDE.md').write_text(context)
    (work / 'GEMINI.md').write_text(context)
    prompt = TEMPLATES[case['language'], case['scope']].replace('{input}', 'input.md').replace('{output}', 'output.md')
    (folder / 'prompt.txt').write_text(prompt + '\n')
    (work / 'prompt.txt').write_text(prompt + '\n')
    cmd = command(host, prompt)
    meta = dict(case, run_id=run_id, host=host, repeat=repeat, input_sha256=digest(work/'input.md'), corpus_manifest_sha256=digest(CORPUS/'manifest.md'), skill_commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT,text=True).strip(), skill_tree=subprocess.check_output(['git','rev-parse','HEAD:skill'], cwd=ROOT,text=True).strip(), command=cmd, platform=platform.platform(), started=datetime.datetime.now(datetime.timezone.utc).isoformat(), timeout_seconds=timeout, discovery='unknown', loading='unknown', tool_execution='unknown', independent_review='pending')
    try:
        version = subprocess.run([{'cursor':'cursor-agent'}.get(host,host),'--version'], text=True, capture_output=True, timeout=20)
        meta['cli_version'] = version.stdout.strip()
    except Exception as e:
        meta['cli_version'] = str(e)
    save(folder/'metadata.json', meta)
    start=time.monotonic()
    with (folder/'stdout.jsonl').open('w') as out, (folder/'stderr.log').open('w') as err:
        process=subprocess.Popen(cmd,cwd=work,stdin=subprocess.DEVNULL,stdout=out,stderr=err,start_new_session=True)
        try:
            meta['exit_code']=process.wait(timeout=timeout)
            meta['timed_out']=False
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGTERM)
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL)
                process.wait()
            meta['exit_code']=process.returncode
            meta['timed_out']=True
    meta['duration_seconds']=round(time.monotonic()-start,2)
    meta['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    meta['input_unchanged']=digest(work/'input.md')==meta['input_sha256']
    for name in ('stdout.jsonl','stderr.log'):
        meta[name+'_sha256']=digest(folder/name)
    output=work/'output.md'
    meta['output_exists']=output.is_file()
    if output.is_file():
        meta['output_sha256']=digest(output)
        tool=ROOT/'skill/scripts/adhd_md.py'
        jobs={
            'audit-before':['audit',str(CORPUS/case['file']),'--level',str(3 if case['level']=='deep' else 2),'--scope',case['scope'],'--json'],
            'audit-after':['audit',str(output),'--level',str(3 if case['level']=='deep' else 2),'--scope',case['scope'],'--json'],
            'verify':['verify',str(CORPUS/case['file']),str(output),'--scope',case['scope'],'--json'],
            'report':['report',str(CORPUS/case['file']),str(output),'--scope',case['scope'],'--level',str(3 if case['level']=='deep' else 2),'--json'],
        }
        for name,args in jobs.items():
            check=subprocess.run(['python3',str(tool)]+args,capture_output=True,text=True)
            (folder/(name+'.json')).write_text(check.stdout)
            (folder/(name+'.stderr')).write_text(check.stderr)
            meta[name+'_exit']=check.returncode
    save(folder/'metadata.json',meta)
    print(json.dumps({k:meta[k] for k in ('run_id','exit_code','timed_out','duration_seconds','output_exists','input_unchanged')},ensure_ascii=False),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('host',choices=['codex','claude','grok','gemini','cursor','opencode'])
    parser.add_argument('--cases',default=','.join(CASES))
    parser.add_argument('--repeat',type=int,default=1)
    parser.add_argument('--timeout',type=int,default=600)
    args=parser.parse_args()
    for case_id in args.cases.split(','):
        run(args.host,case_id,args.repeat,args.timeout)
