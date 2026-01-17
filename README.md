# Deploy Radicale CardDAV Server to Railway

## Step-by-Step Deployment

### 1. **Push Code to GitHub**
```bash
cd radicale
git add .
git commit -m "Add Radicale CardDAV server"
git push
```

### 2. **Create New Railway Project**
1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your ADLCRM repository
5. Railway will detect the Dockerfile in `/radicale` folder

### 3. **Configure Environment Variables**
In Railway dashboard, add these variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | Your Supabase connection string | Format: `postgresql://user:pass@host:5432/database` |
| `PORT` | `5232` | CardDAV server port |

**Get Supabase connection string:**
1. Go to Supabase dashboard
2. Settings → Database
3. Copy "Connection string" (Direct connection)
4. Replace `[YOUR-PASSWORD]` with your actual password

### 4. **Set Root Directory** (Important!)
1. In Railway project settings
2. Go to "Settings" tab
3. Set "Root Directory" to `/radicale`
4. Save changes

### 5. **Deploy**
Railway will automatically:
- Build Docker image from `/radicale/Dockerfile`
- Install Python + Radicale
- Start server on port 5232
- Assign a public URL like `https://radicale-production-xxxx.up.railway.app`

### 6. **Get Your CardDAV URL**
After deployment, Railway provides a URL:
```
https://your-app-name.up.railway.app
```

## Alternative: Railway CLI Deployment

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
cd radicale
railway init

# Link to existing project or create new one
railway link

# Set environment variable
railway variables set DATABASE_URL="postgresql://user:pass@host:5432/database"

# Deploy
railway up
```

## Configure Your Devices

### iPhone/iPad
1. Settings → Contacts → Accounts
2. Add Account → Other → Add CardDAV Account
3. **Server:** `your-app-name.up.railway.app`
4. **Username:** `admin` (or leave blank if auth disabled)
5. **Password:** (leave blank if auth disabled)
6. **Description:** ADLCRM Contacts
7. Tap "Next" → Done

### Android (using DAVx⁵)
1. Install DAVx⁵ from Play Store
2. Open app → ➕ → Login with URL and credentials
3. **Base URL:** `https://your-app-name.up.railway.app`
4. **Contact Group Method:** Automatic
5. Tap "Login"
6. Select "Contacts" to sync
7. Choose which Android account to sync to

### macOS
1. System Settings → Internet Accounts
2. Add Account → CardDAV
3. **Server:** `your-app-name.up.railway.app`
4. **User Name:** `admin` (or leave blank)
5. **Password:** (leave blank if auth disabled)

### Thunderbird
1. Install CardBook extension
2. Address Book → CardBook
3. New Address Book → Remote
4. **Type:** CardDAV
5. **URL:** `https://your-app-name.up.railway.app/contacts.vcf/`
6. **Username/Password:** (if auth enabled)

## Enable Authentication (Optional)

To add password protection, update `radicale/config`:

```ini
[auth]
type = htpasswd
htpasswd_filename = /data/htpasswd
htpasswd_encryption = bcrypt
```

Then create password file:
```bash
# In Dockerfile, add:
RUN htpasswd -Bbc /data/htpasswd admin yourpassword
```

## Verify It's Working

```bash
# Test endpoint
curl https://your-app-name.up.railway.app/.well-known/carddav

# Should return redirect to CardDAV endpoint
```

## Troubleshooting

**Issue:** Railway says "No Dockerfile found"
- **Fix:** Make sure Root Directory is set to `/radicale` in settings

**Issue:** Database connection error
- **Fix:** Verify DATABASE_URL format and that Supabase allows Railway's IP

**Issue:** No contacts showing up
- **Fix:** Check Supabase contacts table has data: `SELECT COUNT(*) FROM contacts;`

**Issue:** iOS says "Cannot verify server identity"
- **Fix:** Railway provides HTTPS by default, but ensure URL starts with `https://`

## Cost Estimate
- **Radicale server:** ~$1-2/month (minimal resources)
- **Supabase database:** Free tier (already using)
- **Total:** ~$1-2/month for unlimited contact syncing

## Next Steps After Deployment
1. Test with one device first
2. Verify contacts sync correctly
3. Roll out to team
4. Set up authentication if needed
5. Add CalDAV support for calendar syncing (similar setup)
