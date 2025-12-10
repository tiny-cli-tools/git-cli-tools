#!/usr/bin/env python3
import os
from git import Actor, Commit, Head, Repo


def commit_tree(
    repo: Repo,
    existing_commit: Commit,
    parent_commit: Commit | None,
    author_name: str,
    author_email: str,
    committer_name: str,
    committer_email: str,
    should_sign: bool,
) -> str:
    new_message = existing_commit.message
    new_author_date = existing_commit.authored_datetime.isoformat()
    new_committer_date = existing_commit.committed_datetime.isoformat()

    env = os.environ.copy()
    env.update(
        {
            'GIT_AUTHOR_NAME': author_name,
            'GIT_AUTHOR_EMAIL': author_email,
            'GIT_AUTHOR_DATE': new_author_date,
            'GIT_COMMITTER_NAME': committer_name,
            'GIT_COMMITTER_EMAIL': committer_email,
            'GIT_COMMITTER_DATE': new_committer_date,
        }
    )

    kwargs = {'m': new_message, 'env': env}

    if parent_commit is not None:
        kwargs['p'] = parent_commit.hexsha

    if should_sign:
        kwargs['S'] = True

    return repo.git.commit_tree(
        existing_commit.tree.hexsha,
        **kwargs,
    )


def rewrite_commit(
    repo: Repo,
    original_commit: Commit,
    new_author: Actor | None,
    should_sign: bool,
    should_rewrite: callable,
) -> Commit:
    def rewrite_parent_commit() -> Commit | None:
        parent_commits = original_commit.parents

        if len(parent_commits) > 1:
            raise ValueError('Commits with multiple parents are not supported')

        if len(parent_commits) == 0:  # A root commit
            return None

        parent_commit = parent_commits[0]

        return rewrite_commit(
            repo=repo,
            original_commit=parent_commit,
            new_author=new_author,
            should_sign=should_sign,
            should_rewrite=should_rewrite,
        )

    # If predicate returns False, return the original commit without rewriting
    if not should_rewrite(original_commit):
        return original_commit

    rewritten_parent_commit = rewrite_parent_commit()

    # Use new author if provided, otherwise keep original author
    author_name = new_author.name if new_author is not None else original_commit.author.name
    author_email = new_author.email if new_author is not None else original_commit.author.email
    committer_name = new_author.name if new_author is not None else original_commit.committer.name
    committer_email = new_author.email if new_author is not None else original_commit.committer.email

    rewritten_commit_sha = commit_tree(
        repo=original_commit.repo,
        existing_commit=original_commit,
        parent_commit=rewritten_parent_commit,
        author_name=author_name,
        author_email=author_email,
        committer_name=committer_name,
        committer_email=committer_email,
        should_sign=should_sign,
    )

    print(f'Rewrote commit {original_commit.hexsha} -> {rewritten_commit_sha}')

    rewritten_commit = repo.commit(rewritten_commit_sha)

    return rewritten_commit


def rewrite_branch(
    repo: Repo,
    branch: Head,
    new_author: Actor | None,
    should_sign: bool,
    should_rewrite: callable,
) -> None:
    original_commit = branch.commit

    rewritten_commit = rewrite_commit(
        repo=repo,
        original_commit=original_commit,
        new_author=new_author,
        should_sign=should_sign,
        should_rewrite=should_rewrite,
    )

    if rewritten_commit.hexsha != original_commit.hexsha:
        branch.commit = rewritten_commit
