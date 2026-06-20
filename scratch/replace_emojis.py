import os
import glob
import re

template_dir = '/Users/hariharans/Documents/intern2/eduflow-lms/templates'
files = glob.glob(os.path.join(template_dir, '**/*.html'), recursive=True)

replacements = {
    '🏆': '<i data-lucide="trophy" class="icon-inline"></i>',
    '📚': '<i data-lucide="book-open" class="icon-inline"></i>',
    '⭐': '<i data-lucide="star" class="icon-inline"></i>',
    '📄': '<i data-lucide="file-text" class="icon-inline"></i>',
    '📝': '<i data-lucide="clipboard-list" class="icon-inline"></i>'
}

for filepath in files:
    with open(filepath, 'r') as f:
        content = f.read()
    
    modified = content
    for emoji, tag in replacements.items():
        modified = modified.replace(emoji, tag)
        
    if modified != content:
        with open(filepath, 'w') as f:
            f.write(modified)
        print(f"Updated {filepath}")
