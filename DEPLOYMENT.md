# Deployment Guide for Cryptocurrency Price Tracker

## Prerequisites
- GitHub Account
- CoinMarketCap API Key
- Node.js and npm installed
- Python 3.8+ installed

## Backend Deployment (Flask)
1. Options for Backend Hosting:
   - Heroku
   - PythonAnywhere
   - Railway.app
   - Render

### Heroku Deployment Steps
1. Create `Procfile` in backend directory:
   ```
   web: gunicorn app:app
   ```

2. Install gunicorn:
   ```
   pip install gunicorn
   ```

3. Create `runtime.txt`:
   ```
   python-3.8.10
   ```

4. Update `requirements.txt`

5. Deploy via Heroku CLI

## Frontend Deployment (GitHub Pages)
1. Update `homepage` in `package.json`:
   ```json
   "homepage": "https://yourusername.github.io/scamcoin-tracker"
   ```

2. Install gh-pages:
   ```
   npm install gh-pages --save-dev
   ```

3. Add deployment scripts to `package.json`:
   ```json
   "scripts": {
     "predeploy": "npm run build",
     "deploy": "gh-pages -d dist"
   }
   ```

4. Deploy to GitHub Pages:
   ```
   npm run deploy
   ```

## Environment Configuration
1. Create `.env` file in backend
2. Add CoinMarketCap API Key:
   ```
   CMC_API_KEY=your_api_key_here
   ```

## CORS Configuration
- Configure backend to allow frontend origin
- Set appropriate CORS headers

## Monitoring and Logging
- Use Sentry for error tracking
- Implement logging in Flask backend

## Cost Considerations
- GitHub Pages: Free
- Heroku: Free tier available
- CoinMarketCap API: Free tier with limitations

## Security Notes
- Never commit API keys to repository
- Use environment variables
- Implement rate limiting
- Secure your API endpoints
