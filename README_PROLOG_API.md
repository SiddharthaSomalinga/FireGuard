# Prolog API Setup for Vercel

Since Vercel doesn't support Prolog, deploy Prolog as a separate API service and call it from Vercel.

## Architecture

```
Vercel (Frontend + Python API) 
    ↓ HTTP Request
Prolog API Service (Render/Fly.io/Railway)
    ↓ Executes
SWI-Prolog
```

## Step 1: Deploy Prolog API (Free on Render)

1. **Go to Render**: https://render.com
2. **Sign up** (free, no credit card needed)
3. **New → Web Service**
4. **Connect your GitHub repo**
5. **Settings**:
   - **Name**: `fireguard-prolog-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python prolog_api.py`
   - **Plan**: Free
6. **Advanced → Add Environment Variable**:
   - `PORT`: `10000` (Render sets this automatically, but good to have)
7. **Deploy**

8. **Copy the service URL** (e.g., `https://fireguard-prolog-api.onrender.com`)

## Step 2: Configure Vercel

1. **Go to your Vercel project**
2. **Settings → Environment Variables**
3. **Add**:
   - **Name**: `PROLOG_API_URL`
   - **Value**: `https://your-prolog-api.onrender.com` (your Render URL)
4. **Redeploy** your Vercel app

## Step 3: Test

Your Vercel app will now call the Prolog API when analyzing locations!

## Local Testing

1. **Start Prolog API locally**:
```bash
python prolog_api.py
# Runs on http://localhost:5001
```

2. **Set environment variable**:
```bash
export PROLOG_API_URL=http://localhost:5001
```

3. **Run your app** - it will use the local Prolog API

## Files Needed for Prolog API

The `prolog_api.py` service needs:
- `prolog.pl` (your Prolog knowledge base)
- `requirements.txt` with:
  ```
  Flask>=3.0.0
  flask-cors>=4.0.0
  ```
- SWI-Prolog installed on the hosting platform

## Render Free Tier Notes

- ✅ **Free forever** (no credit card)
- ⚠️ **Services sleep** after 15 min inactivity
- ⚠️ **Cold start** ~30 seconds when waking up
- ✅ **Perfect for development/testing**

For production with no sleep, use **Fly.io** (also free, but requires CLI setup).

## Alternative: Fly.io (Always On, Free)

1. **Install flyctl**: `curl -L https://fly.io/install.sh | sh`
2. **Login**: `fly auth login`
3. **Create app**: `fly launch` (in directory with prolog_api.py)
4. **Deploy**: `fly deploy`
5. **Get URL**: `fly status` (shows your app URL)
6. **Set PROLOG_API_URL** in Vercel to your Fly.io URL

Fly.io services stay awake (no sleep) and are free for low-resource apps.

