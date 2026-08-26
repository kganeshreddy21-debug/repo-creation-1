pipeline {
  agent {
    docker {
      image 'python:3.11-slim'
    }
  }
  options {
    disableConcurrentBuilds()
  }
  parameters {
    string(name: 'REPO_NAME', description: 'Repository name')
    choice(name: 'VISIBILITY', choices: ['private','public'], description: 'Visibility')
    string(name: 'DESCRIPTION', description: 'Repository description', defaultValue: '')
    booleanParam(name: 'INITIALIZE_README', defaultValue: true, description: 'Initialize with README')
    choice(name: 'SECRET_STORE', choices: ['JENKINS','VAULT'], description: 'Where to read GitHub credentials from')
  }
  stages {
    stage('Create Repository') {
      steps {
        script {
          // (removed GITHUB_API_URL parameter — not required)

          // Retrieve token securely and run the create script inside a virtualenv
          if (params.SECRET_STORE == 'VAULT') {
            withCredentials([
              string(credentialsId: 'vault-role-id', variable: 'ROLE_ID'),
              string(credentialsId: 'vault-secret-id', variable: 'SECRET_ID'),
              string(credentialsId: 'vault-addr', variable: 'VAULT_ADDR')
            ]) {
              sh """
              set -euo pipefail
              chmod +x scripts/fetch_vault_secret.sh
              export GITHUB_TOKEN=\$(scripts/fetch_vault_secret.sh secret/data/github token)
              python -m venv venv
              . venv/bin/activate
              python -m pip install --upgrade pip
              python -m pip install -r requirements.txt
              python -m app.create_repo --repo-name "${params.REPO_NAME}" --visibility "${params.VISIBILITY}" --description "${params.DESCRIPTION}" ${params.INITIALIZE_README ? '--init-readme' : ''} --output repo_result.json
              """
            }
          } else {
            // Use the existing Jenkins credential `repo-creation` which may be 'Username with password'.
            // Bind the password field to GITHUB_TOKEN and username to GITHUB_USERNAME (if present).
            withCredentials([usernamePassword(credentialsId: 'repo-creation', usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GITHUB_TOKEN')]) {
              sh """
              set -euo pipefail
              python -m venv venv
              . venv/bin/activate
              python -m pip install --upgrade pip
              python -m pip install -r requirements.txt
              python -m app.create_repo --repo-name "${params.REPO_NAME}" --visibility "${params.VISIBILITY}" --description "${params.DESCRIPTION}" ${params.INITIALIZE_README ? '--init-readme' : ''} --output repo_result.json
              """
            }
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
