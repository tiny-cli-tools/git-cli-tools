# Tiny Git CLI tools

This repository contains a few very simple command-line tools that can be handy when working with Git and GitHub. The tools are implemented in Python and use the [GitPython](https://gitpython.readthedocs.io/en/stable/) library.

## Installation

You can install the tools using [`pipx`](https://pipxproject.github.io/pipx/):

```sh
pipx install git+https://github.com/tiny-cli-tools/git-cli-tools.git
```

## Configuration

Some tools require configuration. Config file path: `~/.config/tiny_git_tools/config.toml`.

Configuration fields:

- `openai_api_key`: (string, optional) OpenAI API key for tools that use OpenAI services.
- `github_token`: (string, optional) GitHub Personal Access Token for tools that interact with GitHub API.

Example config:

```toml
openai_api_key = "sk-svcacct-abcd1234"
```

## Tools

### `git-normalize-newlines`

Traditionally, a proper non-empty text file should end with a newline. If it doesn't, some tools consider it malformed and display a warning.

Some code editing tools (e.g. IntellJ IDEA) doesn't include a trailing newline in the files it generates.

This tool normalizes the trailing newlines in all modified files in the Git repository. If there's no trailing newline, it is added. If there are multiple, the unnecessary ones are truncated.

Example usage:

```sh
git-normalize-newlines
```

### `git-change-author`

This tool rewrites the current branch so every commit uses a new author identity.

Example usage:

```
git-change-author --author-name "Your Name" --author-email you@example.com
```

This tool supports only trivial, linear history and is definitely not suited for large or complex cases.

### `git-add-missing-signatures`

Rewrites all recent unsigned commits, signing them.

Example usage:

```
git-add-missing-signatures
```

This tools supports only trivial, linear history and is definitely not suited for large or complex cases.

### `git-remote-change-protocol`

Changes the protocol of a remote's URL between `https` and `ssh`. Default remote is `origin`.

Example usage:

```
git-remote-change-protocol --protocol=ssh
```

### `git-name-feature-branch`

This tool generates a name for a feature branch based on the recent commits that aren't merged-in to the target branch
yet. The default target branch is `origin/main`. After generating the name, it creates a new feature branch with that
name. By default, it also switches to the new branch.

Example usage:

```
git-name-feature-branch
```

### `github-create-pr`

Create a new automatically named branch and an automatically filled GitHub Pull Request based on the unmerged commits.
Uses OpenAI API (GPT). Auto-merging can be optionally enabled on the created Pull Request. Requires both OpenAI API key
and GitHub token to be configured.

A classic GitHub personal access token needs at least the `repo` scope enabled.

A fine-grained GitHub personal access token needs at least a "Pull Requests: Read and write" permission. A single
fine-grained token can be used only for repositories owned by a single repository owner (your account _or_ a single
organization). If you want to create Pull Requests in repositories in multiple organizations, you have to use a classic
token instead.

Example usage:

```
github-create-pr --enable-auto-merge
```

### `github-init-organization-readme`

Ensures the organization-level `.github` repository exists and seeds a `profile/README.md` stub. The command infers
the organization from the current repository (unless overridden) and uses a configured GitHub token to create the repo
and push the initial content via a temporary local repository.

Example usage:

```
github-init-organization-readme
```
