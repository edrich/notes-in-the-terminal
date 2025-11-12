# Notes in the Terminal CLI Application

A powerful, feature-rich command-line notes application with support for categories, encryption, and more.

## Features

- **Create, Edit, List, and Delete Notes** - Full CRUD operations
- **Hierarchical Category Organization** - Organize notes with slash-separated categories (e.g., `work/clients/acme`)
- **GPG Encryption** - Encrypt sensitive notes using GPG
- **Search Functionality** - Search notes by title or content
- **Interactive Editing** - Edit notes using your preferred terminal editor
- **Filesystem-based Storage** - Notes stored as files for easy backup and portability

## Installation

### Prerequisites

- Python 3.6 or higher
- GPG (optional, for encryption features)
  - Ubuntu/Debian: `sudo apt-get install gnupg`
  - macOS: `brew install gnupg`
  - Fedora: `sudo dnf install gnupg`

### Install from Source

```bash
# Clone or download this repository
cd notes-in-the-terminal

# Option 1: Install using setup.py
python3 setup.py install

# Option 2: Use the script directly
chmod +x notes
# Add to your PATH or create an alias
```

## Usage

### Basic Commands

```bash
# Create a note (opens your default editor)
notes create "My First Note"

# Create a note with inline content (assigned to 'default' category)
notes create "Quick Note" -m "This is the content"

# Create a note with hierarchical categories
notes create "Meeting Notes" -c work/meetings
notes create "Client Project" -c work/clients/acme

# Create an encrypted note
notes create "Secret" --encrypt

# List top-level categories (default behavior)
notes list

# List all notes (use -a flag)
notes list -a

# List notes in a specific category (and all subcategories)
notes list work
notes list work/clients

# List with category flag (alternative syntax)
notes list -c work

# List with verbose output
notes list -v

# Show a specific note by ID
notes show <note-id>

# Show a note by category and title
notes show work/meetings "Meeting Notes"

# Edit a note interactively
notes edit <note-id> -i

# Edit note fields directly
notes edit <note-id> -t "New Title" -c personal

# Delete a note
notes delete <note-id>

# Delete without confirmation
notes delete <note-id> -f

# Search notes
notes search "keyword"

# List all categories with hierarchical view
notes categories

# List categories under a specific prefix
notes categories -c work

# Show application info
notes info
```

### Examples

```bash
# Create a quick note (assigned to 'default' category)
notes create "Quick Idea" -m "Remember to check this out"

# Create a personal note with a hierarchical category
notes create "Shopping List" -c personal/errands -m "Milk, Eggs, Bread"

# Create a work note with deep nesting
notes create "Project Plan" -c work/clients/acme/projectX -m "Q1 deliverables..."

# Create an encrypted work note
notes create "Passwords" -c work/credentials --encrypt

# List top-level categories
notes list

# List all notes
notes list -a

# List all work-related notes
notes list work

# List all notes under a specific subcategory
notes list work/clients

# Search for notes containing "meeting"
notes search "meeting"

# Show a note by category and title (case-insensitive)
notes show work/meetings "Meeting Notes"

# Edit a note using vim/nano/your default editor
notes edit abc123de -i
```

## Configuration

### Notes Storage Location

By default, notes are stored in `~/.local/share/notes/`. You can change this by setting the `NOTES_DIR` environment variable:

```bash
export NOTES_DIR="/path/to/your/notes"
```

### Default Editor

The application uses your system's default editor for interactive editing. You can set it using the `EDITOR` environment variable:

```bash
export EDITOR=vim
# or
export EDITOR=nano
# or
export EDITOR=code  # VS Code
```

## Notes Organization

Notes are organized as follows:

```
~/.local/share/notes/
├── notes_db.json          # Metadata database
├── <note-id>.txt          # Regular note files
└── <note-id>.gpg          # Encrypted note files
```

Each note has:
- **ID**: Unique identifier (UUID)
- **Title**: Note title
- **Category**: Hierarchical category (slash-separated, e.g., `work/clients/acme`). Notes without an explicit category are assigned to `default`
- **Encrypted**: Whether the note is encrypted
- **Created/Updated timestamps**

## Encryption

The application supports GPG encryption for sensitive notes:

- **Symmetric encryption** (password-based): Default when using `--encrypt`
- **Asymmetric encryption** (public key): Use `--encrypt -r <key-id-or-email>`

### Encrypting a Note

```bash
# Password-based encryption
notes create "Secret Note" --encrypt

# Encrypt for a specific GPG key
notes create "Shared Secret" --encrypt -r user@example.com
```

### Decrypting a Note

Encrypted notes are automatically decrypted when viewing:

```bash
# Will prompt for password if needed
notes show <encrypted-note-id>

# View without decrypting (shows encrypted content)
notes show <encrypted-note-id> --no-decrypt
```

## Tips and Tricks

1. **Quick Note Creation**: Use `-m` flag for quick inline notes
   ```bash
   notes create "Todo" -m "Buy groceries" -c personal
   # Omit -c to assign to 'default' category
   notes create "Quick thought" -m "Remember this"
   ```

2. **Organize with Hierarchical Categories**: Use slash-separated categories for deep organization
   ```bash
   notes create "Project X" -c work/projects/projectx
   notes list work/projects  # Lists all notes under work/projects
   ```

3. **Browse Categories or Notes**: List command shows categories by default, use `-a` for all notes
   ```bash
   notes list              # Show top-level categories (work/, personal/, etc.)
   notes list -a           # Show all notes
   notes list work         # Show all notes in work category
   ```

4. **Show Notes by Category and Title**: No need to remember note IDs
   ```bash
   notes show work/meetings "Meeting Notes"
   # Title matching is case-insensitive
   notes show work/meetings "meeting notes"
   ```

5. **Backup Your Notes**: Simply backup `~/.local/share/notes/` directory

6. **Note IDs**: You can use abbreviated IDs (first 8 characters shown in list)

7. **Environment Variables**: Set `NOTES_DIR` and `EDITOR` in your shell profile for persistence

## Troubleshooting

### GPG not found

If you see "GPG is not available", install GPG:
- Ubuntu/Debian: `sudo apt-get install gnupg`
- macOS: `brew install gnupg`
- Fedora: `sudo dnf install gnupg`

### Editor not opening

Set your `EDITOR` environment variable:
```bash
export EDITOR=nano  # or vim, emacs, etc.
```

### Permission denied

Make sure the notes script is executable:
```bash
chmod +x notes
```

## Development

### Project Structure

```
notes-in-the-terminal/
├── notes_app/
│   ├── __init__.py       # Package initialization
│   ├── cli.py            # Command-line interface
│   ├── notes.py          # Notes management (CRUD)
│   ├── storage.py        # Filesystem operations
│   ├── encryption.py     # GPG encryption
│   └── config.py         # Configuration
├── tests/
│   ├── test_storage.py   # Storage module tests
│   ├── test_notes.py     # Notes management tests
│   ├── test_encryption.py # Encryption tests
│   └── test_cli.py       # CLI tests
├── notes                 # Main executable
├── run_tests.py         # Test runner
├── setup.py             # Installation script
├── requirements.txt     # Dependencies (none!)
└── README.md           # This file
```

### Running Tests

The project includes a comprehensive test suite with 100 tests covering all features.

```bash
# Run all tests
python3 run_tests.py

# Run tests with verbose output
python3 run_tests.py -v

# Run tests quietly (minimal output)
python3 run_tests.py -q

# Run a specific test module
python3 run_tests.py -t test_storage
python3 run_tests.py -t test_notes
python3 run_tests.py -t test_encryption
python3 run_tests.py -t test_cli
```

The test suite covers:
- **Storage operations**: Saving, loading, deleting notes, partial ID resolution
- **Notes management**: CRUD operations, search, categories
- **Encryption**: GPG encryption and decryption (mocked)
- **CLI**: All command-line operations and argument parsing

### Manual Testing

```bash
# Create a test note
notes create "Test Note" -m "Testing the application"

# List it
notes list

# Edit it
notes edit <note-id> -t "Updated Test Note"

# Search for it
notes search "test"

# Delete it
notes delete <note-id>
```

## License

MIT License - Feel free to use and modify as needed.

## Contributing

Contributions are welcome! Feel free to submit issues and pull requests.
