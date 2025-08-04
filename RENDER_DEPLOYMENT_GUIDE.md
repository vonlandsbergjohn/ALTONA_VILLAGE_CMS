# Altona Village CMS - Render Deployment Guide

## Prerequisites

1. GitHub repository with your code
2. Render account (free tier available)

## Deployment Steps

### 1. Prepare Your Repository

Ensure these files are in your repository:
- `render.yaml` (deployment configuration)
- `altona_village_cms/requirements.txt` (Python dependencies)
- `altona-village-frontend/package.json` (Node.js dependencies)

### 2. Deploy to Render

1. **Connect to Render:**
   - Go to [render.com](https://render.com)
   - Sign up/login with GitHub
   - Click "New +" → "Blueprint"

2. **Deploy from Blueprint:**
   - Connect your GitHub repository
   - Select the repository containing this project
   - Render will automatically detect the `render.yaml` file
   - Click "Apply"

3. **Environment Variables:**
   Render will automatically generate:
   - `SECRET_KEY` (Flask secret key)
   - `JWT_SECRET_KEY` (JWT token secret)
   - `FLASK_ENV=production`

   Optional variables you can add:
   - `ADMIN_PASSWORD` (override default admin password)

### 3. Post-Deployment

1. **Health Check:**
   - Visit: `https://your-app-name.onrender.com/api/admin/system-status`
   - Should return JSON with status: "healthy"

2. **Access Admin:**
   - Visit: `https://your-app-name.onrender.com`
   - Login: `vonlandsbergjohn@gmail.com`
   - Password: `dGdFHLCJxx44ykq` (or your ADMIN_PASSWORD env var)

3. **Test Frontend:**
   - All React routes should work
   - API calls should go to the same domain

## Build Process

The deployment automatically:
1. Installs Python dependencies from `requirements.txt`
2. Installs Node.js dependencies from `package.json`
3. Builds React frontend with `npm run build`
4. Copies built files to Flask static folder
5. Starts Flask app with Gunicorn

## Database

- SQLite database is created automatically
- Database file is ephemeral on Render (resets on deployment)
- For persistent data, consider upgrading to PostgreSQL

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Ensure all dependencies are in requirements.txt
- Verify Node.js version compatibility

### App Won't Start
- Check service logs for Python errors
- Verify environment variables are set
- Check health endpoint: `/api/admin/system-status`

### Frontend Issues
- Verify build completed successfully
- Check static files are in correct location
- Ensure API routes are properly configured

## Performance Notes

- Free tier has limitations (sleeps after inactivity)
- Consider paid tier for production use
- Database will be reset on each deployment

## Security

- Change default admin password in production
- Use strong SECRET_KEY and JWT_SECRET_KEY
- Consider adding HTTPS-only cookies in production
