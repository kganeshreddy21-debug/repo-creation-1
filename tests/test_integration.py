import os
import sys
import runpy
import json
import tempfile
import unittest
from unittest.mock import MagicMock, patch


class TestIntegrationCreateRepo(unittest.TestCase):
    def test_cli_creates_repo_with_mocked_github(self):
        repo_py = os.path.join(os.path.dirname(__file__), '..', 'app', 'create_repo.py')
        repo_py = os.path.normpath(repo_py)

        # Prepare temporary output file
        tmpdir = tempfile.mkdtemp()
        outpath = os.path.join(tmpdir, 'repo_result.json')

        # Mock GitHub API calls in app.github_client
        with patch('app.github_client.requests.get') as mock_get, patch('app.github_client.requests.post') as mock_post:
            # Mock authenticated user
            mg = MagicMock()
            mg.status_code = 200
            mg.json = lambda: {'login': 'bob'}
            mock_get.return_value = mg

            # Mock create repo response
            mr = MagicMock()
            mr.status_code = 201
            mr.json = lambda: {
                'id': 123,
                'name': 'repo1',
                'full_name': 'bob/repo1',
                'html_url': 'https://github.com/bob/repo1',
                'clone_url': 'https://github.com/bob/repo1.git',
                'private': True,
                'default_branch': 'main',
                'owner': {'login': 'bob', 'id': 1}
            }
            mock_post.return_value = mr

            # Set env token
            os.environ['GITHUB_TOKEN'] = 'fake-token'

            # Prepare argv and run the script in-process
            old_argv = sys.argv.copy()
            sys.argv = ['create_repo.py', '--repo-name', 'repo1', '--visibility', 'private', '--output', outpath]
            try:
                with self.assertRaises(SystemExit) as cm:
                    runpy.run_path(repo_py, run_name='__main__')
                self.assertEqual(cm.exception.code, 0)
            finally:
                sys.argv = old_argv

            # Verify output file
            with open(outpath, 'r') as f:
                data = json.load(f)
            self.assertTrue(data.get('success'))
            self.assertEqual(data['repo']['full_name'], 'bob/repo1')


if __name__ == '__main__':
    unittest.main()
