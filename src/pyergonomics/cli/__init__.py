"""
CLI utilities for pyergonomics import scripts.
"""

from pathlib import Path


def validate_destination(destination: Path) -> str | None:
    """
    Validate the destination folder for a new project.

    Returns:
        Error message if validation fails, None if valid.
    """
    # Check if target is a file
    if destination.exists() and not destination.is_dir():
        return f"Error: '{destination}' exists and is not a directory."

    # Check if target directory exists (and is not the CWD)
    if destination.is_dir() and str(destination) != ".":
        return f"Error: Directory '{destination}' already exists."

    # Check for existing project file
    if (destination / "project.toml").exists():
        return f"Error: A project.toml file already exists in '{destination}'."

    return None


def persist_project(settings, destination: Path) -> None:
    """
    Persist project settings to the destination folder.
    """
    settings.persist(destination)
    print(f"Project created at {destination}")
