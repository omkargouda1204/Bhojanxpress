"""
Interactive Setup Script for BhojanXpress Supabase Configuration
This script will help you get your database password and create the storage bucket.
"""

import os
import sys
from dotenv import load_dotenv, set_key

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def main():
    print_header("🚀 BhojanXpress Supabase Setup Helper")
    
    # Check if .env exists
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        print("❌ .env file not found!")
        return
    
    load_dotenv()
    current_db_url = os.getenv('DATABASE_URL', '')
    
    print("📋 Current Status:")
    print(f"   Database URL: {current_db_url[:50]}...")
    
    if "your_supabase_db_password" in current_db_url:
        print("\n⚠️  Database password is still a placeholder!\n")
        print("🔐 To get your real password:")
        print("\n   1. Open this URL in your browser:")
        print("      https://supabase.com/dashboard/project/bkbezckcmpitcglonyyz/settings/database")
        print("\n   2. Scroll down to 'Connection string' section")
        print("   3. Click the 'URI' tab")
        print("   4. You'll see something like:")
        print("      postgresql://postgres.bkbezckcmpitcglonyyz:[YOUR-PASSWORD]@aws-...")
        print("\n   5. Copy the password (the part in [YOUR-PASSWORD])")
        print("\n" + "-"*60)
        
        password = input("\n📝 Paste your Supabase database password here: ").strip()
        
        if password and password != "your_supabase_db_password":
            # Update .env file
            new_db_url = f"postgresql://postgres.bkbezckcmpitcglonyyz:{password}@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
            
            # Read .env and update
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith('DATABASE_URL='):
                        f.write(f'DATABASE_URL={new_db_url}\n')
                    else:
                        f.write(line)
            
            print("\n✅ Password updated in .env file!")
        else:
            print("\n❌ No valid password provided. Please try again.")
            return
    else:
        print("✅ Database URL looks good!")
    
    print_header("📦 Storage Bucket Setup")
    print("You need to create the 'bhojanaxpress' bucket in Supabase:")
    print("\n1. Open this URL:")
    print("   https://supabase.com/dashboard/project/bkbezckcmpitcglonyyz/storage/buckets")
    print("\n2. Click 'Create a new bucket' button")
    print("3. Enter bucket name: bhojanaxpress")
    print("4. ⚠️  IMPORTANT: Toggle 'Public bucket' to ON (green)")
    print("5. Click 'Create bucket'")
    
    input("\n✅ Press Enter once you've created the bucket...")
    
    print_header("🗄️  Database Tables Setup")
    print("You need to create the database tables:")
    print("\n1. Open this URL:")
    print("   https://supabase.com/dashboard/project/bkbezckcmpitcglonyyz/sql/new")
    print("\n2. Open the file: database/postgresql_schema.sql")
    print("3. Copy ALL its content")
    print("4. Paste into the Supabase SQL Editor")
    print("5. Click 'Run' (or press Ctrl+Enter)")
    print("6. You should see 'Success. No rows returned'")
    
    input("\n✅ Press Enter once you've created the tables...")
    
    print_header("🧪 Testing Connection")
    print("Now let's test if everything works...")
    print("\nRun this command in a new terminal:")
    print("   python test_supabase_connection.py")
    print("\nYou should see:")
    print("   ✅ PostgreSQL Database: Connected")
    print("   ✅ Supabase Storage: Connected")
    
    print("\n" + "="*60)
    print("🎉 Setup complete! Now you can:")
    print("   1. Test: python test_supabase_connection.py")
    print("   2. Run: python run.py")
    print("   3. Visit: http://localhost:5000")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled.")
        sys.exit(0)
