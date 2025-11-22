"""
Get correct Supabase connection details
Run this to verify your connection string
"""

print("""
╔══════════════════════════════════════════════════════════════════╗
║          Getting Your Supabase Connection String                ║
╚══════════════════════════════════════════════════════════════════╝

Your Supabase project: bkbezckcmpitcglonyyz

📋 Follow these EXACT steps:

1. Go to: https://supabase.com/dashboard/project/bkbezckcmpitcglonyyz/settings/database

2. Find the section called "Connection string"

3. You'll see 3 tabs:
   - Pooler (DEFAULT - USE THIS ONE!)
   - Direct
   - URI

4. Make sure you're on the "Pooler" or "URI" tab

5. You'll see a connection string like:

   postgresql://postgres.bkbezckcmpitcglonyyz:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres

6. The password will either be:
   - Shown in plain text (click "eye" icon to reveal)
   - OR shown as [YOUR-PASSWORD] placeholder

7. If it's a placeholder, click "Reset Database Password" button

8. Copy the NEW password

9. Your .env line should look like:
   DATABASE_URL=postgresql://postgres.bkbezckcmpitcglonyyz:YOUR_PASSWORD_HERE@aws-0-ap-south-1.pooler.supabase.com:6543/postgres

⚠️  SPECIAL CHARACTERS IN PASSWORD:
   If your password contains special characters like @ # $ % & etc.,
   they MUST be URL-encoded:
   
   @  becomes  %40
   #  becomes  %23
   $  becomes  %24
   %  becomes  %25
   &  becomes  %26

📌 Example:
   Password: Omkar@27
   Encoded:  Omkar%4027
   
   Full URL: postgresql://postgres.bkbezckcmpitcglonyyz:Omkar%4027@aws-0-ap-south-1.pooler.supabase.com:6543/postgres

═══════════════════════════════════════════════════════════════════

🔍 Current Issues:
   ❌ "Tenant or user not found" means:
      • Wrong password
      • Password not URL-encoded correctly
      • Database hasn't been activated yet

✅ Try these solutions:
   1. Reset your database password in Supabase dashboard
   2. Use the new password (URL-encode if it has special chars)
   3. Make sure database is "Active" in dashboard

═══════════════════════════════════════════════════════════════════
""")

# Let's also check current password
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()
current_url = os.getenv('DATABASE_URL', '')

if 'postgresql://' in current_url:
    # Extract password
    parts = current_url.split('://')
    if len(parts) > 1:
        creds = parts[1].split('@')[0]
        if ':' in creds:
            password = creds.split(':')[1]
            print(f"\n📝 Current password in .env: {password}")
            
            # Check if it needs encoding
            special_chars = ['@', '#', '$', '%', '&', '=', '+', '/', '?']
            needs_encoding = any(char in password for char in special_chars if char != '%')
            
            if needs_encoding:
                encoded = quote_plus(password)
                print(f"⚠️  Password contains special characters!")
                print(f"✅ Encoded version: {encoded}")
                print(f"\nUpdate your .env to:")
                print(f"DATABASE_URL=postgresql://postgres.bkbezckcmpitcglonyyz:{encoded}@aws-0-ap-south-1.pooler.supabase.com:6543/postgres")
            else:
                print("✅ Password looks properly encoded")

print("\n" + "="*70)
