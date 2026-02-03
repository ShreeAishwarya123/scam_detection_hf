# Render Setup Alternative Methods

## Method 1: Search Bar
1. In Render's "Connect Repository" page
2. Use the search bar and type: `scam_detection_hf`
3. Click on your repository when it appears

## Method 2: Direct URL Import
1. In Render, click "New +" → "Web Service"
2. Instead of "Connect GitHub", choose "Public Git Repository"
3. Enter: `https://github.com/ShreeAishwarya123/scam_detection_hf.git`
4. Continue with deployment settings

## Method 3: Manual Deploy
1. Clone your repo locally
2. Install Render CLI: `npm install -g render`
3. Run: `render init`
4. Follow prompts to deploy

## Method 4: GitHub Actions (Advanced)
Create `.github/workflows/render.yml`:
```yaml
name: Deploy to Render
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Render
        uses: render-inc/render-deploy-action@v1
        with:
          service-id: your-service-id
          api-key: ${{ secrets.RENDER_API_KEY }}
```

## Quick Fix Steps:
1. Disconnect/reconnect GitHub in Render
2. Use search bar to find repo
3. Check repository permissions in GitHub
4. Try direct URL import as fallback
