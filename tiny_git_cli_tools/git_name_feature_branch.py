#!/usr/bin/env python3
import argparse
import sys

import openai
from git import Repo, Commit
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam
from pydantic import BaseModel

from .config import Config


class ResponseModel(BaseModel):
    branch_name: str


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


def generate_feature_branch_name(
        open_ai_client: openai.OpenAI,
        new_commits: list[Commit],
        previous_commits: list[Commit],
) -> str:
    """
    Generates a feature branch name based on the commit messages using OpenAI's GPT.
    """

    separator = '\n----\n'
    joined_new_commit_messages = separator.join(commit.message.strip() for commit in new_commits)
    joined_old_commit_messages = separator.join(commit.message.strip() for commit in previous_commits)

    system_message: ChatCompletionSystemMessageParam = {
        "role": "system",
        "content": "You are a helpful assistant that generates concise, descriptive branch names based on the recent Git commit history. The branch name should describe the changes that aren't merged-in (yet). Don't try to describe all changes - if the unmerged commits include both important and less relevant changes, focus on the important ones. Use kebab-case format (lowercase words separated by hyphens)."
    }

    user_message_content = f"%%%% New Git commits (not merged-in) %%%%\n" \
                           f"{joined_new_commit_messages}\n" \
                           f"%%%% Previous Git commits (already merged-in) %%%%\n" \
                           f"{joined_old_commit_messages}\n"

    user_message: ChatCompletionUserMessageParam = {
        "role": "user",
        "content": user_message_content,
    }

    completion = open_ai_client.chat.completions.parse(
        model="gpt-4o",
        messages=[
            system_message,
            user_message,
        ],
        response_format=ResponseModel,
    )

    completion_message = completion.choices[0].message

    if completion_message.refusal:
        print(f"Error: {completion.refusal}", file=sys.stderr)
        sys.exit(1)
    else:
        parsed_result = completion_message.parsed

    return parsed_result.branch_name


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Name a feature branch based on its commits using OpenAI/GPT and (optionally) switch to it.")
    parser.add_argument('--repo-path', help='Path to the root of the Git repository', default='.')
    parser.add_argument('--target-branch', help='Target branch to compare against', default='origin/main')
    parser.add_argument('--no-switch', help='Do not switch to the new branch after creating it',
                        action='store_false', dest='switch', default=True)
    args: argparse.Namespace = parser.parse_args()

    config = Config.read()

    openai_api_key = config.openai_api_key

    if openai_api_key is None:
        print("Error: OpenAI API key is not configured", file=sys.stderr)
        sys.exit(1)

    open_ai_client = openai.OpenAI(api_key=openai_api_key)

    repo: Repo = Repo(args.repo_path)

    if repo.bare:
        print("Error: This is a bare repository.")

        sys.exit(1)

    # Get current HEAD commit
    head_commit = repo.head.commit

    # Verify target branch exists
    target_branch = args.target_branch

    try:
        target_commit = repo.commit(target_branch)
    except ValueError:
        print(f'Error: Target branch {target_branch} does not exist.', file=sys.stderr)
        sys.exit(1)

    new_commits = get_new_commits(
        repo=repo,
        head_commit=head_commit,
        target_branch_commit=target_commit,
    )

    previous_commits = get_previous_commits(
        repo=repo,
        target_branch_commit=target_commit,
    )

    feature_branch_name = generate_feature_branch_name(
        open_ai_client=open_ai_client,
        new_commits=new_commits,
        previous_commits=previous_commits,
    )

    print(f'Generated feature branch name: {feature_branch_name}')

    existing_branch_names = {head.name for head in repo.heads}

    if feature_branch_name in existing_branch_names:
        print(f"Error: Branch {feature_branch_name} already exists.", file=sys.stderr)
        sys.exit(1)

    new_branch = repo.create_head(feature_branch_name)

    if args.switch:
        new_branch.checkout()
        print(f'Checked out new branch: {feature_branch_name}')
    else:
        print(f'Created new branch: {feature_branch_name}')


if __name__ == "__main__":
    main()
