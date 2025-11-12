"""
Notes management module with CRUD operations.
"""
import uuid
import tempfile
import subprocess
import os
from typing import Optional, List, Dict, Tuple
from .storage import NotesStorage
from .encryption import GPGEncryption


class NotesManager:
    """Main class for managing notes."""

    def __init__(self):
        self.storage = NotesStorage()
        self.encryption = GPGEncryption()

    def create_note(self, title: str, content: str,
                    category: Optional[str] = None,
                    encrypt: bool = False,
                    gpg_recipient: Optional[str] = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        Create a new note.

        Args:
            title: Note title
            content: Note content
            category: Optional category (slash-separated path, e.g., "work/clients/acme")
                     If not provided, defaults to "default" category
            encrypt: Whether to encrypt the note
            gpg_recipient: GPG recipient for encryption (None for symmetric)

        Returns:
            Tuple of (success, message, note_metadata)
        """
        if not title:
            return False, "Title is required", None

        if not content:
            return False, "Content is required", None

        # Assign default category if none provided
        if not category:
            category = "default"

        note_id = str(uuid.uuid4())

        # Encrypt content if requested
        if encrypt:
            if not self.encryption.is_gpg_available():
                return False, "GPG is not available on this system", None

            success, encrypted_content, error = self.encryption.encrypt_interactive(
                content, gpg_recipient
            )
            if not success:
                return False, f"Encryption failed: {error}", None

            content = encrypted_content

        # Save the note
        try:
            note_metadata = self.storage.save_note(
                note_id=note_id,
                title=title,
                content=content,
                category=category,
                encrypted=encrypt
            )
            return True, f"Note created successfully (ID: {note_id})", note_metadata
        except Exception as e:
            return False, f"Failed to create note: {str(e)}", None

    def get_note(self, note_id: str, decrypt: bool = True) -> Tuple[bool, str, Optional[str]]:
        """
        Get a note by ID.

        Args:
            note_id: Note ID
            decrypt: Whether to decrypt encrypted notes

        Returns:
            Tuple of (success, message, content)
        """
        note = self.storage.get_note(note_id)
        if not note:
            return False, f"Note with ID '{note_id}' not found", None

        content = self.storage.read_note_content(note_id)
        if content is None:
            return False, "Note file not found", None

        # Decrypt if necessary
        if note['encrypted'] and decrypt:
            if not self.encryption.is_gpg_available():
                return False, "GPG is not available. Cannot decrypt note.", None

            success, decrypted_content, error = self.encryption.decrypt(content)
            if not success:
                return False, f"Decryption failed: {error}", None

            content = decrypted_content

        return True, "Note retrieved successfully", content

    def edit_note(self, note_id: str, title: Optional[str] = None,
                  content: Optional[str] = None,
                  category: Optional[str] = None) -> Tuple[bool, str]:
        """
        Edit an existing note.

        Args:
            note_id: Note ID (supports partial IDs)
            title: New title (optional)
            content: New content (optional)
            category: New category path (optional, e.g., "work/clients/acme")

        Returns:
            Tuple of (success, message)
        """
        note = self.storage.get_note(note_id)
        if not note:
            return False, f"Note with ID '{note_id}' not found"

        # Resolve to full ID (in case partial ID was provided)
        full_note_id = note['id']

        # Get current content if not provided
        if content is None:
            success, msg, current_content = self.get_note(full_note_id)
            if not success:
                return False, f"Failed to retrieve current note content: {msg}"
            content = current_content

        # Use current title if not provided
        if title is None:
            title = note['title']

        # Use current category if not provided
        if category is None:
            category = note.get('category')

        # If note is encrypted, re-encrypt the content
        if note['encrypted']:
            if not self.encryption.is_gpg_available():
                return False, "GPG is not available. Cannot update encrypted note."

            success, encrypted_content, error = self.encryption.encrypt_interactive(
                content, None
            )
            if not success:
                return False, f"Encryption failed: {error}"

            content = encrypted_content

        # Save updated note (use full ID)
        try:
            self.storage.save_note(
                note_id=full_note_id,
                title=title,
                content=content,
                category=category,
                encrypted=note['encrypted']
            )
            return True, "Note updated successfully"
        except Exception as e:
            return False, f"Failed to update note: {str(e)}"

    def edit_note_interactive(self, note_id: str) -> Tuple[bool, str]:
        """
        Edit a note using the system's default editor.

        Args:
            note_id: Note ID

        Returns:
            Tuple of (success, message)
        """
        # Get the note
        success, msg, content = self.get_note(note_id)
        if not success:
            return False, msg

        note = self.storage.get_note(note_id)

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tf:
            tf.write(content)
            temp_file = tf.name

        try:
            # Open in editor
            editor = os.environ.get('EDITOR', 'nano')
            subprocess.run([editor, temp_file], check=True)

            # Read the edited content
            with open(temp_file, 'r') as f:
                new_content = f.read()

            # Update the note
            return self.edit_note(note_id, content=new_content)

        except subprocess.CalledProcessError:
            return False, "Editor exited with an error"
        except Exception as e:
            return False, f"Failed to edit note: {str(e)}"
        finally:
            # Clean up temp file
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def list_notes(self, category: Optional[str] = None) -> List[Dict]:
        """
        List all notes, optionally filtered by category prefix.

        Args:
            category: Filter by category prefix (e.g., "work" matches "work/clients/acme")

        Returns:
            List of note metadata dictionaries
        """
        return self.storage.list_notes(category)

    def delete_note(self, note_id: str) -> Tuple[bool, str]:
        """
        Delete a note.

        Args:
            note_id: Note ID

        Returns:
            Tuple of (success, message)
        """
        if self.storage.delete_note(note_id):
            return True, "Note deleted successfully"
        else:
            return False, f"Note with ID '{note_id}' not found"

    def search_notes(self, query: str) -> List[Dict]:
        """
        Search notes by title or content.

        Args:
            query: Search query

        Returns:
            List of matching note metadata dictionaries
        """
        all_notes = self.storage.list_notes()
        matching_notes = []

        query_lower = query.lower()

        for note in all_notes:
            # Search in title
            if query_lower in note['title'].lower():
                matching_notes.append(note)
                continue

            # Search in content (only for non-encrypted notes)
            if not note['encrypted']:
                try:
                    content = self.storage.read_note_content(note['id'])
                    if content and query_lower in content.lower():
                        matching_notes.append(note)
                except Exception:
                    pass

        return matching_notes

    def get_categories(self) -> List[str]:
        """Get all unique category paths."""
        return self.storage.get_categories()

    def get_top_level_categories(self) -> Dict[str, int]:
        """Get top-level categories with note counts."""
        return self.storage.get_top_level_categories()

    def get_category_tree(self, prefix: Optional[str] = None) -> Dict[str, int]:
        """Get category tree with note counts."""
        return self.storage.get_category_tree(prefix)

    def get_subcategories(self, parent: str) -> List[str]:
        """Get immediate subcategories under a parent category."""
        return self.storage.get_subcategories(parent)

    def get_note_by_category_and_title(self, category: str, title: str) -> Tuple[bool, str, Optional[str]]:
        """
        Get a note by category and title.

        Args:
            category: Category path
            title: Note title

        Returns:
            Tuple of (success, message, note_id)
        """
        note = self.storage.find_note_by_category_and_title(category, title)
        if not note:
            return False, f"No note found with title '{title}' in category '{category}'", None

        return True, "Note found", note['id']
