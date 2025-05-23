from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
import os

def save_uploaded_file(file, directory=None):
    """
    Save an uploaded file to the specified directory
    Returns the file path relative to the upload folder
    """
    if not file:
        return None
        
    if directory is None:
        directory = current_app.config['UPLOAD_FOLDER']
    else:
        directory = os.path.join(current_app.config['UPLOAD_FOLDER'], directory)
        
    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)
    
    # Generate unique filename
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}" if file_ext else f"{uuid.uuid4().hex}"
    
    # Save file
    file_path = os.path.join(directory, unique_filename)
    file.save(file_path)
    
    # Return relative path from upload folder
    return os.path.relpath(file_path, current_app.config['UPLOAD_FOLDER'])

def get_allowed_extensions():
    """
    Returns a dictionary of allowed file extensions by type
    """
    return {
        'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'document': {'pdf', 'doc', 'docx'},
        'presentation': {'ppt', 'pptx'},
        'spreadsheet': {'xls', 'xlsx'},
    }

def is_allowed_file(filename, file_type=None):
    """
    Check if a file is allowed based on its extension
    If file_type is specified, check only against that type's extensions
    Otherwise, check against all allowed extensions
    """
    if '.' not in filename:
        return False
        
    ext = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = get_allowed_extensions()
    
    if file_type:
        return ext in allowed_extensions.get(file_type, set())
    else:
        # Check against all allowed extensions
        for extensions in allowed_extensions.values():
            if ext in extensions:
                return True
        return False

def get_file_type(filename):
    """
    Determine the file type based on extension
    """
    if '.' not in filename:
        return None
        
    ext = filename.rsplit('.', 1)[1].lower()
    allowed_extensions = get_allowed_extensions()
    
    for file_type, extensions in allowed_extensions.items():
        if ext in extensions:
            return file_type
            
    return None

def get_file_size(file_path):
    """
    Get the size of a file in bytes
    """
    return os.path.getsize(file_path)

def delete_file(file_path):
    """
    Delete a file from the filesystem
    """
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False
