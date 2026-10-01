# kickstart

Personal project bootstrapper for Python projects managed with `uv` and Cursor.

## Usage

```powershell
kickstart my_project
kickstart my_project "Short project description"
```

The command creates a new project under `C:\Users\nhbes\Repos`, initializes a
bare `uv` project, creates an empty `src/`, creates an empty `.docs/`,
initializes git, creates `.venv` via `uv sync`, copies the default Cursor rules
into `.cursor/rules`, writes a starter README, and opens the folder in Cursor.

## Cursor rules

The default rules live in `src/kickstart/rules/`. Every `.mdc` file there is
copied into `.cursor/rules` of each new project. The copy has no link back to
kickstart: each project owns its rules, commits them with its own code, and can
add, edit, or delete them freely.

To change the defaults for future projects, edit the files in
`src/kickstart/rules/`. Existing projects are not affected.

## Options

```powershell
kickstart my_project --no-open
kickstart my_project "Short project description" --no-open
kickstart my_project "Short project description" --python 3.12
```

Use `KICKSTART_REPOS` or `--repos-dir` to override the default repos folder.
