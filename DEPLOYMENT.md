# 🚀 Honeypot API Deployment Guide

## 📋 Deployment Options

### 1. **Heroku (Recommended for Beginners)**
```bash
# Install Heroku CLI
# Login to Heroku
heroku login

# Create new app
heroku create your-honeypot-app

# Set environment variables
heroku config:set HF_TOKEN=your_huggingface_token
heroku config:set API_KEY=your_api_key_here
heroku config:set HF_MODEL_ID=Qwen/Qwen2.5-1.5B-Instruct

# Deploy
git add .
git commit -m "Deploy honeypot"
git push heroku main
```

### 2. **Render (Easy Alternative)**
1. Go to [render.com](https://render.com)
2. Connect your GitHub repository
3. Create a new "Web Service"
4. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`
   - **Python Version**: 3.9.18
5. Add Environment Variables:
   - `HF_TOKEN`: Your Hugging Face token
   - `API_KEY`: Your API key
   - `HF_MODEL_ID`: `Qwen/Qwen2.5-1.5B-Instruct`

### 3. **Docker Deployment**
```bash
# Build Docker image
docker build -t honeypot-api .

# Run container
docker run -p 8000:8000 \
  -e HF_TOKEN=your_huggingface_token \
  -e API_KEY=your_api_key_here \
  honeypot-api
```

### 4. **Vercel (Serverless)**
1. Install Vercel CLI: `npm i -g vercel`
2. Create `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app/main.py"
    }
  ]
}
```
3. Deploy: `vercel --prod`

## 🔧 Required Environment Variables

```bash
HF_TOKEN=your_huggingface_token_here
API_KEY=your_secure_api_key_here
HF_MODEL_ID=Qwen/Qwen2.5-1.5B-Instruct
ENVIRONMENT=production
```

## 📝 Before You Deploy

### 1. **Get Hugging Face Token**
- Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
- Create a new token with "read" permissions
- Copy the token

### 2. **Choose Your API Key**
```bash
# Generate a secure API key
API_KEY=honeypot_secure_$(openssl rand -hex 16)
```

### 3. **Test Locally**
```bash
# Test production setup
export ENVIRONMENT=production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🌐 After Deployment

### Test Your Deployed API
```bash
# Replace with your deployed URL
curl -X POST https://your-app-url.com/honeypot/interact \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"message": "Test scam message"}'
```

### Monitor Your Deployment
- Check logs regularly
- Monitor API usage
- Set up alerts for errors

## 🔒 Security Considerations

1. **API Key Protection**: Never expose your API key in frontend code
2. **Rate Limiting**: Consider adding rate limiting for production
3. **HTTPS**: Always use HTTPS in production
4. **Environment Variables**: Never commit sensitive data to git

## 📊 Scaling Tips

### For High Traffic:
- Increase worker count: `--workers 4`
- Use larger model: `HF_MODEL_ID=Qwen/Qwen2.5-7B-Instruct`
- Add Redis for session storage
- Use load balancer

### For Cost Optimization:
- Use smaller model: `HF_MODEL_ID=Qwen/Qwen2.5-0.5B-Instruct`
- Set request timeouts
- Monitor token usage

## 🚨 Troubleshooting

### Common Issues:
1. **Timeout Errors**: Use smaller model or increase timeout
2. **Memory Issues**: Reduce worker count
3. **CORS Issues**: Check allowed origins
4. **Model Loading**: Ensure HF_TOKEN is correct

### Health Check:
```bash
curl https://your-app-url.com/
# Should return: {"status": "ok", "service": "honeypot"}
```

## 📈 Monitoring

Add these endpoints for monitoring:
```python
@app.get("/metrics")
async def metrics():
    return {
        "status": "ok",
        "model": HF_MODEL_ID,
        "uptime": "your_uptime_here"
    }
```

Your honeypot is now ready for production! 🎉
