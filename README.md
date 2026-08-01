# kickstart

Personal project bootstrapper for Python projects managed with `uv` and Cursor.

## Usage

```powershell
kickstart my_project
kickstart my_project "Short project description"
```

The command creates a new project under `C:\Users\nhbes\Repos`, initializes a
bare `uv` project, creates an empty `src/`, tracks `.docs/` with a placeholder,
initializes git, creates `.venv` via `uv sync`, clones the shared Cursor rules
repo into `.cursor/rules`, writes a starter README, adds `.cursor/` to
`.gitignore`, and opens the folder in Cursor.

## Shared Cursor rules

`.cursor/rules` is a clone of the shared rules repo (default:
`https://github.com/nhbess/cursor-rules`, override with `KICKSTART_RULES_REPO`).
Because `.cursor/` is gitignored in generated projects, the clone has its own
git history: add or edit rules in any project, then commit and push from inside
`.cursor/rules` to make them available to every future project.

The rules repo is the single source of truth: if the clone fails (for example,
offline), kickstart stops with an error instead of creating a project without
rules.

## Options

```powershell
kickstart my_project --no-open
kickstart my_project "Short project description" --no-open
kickstart my_project "Short project description" --python 3.12
```

Use `KICKSTART_REPOS` or `--repos-dir` to override the default repos folder.
