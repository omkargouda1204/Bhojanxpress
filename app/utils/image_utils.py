import os
from flask import current_app
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import io

def save_image(file, folder='uploads', width=800, height=600):
    """
    Save an uploaded image file with resizing
    
    Args:
        file: The file from request.files
        folder: The folder name inside static directory
        width: The width to resize to
        height: The height to resize to
        
    Returns:
        Tuple (binary_data, filename)
    """
    if not file:
        return None, None
    
    # Create a unique filename
    filename = secure_filename(file.filename)
    filename = f"{uuid.uuid4().hex}_{filename}"
    
    # Create uploads directory if it doesn't exist
    uploads_dir = os.path.join(current_app.static_folder, folder)
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Full path to save the image
    filepath = os.path.join(uploads_dir, filename)
    
    # Resize and save the image
    try:
        # Open the image using PIL
        img = Image.open(file.stream)
        
        # Resize while keeping aspect ratio
        img.thumbnail((width, height))
        
        # Save to disk
        img.save(filepath)
        
        # Get binary data for database
        with open(filepath, 'rb') as f:
            binary_data = f.read()
        
        # Return both binary data and the relative URL
        return binary_data, f'/static/{folder}/{filename}'
    
    except Exception as e:
        current_app.logger.error(f"Error saving image: {str(e)}")
        return None, None

def get_image_url_from_data(image_data, image_url):
    """
    Determine the appropriate image URL to use
    
    Args:
        image_data: Binary image data
        image_url: External or stored URL
        
    Returns:
        URL to display
    """
    if image_url and (image_url.startswith('http') or image_url.startswith('/static/')):
        return image_url
    elif image_data:
        return '/static/images/placeholder.png'  # Use a placeholder if we have data but no URL
    else:
        return '/static/images/no-image.png'  # Default no image
