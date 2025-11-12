"""
Storage module for managing notes on the filesystem.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from .config import get_notes_directory, get_notes_db_file


class NotesStorage:
    """Handles storage and retrieval of notes."""

    def __init__(self):
        self.notes_dir = get_notes_directory()
        self.db_file = get_notes_db_file()
        self._ensure_storage()

    def _ensure_storage(self):
        """Ensure the storage directory and database file exist."""
        self.notes_dir.mkdir(parents=True, exist_ok=True)
        if not self.db_file.exists():
            self._save_db({})

    def _load_db(self) -> Dict:
        """Load the notes database."""
        try:
            with open(self.db_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_db(self, db: Dict):
        """Save the notes database."""
        with open(self.db_file, 'w') as f:
            json.dump(db, f, indent=2)

    def get_note_file_path(self, note_id: str, encrypted: bool = False) -> Path:
        """Get the file path for a note."""
        extension = '.gpg' if encrypted else '.txt'
        return self.notes_dir / f"{note_id}{extension}"

    def save_note(self, note_id: str, title: str, content: str,
                  category: Optional[str] = None,
                  encrypted: bool = False) -> Dict:
        """
        Save a note to storage.

        Args:
            note_id: Unique identifier for the note
            title: Note title
            content: Note content
            category: Optional category (slash-separated path, e.g., "work/clients/acme")
            encrypted: Whether the note is encrypted

        Returns:
            Note metadata dictionary
        """
        # Save note content to file
        note_file = self.get_note_file_path(note_id, encrypted)
        with open(note_file, 'w') as f:
            f.write(content)

        # Update database
        db = self._load_db()
        timestamp = datetime.now().isoformat()

        note_metadata = {
            'id': note_id,
            'title': title,
            'category': category,
            'encrypted': encrypted,
            'created_at': db.get(note_id, {}).get('created_at', timestamp),
            'updated_at': timestamp,
            'file': str(note_file)
        }

        db[note_id] = note_metadata
        self._save_db(db)

        return note_metadata

    def resolve_note_id(self, partial_id: str) -> Optional[str]:
        """
        Resolve a partial note ID to a full ID.

        Args:
            partial_id: Full or partial note ID

        Returns:
            Full note ID if found, None otherwise
        """
        db = self._load_db()

        # First try exact match
        if partial_id in db:
            return partial_id

        # Try partial match (must be unique)
        matches = [note_id for note_id in db.keys() if note_id.startswith(partial_id)]

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # Multiple matches - ambiguous
            return None
        else:
            # No matches
            return None

    def get_note(self, note_id: str) -> Optional[Dict]:
        """Get note metadata by ID (supports partial IDs)."""
        db = self._load_db()

        # Try to resolve the ID
        full_id = self.resolve_note_id(note_id)
        if not full_id:
            return None

        return db.get(full_id)

    def read_note_content(self, note_id: str) -> Optional[str]:
        """Read the content of a note."""
        note = self.get_note(note_id)
        if not note:
            return None

        note_file = Path(note['file'])
        if not note_file.exists():
            return None

        with open(note_file, 'r') as f:
            return f.read()

    def list_notes(self, category: Optional[str] = None) -> List[Dict]:
        """
        List all notes, optionally filtered by category prefix.

        Args:
            category: Filter by category prefix (e.g., "work" matches "work/clients/acme")

        Returns:
            List of note metadata dictionaries
        """
        db = self._load_db()
        notes = list(db.values())

        if category:
            # Support both exact match and prefix match
            notes = [
                n for n in notes
                if n.get('category') and (
                    n['category'] == category or
                    n['category'].startswith(category + '/')
                )
            ]

        # Sort by updated_at (newest first)
        notes.sort(key=lambda x: x.get('updated_at', ''), reverse=True)

        return notes

    def delete_note(self, note_id: str) -> bool:
        """
        Delete a note.

        Args:
            note_id: ID of the note to delete (supports partial IDs)

        Returns:
            True if deleted, False if not found
        """
        # Resolve the note ID first
        full_id = self.resolve_note_id(note_id)
        if not full_id:
            return False

        note = self.get_note(full_id)
        if not note:
            return False

        # Delete the file
        note_file = Path(note['file'])
        if note_file.exists():
            note_file.unlink()

        # Remove from database
        db = self._load_db()
        del db[full_id]
        self._save_db(db)

        return True

    def get_categories(self) -> List[str]:
        """Get all unique category paths."""
        db = self._load_db()
        categories = set(note.get('category') for note in db.values()
                        if note.get('category'))
        return sorted(categories)

    def get_top_level_categories(self) -> Dict[str, int]:
        """
        Get top-level categories with note counts.

        Returns:
            Dictionary mapping top-level category names to note counts
        """
        db = self._load_db()
        category_counts = {}

        for note in db.values():
            category = note.get('category')
            if not category:
                continue

            # Extract top-level category (before first /)
            top_level = category.split('/')[0]
            category_counts[top_level] = category_counts.get(top_level, 0) + 1

        return category_counts

    def get_category_tree(self, prefix: Optional[str] = None) -> Dict[str, int]:
        """
        Get category tree with note counts.

        Args:
            prefix: Optional prefix to filter categories (e.g., "work" for "work/*")

        Returns:
            Dictionary mapping category paths to note counts
        """
        db = self._load_db()
        category_counts = {}

        for note in db.values():
            category = note.get('category')
            if not category:
                continue

            # If prefix specified, only include matching categories
            if prefix and not (category == prefix or category.startswith(prefix + '/')):
                continue

            # Count notes for this exact category
            category_counts[category] = category_counts.get(category, 0) + 1

        return category_counts

    def get_subcategories(self, parent: str) -> List[str]:
        """
        Get immediate subcategories under a parent category.

        Args:
            parent: Parent category path (e.g., "work")

        Returns:
            List of immediate child categories (e.g., ["work/clients", "work/projects"])
        """
        db = self._load_db()
        subcategories = set()

        parent_prefix = parent + '/'
        for note in db.values():
            category = note.get('category')
            if not category:
                continue

            # Check if this category is under the parent
            if category.startswith(parent_prefix):
                # Get the immediate child (first level after parent)
                remainder = category[len(parent_prefix):]
                if '/' in remainder:
                    # Has deeper nesting, get just the next level
                    next_level = remainder.split('/')[0]
                    subcategories.add(parent + '/' + next_level)
                else:
                    # Direct child
                    subcategories.add(category)

        return sorted(subcategories)

    def find_note_by_category_and_title(self, category: str, title: str) -> Optional[Dict]:
        """
        Find a note by category and title.

        Args:
            category: Category path
            title: Note title (case-insensitive match)

        Returns:
            Note metadata if found, None otherwise
        """
        db = self._load_db()

        # Search for matching notes
        matches = []
        title_lower = title.lower()

        for note in db.values():
            if note.get('category') == category and note['title'].lower() == title_lower:
                matches.append(note)

        # Return exact match if found
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # Multiple matches - this shouldn't happen but return first one
            return matches[0]
        else:
            return None
