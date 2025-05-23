import os
import json
import datetime
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

# Helper functions for data persistence
def load_sections():
    """Load all sections from JSON file"""
    sections_file = os.path.join(current_app.instance_path, 'sections.json')
    if not os.path.exists(sections_file):
        return []
    
    with open(sections_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_sections(sections):
    """Save sections to JSON file"""
    os.makedirs(current_app.instance_path, exist_ok=True)
    sections_file = os.path.join(current_app.instance_path, 'sections.json')
    
    with open(sections_file, 'w', encoding='utf-8') as f:
        json.dump(sections, f, ensure_ascii=False, indent=2)

def get_section_by_id(section_id):
    """Get a section by its ID"""
    sections = load_sections()
    for section in sections:
        if section['id'] == section_id:
            return section
    return None

def get_section_by_slug(slug):
    """Get a section by its slug"""
    sections = load_sections()
    for section in sections:
        if section['slug'] == slug:
            return section
    return None

def get_children_sections(parent_id):
    """Get all child sections for a parent section"""
    sections = load_sections()
    children = [s for s in sections if s['parent_id'] == parent_id]
    children.sort(key=lambda x: x.get('order', 0))
    return children

def load_contents():
    """Load all contents from JSON file"""
    contents_file = os.path.join(current_app.instance_path, 'contents.json')
    if not os.path.exists(contents_file):
        return []
    
    with open(contents_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_contents(contents):
    """Save contents to JSON file"""
    os.makedirs(current_app.instance_path, exist_ok=True)
    contents_file = os.path.join(current_app.instance_path, 'contents.json')
    
    with open(contents_file, 'w', encoding='utf-8') as f:
        json.dump(contents, f, ensure_ascii=False, indent=2)

def get_content_by_id(content_id):
    """Get a content by its ID"""
    contents = load_contents()
    for content in contents:
        if content['id'] == content_id:
            return content
    return None

def get_content_by_section_id(section_id):
    """Get all contents for a section"""
    contents = load_contents()
    section_contents = [c for c in contents if c['section_id'] == section_id]
    section_contents.sort(key=lambda x: x.get('order', 0))
    return section_contents

def load_media():
    """Load all media from JSON file"""
    media_file = os.path.join(current_app.instance_path, 'media.json')
    if not os.path.exists(media_file):
        return []
    
    with open(media_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_media(media_items):
    """Save media to JSON file"""
    os.makedirs(current_app.instance_path, exist_ok=True)
    media_file = os.path.join(current_app.instance_path, 'media.json')
    
    with open(media_file, 'w', encoding='utf-8') as f:
        json.dump(media_items, f, ensure_ascii=False, indent=2)

def get_media_by_id(media_id):
    """Get a media item by its ID"""
    media_items = load_media()
    for item in media_items:
        if item['id'] == media_id:
            return item
    return None

# User authentication functions
def load_users():
    """Load all users from JSON file"""
    data_folder = os.path.join(current_app.instance_path)
    os.makedirs(data_folder, exist_ok=True)
    users_file = os.path.join(data_folder, 'users.json')
    
    if not os.path.exists(users_file):
        # Create default admin user if file doesn't exist
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump([{
                'id': '1',
                'username': 'admin',
                'password': generate_password_hash('admin')
            }], f, ensure_ascii=False)
    
    with open(users_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    """Save users to JSON file"""
    os.makedirs(current_app.instance_path, exist_ok=True)
    users_file = os.path.join(current_app.instance_path, 'users.json')
    
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_user_by_id(user_id):
    """Get a user by ID"""
    users = load_users()
    for user in users:
        if user['id'] == user_id:
            return user
    return None

def get_user_by_username(username):
    """Get a user by username"""
    users = load_users()
    for user in users:
        if user['username'] == username:
            return user
    return None
