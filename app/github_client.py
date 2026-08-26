import requests
import time
import os
from typing import Optional

try:
    import jwt
except Exception:
    jwt = None


class AuthError(Exception):
    pass


class ApiError(Exception):
    pass


class GitHubClient:
    def __init__(self, token: Optional[str] = None, api_url: str = 'https://api.github.com'):
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.headers = None
        if token:
            self._set_token(token)

    @classmethod
    def from_app_credentials(cls, app_id: str, private_key_pem: str, installation_id: str, api_url: str = 'https://api.github.com'):
        if jwt is None:
            raise RuntimeError('PyJWT is required for GitHub App authentication')
        inst_token = cls._get_installation_token(app_id, private_key_pem, installation_id, api_url)
        return cls(token=inst_token, api_url=api_url)

    @staticmethod
    def _generate_jwt(app_id: str, private_key_pem: str) -> str:
        # JWT expiration: 10 minutes
        now = int(time.time())
        payload = {
            'iat': now - 60,
            'exp': now + (10 * 60),
            'iss': str(app_id)
        }
        return jwt.encode(payload, private_key_pem, algorithm='RS256')

    @classmethod
    def _get_installation_token(cls, app_id: str, private_key_pem: str, installation_id: str, api_url: str = 'https://api.github.com') -> str:
        jwt_token = cls._generate_jwt(app_id, private_key_pem)
        headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {jwt_token}'
        }
        url = f"{api_url.rstrip('/')}/app/installations/{installation_id}/access_tokens"
        r = requests.post(url, headers=headers)
        if r.status_code >= 400:
            raise AuthError(f"Failed to get installation token: {r.status_code} {r.text}")
        data = r.json()
        return data.get('token')

    def _set_token(self, token: str):
        self.token = token
        self.headers = {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'token {self.token}'
        }

    def _get(self, path: str):
        url = f"{self.api_url}{path}"
        r = requests.get(url, headers=self.headers)
        if r.status_code in (401, 403):
            raise AuthError(r.text)
        r.raise_for_status()
        return r.json()

    def get_authenticated_user(self):
        return self._get('/user')

    def repo_exists(self, owner: str, repo_name: str):
        path = f'/repos/{owner}/{repo_name}'
        try:
            data = self._get(path)
            # Ensure response looks like a repository object
            if isinstance(data, dict) and data.get('name') and data.get('full_name'):
                return True, data
            return False, None
        except Exception as e:
            # If 404, repo does not exist
            if isinstance(e, requests.exceptions.HTTPError) and getattr(e.response, 'status_code', None) == 404:
                return False, None
            # Try to detect ApiError wrapper
            if '404' in str(e):
                return False, None
            raise

    def create_repository(self, owner: str, payload: dict, max_retries: int = 3):
        # Idempotency: if repo exists, return it
        exists, data = self.repo_exists(owner, payload.get('name'))
        if exists:
            return data

        # Decide endpoint: create under org or user
        auth_user = self.get_authenticated_user()
        auth_login = auth_user.get('login')
        if owner == auth_login:
            path = '/user/repos'
        else:
            path = f'/orgs/{owner}/repos'

        url = f"{self.api_url}{path}"

        attempt = 0
        while attempt < max_retries:
            r = requests.post(url, headers=self.headers, json=payload)
            if r.status_code == 201:
                return r.json()
            if r.status_code in (401, 403):
                raise AuthError(r.text)
            if r.status_code >= 500 or r.status_code == 429:
                attempt += 1
                backoff = 2 ** attempt
                time.sleep(backoff)
                continue
            # 4xx other than auth
            raise ApiError(f"{r.status_code}: {r.text}")

        raise ApiError('Max retries exceeded')

    @classmethod
    def from_env(cls):
        # Helper to create client based on environment variables
        api_url = os.environ.get('GITHUB_API_URL', 'https://api.github.com')
        token = os.environ.get('GITHUB_TOKEN')
        if token:
            return cls(token=token, api_url=api_url)

        # Try GitHub App variables
        app_id = os.environ.get('GITHUB_APP_ID')
        installation_id = os.environ.get('GITHUB_INSTALLATION_ID')
        private_key = os.environ.get('GITHUB_APP_PRIVATE_KEY')
        if app_id and installation_id and private_key:
            return cls.from_app_credentials(app_id, private_key, installation_id, api_url=api_url)

        raise AuthError('No GITHUB_TOKEN or GitHub App credentials found in environment')
