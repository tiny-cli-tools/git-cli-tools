# Tiny Git CLI tools

This repository contains a few very simple command-line tools that can be handy when working with Git. The tools are implemented in Python and use the [GitPython](https://gitpython.readthedocs.io/en/stable/) library.

## Installation

You can install the tools using [`pipx`](https://pipxproject.github.io/pipx/):

```sh
pipx install git+https://github.com/tiny-cli-tools/git-cli-tools.git
```

## Configuration

Some tools require configuration. Config file path: `~/.config/tiny_git_tools/config.toml`.

Configuration fields:

- `openai_api_key`: (string, optional) OpenAI API key for tools that use OpenAI services.

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

Example:

```
git-add-missing-signatures
```

This tools supports only trivial, linear history and is definitely not suited for large or complex cases.

### `git-remote-change-protocol`

Changes the protocol of a remote's URL between `https` and `ssh`. Default remote is `origin`.

Example:

```
git-remote-change-protocol --protocol=ssh
```

### `git-name-feature-branch`

This tool generates a name for a feature branch based on the recent commits that aren't merged-in to the target branch
yet. The default target branch is `origin/main`. After generating the name, it creates a new feature branch with that
name. By default, it also switches to the new branch.

Example:

```
git-name-feature-branch
```
