import os
from flask import current_app
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import io

# Import Supabase storage functions
from app.utils.supabase_storage import upload_image_to_supabase, get_image_url

def save_image(file, folder='uploads', width=800, height=600):
    """
    Save an uploaded image file with resizing to Supabase Storage
    
    Args:
        file: The file from request.files
        folder: The folder name inside the storage bucket
        width: The width to resize to
        height: The height to resize to
        
    Returns:
        Tuple (binary_data, public_url)
    """
    if not file:
        return None, None
    
    try:
        # Upload to Supabase Storage
        binary_data, public_url = upload_image_to_supabase(file, folder, width, height)
        return binary_data, public_url
    
    except Exception as e:
        current_app.logger.error(f"Error saving image: {str(e)}")
        return None, None

def get_image_url_from_data(image_data, image_url):
    """
    Determine the appropriate image URL to use
    
    Args:
        image_data: Binary image data (deprecated, kept for backward compatibility)
        image_url: External or stored URL
        
    Returns:
        URL to display
    """
    return get_image_url(image_url, default='/static/images/no-image.png')
