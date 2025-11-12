"""
Configuration module for the notes application.
"""
import os
from pathlib import Path

# Default notes directory
DEFAULT_NOTES_DIR = os.path.expanduser("~/.local/share/notes")

def get_notes_directory():
    """
    Get the notes storage directory.
    Can be overridden by the NOTES_DIR environment variable.
    """
    notes_dir = os.environ.get('NOTES_DIR', DEFAULT_NOTES_DIR)
    path = Path(notes_dir)

    # Create directory if it doesn't exist
    path.mkdir(parents=True, exist_ok=True)

    return path

def get_notes_db_file():
    """Get the path to the notes database (JSON) file."""
    return get_notes_directory() / "notes_db.json"
