"""
Supabase Storage utility for uploading and managing files
"""
import os
import uuid
from flask import current_app
from supabase import create_client, Client
from werkzeug.utils import secure_filename
from PIL import Image
import io

def get_supabase_client() -> Client:
    """Initialize and return Supabase client"""
    supabase_url = current_app.config.get('SUPABASE_URL')
    supabase_key = current_app.config.get('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(supabase_url, supabase_key)

def upload_image_to_supabase(file, folder='uploads', width=800, height=600):
    """
    Upload an image file to Supabase Storage with resizing
    
    Args:
        file: The file from request.files
        folder: The folder name inside the bucket
        width: The width to resize to
        height: The height to resize to
        
    Returns:
        Tuple (binary_data, public_url)
    """
    if not file:
        return None, None
    
    try:
        # Create a unique filename
        filename = secure_filename(file.filename)
        filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Get file extension
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Open and resize the image
        img = Image.open(file.stream)
        
        # Convert RGBA to RGB if necessary (for JPEG)
        if img.mode == 'RGBA' and file_ext in ['.jpg', '.jpeg']:
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            img = rgb_img
        
        # Resize while keeping aspect ratio
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        
        # Save to bytes
        img_bytes = io.BytesIO()
        
        # Determine format
        if file_ext in ['.jpg', '.jpeg']:
            img.save(img_bytes, format='JPEG', quality=85)
            content_type = 'image/jpeg'
        elif file_ext == '.png':
            img.save(img_bytes, format='PNG', optimize=True)
            content_type = 'image/png'
        elif file_ext == '.webp':
            img.save(img_bytes, format='WEBP', quality=85)
            content_type = 'image/webp'
        else:
            img.save(img_bytes, format='PNG')
            content_type = 'image/png'
        
        img_bytes.seek(0)
        binary_data = img_bytes.getvalue()
        
        # Upload to Supabase Storage
        supabase = get_supabase_client()
        bucket_name = current_app.config.get('SUPABASE_STORAGE_BUCKET', 'bhojanaxpress')
        
        # Upload file
        file_path = f"{folder}/{filename}"
        response = supabase.storage.from_(bucket_name).upload(
            file_path,
            binary_data,
            file_options={"content-type": content_type}
        )
        
        # Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        
        current_app.logger.info(f"Image uploaded to Supabase: {public_url}")
        
        return binary_data, public_url
    
    except Exception as e:
        current_app.logger.error(f"Error uploading image to Supabase: {str(e)}")
        return None, None

def delete_image_from_supabase(file_path):
    """
    Delete an image from Supabase Storage
    
    Args:
        file_path: The path to the file in the bucket (e.g., 'uploads/filename.jpg')
        
    Returns:
        Boolean indicating success
    """
    try:
        supabase = get_supabase_client()
        bucket_name = current_app.config.get('SUPABASE_STORAGE_BUCKET', 'bhojanaxpress')
        
        # Remove the bucket URL prefix if present
        if file_path.startswith('http'):
            # Extract just the file path from the URL
            file_path = file_path.split(f'{bucket_name}/')[-1]
        
        response = supabase.storage.from_(bucket_name).remove([file_path])
        
        current_app.logger.info(f"Image deleted from Supabase: {file_path}")
        return True
    
    except Exception as e:
        current_app.logger.error(f"Error deleting image from Supabase: {str(e)}")
        return False

def get_image_url(image_url, default='/static/images/no-image.png'):
    """
    Get the appropriate image URL to display
    
    Args:
        image_url: The stored image URL
        default: Default image if none provided
        
    Returns:
        URL to display
    """
    if image_url and (image_url.startswith('http') or image_url.startswith('/static/')):
        return image_url
    else:
        return default
