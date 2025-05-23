from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
import os
import json
import uuid
import datetime
from werkzeug.utils import secure_filename
import mimetypes
import base64
import urllib.request
from src.data_helpers import (
    load_sections, save_sections, get_section_by_id, get_section_by_slug, get_children_sections,
    load_contents, save_contents, get_content_by_id, get_content_by_section_id,
    load_media, save_media, get_media_by_id
)

admin = Blueprint('admin', __name__)

@admin.route('/')
@login_required
def dashboard():
    sections = load_sections()
    contents = load_contents()
    media_items = load_media()
    
    sections_count = len(sections)
    contents_count = len(contents)
    media_count = len(media_items)
    
    return render_template('admin/dashboard.html', 
                          sections_count=sections_count,
                          contents_count=contents_count,
                          media_count=media_count)

@admin.route('/sections')
@login_required
def sections():
    # Get all sections
    all_sections = load_sections()
    
    # Get root sections
    root_sections = [s for s in all_sections if s['parent_id'] is None]
    root_sections.sort(key=lambda x: x.get('order', 0))
    
    # Build hierarchical structure
    hierarchical_sections = []
    for section in root_sections:
        children = [s for s in all_sections if s['parent_id'] == section['id']]
        children.sort(key=lambda x: x.get('order', 0))
        
        section_with_children = {
            'id': section['id'],
            'title': section['title'],
            'slug': section['slug'],
            'order': section.get('order', 0),
            'children': children
        }
        hierarchical_sections.append(section_with_children)
    
    return render_template('admin/sections.html', sections=hierarchical_sections)

@admin.route('/sections/new', methods=['GET', 'POST'])
@login_required
def new_section():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        slug = request.form.get('slug', '').strip()
        parent_id = request.form.get('parent_id') or None
        
        if not title or not slug:
            flash('العنوان والرابط مطلوبان', 'error')
            sections = load_sections()
            return render_template('admin/section_form.html', sections=sections)
        
        # Check if slug is unique
        all_sections = load_sections()
        if any(s['slug'] == slug for s in all_sections):
            flash('الرابط موجود بالفعل، يرجى اختيار رابط آخر', 'error')
            return render_template('admin/section_form.html', sections=all_sections)
        
        # Determine order (place at end of siblings)
        siblings = [s for s in all_sections if s['parent_id'] == parent_id]
        max_order = max([s.get('order', 0) for s in siblings]) if siblings else 0
        
        # Create new section
        new_section = {
            'id': str(uuid.uuid4()),
            'title': title,
            'slug': slug,
            'parent_id': parent_id,
            'order': max_order + 1,
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat()
        }
        
        all_sections.append(new_section)
        save_sections(all_sections)
        
        flash('تم إنشاء القسم بنجاح', 'success')
        return redirect(url_for('admin.sections'))
    
    sections = load_sections()
    return render_template('admin/section_form.html', sections=sections)

@admin.route('/sections/edit/<section_id>', methods=['GET', 'POST'])
@login_required
def edit_section(section_id):
    all_sections = load_sections()
    section = next((s for s in all_sections if s['id'] == section_id), None)
    
    if not section:
        flash('القسم غير موجود', 'error')
        return redirect(url_for('admin.sections'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        slug = request.form.get('slug', '').strip()
        parent_id = request.form.get('parent_id') or None
        
        if not title or not slug:
            flash('العنوان والرابط مطلوبان', 'error')
            return render_template('admin/section_form.html', section=section, sections=all_sections)
        
        # Check if slug is unique (except for this section)
        if any(s['slug'] == slug and s['id'] != section_id for s in all_sections):
            flash('الرابط موجود بالفعل، يرجى اختيار رابط آخر', 'error')
            return render_template('admin/section_form.html', section=section, sections=all_sections)
        
        # Update section
        for s in all_sections:
            if s['id'] == section_id:
                s['title'] = title
                s['slug'] = slug
                s['parent_id'] = parent_id
                s['updated_at'] = datetime.datetime.now().isoformat()
                break
        
        save_sections(all_sections)
        
        flash('تم تحديث القسم بنجاح', 'success')
        return redirect(url_for('admin.sections'))
    
    return render_template('admin/section_form.html', section=section, sections=all_sections)

@admin.route('/sections/delete/<section_id>', methods=['POST'])
@login_required
def delete_section(section_id):
    all_sections = load_sections()
    
    # Check if section has children
    if any(s['parent_id'] == section_id for s in all_sections):
        flash('لا يمكن حذف قسم يحتوي على أقسام فرعية', 'error')
        return redirect(url_for('admin.sections'))
    
    # Delete section
    all_sections = [s for s in all_sections if s['id'] != section_id]
    save_sections(all_sections)
    
    # Delete section contents
    all_contents = load_contents()
    all_contents = [c for c in all_contents if c['section_id'] != section_id]
    save_contents(all_contents)
    
    flash('تم حذف القسم بنجاح', 'success')
    return redirect(url_for('admin.sections'))

@admin.route('/contents')
@login_required
def contents():
    section_id = request.args.get('section_id')
    
    all_contents = load_contents()
    all_sections = load_sections()
    
    if section_id:
        contents = [c for c in all_contents if c['section_id'] == section_id]
    else:
        contents = all_contents
    
    # Sort by order
    contents.sort(key=lambda x: x.get('order', 0))
    
    # Add section info to contents
    for content in contents:
        section = next((s for s in all_sections if s['id'] == content['section_id']), None)
        content['section_title'] = section['title'] if section else 'غير معروف'
    
    return render_template('admin/contents.html', contents=contents, sections=all_sections)

@admin.route('/contents/new', methods=['GET', 'POST'])
@login_required
def new_content():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content_html = request.form.get('content_html', '')
        section_id = request.form.get('section_id')
        
        if not title or not section_id:
            flash('العنوان والقسم مطلوبان', 'error')
            sections = load_sections()
            return render_template('admin/content_form.html', sections=sections)
        
        # Determine order (place at end of siblings)
        all_contents = load_contents()
        siblings = [c for c in all_contents if c['section_id'] == section_id]
        max_order = max([c.get('order', 0) for c in siblings]) if siblings else 0
        
        # Create new content
        new_content = {
            'id': str(uuid.uuid4()),
            'title': title,
            'body': content_html,
            'section_id': section_id,
            'content_type': 'text',
            'order': max_order + 1,
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat()
        }
        
        all_contents.append(new_content)
        save_contents(all_contents)
        
        flash('تم إنشاء المحتوى بنجاح', 'success')
        return redirect(url_for('admin.contents'))
    
    sections = load_sections()
    return render_template('admin/content_form.html', sections=sections)

@admin.route('/contents/edit/<content_id>', methods=['GET', 'POST'])
@login_required
def edit_content(content_id):
    all_contents = load_contents()
    content = next((c for c in all_contents if c['id'] == content_id), None)
    
    if not content:
        flash('المحتوى غير موجود', 'error')
        return redirect(url_for('admin.contents'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content_html = request.form.get('content_html', '')
        section_id = request.form.get('section_id')
        
        if not title or not section_id:
            flash('العنوان والقسم مطلوبان', 'error')
            sections = load_sections()
            return render_template('admin/content_form.html', content=content, sections=sections)
        
        # Update content
        for c in all_contents:
            if c['id'] == content_id:
                c['title'] = title
                c['body'] = content_html
                c['section_id'] = section_id
                c['updated_at'] = datetime.datetime.now().isoformat()
                break
        
        save_contents(all_contents)
        
        flash('تم تحديث المحتوى بنجاح', 'success')
        return redirect(url_for('admin.contents'))
    
    sections = load_sections()
    return render_template('admin/content_form.html', content=content, sections=sections)

@admin.route('/contents/delete/<content_id>', methods=['POST'])
@login_required
def delete_content(content_id):
    all_contents = load_contents()
    
    # Delete content
    all_contents = [c for c in all_contents if c['id'] != content_id]
    save_contents(all_contents)
    
    flash('تم حذف المحتوى بنجاح', 'success')
    return redirect(url_for('admin.contents'))

@admin.route('/media')
@login_required
def media():
    media_items = load_media()
    return render_template('admin/media.html', media_items=media_items)

@admin.route('/media/upload', methods=['GET', 'POST'])
@login_required
def upload_media():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('لم يتم اختيار ملف', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('لم يتم اختيار ملف', 'error')
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            
            # Ensure unique filename
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(file_path):
                filename = f"{base}_{counter}{ext}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                counter += 1
            
            file.save(file_path)
            
            # Determine file type
            mime_type, _ = mimetypes.guess_type(file_path)
            file_type = 'image' if mime_type and mime_type.startswith('image/') else 'document'
            
            # Create media entry
            all_media = load_media()
            new_media = {
                'id': str(uuid.uuid4()),
                'filename': filename,
                'file_path': os.path.join('uploads', filename),
                'file_type': file_type,
                'file_size': os.path.getsize(file_path),
                'uploaded_at': datetime.datetime.now().isoformat()
            }
            
            all_media.append(new_media)
            save_media(all_media)
            
            flash('تم رفع الملف بنجاح', 'success')
            return redirect(url_for('admin.media'))
    
    return render_template('admin/upload_media.html')

@admin.route('/media/delete/<media_id>', methods=['POST'])
@login_required
def delete_media(media_id):
    all_media = load_media()
    media_item = next((m for m in all_media if m['id'] == media_id), None)
    
    if not media_item:
        flash('الملف غير موجود', 'error')
        return redirect(url_for('admin.media'))
    
    # Delete file
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(media_item['file_path']))
    if os.path.exists(file_path):
        os.remove(file_path)
    
    # Remove from media list
    all_media = [m for m in all_media if m['id'] != media_id]
    save_media(all_media)
    
    flash('تم حذف الملف بنجاح', 'success')
    return redirect(url_for('admin.media'))

@admin.route('/api/media')
@login_required
def api_media():
    media_items = load_media()
    return jsonify(media_items)

@admin.route('/api/update-section-order', methods=['POST'])
@login_required
def update_section_order():
    data = request.json
    if not data or 'sections' not in data:
        return jsonify({'success': False, 'message': 'بيانات غير صالحة'})
    
    sections_data = data['sections']
    all_sections = load_sections()
    
    # Update order and parent_id for each section
    for section_data in sections_data:
        section_id = section_data.get('id')
        new_order = section_data.get('order')
        new_parent_id = section_data.get('parent_id')
        
        for section in all_sections:
            if section['id'] == section_id:
                section['order'] = new_order
                section['parent_id'] = new_parent_id
                break
    
    save_sections(all_sections)
    return jsonify({'success': True})

@admin.route('/api/update-content-order', methods=['POST'])
@login_required
def update_content_order():
    data = request.json
    if not data or 'contents' not in data:
        return jsonify({'success': False, 'message': 'بيانات غير صالحة'})
    
    contents_data = data['contents']
    all_contents = load_contents()
    
    # Update order for each content
    for content_data in contents_data:
        content_id = content_data.get('id')
        new_order = content_data.get('order')
        
        for content in all_contents:
            if content['id'] == content_id:
                content['order'] = new_order
                break
    
    save_contents(all_contents)
    return jsonify({'success': True})
