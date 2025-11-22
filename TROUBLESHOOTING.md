# 🔧 Troubleshooting Database Connection

## Current Issue
Error: `FATAL: Tenant or user not found`

## This means ONE of these:
1. ❌ Wrong database password
2. ❌ Database not activated in Supabase
3. ❌ Using wrong connection pooler

## ✅ SOLUTION - Reset Database Password

### Step 1: Reset Password in Supabase
1. Go to: https://supabase.com/dashboard/project/bkbezckcmpitcglonyyz/settings/database
2. Scroll to **"Database password"** section (not Connection string)
3. Click **"Reset database password"** button
4. **COPY THE NEW PASSWORD IMMEDIATELY** (you won't see it again!)
5. If it has special characters like `@`, you need to encode them:
   - `@` → `%40`
   - `#` → `%23`  
   - `$` → `%24`
   - `%` → `%25`
   - `&` → `%26`

### Step 2: Update .env File
```env
DATABASE_URL=postgresql://postgres.bkbezckcmpitcglonyyz:YOUR_NEW_PASSWORD@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
```

### Step 3: Test Connection
```powershell
python test_supabase_connection.py
```

---

## Alternative: Use Direct Connection (Not Pooler)

If pooler still fails, try direct connection:

1. In Supabase dashboard, go to Settings → Database
2. Under "Connection string", click **"Direct"** tab (not Pooler)
3. Copy that connection string
4. Update `.env` with the direct connection URL

---

## Create Storage Bucket

While waiting for database:

1. Go to: https://supabase.com/dashboard/project/bkbezckcmpitcglonyyz/storage/buckets
2. Click **"Create a new bucket"**
3. Name: `bhojanaxpress`
4. **Toggle "Public bucket" to ON**
5. Click **"Create"**

---

## Create Database Tables

After database connects successfully:

1. Go to: https://supabase.com/dashboard/project/bkbezckcmpitcglonyyz/sql/new
2. Copy content from `database/postgresql_schema.sql`
3. Paste and click **"Run"**

---

## Still Not Working?

Check if your Supabase project is **paused**:
- Go to: https://supabase.com/dashboard/project/bkbezckcmpitcglonyyz
- Look for "Project paused" banner
- Click "Resume project" if needed
