#!/usr/bin/env python3
import argparse
import sys

import openai
from git import Repo, Commit
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from pydantic import BaseModel, Field

from tiny_git_cli_tools.git_repo_utils import open_repository_conventionally
from tiny_git_cli_tools.github_utils import create_github_client_conventionally
from tiny_git_cli_tools.remote_locator import RemoteLocator
from .config import Config


class PullRequestDetails(BaseModel):
    pull_request_title: str = Field(..., title="Pull Request Title",
                                    description="Human-readable title for the Pull Request (Markdown is supported)")
    feature_branch_name: str = Field(..., title="Feature Branch Name",
                                     description="Kebab-case name for the feature branch associated with the Pull Request")


def get_new_commits(
        repo: Repo,
        head_commit: Commit,
        target_branch_commit: Commit,
) -> list[Commit]:
    """
    Returns a list of commits that are not included in the target branch.
    """
    return list(repo.iter_commits(f'{target_branch_commit.hexsha}..{head_commit.hexsha}'))


def get_previous_commits(
        repo: Repo,
        target_branch_commit: Commit,
        limit: int = 8,
) -> list[Commit]:
    """
    Returns a list of commits that are included in the target branch.
    """
    return list(repo.iter_commits(f'{target_branch_commit.hexsha}', max_count=limit))


def generate_pull_request_details(
        open_ai_client: openai.OpenAI,
        new_commits: list[Commit],
        previous_commits: list[Commit],
) -> PullRequestDetails:
    """
    Generates a Pull Request details based on the commit messages using OpenAI's GPT.
    """

    separator = '\n----\n'
    joined_new_commit_messages = separator.join(commit.message.strip() for commit in new_commits)
    joined_previous_commit_messages = separator.join(commit.message.strip() for commit in previous_commits)

    system_message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": "You are a helpful assistant that generates pull request titles and feature branch names based on Git commit history. Analyze the unmerged commits and determine which ones are important. Generate a PR title that covers all important commits together - ignore unimportant commits (like formatting, typos, minor fixes) entirely. If there's only one obviously important commit, you can use its message as the PR title as-is. The branch name should be a kebab-case version summarizing the same changes (lowercase words separated by hyphens)."
    }

    user_message_content = f"%%%% New Git commits (not merged-in) %%%%\n" \
                           f"{joined_new_commit_messages}\n" \
                           f"%%%% Previous Git commits (already merged-in) %%%%\n" \
                           f"{joined_previous_commit_messages}\n"

    user_message: ChatCompletionUserMessageParam = {
        "role": "user",
        "content": user_message_content,
    }

    completion = open_ai_client.chat.completions.parse(
        model="gpt-5-mini",
        messages=[
            system_message,
            user_message,
        ],
        response_format=PullRequestDetails,
    )

    completion_message = completion.choices[0].message

    if completion_message.refusal:
        print(f"Error: {completion.refusal}", file=sys.stderr)
        sys.exit(1)
    else:
        pull_request_details = completion_message.parsed

    return pull_request_details


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a new automatically named branch and an automatically filled GitHub Pull Request based on the unmerged commits. Uses OpenAI API (GPT).")
    parser.add_argument('--repo-path', help='Path to the root of the Git repository', default='.')
    parser.add_argument('--remote', help='Remote name to use', default='origin')
    parser.add_argument('--target-branch', help='Target branch to compare against', default='main')
    parser.add_argument('--no-switch', help='Do not switch to the new feature branch after creating it',
                        action='store_false', dest='switch', default=True)
    parser.add_argument('--enable-auto-merge', help='Enable auto-merge for the created pull request',
                        action='store_true', dest='enable_auto_merge', default=False)
    args: argparse.Namespace = parser.parse_args()

    config = Config.read()

    openai_api_key = config.openai_api_key

    if openai_api_key is None:
        print("Error: OpenAI API key is not configured", file=sys.stderr)
        sys.exit(1)

    open_ai_client = openai.OpenAI(api_key=openai_api_key)

    github_client = create_github_client_conventionally(config)

    git_repo: Repo = open_repository_conventionally(args.repo_path)

    try:
        remote = git_repo.remotes[args.remote]
    except IndexError:
        print(f'Error: Remote {args.remote} does not exist.', file=sys.stderr)
        sys.exit(1)

    remote_url = next(iter(remote.urls))
    remote_locator = RemoteLocator.parse_url(remote_url)

    if remote_locator.host != 'github.com':
        print(f'Error: Remote host {remote_locator.host} is not supported. Only github.com is supported.',
              file=sys.stderr)
        sys.exit(1)

    github_repo_path = remote_locator.path

    # Get current HEAD commit
    head_commit = git_repo.head.commit

    # Verify target branch exists (check remote branch first, then local)
    target_branch_name = args.target_branch
    remote_target_branch_path = f'{args.remote}/{target_branch_name}'

    try:
        target_branch_commit = git_repo.commit(remote_target_branch_path)
    except (ValueError, Exception):
        print(f'Error: Target branch {remote_target_branch_path} does not exist.', file=sys.stderr)
        sys.exit(1)

    new_commits = get_new_commits(
        repo=git_repo,
        head_commit=head_commit,
        target_branch_commit=target_branch_commit,
    )

    previous_commits = get_previous_commits(
        repo=git_repo,
        target_branch_commit=target_branch_commit,
    )

    pull_request_details = generate_pull_request_details(
        open_ai_client=open_ai_client,
        new_commits=new_commits,
        previous_commits=previous_commits,
    )

    feature_branch_name = pull_request_details.feature_branch_name
    pull_request_title = pull_request_details.pull_request_title

    # Create a local branch
    print(f'Creating branch: {feature_branch_name}')

    try:
        feature_branch = git_repo.create_head(feature_branch_name, head_commit.hexsha)

        if args.switch:
            feature_branch.checkout()
            print(f'Checked out new branch: {feature_branch_name}')
    except Exception as e:
        print(f'Error: Failed to create branch {feature_branch_name}: {e}', file=sys.stderr)
        sys.exit(1)

    # Push the branch upstream with tracking
    print(f'Pushing branch {feature_branch_name} to {args.remote}...')

    try:
        remote.push(refspec=f'{feature_branch_name}:{feature_branch_name}', set_upstream=True)
    except Exception as e:
        print(f'Error: Failed to push branch {feature_branch_name}: {e}', file=sys.stderr)
        sys.exit(1)

    print(f'Generated PR title: {pull_request_title}')

    # Create a pull request
    print(f'Creating pull request...')

    try:
        github_repo = github_client.get_repo(github_repo_path)

        pull_request = github_repo.create_pull(
            title=pull_request_title,
            body=f"Auto-generated pull request for changes in the `{feature_branch_name}` branch.",
            head=feature_branch_name,
            base=target_branch_name,
        )

        print(f'Successfully created pull request: {pull_request.html_url}')

        # Enable auto-merge
        if args.enable_auto_merge:
            print('Enabling auto-merge for the pull request...')

            pull_request.enable_automerge()

            print('Auto-merge enabled.')
    except Exception as e:
        print(f'Error: Failed to create pull request: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
