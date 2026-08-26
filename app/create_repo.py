#!/usr/bin/env python3
import argparse
import os
import sys
import json
import logging
from app.github_client import GitHubClient

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

EXIT_OK = 0
EXIT_VALIDATION = 1
EXIT_AUTH = 2
EXIT_API = 3
EXIT_ERROR = 4


def parse_args():
    p = argparse.ArgumentParser(description='Create GitHub repository (used by Jenkins)')
    p.add_argument('--repo-name', required=True)
    p.add_argument('--visibility', choices=['private', 'public'], default='private')
    p.add_argument('--description', default='')
    p.add_argument('--init-readme', action='store_true')
    p.add_argument('--gitignore', default='')
    p.add_argument('--license', default='')
    p.add_argument('--default-branch', default='main')
    p.add_argument('--dry-run', action='store_true')
    p.add_argument('--output', default='-')
    p.add_argument('--whoami', action='store_true', help='Print authenticated user and exit')
    return p.parse_args()


def main():
    args = parse_args()
    # create client from environment (supports PAT or GitHub App env variables)
    try:
        client = GitHubClient.from_env()
    except Exception as e:
        logging.error('Authentication setup error: %s', e)
        sys.exit(EXIT_AUTH)

    if args.whoami:
        try:
            who = client.get_authenticated_user()
            out = {'user': who}
            if args.output == '-':
                print(json.dumps(out))
            else:
                with open(args.output, 'w') as f:
                    json.dump(out, f)
            sys.exit(EXIT_OK)
        except Exception as e:
            logging.error('Failed to get authenticated user: %s', e)
            sys.exit(EXIT_AUTH)

    payload = dict(
        name=args.repo_name,
        description=args.description,
        private=(args.visibility == 'private'),
        has_issues=True,
        has_projects=False,
        has_wiki=False,
        auto_init=args.init_readme,
        gitignore_template=args.gitignore or None,
        license_template=args.license or None,
        default_branch=args.default_branch or None,
    )

    if args.dry_run:
        result = {
            'success': True,
            'repo': dict(
                name=args.repo_name,
                full_name=f"{args.owner}/{args.repo_name}",
                html_url=f"https://github.com/{args.owner}/{args.repo_name}",
                private=(args.visibility == 'private'),
                default_branch=args.default_branch,
            ),
            'warnings': ['dry-run: no repository created'],
            'errors': []
        }
        out = json.dumps(result)
        if args.output == '-' :
            print(out)
        else:
            with open(args.output, 'w') as f:
                f.write(out)
        logging.info('Dry-run complete')
        sys.exit(EXIT_OK)

    try:
        # Determine authenticated user as owner (do not accept owner from Jenkins)
        auth_user = client.get_authenticated_user()
        owner = auth_user.get('login')
        # Idempotency check: if repo exists, return it
        created = client.create_repository(owner=owner, payload=payload)
    except client.AuthError as e:
        logging.error('Authentication/permission error: %s', e)
        sys.exit(EXIT_AUTH)
    except client.ApiError as e:
        logging.error('GitHub API error: %s', e)
        result = {'success': False, 'errors': [str(e)]}
        if args.output == '-':
            print(json.dumps(result))
        else:
            with open(args.output, 'w') as f:
                json.dump(result, f)
        sys.exit(EXIT_API)
    except Exception as e:
        logging.exception('Unexpected error')
        sys.exit(EXIT_ERROR)

    result = {
        'success': True,
        'repo': {
            'id': created.get('id'),
            'name': created.get('name'),
            'full_name': created.get('full_name'),
            'html_url': created.get('html_url'),
            'clone_url': created.get('clone_url'),
            'private': created.get('private'),
            'visibility': created.get('visibility', 'private' if created.get('private') else 'public'),
            'owner': created.get('owner'),
            'created_at': created.get('created_at'),
            'default_branch': created.get('default_branch')
        },
        'warnings': [],
        'errors': [],
        'raw_response': created
    }

    if args.output == '-':
        print(json.dumps(result))
    else:
        with open(args.output, 'w') as f:
            json.dump(result, f)
    logging.info('Repository created: %s', created.get('html_url'))
    sys.exit(EXIT_OK)


if __name__ == '__main__':
    main()
