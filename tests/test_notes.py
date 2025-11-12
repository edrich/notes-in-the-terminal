"""
Tests for the notes management module.
"""
import unittest
import tempfile
import shutil
import os
from notes_app.notes import NotesManager


class TestNotesManager(unittest.TestCase):
    """Test cases for NotesManager class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test notes
        self.test_dir = tempfile.mkdtemp()
        os.environ['NOTES_DIR'] = self.test_dir
        self.manager = NotesManager()

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        if 'NOTES_DIR' in os.environ:
            del os.environ['NOTES_DIR']

    def test_create_note_basic(self):
        """Test creating a basic note."""
        success, message, note = self.manager.create_note(
            title='Test Note',
            content='This is a test',
            category='test'
        )

        self.assertTrue(success)
        self.assertIn('successfully', message)
        self.assertIsNotNone(note)
        self.assertEqual(note['title'], 'Test Note')
        self.assertEqual(note['category'], 'test')

    def test_create_note_with_hierarchical_category(self):
        """Test creating a note with hierarchical category."""
        success, message, note = self.manager.create_note(
            title='Work Note',
            content='Content',
            category='work/clients/acme'
        )

        self.assertTrue(success)
        self.assertEqual(note['category'], 'work/clients/acme')

    def test_create_note_without_category(self):
        """Test creating a note without category gets assigned 'default'."""
        success, message, note = self.manager.create_note(
            title='No Category',
            content='Content'
        )

        self.assertTrue(success)
        self.assertEqual(note['category'], 'default')

    def test_create_note_without_title(self):
        """Test creating a note without title fails."""
        success, message, note = self.manager.create_note(
            title='',
            content='Content'
        )

        self.assertFalse(success)
        self.assertIn('Title is required', message)
        self.assertIsNone(note)

    def test_create_note_without_content(self):
        """Test creating a note without content fails."""
        success, message, note = self.manager.create_note(
            title='Test',
            content=''
        )

        self.assertFalse(success)
        self.assertIn('Content is required', message)
        self.assertIsNone(note)

    def test_get_note(self):
        """Test retrieving a note."""
        # Create a note
        success, message, note = self.manager.create_note(
            title='Get Test',
            content='Test content'
        )
        note_id = note['id']

        # Get the note
        success, message, content = self.manager.get_note(note_id)

        self.assertTrue(success)
        self.assertEqual(content, 'Test content')

    def test_get_note_with_partial_id(self):
        """Test retrieving a note with partial ID."""
        # Create a note
        success, message, note = self.manager.create_note(
            title='Partial ID Test',
            content='Content'
        )
        note_id = note['id']
        partial_id = note_id[:8]

        # Get with partial ID
        success, message, content = self.manager.get_note(partial_id)

        self.assertTrue(success)
        self.assertEqual(content, 'Content')

    def test_get_nonexistent_note(self):
        """Test retrieving a nonexistent note."""
        success, message, content = self.manager.get_note('nonexistent-id')

        self.assertFalse(success)
        self.assertIn('not found', message)
        self.assertIsNone(content)

    def test_edit_note_content(self):
        """Test editing note content."""
        # Create a note
        _, _, note = self.manager.create_note('Original', 'Original content')
        note_id = note['id']

        # Edit it
        success, message = self.manager.edit_note(
            note_id=note_id,
            content='Updated content'
        )

        self.assertTrue(success)

        # Verify the edit
        _, _, content = self.manager.get_note(note_id)
        self.assertEqual(content, 'Updated content')

    def test_edit_note_title(self):
        """Test editing note title."""
        _, _, note = self.manager.create_note('Original', 'Content')
        note_id = note['id']

        success, message = self.manager.edit_note(
            note_id=note_id,
            title='Updated Title'
        )

        self.assertTrue(success)

        # Verify
        note_data = self.manager.storage.get_note(note_id)
        self.assertEqual(note_data['title'], 'Updated Title')

    def test_edit_note_category(self):
        """Test editing note category."""
        _, _, note = self.manager.create_note('Test', 'Content', 'old/category')
        note_id = note['id']

        success, message = self.manager.edit_note(
            note_id=note_id,
            category='new/category'
        )

        self.assertTrue(success)

        note_data = self.manager.storage.get_note(note_id)
        self.assertEqual(note_data['category'], 'new/category')

    def test_edit_nonexistent_note(self):
        """Test editing a nonexistent note."""
        success, message = self.manager.edit_note(
            note_id='nonexistent',
            title='New Title'
        )

        self.assertFalse(success)
        self.assertIn('not found', message)

    def test_list_notes_empty(self):
        """Test listing notes when there are none."""
        notes = self.manager.list_notes()
        self.assertEqual(len(notes), 0)

    def test_list_notes_all(self):
        """Test listing all notes."""
        self.manager.create_note('Note 1', 'Content 1')
        self.manager.create_note('Note 2', 'Content 2')
        self.manager.create_note('Note 3', 'Content 3')

        notes = self.manager.list_notes()
        self.assertEqual(len(notes), 3)

    def test_list_notes_by_category(self):
        """Test listing notes filtered by category."""
        self.manager.create_note('Work 1', 'C1', 'work')
        self.manager.create_note('Work 2', 'C2', 'work/clients')
        self.manager.create_note('Personal', 'C3', 'personal')

        notes = self.manager.list_notes(category='work')
        self.assertEqual(len(notes), 2)

        notes = self.manager.list_notes(category='personal')
        self.assertEqual(len(notes), 1)

    def test_delete_note(self):
        """Test deleting a note."""
        _, _, note = self.manager.create_note('Delete Me', 'Content')
        note_id = note['id']

        # Delete it
        success, message = self.manager.delete_note(note_id)
        self.assertTrue(success)

        # Verify it's gone
        success, _, _ = self.manager.get_note(note_id)
        self.assertFalse(success)

    def test_delete_note_with_partial_id(self):
        """Test deleting a note with partial ID."""
        _, _, note = self.manager.create_note('Delete Me', 'Content')
        note_id = note['id']
        partial_id = note_id[:8]

        success, message = self.manager.delete_note(partial_id)
        self.assertTrue(success)

    def test_delete_nonexistent_note(self):
        """Test deleting a nonexistent note."""
        success, message = self.manager.delete_note('nonexistent')
        self.assertFalse(success)

    def test_search_notes_by_title(self):
        """Test searching notes by title."""
        self.manager.create_note('Meeting Notes', 'Content 1')
        self.manager.create_note('Project Plan', 'Content 2')
        self.manager.create_note('Meeting Summary', 'Content 3')

        results = self.manager.search_notes('meeting')
        self.assertEqual(len(results), 2)

    def test_search_notes_by_content(self):
        """Test searching notes by content."""
        self.manager.create_note('Note 1', 'Contains important info')
        self.manager.create_note('Note 2', 'Random content')
        self.manager.create_note('Note 3', 'Also important stuff')

        results = self.manager.search_notes('important')
        self.assertEqual(len(results), 2)

    def test_search_notes_case_insensitive(self):
        """Test that search is case insensitive."""
        self.manager.create_note('Test Note', 'UPPERCASE CONTENT')

        results = self.manager.search_notes('uppercase')
        self.assertEqual(len(results), 1)

        results = self.manager.search_notes('test')
        self.assertEqual(len(results), 1)

    def test_search_notes_no_results(self):
        """Test searching with no matching notes."""
        self.manager.create_note('Note 1', 'Content 1')

        results = self.manager.search_notes('nonexistent')
        self.assertEqual(len(results), 0)

    def test_get_categories(self):
        """Test getting all categories."""
        self.manager.create_note('N1', 'C1', 'work')
        self.manager.create_note('N2', 'C2', 'personal')
        self.manager.create_note('N3', 'C3', 'work/clients')

        categories = self.manager.get_categories()
        self.assertIn('work', categories)
        self.assertIn('personal', categories)
        self.assertIn('work/clients', categories)

    def test_get_top_level_categories(self):
        """Test getting top-level categories with counts."""
        self.manager.create_note('N1', 'C1', 'work')
        self.manager.create_note('N2', 'C2', 'work/clients')
        self.manager.create_note('N3', 'C3', 'personal')
        self.manager.create_note('N4', 'C4', 'personal/health')

        top_level = self.manager.get_top_level_categories()
        self.assertEqual(top_level['work'], 2)
        self.assertEqual(top_level['personal'], 2)
        self.assertEqual(len(top_level), 2)

    def test_get_category_tree(self):
        """Test getting category tree with counts."""
        self.manager.create_note('N1', 'C1', 'work')
        self.manager.create_note('N2', 'C2', 'work')
        self.manager.create_note('N3', 'C3', 'work/clients')

        tree = self.manager.get_category_tree()
        self.assertEqual(tree['work'], 2)
        self.assertEqual(tree['work/clients'], 1)

    def test_get_subcategories(self):
        """Test getting subcategories."""
        self.manager.create_note('N1', 'C1', 'work/clients/acme')
        self.manager.create_note('N2', 'C2', 'work/projects')

        subcats = self.manager.get_subcategories('work')
        self.assertIn('work/clients', subcats)
        self.assertIn('work/projects', subcats)

    def test_notes_sorted_by_update_time(self):
        """Test that notes are sorted by update time (newest first)."""
        _, _, note1 = self.manager.create_note('First', 'Content')
        _, _, note2 = self.manager.create_note('Second', 'Content')
        _, _, note3 = self.manager.create_note('Third', 'Content')

        notes = self.manager.list_notes()

        # Most recent should be first
        self.assertEqual(notes[0]['title'], 'Third')
        self.assertEqual(notes[1]['title'], 'Second')
        self.assertEqual(notes[2]['title'], 'First')

    def test_get_note_by_category_and_title(self):
        """Test getting note by category and title."""
        _, _, note = self.manager.create_note('Meeting Notes', 'Content', 'work/meetings')
        note_id = note['id']

        success, message, found_id = self.manager.get_note_by_category_and_title(
            'work/meetings', 'Meeting Notes'
        )

        self.assertTrue(success)
        self.assertEqual(found_id, note_id)

    def test_get_note_by_category_and_title_case_insensitive(self):
        """Test getting note by category and title with different case."""
        _, _, note = self.manager.create_note('Meeting Notes', 'Content', 'work/meetings')
        note_id = note['id']

        success, _, found_id = self.manager.get_note_by_category_and_title(
            'work/meetings', 'meeting notes'
        )

        self.assertTrue(success)
        self.assertEqual(found_id, note_id)

    def test_get_note_by_category_and_title_not_found(self):
        """Test getting note by category and title when not found."""
        self.manager.create_note('Meeting Notes', 'Content', 'work/meetings')

        success, message, note_id = self.manager.get_note_by_category_and_title(
            'work/projects', 'Meeting Notes'
        )

        self.assertFalse(success)
        self.assertIsNone(note_id)
        self.assertIn('no note found', message.lower())


if __name__ == '__main__':
    unittest.main()
