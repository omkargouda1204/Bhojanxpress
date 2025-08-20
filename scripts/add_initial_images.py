from app import create_app, db
from app.models.banner import Banner, SiteImage
from config import Config

app = create_app(Config)

with app.app_context():
    # Create initial banner
    banner = Banner(
        image_path='uploads/banners/masala_magic_biryani.jpg',
        title='Masala Magic Biryani',
        subtitle='50% Special Discount',
        order=1,
        is_active=True
    )
    
    # Create logo image
    logo = SiteImage(
        image_path='uploads/site/bhojanaxpress_logo.jpg',
        type='logo',
        is_active=True
    )
    
    db.session.add(banner)
    db.session.add(logo)
    db.session.commit()
    
    print("Initial images added successfully!")
