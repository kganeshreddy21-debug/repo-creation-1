Runbook — GitHub Repository Automation

Purpose
-------
Operational runbook for the Jenkins-driven GitHub Repository Automation system.

Contacts
--------
- On-call/Owners: platform-team@example.com
- Slack channel: #platform-automation

Incident Prioritization
-----------------------
- P0: rogue repo creation, leaked token, org-wide outage
- P1: repeated create failures (rate limit / 5xx)
- P2: single-repo create failure, validation errors

Immediate Actions (P0)
----------------------
1. Revoke credentials immediately:
   - For PAT: go to https://github.com/settings/tokens and revoke the token.
   - For GitHub App: remove the App installation from the org or rotate the private key in App settings.
2. Disable Jenkins job (disable build) and revoke job permissions.
3. Notify stakeholders (Slack + email) and open incident ticket.
4. Audit created repos: use GitHub audit logs or search for recent repos matching pattern. Remove malicious repos if required.
5. Rotate secrets in Vault or Jenkins credentials, add new secrets, and re-enable job after verification.

Token Rotation (PAT)
---------------------
- Create a new PAT with minimal scopes used (repo, admin:org only if required).
- In Jenkins: update the credential `github-token` (replace secret text), or create a new credential and update job to use it.
- Test: run job in `dry-run` mode or `--whoami` to verify identity.
- Remove old PAT and update documentation.

Token Rotation (GitHub App)
---------------------------
- In GitHub App settings, generate a new private key.
- Store private key in Jenkins as file credential `github-app-private-key` (or in Vault) and update `github-app-id` if changed.
- Test: use `python3 app/create_repo.py --whoami --output whoami.json` via Jenkins job or locally with env vars (`GITHUB_APP_PRIVATE_KEY`, `GITHUB_APP_ID`, `GITHUB_INSTALLATION_ID`).
- If installation needs re-authorization, re-install the App on the org and ensure installation ID is correct.

Approval Workflow
-----------------
- The Jenkins `Jenkinsfile` includes an `input` step which prompts for manual approval when the authenticated user differs from the target owner and `REQUIRE_APPROVAL_FOR_ORG` is enabled.
- To require stronger checks, add a manual approval stage requiring an approver group in Jenkins RBAC.

Rollback / Remediation
----------------------
- If a repository must be removed:
  - Use GitHub UI or API: `DELETE /repos/:owner/:repo` (requires appropriate admin token).
  - Verify deletion and update audit log.
- If content needs to be removed from history, follow GitHub guidance (force push or contact support for sensitive leaks).

Monitoring & Alerts
-------------------
- Add logging with structured outputs (stdout JSON) and ingest logs into centralized logging (ELK/CloudWatch).
- Monitor failures, rate limits (HTTP 429), and job error rates.
- Alert on repeated 5xx or high error rate (>5% over 5min).

Testing & CI
------------
- Use the included GitHub Actions workflow to run unit and mocked integration tests.
- For end-to-end, provision a throwaway GitHub org and App for CI with limited scope and cleanup policy.

Operational Checklist (pre-deploy)
----------------------------------
- Ensure Jenkins job is restricted to authorized users.
- Store credentials in Vault or Jenkins Credentials with strict ACLs.
- EnableREQ approval for org creations.
- Verify monitoring and alerts are configured.
- Document token rotation steps and emergency contacts.

Notes
-----
- For production, prefer GitHub App over long-lived PATs. Use short-lived installation tokens and central secrets management.
- Keep `repo_result.json` artifacts private and avoid storing secrets in logs or artifacts.
