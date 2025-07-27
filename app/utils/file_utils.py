"""Utility functions for file handling in the airspace-viewer application.

This module provides helpers for validating file extensions, generating secure file paths,
cleaning up temporary files, and retrieving the default airspace file path.
"""

import os

from werkzeug.utils import secure_filename


def allowed_file(filename: str, allowed_extensions: set[str] | list[str]) -> bool:
    """Check if the uploaded file has an allowed extension.

    Args:
        filename (str): The name of the file to check.
        allowed_extensions (set or list): Allowed file extensions (lowercase, without dot).

    Returns:
        bool: True if the file has an allowed extension, False otherwise.
    """
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def get_secure_filepath(filename: str, upload_folder: str) -> str:
    """Generate a secure file path for an uploaded file.

    Args:
        filename (str): The original filename.
        upload_folder (str): The directory where the file should be saved.

    Returns:
        str: The full, secure file path for saving the file.
    """
    filename = secure_filename(filename)
    return os.path.join(upload_folder, filename)


def cleanup_temp_file(filepath: str) -> None:
    """Safely remove a temporary file if it exists.

    Args:
        filepath (str): The path to the file to remove.

    Returns:
        None

    Warns:
        Prints a warning if the file could not be removed.
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Warning: Could not remove temp file {filepath}: {e}")


def get_default_airspace_path() -> str:
    """Get the path to the default airspace file.

    Returns:
        str: The path to the default Switzerland.txt airspace file.
    """
    return os.path.join(os.path.dirname(__file__), "..", "examples", "Switzerland.txt")
