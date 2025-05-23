from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import uuid
import datetime
import base64
from functools import wraps

# Pure Python alternatives to Pillow
import io
import re
import mimetypes
import urllib.request

# Import User class from auth.py
from src.auth import User

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    app.config['DATA_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    # Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DATA_FOLDER'], exist_ok=True)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)
    
    # Register custom Jinja2 filters
    @app.template_filter('datetime')
    def format_datetime(value, format='%Y-%m-%d %H:%M'):
        if isinstance(value, str):
            try:
                value = datetime.datetime.fromisoformat(value)
            except ValueError:
                return value
        return value.strftime(format) if value else ''
    
    # Register blueprints
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    from .public import public as public_blueprint
    app.register_blueprint(public_blueprint)
    
    # Initialize data if not exists
    with app.app_context():
        init_data(app)
    
    return app

def init_data(app):
    # Create instance folder if not exists
    os.makedirs(app.instance_path, exist_ok=True)
    
    # Import here to avoid circular imports
    from src.data_helpers import load_users, load_sections, save_sections
    
    # Create sections.json if not exists
    sections_file = os.path.join(app.instance_path, 'sections.json')
    if not os.path.exists(sections_file):
        with open(sections_file, 'w', encoding='utf-8') as f:
            json.dump([
                {
                    'id': str(uuid.uuid4()),
                    'title': 'الصفحة الرئيسية',
                    'slug': 'home',
                    'parent_id': None,
                    'order': 0,
                    'created_at': datetime.datetime.now().isoformat()
                },
                {
                    'id': str(uuid.uuid4()),
                    'title': 'الفهرس',
                    'slug': 'index',
                    'parent_id': None,
                    'order': 1,
                    'created_at': datetime.datetime.now().isoformat()
                },
                {
                    'id': str(uuid.uuid4()),
                    'title': 'الملف الشخصي',
                    'slug': 'personal',
                    'parent_id': None,
                    'order': 2,
                    'created_at': datetime.datetime.now().isoformat()
                }
            ], f, ensure_ascii=False)
    
    # Create contents.json if not exists
    contents_file = os.path.join(app.instance_path, 'contents.json')
    if not os.path.exists(contents_file):
        with open(contents_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)
    
    # Create media.json if not exists
    media_file = os.path.join(app.instance_path, 'media.json')
    if not os.path.exists(media_file):
        with open(media_file, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False)

# Pure Python image handling functions
def is_valid_image_url(url):
    try:
        with urllib.request.urlopen(url) as response:
            content_type = response.info().get_content_type()
            return content_type.startswith('image/')
    except:
        return False

def get_image_dimensions_from_data(image_data):
    # Simple dimension detection for common formats
    # This is a basic implementation and won't work for all image types
    try:
        if image_data.startswith(b'\xff\xd8'):  # JPEG
            # Find SOF marker
            i = 2
            while i < len(image_data):
                if image_data[i] == 0xFF and image_data[i+1] in (0xC0, 0xC1, 0xC2):
                    height = (image_data[i+5] << 8) + image_data[i+6]
                    width = (image_data[i+7] << 8) + image_data[i+8]
                    return width, height
                i += 1
        elif image_data.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG
            # Width is at offset 16, height at offset 20
            width = int.from_bytes(image_data[16:20], byteorder='big')
            height = int.from_bytes(image_data[20:24], byteorder='big')
            return width, height
    except:
        pass
    
    # Default dimensions if detection fails
    return 300, 200

def create_thumbnail_data(image_data, max_size=(200, 200)):
    # In a pure Python environment without Pillow, we can't easily create thumbnails
    # Instead, we'll just return the original data and rely on browser scaling
    # In a real implementation, you might use a web service API for this
    return image_data
