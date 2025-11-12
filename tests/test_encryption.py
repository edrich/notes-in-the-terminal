"""
Tests for the encryption module.
"""
import unittest
from unittest.mock import patch, MagicMock
from notes_app.encryption import GPGEncryption


class TestGPGEncryption(unittest.TestCase):
    """Test cases for GPGEncryption class."""

    def test_is_gpg_available_true(self):
        """Test checking if GPG is available (when it is)."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = GPGEncryption.is_gpg_available()
            self.assertTrue(result)

    def test_is_gpg_available_false(self):
        """Test checking if GPG is available (when it's not)."""
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = GPGEncryption.is_gpg_available()
            self.assertFalse(result)

    def test_is_gpg_available_error(self):
        """Test checking if GPG is available (when command fails)."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = GPGEncryption.is_gpg_available()
            self.assertFalse(result)

    def test_list_keys_success(self):
        """Test listing GPG keys successfully."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='pub   rsa2048 2024-01-01 [SC]'
            )
            success, output = GPGEncryption.list_keys()
            self.assertTrue(success)
            self.assertIn('rsa2048', output)

    def test_list_keys_failure(self):
        """Test listing GPG keys when it fails."""
        import subprocess as sp
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = sp.SubprocessError('GPG error')
            success, output = GPGEncryption.list_keys()
            self.assertFalse(success)
            self.assertIn('GPG error', output)

    @patch('notes_app.encryption.GPGEncryption.is_gpg_available')
    def test_encrypt_gpg_not_available(self, mock_available):
        """Test encryption when GPG is not available."""
        mock_available.return_value = False

        success, encrypted, error = GPGEncryption.encrypt('test content')

        self.assertFalse(success)
        self.assertEqual(encrypted, '')
        self.assertIn('not available', error)

    @patch('notes_app.encryption.GPGEncryption.is_gpg_available')
    @patch('subprocess.run')
    def test_encrypt_symmetric_success(self, mock_run, mock_available):
        """Test symmetric encryption success."""
        mock_available.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='-----BEGIN PGP MESSAGE-----\nencrypted\n-----END PGP MESSAGE-----'
        )

        success, encrypted, error = GPGEncryption.encrypt('test content')

        self.assertTrue(success)
        self.assertIn('BEGIN PGP MESSAGE', encrypted)
        self.assertEqual(error, '')

    @patch('notes_app.encryption.GPGEncryption.is_gpg_available')
    @patch('subprocess.run')
    def test_encrypt_with_recipient(self, mock_run, mock_available):
        """Test encryption with recipient."""
        mock_available.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='-----BEGIN PGP MESSAGE-----\nencrypted\n-----END PGP MESSAGE-----'
        )

        success, encrypted, error = GPGEncryption.encrypt(
            'test content',
            recipient='user@example.com'
        )

        self.assertTrue(success)
        # Verify recipient was passed in the command
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn('--recipient', args)
        self.assertIn('user@example.com', args)

    @patch('notes_app.encryption.GPGEncryption.is_gpg_available')
    @patch('subprocess.run')
    def test_encrypt_failure(self, mock_run, mock_available):
        """Test encryption failure."""
        mock_available.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr='encryption failed'
        )

        success, encrypted, error = GPGEncryption.encrypt('test content')

        self.assertFalse(success)
        self.assertEqual(encrypted, '')
        self.assertIn('encryption failed', error)

    @patch('notes_app.encryption.GPGEncryption.is_gpg_available')
    def test_decrypt_gpg_not_available(self, mock_available):
        """Test decryption when GPG is not available."""
        mock_available.return_value = False

        success, decrypted, error = GPGEncryption.decrypt('encrypted content')

        self.assertFalse(success)
        self.assertEqual(decrypted, '')
        self.assertIn('not available', error)

    @patch('notes_app.encryption.GPGEncryption.is_gpg_available')
    @patch('subprocess.run')
    def test_decrypt_success(self, mock_run, mock_available):
        """Test decryption success."""
        mock_available.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='decrypted content'
        )

        success, decrypted, error = GPGEncryption.decrypt('encrypted')

        self.assertTrue(success)
        self.assertEqual(decrypted, 'decrypted content')
        self.assertEqual(error, '')

    @patch('notes_app.encryption.GPGEncryption.is_gpg_available')
    @patch('subprocess.run')
    def test_decrypt_failure(self, mock_run, mock_available):
        """Test decryption failure."""
        mock_available.return_value = True
        mock_run.return_value = MagicMock(
            returncode=1,
            stderr='decryption failed'
        )

        success, decrypted, error = GPGEncryption.decrypt('encrypted')

        self.assertFalse(success)
        self.assertEqual(decrypted, '')
        self.assertIn('decryption failed', error)

    @patch('notes_app.encryption.GPGEncryption.is_gpg_available')
    @patch('subprocess.Popen')
    def test_encrypt_interactive_symmetric(self, mock_popen, mock_available):
        """Test interactive symmetric encryption."""
        mock_available.return_value = True

        # Mock the process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (
            '-----BEGIN PGP MESSAGE-----\nencrypted\n-----END PGP MESSAGE-----',
            ''
        )
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        success, encrypted, error = GPGEncryption.encrypt_interactive('content')

        self.assertTrue(success)
        self.assertIn('BEGIN PGP MESSAGE', encrypted)

    @patch('notes_app.encryption.GPGEncryption.is_gpg_available')
    @patch('notes_app.encryption.GPGEncryption.encrypt')
    def test_encrypt_interactive_with_recipient(self, mock_encrypt, mock_available):
        """Test interactive encryption with recipient (uses non-interactive)."""
        mock_available.return_value = True
        mock_encrypt.return_value = (True, 'encrypted', '')

        success, encrypted, error = GPGEncryption.encrypt_interactive(
            'content',
            recipient='user@example.com'
        )

        self.assertTrue(success)
        mock_encrypt.assert_called_once_with('content', 'user@example.com')


if __name__ == '__main__':
    unittest.main()
