# Complete Guide: Deploy Prolog API on Render

## Prerequisites

- GitHub account
- Your code pushed to a GitHub repository
- Render account (free signup)

## Step 1: Prepare Your Repository

Make sure your GitHub repo has these files:
- `prolog_api.py`
- `prolog.pl`
- `requirements_prolog_api.txt` (or `requirements.txt`)

## Step 2: Create Render Account

1. Go to **https://render.com**
2. Click **"Get Started for Free"**
3. Sign up with GitHub (recommended) or email
4. No credit card required for free tier

## Step 3: Create New Web Service

1. In Render dashboard, click **"New +"** button (top right)
2. Select **"Web Service"**
3. Connect your GitHub account if not already connected
4. Select your repository (the one with `prolog_api.py`)
5. Click **"Connect"**

## Step 4: Configure the Service

Fill in the settings:

### Basic Settings:
- **Name**: `fireguard-prolog-api` (or any name you like)
- **Region**: Choose closest to you (e.g., `Oregon (US West)`)
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty (or `./` if files are in subdirectory)
- **Runtime**: `Python 3`
- **Build Command**: 
  ```
  pip install -r requirements_prolog_api.txt
  ```
  (Or `pip install -r requirements.txt` if you're using the main requirements file)
  
- **Start Command**: 
  ```
  python prolog_api.py
  ```

### Plan:
- Select **"Free"** plan

### Advanced Settings (Optional):
Click **"Advanced"** to add environment variables:
- **Key**: `PORT`
- **Value**: `10000` (Render sets this automatically, but good to have as fallback)

## Step 5: Install SWI-Prolog on Render

Render doesn't have SWI-Prolog pre-installed. You need to add it in the build command:

### Update Build Command:
Replace your build command with:
```bash
apt-get update && apt-get install -y swi-prolog && pip install -r requirements_prolog_api.txt
```

**OR** if that doesn't work, use a build script:

### Option A: Using Build Command (Simpler)
Change your **Build Command** to:
```bash
apt-get update && apt-get install -y swi-prolog && pip install Flask flask-cors
```

### Option B: Using Build Script (More Reliable)

1. Create a file `build.sh` in your repo:
```bash
#!/bin/bash
apt-get update
apt-get install -y swi-prolog
pip install -r requirements_prolog_api.txt
```

2. Make it executable (in your local repo):
```bash
chmod +x build.sh
```

3. Commit and push to GitHub

4. In Render, set **Build Command** to:
```bash
./build.sh
```

## Step 6: Deploy

1. Scroll down and click **"Create Web Service"**
2. Render will start building your service
3. Watch the build logs - it will show:
   - Installing dependencies
   - Installing SWI-Prolog
   - Starting your service

## Step 7: Get Your Service URL

1. Once deployment completes, you'll see:
   - **Status**: Live
   - **URL**: `https://fireguard-prolog-api.onrender.com` (or similar)

2. **Copy this URL** - you'll need it for Vercel!

## Step 8: Test Your API

1. Click on your service URL or visit it in browser
2. You should see an error (normal - no route for GET `/`)
3. Test the health endpoint:
   ```
   https://your-api.onrender.com/health
   ```
   Should return: `{"status":"ok","service":"prolog-api"}`

4. Test with curl (optional):
   ```bash
   curl -X POST https://your-api.onrender.com/classify \
     -H "Content-Type: application/json" \
     -d '{
       "area_name": "test_area",
       "fuel": "moderate",
       "temp": "moderate",
       "hum": "moderate",
       "wind": "moderate",
       "topo": "flat",
       "pop": "medium",
       "infra": "no_critical"
     }'
   ```

## Step 9: Configure Vercel

1. Go to your **Vercel project dashboard**
2. Click on your project
3. Go to **Settings** → **Environment Variables**
4. Click **"Add New"**
5. Add:
   - **Key**: `PROLOG_API_URL`
   - **Value**: `https://your-api.onrender.com` (your Render URL)
   - **Environment**: Production, Preview, Development (select all)
6. Click **"Save"**
7. **Redeploy** your Vercel app (or it will auto-deploy on next push)

## Step 10: Verify Everything Works

1. Test your Vercel app
2. Try analyzing a location
3. Check Vercel function logs to see if it's calling the Prolog API
4. Check Render service logs to see API requests

## Troubleshooting

### Build Fails - SWI-Prolog Not Found
- Make sure build command includes `apt-get install -y swi-prolog`
- Check build logs for errors

### Service Crashes
- Check Render logs: Click on your service → **Logs** tab
- Verify `prolog.pl` file is in the repo
- Check that Start Command is correct: `python prolog_api.py`

### API Returns 500 Error
- Check Render logs for Prolog errors
- Verify `prolog.pl` syntax is correct
- Test locally first: `python prolog_api.py`

### Cold Start Delay
- Render free tier services sleep after 15 min inactivity
- First request after sleep takes ~30 seconds
- This is normal for free tier

### Vercel Can't Connect to API
- Verify `PROLOG_API_URL` is set correctly in Vercel
- Check Render service is "Live" (not sleeping)
- Test API directly: `curl https://your-api.onrender.com/health`

## Free Tier Limitations

- ✅ **Free forever** (no credit card)
- ⚠️ **Services sleep** after 15 min inactivity
- ⚠️ **Cold start** ~30 seconds when waking
- ✅ **750 hours/month** free compute time
- ✅ **Perfect for development/testing**

## Next Steps

Once deployed:
1. Your Prolog API is live at: `https://your-api.onrender.com`
2. Vercel app calls it automatically via `PROLOG_API_URL`
3. Everything works! 🎉

## Alternative: Always-On with Fly.io

If you need no sleep time, use Fly.io (also free):
1. Install flyctl: `curl -L https://fly.io/install.sh | sh`
2. `fly auth login`
3. `fly launch` (in directory with prolog_api.py)
4. `fly deploy`
5. Get URL: `fly status`
6. Set `PROLOG_API_URL` in Vercel


