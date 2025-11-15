"""File upload validation utilities."""
import magic
from pathlib import Path
from werkzeug.utils import secure_filename
import uuid


# Allowed MIME types for uploads
ALLOWED_MIME_TYPES = {
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'application/pdf'
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf'}


def validate_file_extension(filename: str) -> tuple[bool, str]:
    """
    Validate file has an allowed extension.

    Args:
        filename: Original filename

    Returns:
        (is_valid, error_message)
    """
    if not filename or '.' not in filename:
        return False, "Invalid file extension"

    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"File extension '.{ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

    return True, ""


def validate_file_mime_type(file_path: Path) -> tuple[bool, str]:
    """
    Validate file MIME type using magic numbers.

    Args:
        file_path: Path to uploaded file

    Returns:
        (is_valid, error_message)
    """
    try:
        mime = magic.Magic(mime=True)
        file_mime_type = mime.from_file(str(file_path))

        if file_mime_type not in ALLOWED_MIME_TYPES:
            return False, f"Invalid file type: {file_mime_type}. Must be an image or PDF."

        return True, ""
    except Exception as e:
        return False, f"Failed to validate file type: {str(e)}"


def validate_file_not_empty(file_path: Path) -> tuple[bool, str]:
    """
    Validate file is not empty.

    Args:
        file_path: Path to uploaded file

    Returns:
        (is_valid, error_message)
    """
    if file_path.stat().st_size == 0:
        return False, "File is empty"

    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename with UUID prefix
    """
    # Use werkzeug's secure_filename to remove dangerous characters
    safe_filename = secure_filename(filename)

    # Add UUID prefix to prevent conflicts and add uniqueness
    unique_id = str(uuid.uuid4())[:8]

    if '.' in safe_filename:
        name, ext = safe_filename.rsplit('.', 1)
        return f"{unique_id}_{name}.{ext}"
    else:
        return f"{unique_id}_{safe_filename}"


def validate_upload_file(file_path: Path, original_filename: str) -> tuple[bool, str]:
    """
    Perform all validation checks on an uploaded file.

    Args:
        file_path: Path to the saved file
        original_filename: Original filename from upload

    Returns:
        (is_valid, error_message)
    """
    # Check extension
    is_valid, error = validate_file_extension(original_filename)
    if not is_valid:
        return False, error

    # Check file not empty
    is_valid, error = validate_file_not_empty(file_path)
    if not is_valid:
        return False, error

    # Check MIME type
    is_valid, error = validate_file_mime_type(file_path)
    if not is_valid:
        return False, error

    return True, ""
