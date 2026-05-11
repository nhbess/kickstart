import argparse
import os
import re
import shutil
import subprocess
import sys
from importlib import resources
from pathlib import Path
from textwrap import dedent


DEFAULT_REPOS_DIR = Path(os.environ.get("KICKSTART_REPOS", r"C:\Users\nhbes\Repos"))
VALID_PROJECT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
BUNDLED_RULES_PACKAGE = "kickstart.rules"


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project_name = args.name.strip()
    description = " ".join(args.description).strip() or None
    repos_dir = args.repos_dir.expanduser().resolve()
    project_dir = repos_dir / project_name

    try:
        validate_inputs(project_name, repos_dir, project_dir)
        create_project(
            project_name=project_name,
            description=description,
            project_dir=project_dir,
            kind=args.kind,
            python_version=args.python_version,
            open_cursor=not args.no_open,
        )
    except KickstartError as error:
        print(f"kickstart: {error}", file=sys.stderr)
        return 1

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kickstart",
        description="Create a uv-managed Python project with default Cursor rules.",
        epilog=dedent(
            """\
            examples:
              kickstart my_project
              kickstart my_project "Short project description"

            The project name is a folder/package-style name: use no quotes,
            no spaces, and only letters, numbers, dots, underscores, or hyphens.
            Put the optional description in quotes if you want to keep it together.
            """
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "name",
        help="Project folder name, for example: my_project. No spaces or quotes.",
    )
    parser.add_argument(
        "description",
        nargs="*",
        help="Optional short project description. Quotes are optional.",
    )
    parser.add_argument(
        "--repos-dir",
        type=Path,
        default=DEFAULT_REPOS_DIR,
        help=f"Folder where projects are created. Default: {DEFAULT_REPOS_DIR}",
    )
    parser.add_argument(
        "--kind",
        choices=("package", "app", "lib"),
        default="package",
        help="uv project kind to initialize. Default: package",
    )
    parser.add_argument(
        "--python",
        dest="python_version",
        help="Python version to request from uv, for example: 3.12",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Create the project without opening Cursor.",
    )
    return parser


def validate_inputs(
    project_name: str,
    repos_dir: Path,
    project_dir: Path,
) -> None:
    if not VALID_PROJECT_NAME.match(project_name):
        raise KickstartError(
            "project names must start with a letter or number and contain only "
            "letters, numbers, dots, underscores, or hyphens"
        )

    if not repos_dir.exists():
        raise KickstartError(f"repos directory does not exist: {repos_dir}")

    if not repos_dir.is_dir():
        raise KickstartError(f"repos path is not a directory: {repos_dir}")

    if project_dir.exists():
        raise KickstartError(f"project directory already exists: {project_dir}")

    if shutil.which("uv") is None:
        raise KickstartError("uv is not available on PATH")

    if shutil.which("git") is None:
        raise KickstartError("git is not available on PATH")


def create_project(
    *,
    project_name: str,
    description: str | None,
    project_dir: Path,
    kind: str,
    python_version: str | None,
    open_cursor: bool,
) -> None:
    project_dir.mkdir(parents=False, exist_ok=True)

    run_uv_init(project_name, description, project_dir, kind, python_version)
    update_gitignore(project_dir)
    run_git_init(project_dir)
    run(["uv", "sync"], cwd=project_dir)
    write_cursor_rules(project_dir)
    write_readme(project_name, description, project_dir)

    print()
    print(f"Created {project_name} at {project_dir}")
    print("Next steps:")
    print(f"  cd {project_dir}")
    print("  uv run python --version")

    if open_cursor:
        open_in_cursor(project_dir)


def run_uv_init(
    project_name: str,
    description: str | None,
    project_dir: Path,
    kind: str,
    python_version: str | None,
) -> None:
    command = [
        "uv",
        "init",
        ".",
        f"--{kind}",
        "--name",
        project_name,
    ]

    if description is None:
        command.append("--no-description")
    else:
        command.extend(["--description", description])

    if python_version:
        command.extend(["--python", python_version])

    run(command, cwd=project_dir)


def run_git_init(project_dir: Path) -> None:
    run(["git", "init"], cwd=project_dir)


def write_cursor_rules(project_dir: Path) -> None:
    rules_dir = project_dir / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    copy_bundled_rules(rules_dir)


def copy_bundled_rules(rules_dir: Path) -> None:
    for rule_file in resources.files(BUNDLED_RULES_PACKAGE).iterdir():
        if rule_file.is_file() and rule_file.name.endswith(".mdc"):
            destination = rules_dir / rule_file.name
            destination.write_text(rule_file.read_text(encoding="utf-8"), encoding="utf-8")


def update_gitignore(project_dir: Path) -> None:
    gitignore = project_dir / ".gitignore"
    lines = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    normalized_lines = {line.strip() for line in lines}

    if ".cursor/" in normalized_lines or ".cursor" in normalized_lines:
        return

    if lines and lines[-1] != "":
        lines.append("")
    lines.append(".cursor/")
    gitignore.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_readme(project_name: str, description: str | None, project_dir: Path) -> None:
    description_section = f"\n\n{description}" if description else ""
    readme = dedent(
        f"""\
        # {project_name}{description_section}

        ## Setup

        ```powershell
        uv sync
        ```

        ## Run

        ```powershell
        uv run python -m {python_module_name(project_name)}
        ```
        """
    )

    (project_dir / "README.md").write_text(readme, encoding="utf-8")


def python_module_name(project_name: str) -> str:
    module_name = project_name.replace("-", "_").replace(".", "_")
    if module_name.isidentifier():
        return module_name
    return "main"


def open_in_cursor(project_dir: Path) -> None:
    cursor_command = shutil.which("cursor")
    if cursor_command is None:
        print("Cursor command was not found on PATH, so the project was not opened.")
        return

    try:
        subprocess.Popen(
            [cursor_command, "."],
            cwd=project_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print("Opened project in Cursor.")
    except OSError as error:
        print(f"Could not open Cursor automatically: {error}")


def run(command: list[str], *, cwd: Path) -> None:
    print(f"> {' '.join(command)}", flush=True)
    try:
        subprocess.run(command, cwd=cwd, check=True)
    except FileNotFoundError as error:
        raise KickstartError(f"command not found: {command[0]}") from error
    except subprocess.CalledProcessError as error:
        raise KickstartError(f"command failed with exit code {error.returncode}: {' '.join(command)}") from error


class KickstartError(Exception):
    """Raised for user-facing setup errors."""
