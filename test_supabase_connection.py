"""
Test Supabase PostgreSQL connection and storage
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from supabase import create_client

def test_database_connection():
    """Test PostgreSQL database connection"""
    print("\n" + "="*60)
    print("Testing Supabase PostgreSQL Connection")
    print("="*60 + "\n")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Test database connection
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            print(f"✅ Database URI configured: {db_uri.split('@')[0]}@***")
            
            # Try to connect
            db.engine.connect()
            print("✅ Successfully connected to Supabase PostgreSQL!")
            
            # Create tables
            db.create_all()
            print("✅ Database tables created/verified successfully!")
            
            return True
            
        except Exception as e:
            print(f"❌ Database connection error: {str(e)}")
            return False

def test_supabase_storage():
    """Test Supabase Storage connection"""
    print("\n" + "="*60)
    print("Testing Supabase Storage Connection")
    print("="*60 + "\n")
    
    try:
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_KEY')
        bucket_name = os.environ.get('SUPABASE_STORAGE_BUCKET', 'bhojanaxpress')
        
        if not supabase_url or not supabase_key:
            print("❌ Supabase credentials not configured in .env")
            return False
        
        print(f"✅ Supabase URL: {supabase_url}")
        print(f"✅ Supabase Bucket: {bucket_name}")
        
        # Create Supabase client
        supabase = create_client(supabase_url, supabase_key)
        
        # Test storage access
        buckets = supabase.storage.list_buckets()
        print(f"✅ Successfully connected to Supabase Storage!")
        print(f"📦 Available buckets: {[b.name for b in buckets]}")
        
        # Check if our bucket exists
        bucket_exists = any(b.name == bucket_name for b in buckets)
        if bucket_exists:
            print(f"✅ Bucket '{bucket_name}' exists and is ready!")
        else:
            print(f"⚠️ Bucket '{bucket_name}' not found. Please create it in Supabase dashboard.")
            print(f"   Go to: {supabase_url}/project/_/storage/buckets")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase Storage error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("\n🚀 BhojanXpress Supabase Setup Test")
    print("="*60 + "\n")
    
    db_success = test_database_connection()
    storage_success = test_supabase_storage()
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"{'✅' if db_success else '❌'} PostgreSQL Database: {'Connected' if db_success else 'Failed'}")
    print(f"{'✅' if storage_success else '❌'} Supabase Storage: {'Connected' if storage_success else 'Failed'}")
    print("="*60 + "\n")
    
    if db_success and storage_success:
        print("🎉 All tests passed! Your app is ready to use Supabase!")
        print("\nNext steps:")
        print("1. Create the storage bucket 'bhojanaxpress' in Supabase dashboard")
        print("2. Set bucket to public (for image URLs)")
        print("3. Run: python run.py (to start the app)")
        print("4. Update Render environment variables with Supabase credentials")
    else:
        print("⚠️ Some tests failed. Please check:")
        print("1. .env file has correct Supabase credentials")
        print("2. DATABASE_URL has correct password")
        print("3. Supabase project is active")
        print("4. Storage bucket 'bhojanaxpress' exists")

if __name__ == '__main__':
    main()
