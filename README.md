# kickstart

Personal project bootstrapper for Python projects managed with `uv` and Cursor.

## Usage

```powershell
kickstart my_project
kickstart my_project "Short project description"
```

The command creates a new project under `C:\Users\nhbes\Repos`, initializes it
with `uv`, creates `.venv` via `uv sync`, copies the bundled Cursor rules,
writes a starter README, adds `.cursor/` to `.gitignore`, and opens the folder
in Cursor.

## Options

```powershell
kickstart my_project --no-open
kickstart my_project "Short project description" --no-open
kickstart my_project "Short project description" --python 3.12
kickstart my_project "Short project description" --kind package
```

Use `KICKSTART_REPOS` or `--repos-dir` to override the default repos folder.
