from __future__ import annotations

from pathlib import Path
import tomllib


def get_version_from_pyproject(pyproject: Path) -> str:
    """Read `pyproject.toml` and return the project version.

    Tries PEP 621 `[project].version` first, then falls back to
    Poetry-style `[tool.poetry].version`.
    """
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))

    project = data.get("project")
    if isinstance(project, dict):
        version = project.get("version")
        if isinstance(version, str):
            return version

    # Fallback: Poetry-style pyproject
    tool = data.get("tool")
    if isinstance(tool, dict):
        poetry = tool.get("poetry")
        if isinstance(poetry, dict):
            version = poetry.get("version")
            if isinstance(version, str):
                return version

    raise RuntimeError(
        "Could not find 'version' in pyproject.toml (checked [project] and [tool.poetry])"
    )


def main() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    print(get_version_from_pyproject(pyproject))


if __name__ == "__main__":
    main()
