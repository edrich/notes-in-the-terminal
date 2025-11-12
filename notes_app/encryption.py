"""
Encryption module for handling GPG operations.
"""
import subprocess
import sys
from typing import Optional, Tuple


class GPGEncryption:
    """Handles GPG encryption and decryption of notes."""

    @staticmethod
    def is_gpg_available() -> bool:
        """Check if GPG is available on the system."""
        try:
            result = subprocess.run(
                ['gpg', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @staticmethod
    def list_keys() -> Tuple[bool, str]:
        """
        List available GPG keys.

        Returns:
            Tuple of (success, output)
        """
        try:
            result = subprocess.run(
                ['gpg', '--list-keys'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0, result.stdout
        except subprocess.SubprocessError as e:
            return False, str(e)

    @staticmethod
    def encrypt(content: str, recipient: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Encrypt content using GPG.

        Args:
            content: The text content to encrypt
            recipient: GPG key recipient (email/key ID). If None, uses symmetric encryption.

        Returns:
            Tuple of (success, encrypted_content, error_message)
        """
        if not GPGEncryption.is_gpg_available():
            return False, "", "GPG is not available on this system"

        try:
            if recipient:
                # Asymmetric encryption with recipient's public key
                cmd = [
                    'gpg',
                    '--encrypt',
                    '--armor',
                    '--recipient', recipient,
                    '--trust-model', 'always'
                ]
            else:
                # Symmetric encryption (password-based)
                cmd = [
                    'gpg',
                    '--symmetric',
                    '--armor',
                    '--batch',
                    '--passphrase-fd', '0'
                ]

            result = subprocess.run(
                cmd,
                input=content,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return True, result.stdout, ""
            else:
                return False, "", result.stderr

        except subprocess.SubprocessError as e:
            return False, "", str(e)

    @staticmethod
    def decrypt(encrypted_content: str) -> Tuple[bool, str, str]:
        """
        Decrypt GPG-encrypted content.

        Args:
            encrypted_content: The encrypted content

        Returns:
            Tuple of (success, decrypted_content, error_message)
        """
        if not GPGEncryption.is_gpg_available():
            return False, "", "GPG is not available on this system"

        try:
            cmd = ['gpg', '--decrypt', '--quiet']

            result = subprocess.run(
                cmd,
                input=encrypted_content,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return True, result.stdout, ""
            else:
                return False, "", result.stderr

        except subprocess.SubprocessError as e:
            return False, "", str(e)

    @staticmethod
    def encrypt_interactive(content: str, recipient: Optional[str] = None) -> Tuple[bool, str, str]:
        """
        Encrypt content with interactive password prompt for symmetric encryption.

        Args:
            content: The text content to encrypt
            recipient: GPG key recipient. If None, prompts for password.

        Returns:
            Tuple of (success, encrypted_content, error_message)
        """
        if not GPGEncryption.is_gpg_available():
            return False, "", "GPG is not available on this system"

        try:
            if recipient:
                # Use non-interactive encryption with recipient
                return GPGEncryption.encrypt(content, recipient)
            else:
                # Interactive symmetric encryption
                # Create a temporary process that allows GPG to prompt for password
                cmd = [
                    'gpg',
                    '--symmetric',
                    '--armor'
                ]

                # Use a pipe to send content to stdin
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                stdout, stderr = process.communicate(input=content, timeout=60)

                if process.returncode == 0:
                    return True, stdout, ""
                else:
                    return False, "", stderr

        except subprocess.SubprocessError as e:
            return False, "", str(e)
