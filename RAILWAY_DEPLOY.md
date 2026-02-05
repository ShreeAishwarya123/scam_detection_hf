# RAILWAY QUICK DEPLOY

## Step 1: Go to Railway
https://railway.app

## Step 2: New Project
1. Click "New Project"
2. Click "Deploy from GitHub repo"
3. Select: ShreeAishwarya123/scam_detection_hf

## Step 3: Configure
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn server:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

## Step 4: Deploy
- Click "Deploy Now"
- Wait 2-3 minutes
- Test the new URL

## Expected Result:
Correct hackathon format:
```json
{
  "status": "success",
  "reply": "Oh no! My account is blocked? What should I do?"
}
```
