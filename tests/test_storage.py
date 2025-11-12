"""
Tests for the storage module.
"""
import unittest
import tempfile
import shutil
import os
from pathlib import Path
from notes_app.storage import NotesStorage


class TestNotesStorage(unittest.TestCase):
    """Test cases for NotesStorage class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test notes
        self.test_dir = tempfile.mkdtemp()
        os.environ['NOTES_DIR'] = self.test_dir
        self.storage = NotesStorage()

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        if 'NOTES_DIR' in os.environ:
            del os.environ['NOTES_DIR']

    def test_storage_initialization(self):
        """Test storage initialization creates necessary files."""
        self.assertTrue(self.storage.notes_dir.exists())
        self.assertTrue(self.storage.db_file.exists())

    def test_save_note(self):
        """Test saving a note."""
        note_metadata = self.storage.save_note(
            note_id='test-id-1',
            title='Test Note',
            content='This is a test note',
            category='test/category',
            encrypted=False
        )

        self.assertEqual(note_metadata['id'], 'test-id-1')
        self.assertEqual(note_metadata['title'], 'Test Note')
        self.assertEqual(note_metadata['category'], 'test/category')
        self.assertFalse(note_metadata['encrypted'])

        # Verify file was created
        note_file = self.storage.get_note_file_path('test-id-1')
        self.assertTrue(note_file.exists())

    def test_save_note_without_category(self):
        """Test saving a note without category."""
        note_metadata = self.storage.save_note(
            note_id='test-id-2',
            title='No Category',
            content='Content',
            encrypted=False
        )

        self.assertIsNone(note_metadata['category'])

    def test_get_note(self):
        """Test retrieving a note by ID."""
        # Save a note first
        self.storage.save_note(
            note_id='test-id-3',
            title='Get Test',
            content='Content',
            category='test',
            encrypted=False
        )

        # Retrieve it
        note = self.storage.get_note('test-id-3')
        self.assertIsNotNone(note)
        self.assertEqual(note['id'], 'test-id-3')
        self.assertEqual(note['title'], 'Get Test')

    def test_get_nonexistent_note(self):
        """Test retrieving a note that doesn't exist."""
        note = self.storage.get_note('nonexistent')
        self.assertIsNone(note)

    def test_resolve_note_id_full(self):
        """Test resolving a full note ID."""
        self.storage.save_note(
            note_id='test-id-4',
            title='Test',
            content='Content',
            encrypted=False
        )

        resolved = self.storage.resolve_note_id('test-id-4')
        self.assertEqual(resolved, 'test-id-4')

    def test_resolve_note_id_partial(self):
        """Test resolving a partial note ID."""
        self.storage.save_note(
            note_id='abc123def456',
            title='Test',
            content='Content',
            encrypted=False
        )

        resolved = self.storage.resolve_note_id('abc123')
        self.assertEqual(resolved, 'abc123def456')

    def test_resolve_note_id_ambiguous(self):
        """Test resolving an ambiguous partial ID."""
        self.storage.save_note('abc123', 'Test 1', 'Content', encrypted=False)
        self.storage.save_note('abc456', 'Test 2', 'Content', encrypted=False)

        resolved = self.storage.resolve_note_id('ab')
        self.assertIsNone(resolved)  # Ambiguous

    def test_read_note_content(self):
        """Test reading note content."""
        self.storage.save_note(
            note_id='test-id-5',
            title='Content Test',
            content='This is the content',
            encrypted=False
        )

        content = self.storage.read_note_content('test-id-5')
        self.assertEqual(content, 'This is the content')

    def test_list_notes_all(self):
        """Test listing all notes."""
        self.storage.save_note('id1', 'Note 1', 'Content 1', 'work', False)
        self.storage.save_note('id2', 'Note 2', 'Content 2', 'personal', False)
        self.storage.save_note('id3', 'Note 3', 'Content 3', 'work/clients', False)

        notes = self.storage.list_notes()
        self.assertEqual(len(notes), 3)

    def test_list_notes_by_category(self):
        """Test listing notes filtered by category."""
        self.storage.save_note('id1', 'Note 1', 'Content 1', 'work', False)
        self.storage.save_note('id2', 'Note 2', 'Content 2', 'personal', False)
        self.storage.save_note('id3', 'Note 3', 'Content 3', 'work/clients', False)

        notes = self.storage.list_notes(category='work')
        self.assertEqual(len(notes), 2)  # 'work' and 'work/clients'

        notes = self.storage.list_notes(category='personal')
        self.assertEqual(len(notes), 1)

    def test_list_notes_by_category_prefix(self):
        """Test listing notes with category prefix matching."""
        self.storage.save_note('id1', 'Note 1', 'C1', 'work/clients/acme', False)
        self.storage.save_note('id2', 'Note 2', 'C2', 'work/clients/beta', False)
        self.storage.save_note('id3', 'Note 3', 'C3', 'work/projects', False)

        notes = self.storage.list_notes(category='work/clients')
        self.assertEqual(len(notes), 2)  # Both client notes

    def test_delete_note(self):
        """Test deleting a note."""
        self.storage.save_note('id-delete', 'Delete Me', 'Content', encrypted=False)

        # Verify it exists
        note = self.storage.get_note('id-delete')
        self.assertIsNotNone(note)

        # Delete it
        result = self.storage.delete_note('id-delete')
        self.assertTrue(result)

        # Verify it's gone
        note = self.storage.get_note('id-delete')
        self.assertIsNone(note)

    def test_delete_note_with_partial_id(self):
        """Test deleting a note with partial ID."""
        self.storage.save_note('xyz123abc456', 'Delete Me', 'Content', encrypted=False)

        result = self.storage.delete_note('xyz123')
        self.assertTrue(result)

        note = self.storage.get_note('xyz123abc456')
        self.assertIsNone(note)

    def test_delete_nonexistent_note(self):
        """Test deleting a note that doesn't exist."""
        result = self.storage.delete_note('nonexistent')
        self.assertFalse(result)

    def test_get_categories(self):
        """Test getting all unique categories."""
        self.storage.save_note('id1', 'N1', 'C1', 'work', False)
        self.storage.save_note('id2', 'N2', 'C2', 'personal', False)
        self.storage.save_note('id3', 'N3', 'C3', 'work/clients', False)

        categories = self.storage.get_categories()
        self.assertIn('work', categories)
        self.assertIn('personal', categories)
        self.assertIn('work/clients', categories)
        self.assertEqual(len(categories), 3)

    def test_get_top_level_categories(self):
        """Test getting top-level categories with counts."""
        self.storage.save_note('id1', 'N1', 'C1', 'work', False)
        self.storage.save_note('id2', 'N2', 'C2', 'work/clients', False)
        self.storage.save_note('id3', 'N3', 'C3', 'work/clients/acme', False)
        self.storage.save_note('id4', 'N4', 'C4', 'personal', False)
        self.storage.save_note('id5', 'N5', 'C5', 'personal/health', False)

        top_level = self.storage.get_top_level_categories()
        self.assertEqual(top_level['work'], 3)  # work, work/clients, work/clients/acme
        self.assertEqual(top_level['personal'], 2)  # personal, personal/health
        self.assertEqual(len(top_level), 2)  # Only 'work' and 'personal'

    def test_get_category_tree(self):
        """Test getting category tree with counts."""
        self.storage.save_note('id1', 'N1', 'C1', 'work', False)
        self.storage.save_note('id2', 'N2', 'C2', 'work', False)
        self.storage.save_note('id3', 'N3', 'C3', 'work/clients', False)

        tree = self.storage.get_category_tree()
        self.assertEqual(tree['work'], 2)
        self.assertEqual(tree['work/clients'], 1)

    def test_get_category_tree_with_prefix(self):
        """Test getting category tree filtered by prefix."""
        self.storage.save_note('id1', 'N1', 'C1', 'work/clients/acme', False)
        self.storage.save_note('id2', 'N2', 'C2', 'work/clients/beta', False)
        self.storage.save_note('id3', 'N3', 'C3', 'personal', False)

        tree = self.storage.get_category_tree(prefix='work')
        self.assertIn('work/clients/acme', tree)
        self.assertIn('work/clients/beta', tree)
        self.assertNotIn('personal', tree)

    def test_get_subcategories(self):
        """Test getting immediate subcategories."""
        self.storage.save_note('id1', 'N1', 'C1', 'work/clients/acme', False)
        self.storage.save_note('id2', 'N2', 'C2', 'work/clients/beta', False)
        self.storage.save_note('id3', 'N3', 'C3', 'work/projects', False)

        subcats = self.storage.get_subcategories('work')
        # Should return next level categories
        self.assertIn('work/clients', subcats)
        self.assertIn('work/projects', subcats)

    def test_encrypted_note_file_extension(self):
        """Test that encrypted notes use .gpg extension."""
        note_file = self.storage.get_note_file_path('test-id', encrypted=True)
        self.assertTrue(str(note_file).endswith('.gpg'))

        note_file = self.storage.get_note_file_path('test-id', encrypted=False)
        self.assertTrue(str(note_file).endswith('.txt'))

    def test_note_update_preserves_created_at(self):
        """Test that updating a note preserves created_at timestamp."""
        # Create note
        note1 = self.storage.save_note('id-update', 'Original', 'Content', encrypted=False)
        created_at = note1['created_at']

        # Update note
        note2 = self.storage.save_note('id-update', 'Updated', 'New Content', encrypted=False)

        self.assertEqual(note2['created_at'], created_at)
        self.assertNotEqual(note2['updated_at'], created_at)

    def test_find_note_by_category_and_title(self):
        """Test finding a note by category and title."""
        self.storage.save_note('id1', 'Meeting Notes', 'Content', 'work/meetings', False)
        self.storage.save_note('id2', 'Project Plan', 'Content', 'work/projects', False)

        # Find existing note
        note = self.storage.find_note_by_category_and_title('work/meetings', 'Meeting Notes')
        self.assertIsNotNone(note)
        self.assertEqual(note['id'], 'id1')
        self.assertEqual(note['title'], 'Meeting Notes')

    def test_find_note_by_category_and_title_case_insensitive(self):
        """Test that title matching is case-insensitive."""
        self.storage.save_note('id1', 'Meeting Notes', 'Content', 'work/meetings', False)

        # Find with different case
        note = self.storage.find_note_by_category_and_title('work/meetings', 'meeting notes')
        self.assertIsNotNone(note)
        self.assertEqual(note['id'], 'id1')

        note = self.storage.find_note_by_category_and_title('work/meetings', 'MEETING NOTES')
        self.assertIsNotNone(note)
        self.assertEqual(note['id'], 'id1')

    def test_find_note_by_category_and_title_not_found(self):
        """Test finding a note that doesn't exist."""
        self.storage.save_note('id1', 'Meeting Notes', 'Content', 'work/meetings', False)

        # Wrong category
        note = self.storage.find_note_by_category_and_title('work/projects', 'Meeting Notes')
        self.assertIsNone(note)

        # Wrong title
        note = self.storage.find_note_by_category_and_title('work/meetings', 'Nonexistent')
        self.assertIsNone(note)

    def test_find_note_by_category_and_title_no_category(self):
        """Test finding a note without category."""
        self.storage.save_note('id1', 'Uncategorized Note', 'Content', None, False)

        # Cannot find by category if note has no category
        note = self.storage.find_note_by_category_and_title('', 'Uncategorized Note')
        self.assertIsNone(note)


if __name__ == '__main__':
    unittest.main()
