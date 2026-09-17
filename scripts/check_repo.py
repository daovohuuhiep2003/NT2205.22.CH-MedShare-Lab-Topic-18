"""Run the repository's read-only checks; no services, dependencies or network."""
from pathlib import Path
import ast
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    # Validate syntax without writing bytecode; only explicit source/tooling trees.
    files=[]
    for dirname in ('scripts','src','tests'):
        files.extend((ROOT/dirname).rglob('*.py'))
    for path in files:
        ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path.relative_to(ROOT)))
    print('Python syntax checks:',len(files),'files',flush=True)
    commands=[
        ['scripts/validate_docs.py','--self-test'],
        ['scripts/validate_proposal_sync.py','--self-test'],
        ['scripts/validate_docs.py'],
        ['scripts/validate_proposal_sync.py'],
        ['scripts/render_proposal.py','--check'],
        ['-m','unittest','discover','-s','tests/tooling','-p','test_*.py','-v'],
    ]
    for command in commands:
        print('CHECK:', ' '.join(command),flush=True)
        result=subprocess.run([sys.executable,'-B',*command],cwd=ROOT,check=False)
        if result.returncode:
            print('FAILED:',command[0],flush=True)
            return result.returncode
    print('PASS: repository/tooling checks only; application tests and benchmarks NOT_RUN.',flush=True)
    return 0


if __name__=='__main__': raise SystemExit(main())
