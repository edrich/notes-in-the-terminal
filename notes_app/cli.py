"""
Command-line interface for the notes application.
"""
import argparse
import sys
from datetime import datetime
from typing import Optional
from .notes import NotesManager
from .config import get_notes_directory


class NotesCLI:
    """Command-line interface handler."""

    def __init__(self):
        self.manager = NotesManager()

    def run(self, args=None):
        """Run the CLI with the given arguments."""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)

        if hasattr(parsed_args, 'func'):
            parsed_args.func(parsed_args)
        else:
            parser.print_help()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser."""
        parser = argparse.ArgumentParser(
            description='Notes in the Terminal Application - Manage your notes from the command line',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  notes create "Quick Note" -m "Content"  # Assigned to 'default' category
  notes create "My Note" -c personal/ideas
  notes create "Work Project" -c work/clients/acme
  notes create "Secret" --encrypt
  notes list                    # Show top-level categories
  notes list -a                 # Show all notes
  notes list work               # Show notes in work category
  notes list work/clients       # Show notes in work/clients category
  notes show <note-id>
  notes show work/meetings "Meeting Notes"
  notes edit <note-id>
  notes edit work/meetings "Meeting Notes"
  notes delete <note-id>
  notes delete work/meetings "Meeting Notes"
  notes search "keyword"
  notes categories
            """
        )

        subparsers = parser.add_subparsers(title='commands', dest='command')

        # Create command
        create_parser = subparsers.add_parser('create', help='Create a new note')
        create_parser.add_argument('title', help='Note title')
        create_parser.add_argument('-c', '--category', help='Category (slash-separated, e.g., work/clients/acme). Defaults to "default" if not provided')
        create_parser.add_argument('-m', '--message', help='Note content (if not provided, opens editor)')
        create_parser.add_argument('-e', '--encrypt', action='store_true', help='Encrypt the note with GPG')
        create_parser.add_argument('-r', '--recipient', help='GPG recipient (key ID or email)')
        create_parser.set_defaults(func=self.cmd_create)

        # List command
        list_parser = subparsers.add_parser('list', help='List notes or categories')
        list_parser.add_argument('category', nargs='?',
                               help='Category to filter by (optional, e.g., work or work/clients)')
        list_parser.add_argument('-a', '--all', action='store_true',
                               help='Show all notes (default shows top-level categories)')
        list_parser.add_argument('-c', '--category-flag', dest='category_flag',
                               help='Filter by category prefix (alternative to positional argument)')
        list_parser.add_argument('-v', '--verbose', action='store_true', help='Show more details')
        list_parser.set_defaults(func=self.cmd_list)

        # Show command
        show_parser = subparsers.add_parser('show', help='Show a note')
        show_parser.add_argument('identifier', nargs='+',
                               help='Note ID, or "category title" to show by category and title')
        show_parser.add_argument('--no-decrypt', action='store_true', help='Do not decrypt encrypted notes')
        show_parser.set_defaults(func=self.cmd_show)

        # Edit command
        edit_parser = subparsers.add_parser('edit', help='Edit a note')
        edit_parser.add_argument('identifier', nargs='+',
                               help='Note ID, or "category title" to edit by category and title')
        edit_parser.add_argument('-t', '--title', help='New title')
        edit_parser.add_argument('-m', '--message', help='New content')
        edit_parser.add_argument('-c', '--category', help='New category (slash-separated)')
        edit_parser.add_argument('-i', '--interactive', action='store_true',
                               help='Edit in default editor')
        edit_parser.set_defaults(func=self.cmd_edit)

        # Delete command
        delete_parser = subparsers.add_parser('delete', help='Delete a note')
        delete_parser.add_argument('identifier', nargs='+',
                                  help='Note ID, or "category title" to delete by category and title')
        delete_parser.add_argument('-f', '--force', action='store_true',
                                  help='Do not ask for confirmation')
        delete_parser.set_defaults(func=self.cmd_delete)

        # Search command
        search_parser = subparsers.add_parser('search', help='Search notes')
        search_parser.add_argument('query', help='Search query')
        search_parser.set_defaults(func=self.cmd_search)

        # Categories command
        categories_parser = subparsers.add_parser('categories', help='List all categories')
        categories_parser.add_argument('-c', '--category', help='Show subcategories for this category')
        categories_parser.set_defaults(func=self.cmd_categories)

        # Info command
        info_parser = subparsers.add_parser('info', help='Show application info')
        info_parser.set_defaults(func=self.cmd_info)

        return parser

    def cmd_create(self, args):
        """Handle create command."""
        title = args.title
        category = args.category
        encrypt = args.encrypt
        recipient = args.recipient

        # Get content
        if args.message:
            content = args.message
        else:
            content = self._get_content_from_editor()
            if content is None:
                self._error("Failed to get content from editor")
                return

        # Create the note
        success, message, note = self.manager.create_note(
            title=title,
            content=content,
            category=category,
            encrypt=encrypt,
            gpg_recipient=recipient
        )

        if success:
            self._success(message)
            if note:
                self._print_note_summary(note)
        else:
            self._error(message)

    def cmd_list(self, args):
        """Handle list command."""
        # Determine category from positional arg or flag
        # Positional argument takes precedence
        category = args.category if args.category else args.category_flag

        # If no category specified and -a flag not set, show top-level categories
        if not category and not args.all:
            categories = self.manager.get_top_level_categories()
            if not categories:
                self._info("No categories found")
                return

            self._info(f"Found {len(categories)} top-level categor{'y' if len(categories) == 1 else 'ies'}:")
            print()

            for cat_name in sorted(categories.keys()):
                count = categories[cat_name]
                print(f"  {cat_name} ({count} note{'s' if count != 1 else ''})")
            return

        # Otherwise, show notes (filtered by category if provided)
        notes = self.manager.list_notes(category=category)

        if not notes:
            self._info("No notes found")
            return

        self._info(f"Found {len(notes)} note(s):")
        print()

        for note in notes:
            self._print_note_summary(note, verbose=args.verbose)
            print()

    def cmd_show(self, args):
        """Handle show command."""
        decrypt = not args.no_decrypt

        # Determine if using note ID or category/title
        if len(args.identifier) == 1:
            # Single argument - treat as note ID
            note_id = args.identifier[0]
        elif len(args.identifier) == 2:
            # Two arguments - treat as category and title
            category = args.identifier[0]
            title = args.identifier[1]

            # Find the note by category and title
            success, message, note_id = self.manager.get_note_by_category_and_title(category, title)
            if not success:
                self._error(message)
                return
        else:
            self._error("Invalid arguments. Use: notes show <note-id> OR notes show <category> <title>")
            return

        # Get and display the note
        success, message, content = self.manager.get_note(note_id, decrypt=decrypt)

        if not success:
            self._error(message)
            return

        note = self.manager.storage.get_note(note_id)
        if note:
            print(f"Title: {note['title']}")
            print(f"ID: {note['id']}")
            if note.get('category'):
                print(f"Category: {note['category']}")
            print(f"Created: {self._format_datetime(note.get('created_at'))}")
            print(f"Updated: {self._format_datetime(note.get('updated_at'))}")
            if note.get('encrypted'):
                print("Encrypted: Yes")
            print("-" * 60)

        print(content)

    def cmd_edit(self, args):
        """Handle edit command."""
        # Determine if using note ID or category/title
        if len(args.identifier) == 1:
            # Single argument - treat as note ID
            note_id = args.identifier[0]
        elif len(args.identifier) == 2:
            # Two arguments - treat as category and title
            category = args.identifier[0]
            title = args.identifier[1]

            # Find the note by category and title
            success, message, note_id = self.manager.get_note_by_category_and_title(category, title)
            if not success:
                self._error(message)
                return
        else:
            self._error("Invalid arguments. Use: notes edit <note-id> OR notes edit <category> <title>")
            return

        if args.interactive:
            success, message = self.manager.edit_note_interactive(note_id)
        else:
            # Update specific fields
            if not any([args.title, args.message, args.category]):
                self._error("Provide at least one field to update (or use -i for interactive editing)")
                return

            success, message = self.manager.edit_note(
                note_id=note_id,
                title=args.title,
                content=args.message,
                category=args.category
            )

        if success:
            self._success(message)
        else:
            self._error(message)

    def cmd_delete(self, args):
        """Handle delete command."""
        # Determine if using note ID or category/title
        if len(args.identifier) == 1:
            # Single argument - treat as note ID
            note_id = args.identifier[0]
        elif len(args.identifier) == 2:
            # Two arguments - treat as category and title
            category = args.identifier[0]
            title = args.identifier[1]

            # Find the note by category and title
            success, message, note_id = self.manager.get_note_by_category_and_title(category, title)
            if not success:
                self._error(message)
                return
        else:
            self._error("Invalid arguments. Use: notes delete <note-id> OR notes delete <category> <title>")
            return

        # Get note info
        note = self.manager.storage.get_note(note_id)
        if not note:
            self._error(f"Note with ID '{note_id}' not found")
            return

        # Confirm deletion
        if not args.force:
            print(f"Delete note '{note['title']}' (ID: {note_id})?")
            response = input("Type 'yes' to confirm: ")
            if response.lower() != 'yes':
                self._info("Deletion cancelled")
                return

        success, message = self.manager.delete_note(note_id)

        if success:
            self._success(message)
        else:
            self._error(message)

    def cmd_search(self, args):
        """Handle search command."""
        notes = self.manager.search_notes(args.query)

        if not notes:
            self._info(f"No notes found matching '{args.query}'")
            return

        self._info(f"Found {len(notes)} note(s) matching '{args.query}':")
        print()

        for note in notes:
            self._print_note_summary(note)
            print()

    def cmd_categories(self, args):
        """Handle categories command."""
        if args.category:
            # Show category tree under a specific prefix
            category_tree = self.manager.get_category_tree(args.category)
            if not category_tree:
                self._info(f"No categories found under '{args.category}'")
                return

            self._info(f"Categories under '{args.category}':")
            for cat, count in sorted(category_tree.items()):
                # Calculate indentation based on depth from prefix
                if cat == args.category:
                    indent = ""
                else:
                    remaining = cat[len(args.category):].lstrip('/')
                    depth = remaining.count('/')
                    indent = "  " * (depth + 1)

                print(f"{indent}{cat} ({count} note{'s' if count != 1 else ''})")
        else:
            # Show all categories with note counts
            category_tree = self.manager.get_category_tree()
            if not category_tree:
                self._info("No categories found")
                return

            self._info("All categories:")
            for cat, count in sorted(category_tree.items()):
                print(f"  {cat} ({count} note{'s' if count != 1 else ''})")

    def cmd_info(self, args):
        """Handle info command."""
        notes_dir = get_notes_directory()
        all_notes = self.manager.list_notes()
        encrypted_notes = sum(1 for n in all_notes if n.get('encrypted'))
        categories = self.manager.get_categories()

        print("Notes Application Info")
        print("=" * 60)
        print(f"Notes directory: {notes_dir}")
        print(f"Total notes: {len(all_notes)}")
        print(f"Encrypted notes: {encrypted_notes}")
        print(f"Categories: {len(categories)}")
        print(f"GPG available: {'Yes' if self.manager.encryption.is_gpg_available() else 'No'}")

    def _print_note_summary(self, note: dict, verbose: bool = False):
        """Print a summary of a note."""
        encrypted_marker = " [ENCRYPTED]" if note.get('encrypted') else ""
        print(f"[{note['id'][:8]}] {note['title']}{encrypted_marker}")

        if verbose or note.get('category'):
            if note.get('category'):
                print(f"  Category: {note['category']}")

        if verbose:
            print(f"  Created: {self._format_datetime(note.get('created_at'))}")
            print(f"  Updated: {self._format_datetime(note.get('updated_at'))}")

    def _get_content_from_editor(self) -> Optional[str]:
        """Open an editor to get content from the user."""
        import tempfile
        import subprocess
        import os

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as tf:
            temp_file = tf.name

        try:
            editor = os.environ.get('EDITOR', 'nano')
            subprocess.run([editor, temp_file], check=True)

            with open(temp_file, 'r') as f:
                content = f.read()

            return content.strip()

        except subprocess.CalledProcessError:
            return None
        except Exception:
            return None
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    @staticmethod
    def _format_datetime(dt_str: Optional[str]) -> str:
        """Format a datetime string for display."""
        if not dt_str:
            return "Unknown"

        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, AttributeError):
            return dt_str

    @staticmethod
    def _success(message: str):
        """Print a success message."""
        print(f"✓ {message}")

    @staticmethod
    def _error(message: str):
        """Print an error message."""
        print(f"✗ Error: {message}", file=sys.stderr)
        sys.exit(1)

    @staticmethod
    def _info(message: str):
        """Print an info message."""
        print(f"ℹ {message}")


def main():
    """Main entry point for the CLI."""
    cli = NotesCLI()
    cli.run()


if __name__ == '__main__':
    main()
