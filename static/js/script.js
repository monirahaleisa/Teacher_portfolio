// Main script for teacher portfolio CMS

document.addEventListener('DOMContentLoaded', function() {
    // Sidebar resizer functionality
    const sidebar = document.querySelector('.sidebar');
    const sidebarResizer = document.createElement('div');
    sidebarResizer.className = 'sidebar-resizer';
    
    if (sidebar) {
        sidebar.appendChild(sidebarResizer);
        
        sidebarResizer.addEventListener('mousedown', initResize);
        
        function initResize(e) {
            window.addEventListener('mousemove', resize);
            window.addEventListener('mouseup', stopResize);
            
            // Add a class to prevent text selection during resize
            document.body.classList.add('resizing');
        }
        
        function resize(e) {
            // Calculate new width based on mouse position
            // For RTL layout, we need to calculate from right edge
            const containerWidth = document.querySelector('.container').offsetWidth;
            const newWidth = containerWidth - e.clientX;
            
            // Set minimum and maximum width
            if (newWidth > 150 && newWidth < 400) {
                sidebar.style.width = newWidth + 'px';
            }
        }
        
        function stopResize() {
            window.removeEventListener('mousemove', resize);
            window.removeEventListener('mouseup', stopResize);
            document.body.classList.remove('resizing');
            
            // Save sidebar width preference in localStorage
            localStorage.setItem('sidebarWidth', sidebar.style.width);
        }
        
        // Restore saved sidebar width if available
        const savedWidth = localStorage.getItem('sidebarWidth');
        if (savedWidth) {
            sidebar.style.width = savedWidth;
        }
    }
    
    // Media library integration for content editor
    setupMediaLibrary();
    
    // Section ordering with drag and drop
    setupSectionOrdering();
    
    // Initialize tooltips
    initTooltips();
});

// Media library integration
function setupMediaLibrary() {
    const mediaButton = document.getElementById('media-library-button');
    const mediaModal = document.getElementById('media-library-modal');
    
    if (mediaButton && mediaModal) {
        // Open media library modal
        mediaButton.addEventListener('click', function() {
            mediaModal.style.display = 'block';
            loadMediaItems();
        });
        
        // Close modal when clicking the close button
        const closeButton = mediaModal.querySelector('.close-button');
        if (closeButton) {
            closeButton.addEventListener('click', function() {
                mediaModal.style.display = 'none';
            });
        }
        
        // Close modal when clicking outside the content
        window.addEventListener('click', function(event) {
            if (event.target === mediaModal) {
                mediaModal.style.display = 'none';
            }
        });
    }
}

// Load media items via AJAX
function loadMediaItems() {
    const mediaContainer = document.getElementById('media-items-container');
    
    if (mediaContainer) {
        fetch('/admin/api/media')
            .then(response => response.json())
            .then(data => {
                mediaContainer.innerHTML = '';
                
                if (data.length === 0) {
                    mediaContainer.innerHTML = '<p class="empty-message">لا توجد وسائط متاحة. قم برفع بعض الملفات أولاً.</p>';
                    return;
                }
                
                data.forEach(item => {
                    const mediaItem = document.createElement('div');
                    mediaItem.className = 'media-item';
                    
                    let preview = '';
                    if (item.file_type === 'image') {
                        preview = `<img src="/uploads/${item.filename}" alt="${item.filename}">`;
                    } else {
                        preview = `<div class="document-icon"><i class="fas fa-file"></i></div>`;
                    }
                    
                    mediaItem.innerHTML = `
                        <div class="media-preview">${preview}</div>
                        <div class="media-info">
                            <h3>${item.filename}</h3>
                            <button class="btn btn-sm btn-primary insert-media" data-path="/uploads/${item.filename}" data-type="${item.file_type}">إدراج</button>
                        </div>
                    `;
                    
                    mediaContainer.appendChild(mediaItem);
                });
                
                // Add event listeners to insert buttons
                document.querySelectorAll('.insert-media').forEach(button => {
                    button.addEventListener('click', function() {
                        insertMedia(this.dataset.path, this.dataset.type);
                        document.getElementById('media-library-modal').style.display = 'none';
                    });
                });
            })
            .catch(error => {
                console.error('Error loading media:', error);
                mediaContainer.innerHTML = '<p class="error-message">حدث خطأ أثناء تحميل الوسائط. يرجى المحاولة مرة أخرى.</p>';
            });
    }
}

// Insert media into TinyMCE editor
function insertMedia(path, type) {
    if (tinymce && tinymce.activeEditor) {
        if (type === 'image') {
            tinymce.activeEditor.execCommand('mceInsertContent', false, `<img src="${path}" alt="" style="max-width: 100%; height: auto;" />`);
        } else {
            const filename = path.split('/').pop();
            tinymce.activeEditor.execCommand('mceInsertContent', false, `<a href="${path}" target="_blank">${filename}</a>`);
        }
    }
}

// Section ordering with drag and drop
function setupSectionOrdering() {
    const sectionsList = document.getElementById('sections-list');
    
    if (sectionsList && typeof Sortable !== 'undefined') {
        Sortable.create(sectionsList, {
            handle: '.drag-handle',
            animation: 150,
            onEnd: function(evt) {
                updateSectionOrder();
            }
        });
        
        // Also setup for child sections
        document.querySelectorAll('.child-sections').forEach(childList => {
            Sortable.create(childList, {
                handle: '.drag-handle',
                animation: 150,
                onEnd: function(evt) {
                    updateSectionOrder();
                }
            });
        });
    }
}

// Update section order after drag and drop
function updateSectionOrder() {
    const sections = [];
    
    // Get all root sections
    document.querySelectorAll('#sections-list > .section-item').forEach((item, index) => {
        const sectionId = item.dataset.id;
        sections.push({
            id: sectionId,
            order: index,
            parent_id: null
        });
        
        // Get child sections if any
        const childList = item.querySelector('.child-sections');
        if (childList) {
            childList.querySelectorAll('.section-item').forEach((childItem, childIndex) => {
                const childId = childItem.dataset.id;
                sections.push({
                    id: childId,
                    order: childIndex,
                    parent_id: sectionId
                });
            });
        }
    });
    
    // Send updated order to server
    fetch('/admin/api/update-section-order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sections: sections }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('تم تحديث ترتيب الأقسام بنجاح', 'success');
        } else {
            showNotification('حدث خطأ أثناء تحديث ترتيب الأقسام', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating section order:', error);
        showNotification('حدث خطأ أثناء تحديث ترتيب الأقسام', 'error');
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Hide and remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Initialize tooltips
function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    
    tooltips.forEach(tooltip => {
        tooltip.addEventListener('mouseenter', function() {
            const tooltipText = this.dataset.tooltip;
            
            const tooltipElement = document.createElement('div');
            tooltipElement.className = 'tooltip';
            tooltipElement.textContent = tooltipText;
            
            document.body.appendChild(tooltipElement);
            
            const rect = this.getBoundingClientRect();
            tooltipElement.style.top = rect.bottom + 10 + 'px';
            tooltipElement.style.left = rect.left + (rect.width / 2) - (tooltipElement.offsetWidth / 2) + 'px';
            
            tooltipElement.classList.add('show');
            
            this.addEventListener('mouseleave', function onMouseLeave() {
                tooltipElement.classList.remove('show');
                setTimeout(() => {
                    document.body.removeChild(tooltipElement);
                }, 300);
                
                this.removeEventListener('mouseleave', onMouseLeave);
            });
        });
    });
}
