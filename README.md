# Cryptocurrency Price Tracker

## Overview
A web application to track and monitor cryptocurrency prices in real-time using CoinMarketCap API.

## Features
- Display top 100 cryptocurrencies
- Real-time price tracking
- Search functionality
- 24-hour price change visualization

## Prerequisites
- Node.js (v14+)
- Python (v3.8+)
- CoinMarketCap API Key

## Setup

### Backend (Flask)
1. Navigate to `backend` directory
2. Create virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Set CoinMarketCap API Key in `.env`
5. Run backend:
   ```
   python app.py
   ```

### Frontend (React)
1. Navigate to `frontend` directory
2. Install dependencies:
   ```
   npm install
   ```
3. Run development server:
   ```
   npm run dev
   ```

## Deployment
- Backend: Heroku/PythonAnywhere
- Frontend: GitHub Pages

## Technologies
- Frontend: React, TypeScript, Material-UI
- Backend: Flask, Python
- API: CoinMarketCap

## License
MIT License
