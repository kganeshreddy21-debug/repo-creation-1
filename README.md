GitHub Repository Automation

This project provides a Jenkins-driven automation to create GitHub repositories for the authenticated account associated with a Jenkins-stored token (GitHub Enterprise supported).

Quick start

1. Store your existing GitHub Enterprise Personal Access Token in Jenkins Credentials with ID `github-enterprise-token`.
2. Create a Jenkins Pipeline job using the provided `Jenkinsfile` and enable "Build with Parameters".
3. When running, provide `REPO_NAME`, `VISIBILITY`, `DESCRIPTION`, `INITIALIZE_README`, and set `GITHUB_API_URL` to your GitHub Enterprise API URL (e.g. `https://github.example.com/api/v3`).
4. The pipeline will inject the stored token as `GITHUB_TOKEN` (securely, via Jenkins Credentials Binding) and run `python3 app/create_repo.py`.

Python CLI

The CLI no longer accepts an `--owner` parameter. The repository is created under the authenticated account derived from the token.

Example (local test only):

```bash
export GITHUB_TOKEN="<your-token>"
export GITHUB_API_URL="https://github.example.com/api/v3"
python3 app/create_repo.py --repo-name employee-api --visibility private --init-readme --description "Repo created by Jenkins" --output repo_result.json
```

Security

- The Jenkinsfile uses the existing credential `github-enterprise-token` (change the credential id in `Jenkinsfile` if yours differs).
- The token is injected as `GITHUB_TOKEN` for the process and is never printed, written to files, or committed.
- For Vault-based secrets, set `SECRET_STORE=VAULT` and configure AppRole credentials as documented in the README.


Vault integration (optional)

This repository includes a simple example showing how to fetch secrets from HashiCorp Vault using AppRole and use them as `GITHUB_TOKEN` in the Jenkins job.

1. Create AppRole in Vault and store role_id/secret_id as Jenkins credentials named `vault-role-id` and `vault-secret-id`.
2. Put your GitHub token at `secret/data/github` with key `token` (KV v2).
3. In Jenkins job, set `SECRET_STORE` to `VAULT` and add credential `vault-addr` pointing to your Vault address (e.g. https://vault.example.com).
4. The pipeline will run `scripts/fetch_vault_secret.sh secret/data/github token` to retrieve and export `GITHUB_TOKEN` for the CLI.

Note: This is a minimal example. For production, use the official Jenkins Vault plugin or a secure approle bootstrap and avoid storing secret IDs in plaintext Jenkins credentials.

Containerize and version the CLI; publish images and pin versions in Jenkins to avoid environment drift.
  - Use the included GitHub Actions workflow to publish a Docker image to GitHub Container Registry when you tag a release. Update `Jenkinsfile` to pull and run the published image instead of running local Python.
GitHub Repository Automation

This project provides a Jenkins-driven automation to create GitHub repositories.

Quick start

1. Place a GitHub token in Jenkins credentials as `github-token` and bind it to `GITHUB_TOKEN` env var.
	Alternatively, configure a GitHub App and store its private key as a Jenkins `file` credential named `github-app-private-key`, plus `github-app-id` and `github-installation-id` as string credentials.
2. Configure the `Jenkinsfile` parameters via Jenkins job (or use Multibranch Pipeline).
3. Run the job; the pipeline will invoke `python3 app/create_repo.py` and produce `repo_result.json`.

Python CLI

Example:

```bash
export GITHUB_TOKEN="ghp_xxx"
python3 app/create_repo.py --repo-name employee-api --owner my-company --visibility private --init-readme --output repo_result.json
```

Docker

Build:

```bash
docker build -t repo-creator:latest .
```

Run:

```bash
docker run -e GITHUB_TOKEN -v $(pwd):/out repo-creator:latest --repo-name employee-api --owner my-company --visibility private --output /out/repo_result.json
```

Security

Prefer using a GitHub App or a minimally-scoped PAT stored in Jenkins credentials. Do not print tokens in logs.

GitHub App notes:
- Store the private key as a file credential (`github-app-private-key`).
- Add `github-app-id` and `github-installation-id` as string credentials.
- Set `AUTH_TYPE` parameter to `GITHUB_APP` in the Jenkins job.
