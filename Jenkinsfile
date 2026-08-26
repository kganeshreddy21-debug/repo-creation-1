pipeline {
  agent any
  parameters {
    string(name: 'REPO_NAME', description: 'Repository name')
    choice(name: 'VISIBILITY', choices: ['private','public'], description: 'Visibility')
    string(name: 'DESCRIPTION', description: 'Repository description', defaultValue: '')
    booleanParam(name: 'INITIALIZE_README', defaultValue: true, description: 'Initialize with README')
    string(name: 'GITHUB_API_URL', defaultValue: '', description: 'GitHub Enterprise API URL (e.g. https://github.example.com/api/v3)')
    choice(name: 'SECRET_STORE', choices: ['JENKINS','VAULT'], description: 'Where to read GitHub credentials from')
  }
  stages {
    stage('Create Repository') {
      steps {
        script {
          // Export GITHUB_API_URL to environment if provided
          if (params.GITHUB_API_URL?.trim()) {
            env.GITHUB_API_URL = params.GITHUB_API_URL
          }

          // Retrieve token securely: prefer Jenkins credential `github-enterprise-token` unless Vault is selected
          if (params.SECRET_STORE == 'VAULT') {
            withCredentials([
              string(credentialsId: 'vault-role-id', variable: 'ROLE_ID'),
              string(credentialsId: 'vault-secret-id', variable: 'SECRET_ID'),
              string(credentialsId: 'vault-addr', variable: 'VAULT_ADDR')
            ]) {
              sh 'chmod +x scripts/fetch_vault_secret.sh'
              sh 'export GITHUB_TOKEN=$(scripts/fetch_vault_secret.sh secret/data/github token)'
            }
          } else {
            // Use the existing Jenkins credential `repo-creation` which may be 'Username with password'.
            // Bind the password field to GITHUB_TOKEN and username to GITHUB_USERNAME (if present).
            withCredentials([usernamePassword(credentialsId: 'repo-creation', usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GITHUB_TOKEN')]) {
              // GITHUB_TOKEN and GITHUB_USERNAME are available to the process. Do NOT echo or log them.
            }
          }

          // Run creation inside a lock to prevent concurrent creates of same repo name
          lock(resource: "repo-${REPO_NAME}") {
            sh "python3 app/create_repo.py --repo-name \"${REPO_NAME}\" --visibility \"${VISIBILITY}\" --description \"${DESCRIPTION}\" ${INITIALIZE_README ? '--init-readme' : ''} --output repo_result.json"
          }

          def result = readJSON file: 'repo_result.json'
          if (result.success) {
            currentBuild.description = "Repo: ${result.repo.html_url}"
            echo "GitHub Repository Created Successfully"
            echo "Owner: ${result.repo.owner.login}"
            echo "Repository: ${result.repo.name}"
            echo "Visibility: ${result.repo.visibility ?: (result.repo.private ? 'private' : 'public')}"
            echo "Repository URL:\n${result.repo.html_url}"
          } else {
            error "Repository creation failed: ${result.errors.join(', ')}"
          }
        }
      }
    }
  }
}
