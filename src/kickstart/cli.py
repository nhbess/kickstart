import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from textwrap import dedent


DEFAULT_REPOS_DIR = Path(os.environ.get("KICKSTART_REPOS", r"C:\Users\nhbes\Repos"))
VALID_PROJECT_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
BUNDLED_RULES_PACKAGE = "kickstart.rules"
GITIGNORE_ENTRIES = (".cursor/",)
REQUIRED_COMMANDS = ("git", "uv")
TRACKED_EMPTY_DIRS = (".docs",)


@dataclass(frozen=True)
class Project:
    name: str
    description: str | None
    repos_dir: Path
    directory: Path
    python_version: str | None
    open_cursor: bool


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    project = project_from_args(parser.parse_args(argv))

    try:
        validate_project(project)
        create_project(project)
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


def project_from_args(args: argparse.Namespace) -> Project:
    project_name = args.name.strip()
    repos_dir = args.repos_dir.expanduser().resolve()
    return Project(
        name=project_name,
        description=" ".join(args.description).strip() or None,
        repos_dir=repos_dir,
        directory=repos_dir / project_name,
        python_version=args.python_version,
        open_cursor=not args.no_open,
    )


def validate_project(project: Project) -> None:
    if not VALID_PROJECT_NAME.fullmatch(project.name):
        raise KickstartError(
            "project names must start with a letter or number and contain only "
            "letters, numbers, dots, underscores, or hyphens"
        )

    if not project.repos_dir.exists():
        raise KickstartError(f"repos directory does not exist: {project.repos_dir}")

    if not project.repos_dir.is_dir():
        raise KickstartError(f"repos path is not a directory: {project.repos_dir}")

    if project.directory.exists():
        raise KickstartError(f"project directory already exists: {project.directory}")

    require_commands(REQUIRED_COMMANDS)


def require_commands(commands: tuple[str, ...]) -> None:
    missing_commands = [command for command in commands if shutil.which(command) is None]
    if missing_commands:
        raise KickstartError(f"command not found on PATH: {', '.join(missing_commands)}")


def create_project(project: Project) -> None:
    project.directory.mkdir(parents=False, exist_ok=True)

    run_uv_init(project)
    ensure_empty_directory(project.directory / "src")
    ensure_tracked_empty_dirs(project.directory, TRACKED_EMPTY_DIRS)
    ensure_gitignore_entries(project.directory / ".gitignore", GITIGNORE_ENTRIES)
    run(["git", "init"], cwd=project.directory)
    run(["uv", "sync"], cwd=project.directory)
    write_cursor_rules(project.directory)
    write_readme(project)
    print_next_steps(project)

    if project.open_cursor:
        open_in_cursor(project.directory)


def run_uv_init(project: Project) -> None:
    command = [
        "uv",
        "init",
        ".",
        "--bare",
        "--vcs",
        "none",
        "--name",
        project.name,
    ]

    if project.description is None:
        command.append("--no-description")
    else:
        command.extend(["--description", project.description])

    if project.python_version:
        command.extend(["--python", project.python_version])

    run(command, cwd=project.directory)


def ensure_empty_directory(directory: Path) -> None:
    if directory.exists() and not directory.is_dir():
        raise KickstartError(f"expected a directory but found a file: {directory}")

    directory.mkdir(exist_ok=True)
    for child in directory.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def ensure_tracked_empty_dirs(project_dir: Path, directories: tuple[str, ...]) -> None:
    for directory_name in directories:
        directory = project_dir / directory_name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").touch()


def write_cursor_rules(project_dir: Path) -> None:
    rules_dir = project_dir / ".cursor" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    copy_bundled_rules(rules_dir)


def copy_bundled_rules(rules_dir: Path) -> None:
    for rule_file in resources.files(BUNDLED_RULES_PACKAGE).iterdir():
        if rule_file.is_file() and rule_file.name.endswith(".mdc"):
            destination = rules_dir / rule_file.name
            destination.write_text(rule_file.read_text(encoding="utf-8"), encoding="utf-8")


def ensure_gitignore_entries(gitignore: Path, entries: tuple[str, ...]) -> None:
    lines = gitignore.read_text(encoding="utf-8").splitlines() if gitignore.exists() else []
    existing_entries = {gitignore_entry_key(line) for line in lines}
    missing_entries = [entry for entry in entries if gitignore_entry_key(entry) not in existing_entries]

    if not missing_entries:
        return

    if lines and lines[-1] != "":
        lines.append("")
    lines.extend(missing_entries)
    gitignore.write_text("\n".join(lines) + "\n", encoding="utf-8")


def gitignore_entry_key(entry: str) -> str:
    return entry.strip().rstrip("/")


def write_readme(project: Project) -> None:
    description_section = f"\n\n{project.description}" if project.description else ""
    readme = dedent(
        f"""\
        # {project.name}{description_section}

        ## Setup

        ```powershell
        uv sync
        ```

        ## Structure

        Add code under `src/` and project notes under `.docs/`.
        """
    )

    (project.directory / "README.md").write_text(readme, encoding="utf-8")


def print_next_steps(project: Project) -> None:
    print()
    print(f"Created {project.name} at {project.directory}")
    print("Next steps:")
    print(f"  cd {project.directory}")
    print("  git status")
    print("  uv run python --version")


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
    formatted_command = subprocess.list2cmdline(command)
    print(f"> {formatted_command}", flush=True)
    try:
        subprocess.run(command, cwd=cwd, check=True)
    except FileNotFoundError as error:
        raise KickstartError(f"command not found: {command[0]}") from error
    except subprocess.CalledProcessError as error:
        raise KickstartError(
            f"command failed with exit code {error.returncode}: {formatted_command}"
        ) from error


class KickstartError(Exception):
    """Raised for user-facing setup errors."""
