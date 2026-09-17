from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_docs import SOURCE_HASHES, validate
from validate_proposal_sync import validate as validate_sync


class RepositoryTests(unittest.TestCase):
    def test_relocated_requirements_are_unchanged(self):
        for name,digest in SOURCE_HASHES.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest().upper(),digest)

    def test_documents_and_links_pass(self):
        self.assertEqual(validate(ROOT)['errors'],[])

    def test_proposal_sync_passes(self):
        self.assertEqual(validate_sync(ROOT)['errors'],[])

    def test_core_is_explicitly_a_scaffold(self):
        source=ROOT/'src/medshare'
        self.assertTrue((source/'README.md').is_file())
        for component in ('gateway','crypto','broker','policy','storage'):
            self.assertTrue((source/component/'__init__.py').is_file())
        self.assertIn('chưa được triển khai',(ROOT/'README.md').read_text(encoding='utf-8'))

    def test_sources_keep_original_line_endings_in_git(self):
        attributes=(ROOT/'.gitattributes').read_text(encoding='utf-8')
        for name in SOURCE_HASHES:
            self.assertIn(name+' -text',attributes)

    def test_gitignore_hides_local_sensitive_paths_not_docs(self):
        git=shutil.which('git')
        if not git or not (ROOT/'.git').exists():
            self.skipTest('Git metadata not initialized')
        hidden=['.local-backups/check.zip','.env','.env.dev','infra/runtime/db/file',
                'datasets/generated/sample.json','datasets/oracle/plaintext.json',
                'evidence/runs/run.json','benchmarks/results/raw.csv',
                'private.key','private.pem','docs/proposal/~$project-proposal.docx']
        command=[git,'-c','safe.directory='+ROOT.as_posix(),'check-ignore','-z','--stdin']
        result=subprocess.run(command,input=(chr(0).join(hidden)+chr(0)).encode('utf-8'),
                              cwd=ROOT,capture_output=True,check=False)
        self.assertEqual(result.returncode,0)
        self.assertEqual(set(result.stdout.decode('utf-8').strip(chr(0)).split(chr(0))),set(hidden))
        visible=['README.md','docs/proposal/project-proposal.md','docs/proposal/project-proposal.docx',
                 'docs/requirements/course-guideline.md','src/medshare/__init__.py']
        result=subprocess.run(command,input=(chr(0).join(visible)+chr(0)).encode('utf-8'),
                              cwd=ROOT,capture_output=True,check=False)
        self.assertEqual(result.returncode,1)
        self.assertEqual(result.stdout,b'')


if __name__=='__main__': unittest.main()
