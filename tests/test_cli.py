"""
Tests for the CLI module.
"""
import unittest
import tempfile
import shutil
import os
import sys
from io import StringIO
from unittest.mock import patch
from notes_app.cli import NotesCLI


class TestNotesCLI(unittest.TestCase):
    """Test cases for NotesCLI class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test notes
        self.test_dir = tempfile.mkdtemp()
        os.environ['NOTES_DIR'] = self.test_dir
        self.cli = NotesCLI()

    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
        if 'NOTES_DIR' in os.environ:
            del os.environ['NOTES_DIR']

    def test_create_command_with_message(self):
        """Test create command with inline message."""
        with patch('sys.stdout', new=StringIO()):
            self.cli.run(['create', 'Test Note', '-m', 'Test content'])

        # Verify note was created
        notes = self.cli.manager.list_notes()
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]['title'], 'Test Note')

    def test_create_command_with_category(self):
        """Test create command with category."""
        with patch('sys.stdout', new=StringIO()):
            self.cli.run(['create', 'Work Note', '-m', 'Content', '-c', 'work/clients'])

        notes = self.cli.manager.list_notes()
        self.assertEqual(notes[0]['category'], 'work/clients')

    def test_list_command_empty(self):
        """Test list command with no notes."""
        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['list'])
            self.assertIn('No categories found', output.getvalue())

    def test_list_command_shows_top_level_categories(self):
        """Test list command shows top-level categories by default."""
        # Create notes with categories
        self.cli.manager.create_note('Work Note', 'Content 1', 'work/projects')
        self.cli.manager.create_note('Personal Note', 'Content 2', 'personal')

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['list'])
            output_str = output.getvalue()
            # Should show category names, not note titles
            self.assertIn('work', output_str)
            self.assertIn('personal', output_str)
            self.assertNotIn('Work Note', output_str)
            self.assertNotIn('Personal Note', output_str)

    def test_list_command_with_all_flag(self):
        """Test list command with -a flag shows all notes."""
        # Create notes with categories
        self.cli.manager.create_note('Note 1', 'Content 1', 'work')
        self.cli.manager.create_note('Note 2', 'Content 2', 'personal')

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['list', '-a'])
            output_str = output.getvalue()
            self.assertIn('Note 1', output_str)
            self.assertIn('Note 2', output_str)

    def test_list_command_with_category_filter(self):
        """Test list command filtered by category."""
        self.cli.manager.create_note('Work', 'C1', 'work')
        self.cli.manager.create_note('Personal', 'C2', 'personal')

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['list', '-c', 'work'])
            output_str = output.getvalue()
            self.assertIn('Work', output_str)
            self.assertNotIn('Personal', output_str)

    def test_list_command_with_positional_category(self):
        """Test list command with positional category argument."""
        self.cli.manager.create_note('Work', 'C1', 'work')
        self.cli.manager.create_note('Personal', 'C2', 'personal')

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['list', 'work'])
            output_str = output.getvalue()
            self.assertIn('Work', output_str)
            self.assertNotIn('Personal', output_str)

    def test_list_command_with_hierarchical_category_positional(self):
        """Test list command with hierarchical category as positional argument."""
        self.cli.manager.create_note('Client A', 'C1', 'work/clients/acme')
        self.cli.manager.create_note('Client B', 'C2', 'work/clients/beta')
        self.cli.manager.create_note('Project', 'C3', 'work/projects')

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['list', 'work/clients'])
            output_str = output.getvalue()
            self.assertIn('Client A', output_str)
            self.assertIn('Client B', output_str)
            self.assertNotIn('Project', output_str)

    def test_list_command_positional_takes_precedence(self):
        """Test that positional category argument takes precedence over flag."""
        self.cli.manager.create_note('Work', 'C1', 'work')
        self.cli.manager.create_note('Personal', 'C2', 'personal')

        # If both positional and flag are provided, positional should win
        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['list', 'work', '-c', 'personal'])
            output_str = output.getvalue()
            self.assertIn('Work', output_str)
            self.assertNotIn('Personal', output_str)

    def test_show_command(self):
        """Test show command."""
        _, _, note = self.cli.manager.create_note('Show Test', 'Content to show')
        note_id = note['id'][:8]

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['show', note_id])
            output_str = output.getvalue()
            self.assertIn('Show Test', output_str)
            self.assertIn('Content to show', output_str)

    def test_show_command_nonexistent(self):
        """Test show command with nonexistent note."""
        with patch('sys.stderr', new=StringIO()) as stderr:
            with self.assertRaises(SystemExit):
                self.cli.run(['show', 'nonexistent'])
            self.assertIn('not found', stderr.getvalue())

    def test_show_command_by_category_and_title(self):
        """Test show command using category and title."""
        self.cli.manager.create_note('Meeting Notes', 'Important meeting content', 'work/meetings')

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['show', 'work/meetings', 'Meeting Notes'])
            output_str = output.getvalue()
            self.assertIn('Meeting Notes', output_str)
            self.assertIn('Important meeting content', output_str)
            self.assertIn('work/meetings', output_str)

    def test_show_command_by_category_and_title_not_found(self):
        """Test show command with category/title that doesn't exist."""
        self.cli.manager.create_note('Meeting Notes', 'Content', 'work/meetings')

        with patch('sys.stderr', new=StringIO()) as stderr:
            with self.assertRaises(SystemExit):
                self.cli.run(['show', 'work/projects', 'Meeting Notes'])
            self.assertIn('no note found', stderr.getvalue().lower())

    def test_show_command_too_many_args(self):
        """Test show command with too many arguments."""
        with patch('sys.stderr', new=StringIO()) as stderr:
            with self.assertRaises(SystemExit):
                self.cli.run(['show', 'arg1', 'arg2', 'arg3'])
            self.assertIn('Invalid arguments', stderr.getvalue())

    def test_edit_command_title(self):
        """Test edit command to change title."""
        _, _, note = self.cli.manager.create_note('Original', 'Content')
        note_id = note['id']

        with patch('sys.stdout', new=StringIO()):
            self.cli.run(['edit', note_id[:8], '-t', 'New Title'])

        # Verify the edit
        note_data = self.cli.manager.storage.get_note(note_id)
        self.assertEqual(note_data['title'], 'New Title')

    def test_edit_command_category(self):
        """Test edit command to change category."""
        _, _, note = self.cli.manager.create_note('Test', 'Content', 'old')
        note_id = note['id']

        with patch('sys.stdout', new=StringIO()):
            self.cli.run(['edit', note_id[:8], '-c', 'new/category'])

        note_data = self.cli.manager.storage.get_note(note_id)
        self.assertEqual(note_data['category'], 'new/category')

    def test_edit_command_no_fields(self):
        """Test edit command without any fields to update."""
        _, _, note = self.cli.manager.create_note('Test', 'Content')
        note_id = note['id'][:8]

        with patch('sys.stderr', new=StringIO()) as stderr:
            with self.assertRaises(SystemExit):
                self.cli.run(['edit', note_id])
            self.assertIn('at least one field', stderr.getvalue())

    def test_delete_command_with_force(self):
        """Test delete command with force flag."""
        _, _, note = self.cli.manager.create_note('Delete Me', 'Content')
        note_id = note['id'][:8]

        with patch('sys.stdout', new=StringIO()):
            self.cli.run(['delete', note_id, '-f'])

        # Verify deletion
        notes = self.cli.manager.list_notes()
        self.assertEqual(len(notes), 0)

    def test_delete_command_with_confirmation(self):
        """Test delete command with user confirmation."""
        _, _, note = self.cli.manager.create_note('Delete Me', 'Content')
        note_id = note['id'][:8]

        with patch('builtins.input', return_value='yes'):
            with patch('sys.stdout', new=StringIO()):
                self.cli.run(['delete', note_id])

        # Verify deletion
        notes = self.cli.manager.list_notes()
        self.assertEqual(len(notes), 0)

    def test_delete_command_cancelled(self):
        """Test delete command cancelled by user."""
        _, _, note = self.cli.manager.create_note('Keep Me', 'Content')
        note_id = note['id'][:8]

        with patch('builtins.input', return_value='no'):
            with patch('sys.stdout', new=StringIO()):
                self.cli.run(['delete', note_id])

        # Verify not deleted
        notes = self.cli.manager.list_notes()
        self.assertEqual(len(notes), 1)

    def test_search_command(self):
        """Test search command."""
        self.cli.manager.create_note('Meeting Notes', 'Important meeting')
        self.cli.manager.create_note('Project Plan', 'Random content')

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['search', 'meeting'])
            output_str = output.getvalue()
            self.assertIn('Meeting Notes', output_str)
            self.assertNotIn('Project Plan', output_str)

    def test_search_command_no_results(self):
        """Test search command with no results."""
        self.cli.manager.create_note('Note', 'Content')

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['search', 'nonexistent'])
            self.assertIn('No notes found', output.getvalue())

    def test_categories_command(self):
        """Test categories command."""
        self.cli.manager.create_note('N1', 'C1', 'work')
        self.cli.manager.create_note('N2', 'C2', 'personal')

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['categories'])
            output_str = output.getvalue()
            self.assertIn('work', output_str)
            self.assertIn('personal', output_str)

    def test_categories_command_with_prefix(self):
        """Test categories command with prefix filter."""
        self.cli.manager.create_note('N1', 'C1', 'work/clients')
        self.cli.manager.create_note('N2', 'C2', 'work/projects')

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['categories', '-c', 'work'])
            output_str = output.getvalue()
            self.assertIn('work/clients', output_str)
            self.assertIn('work/projects', output_str)

    def test_info_command(self):
        """Test info command."""
        self.cli.manager.create_note('Note 1', 'Content')
        self.cli.manager.create_note('Note 2', 'Content')

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run(['info'])
            output_str = output.getvalue()
            self.assertIn('Total notes: 2', output_str)
            self.assertIn('Notes directory:', output_str)

    def test_help_command(self):
        """Test help output."""
        with patch('sys.stdout', new=StringIO()) as output:
            with self.assertRaises(SystemExit) as cm:
                self.cli.run(['--help'])
            self.assertEqual(cm.exception.code, 0)
            output_str = output.getvalue()
            self.assertIn('Notes in the Terminal Application', output_str)
            self.assertIn('create', output_str)
            self.assertIn('list', output_str)

    def test_no_command(self):
        """Test running with no command shows help."""
        with patch('sys.stdout', new=StringIO()) as output:
            self.cli.run([])
            output_str = output.getvalue()
            self.assertIn('Notes in the Terminal Application', output_str)

    def test_print_note_summary_basic(self):
        """Test printing note summary."""
        note = {
            'id': 'abc123def456',
            'title': 'Test Note',
            'category': None,
            'encrypted': False
        }

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli._print_note_summary(note)
            output_str = output.getvalue()
            self.assertIn('[abc123de]', output_str)
            self.assertIn('Test Note', output_str)

    def test_print_note_summary_with_category(self):
        """Test printing note summary with category."""
        note = {
            'id': 'abc123def456',
            'title': 'Work Note',
            'category': 'work/clients',
            'encrypted': False
        }

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli._print_note_summary(note)
            output_str = output.getvalue()
            self.assertIn('work/clients', output_str)

    def test_print_note_summary_encrypted(self):
        """Test printing note summary for encrypted note."""
        note = {
            'id': 'abc123def456',
            'title': 'Secret',
            'category': None,
            'encrypted': True
        }

        with patch('sys.stdout', new=StringIO()) as output:
            self.cli._print_note_summary(note)
            output_str = output.getvalue()
            self.assertIn('[ENCRYPTED]', output_str)


if __name__ == '__main__':
    unittest.main()
