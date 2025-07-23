# 🚀 Deployment Guide - Railway

## Pre-deployment Checklist

✅ Files sudah dibuat:
- `Procfile` - Railway process definition
- `runtime.txt` - Python version specification
- `requirements.txt` - Updated dependencies
- `.gitignore` - Ignore sensitive files
- `.env.example` - Environment variables template

✅ Code sudah dioptimasi:
- App.py updated untuk production
- Face recognition dioptimasi
- Health check endpoint ditambahkan

## Railway Deployment Steps

### 1. Push ke GitHub
```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### 2. Deploy di Railway
1. Login ke [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `hadirku-project` repository

### 3. Environment Variables
Set di Railway dashboard:
```
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production
PYTHONUNBUFFERED=1
```

### 4. Add PostgreSQL Database
1. Click "New Service" di project
2. Select "Database" → "PostgreSQL"
3. Railway akan auto-generate `DATABASE_URL`

### 5. Monitor Deployment
- Check logs: `railway logs`
- Access app: `your-project.up.railway.app`
- Health check: `your-project.up.railway.app/health`

## Resource Limits (Free Tier)
- RAM: 512MB
- CPU: Shared
- Bandwidth: 100GB/month
- Build Minutes: 500/month

## Troubleshooting
- Face recognition issues: Check memory usage
- Database errors: Verify PostgreSQL connection
- Build failures: Check requirements.txt

Deployment ready! 🎉
