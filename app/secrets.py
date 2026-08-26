import os
import requests


def fetch_from_vault(secret_path: str, key: str = 'value') -> str:
    """Simple Vault fetch helper. Expects VAULT_ADDR and VAULT_TOKEN in env.
    Returns secret value for given path; assumes KV v2 common structure.
    """
    vault_addr = os.environ.get('VAULT_ADDR')
    vault_token = os.environ.get('VAULT_TOKEN')
    if not vault_addr or not vault_token:
        raise RuntimeError('Vault not configured (VAULT_ADDR/VAULT_TOKEN)')

    url = f"{vault_addr.rstrip('/')}/v1/{secret_path}"
    headers = {'X-Vault-Token': vault_token}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    # Try KV v2 structure
    if 'data' in data and isinstance(data['data'], dict):
        # KV v2 has nested data.data
        if 'data' in data['data']:
            return data['data']['data'].get(key)
        return data['data'].get(key)
    return None
