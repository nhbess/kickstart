# kickstart

Personal project bootstrapper for Python projects managed with `uv` and Cursor.

## Usage

```powershell
kickstart my_project
kickstart my_project "Short project description"
```

The command creates a new project under `~\Repos`, initializes a
bare `uv` project, creates an empty `src/`, creates an empty `.docs/`,
initializes git, creates `.venv` via `uv sync`, copies the default Cursor rules
into `.cursor/rules`, and opens the folder in Cursor. No README is created.

The generated `.gitignore` ignores `.cursor/`, `.docs/`, `.venv/`, `.vscode/`,
and `__pycache__/`.

## Cursor rules

The default rules live in `src/kickstart/rules/`. Every `.mdc` file there is
copied into `.cursor/rules` of each new project. The copy has no link back to
kickstart: each project owns its rules and can add, edit, or delete them freely.
They are gitignored along with the rest of `.cursor/`.

To change the defaults for future projects, edit the files in
`src/kickstart/rules/`. Existing projects are not affected.

## Keeping Cursor light

Everything in `src/kickstart/templates/` is copied into the project root:

- `.cursorignore`: binary data (`.npz`, `.npy`, `.sqlite`, checkpoints, archives,
  media) is hidden from Cursor's AI and index.
- `.cursorindexingignore`: text data, images, PDFs, and output folders (`data/`,
  `output/`, `results/`, ...) are not indexed, but can still be opened with `@`.
- `.vscode/settings.json`: the file watcher and search skip `.venv` and the same
  data folders and file types.

Add project-specific data folders to these files as the project grows.

## Options

```powershell
kickstart my_project --no-open
kickstart my_project "Short project description" --no-open
kickstart my_project "Short project description" --python 3.12
```

Use `KICKSTART_REPOS` or `--repos-dir` to override the default repos folder.
