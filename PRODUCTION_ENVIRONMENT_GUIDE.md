# Production Environment Configuration

This document outlines the environment variables needed for production deployment.

## Required Environment Variables

### Backend (Python Flask)

Create a `.env` file in the `altona_village_cms/src/` directory:

```env
# Flask Configuration
SECRET_KEY=your-super-secure-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
FLASK_ENV=production

# Database (for SQLite - file will be created)
DATABASE_URL=sqlite:///app.db

# Email Configuration (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
FROM_EMAIL=your-community-email@gmail.com
EMAIL_PASSWORD=your-gmail-app-password
APP_URL=https://your-app-name.onrender.com

# Admin User (Optional - for initial setup)
ADMIN_PASSWORD=your-secure-admin-password

# Security Settings
CORS_ORIGINS=https://your-app-name.onrender.com
```

### Frontend (React/Vite)

Create a `.env.production` file in the `altona-village-frontend/` directory:

```env
# API Base URL (usually same domain in production)
VITE_API_BASE_URL=https://your-app-name.onrender.com/api

# App Configuration
VITE_APP_NAME="Altona Village CMS"
VITE_APP_VERSION=1.0.0
```

## Email Setup (Gmail)

1. **Enable 2FA** on your Gmail account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password in `EMAIL_PASSWORD`

## Security Notes

### For Production:
- Use strong, random SECRET_KEY and JWT_SECRET_KEY
- Never commit .env files to Git
- Use environment variables in hosting platform
- Enable HTTPS only
- Set secure CORS origins

### Render.com Deployment:
- Set environment variables in Render dashboard
- Use Render's generated values for secrets
- Enable "Auto-Deploy" for continuous deployment

## Database Considerations

### SQLite (Current):
- ✅ **Pros**: Simple, no additional setup
- ⚠️ **Cons**: Data lost on each deployment (Render)

### PostgreSQL (Recommended for Production):
- ✅ **Pros**: Persistent data, better performance
- ⚠️ **Setup**: Requires database service

To upgrade to PostgreSQL:
1. Add PostgreSQL service in Render
2. Update `DATABASE_URL` environment variable
3. Install `psycopg2` in requirements.txt

## Health Checks

The app includes health check endpoints:
- `/api/admin/system-status` - Basic health check
- Monitor database connectivity
- Check essential services

## Logging

In production, consider:
- Structured logging (JSON format)
- Log aggregation service
- Error tracking (Sentry, etc.)
- Performance monitoring

## Backup Strategy

### Important Data:
- User accounts and profiles
- Property information
- Transition requests
- Vehicle registrations
- Communication history

### Backup Methods:
- Database exports (automated)
- File system backups
- Version control for code

## Monitoring

### Key Metrics:
- Application uptime
- Response times
- Error rates
- User activity
- Database performance

### Alerts:
- Server downtime
- High error rates
- Failed email deliveries
- Database connection issues
