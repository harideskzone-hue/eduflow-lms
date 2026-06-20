import os
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

@deconstructible
class FileValidator:
    def __init__(self, allowed_extensions=None, allowed_mimetypes=None, max_size=None):
        self.allowed_extensions = allowed_extensions
        self.allowed_mimetypes = allowed_mimetypes
        self.max_size = max_size

    def __call__(self, value):
        if self.max_size is not None and value.size > self.max_size:
            raise ValidationError(f'File size too large. Max size is {self.max_size} bytes.')
        if self.allowed_extensions:
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in self.allowed_extensions:
                raise ValidationError(f'Extension not supported. Allowed: {self.allowed_extensions}')

def validate_image_upload(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension. Allowed: jpg, jpeg, png, webp.')
    
    limit = 5 * 1024 * 1024 # 5 MB
    if value.size > limit:
        raise ValidationError('File size too large. Size should not exceed 5 MB.')
