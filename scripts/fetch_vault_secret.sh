#!/usr/bin/env bash
# Simple helper to fetch a secret from HashiCorp Vault (KV v2) using AppRole
# Expects VAULT_ADDR, ROLE_ID and SECRET_ID environment variables or Jenkins credentials.

set -euo pipefail

if [ -z "${VAULT_ADDR:-}" ]; then
  echo "VAULT_ADDR not set" >&2
  exit 2
fi

if [ -z "${ROLE_ID:-}" ] || [ -z "${SECRET_ID:-}" ]; then
  echo "ROLE_ID and SECRET_ID must be provided" >&2
  exit 2
fi

# Authenticate with AppRole
TOKEN=$(curl -s --request POST --data "{\"role_id\": \"$ROLE_ID\", \"secret_id\": \"$SECRET_ID\"}" "$VAULT_ADDR/v1/auth/approle/login" | jq -r .auth.client_token)
if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "Failed to obtain Vault token" >&2
  exit 3
fi

SECRET_PATH="$1"
KEY=${2:-value}

RESP=$(curl -s --header "X-Vault-Token: $TOKEN" "$VAULT_ADDR/v1/$SECRET_PATH")
echo "$RESP" | jq -r ".data.data.$KEY"
