from flask import Blueprint, render_template, request, redirect, url_for, abort
from src.data_helpers import load_sections, get_section_by_slug, get_children_sections, get_content_by_section_id
from flask import current_app
import os

public = Blueprint('public', __name__)

@public.route('/')
def index():
    # Get all sections
    all_sections = load_sections()
    
    # Get root sections for navigation
    root_sections = [s for s in all_sections if s['parent_id'] is None]
    root_sections.sort(key=lambda x: x.get('order', 0))
    
    # Build hierarchical structure for navigation
    nav_sections = []
    for section in root_sections:
        children = [s for s in all_sections if s['parent_id'] == section['id']]
        children.sort(key=lambda x: x.get('order', 0))
        
        section_with_children = {
            'id': section['id'],
            'title': section['title'],
            'slug': section['slug'],
            'children': children
        }
        nav_sections.append(section_with_children)
    
    # Get home page content
    home_section = next((s for s in all_sections if s['slug'] == 'home'), None)
    home_contents = []
    if home_section:
        home_contents = get_content_by_section_id(home_section['id'])
        home_contents.sort(key=lambda x: x.get('order', 0))
    
    return render_template('public/index.html', 
                          nav_sections=nav_sections,
                          contents=home_contents,
                          current_section=home_section)

@public.route('/<slug>')
def section(slug):
    # Get all sections
    all_sections = load_sections()
    
    # Get root sections for navigation
    root_sections = [s for s in all_sections if s['parent_id'] is None]
    root_sections.sort(key=lambda x: x.get('order', 0))
    
    # Build hierarchical structure for navigation
    nav_sections = []
    for section in root_sections:
        children = [s for s in all_sections if s['parent_id'] == section['id']]
        children.sort(key=lambda x: x.get('order', 0))
        
        section_with_children = {
            'id': section['id'],
            'title': section['title'],
            'slug': section['slug'],
            'children': children
        }
        nav_sections.append(section_with_children)
    
    # Get requested section
    current_section = get_section_by_slug(slug)
    if not current_section:
        abort(404)
    
    # Get section content
    contents = get_content_by_section_id(current_section['id'])
    contents.sort(key=lambda x: x.get('order', 0))
    
    # Get child sections if any
    child_sections = [s for s in all_sections if s['parent_id'] == current_section['id']]
    child_sections.sort(key=lambda x: x.get('order', 0))
    
    return render_template('public/section.html', 
                          nav_sections=nav_sections,
                          current_section=current_section,
                          contents=contents,
                          child_sections=child_sections)

@public.route('/uploads/<filename>')
def uploaded_file(filename):
    return redirect(url_for('static', filename=f'uploads/{filename}'))
