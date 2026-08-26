import unittest
from unittest.mock import patch, MagicMock

from app.github_client import GitHubClient, AuthError, ApiError

class TestGitHubClient(unittest.TestCase):
    @patch('app.github_client.requests.get')
    @patch('app.github_client.requests.post')
    def test_create_repo_user(self, mock_post, mock_get):
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {'login': 'alice'})
        mock_post.return_value = MagicMock(status_code=201, json=lambda: {'name': 'repo'})
        client = GitHubClient('fake-token')
        res = client.create_repository(owner='alice', payload={'name': 'repo'})
        self.assertEqual(res.get('name'), 'repo')

    def test_from_env_with_token(self):
        import os
        os.environ['GITHUB_TOKEN'] = 'env-token'
        client = GitHubClient.from_env()
        self.assertIsNotNone(client.token)
        del os.environ['GITHUB_TOKEN']

if __name__ == '__main__':
    unittest.main()
