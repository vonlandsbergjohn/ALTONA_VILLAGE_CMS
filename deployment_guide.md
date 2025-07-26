# Altona Village Community Management System - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Altona Village Community Management System to production using Render or similar platforms.

## Prerequisites

- GitHub account
- Render account (or similar cloud platform)
- Domain name (optional)

## Project Structure

```
altona_village_cms/
├── src/
│   ├── models/
│   │   └── user.py          # Database models
│   ├── routes/
│   │   ├── auth.py          # Authentication routes
│   │   ├── admin.py         # Admin management routes
│   │   ├── resident.py      # Resident portal routes
│   │   ├── communication.py # Email/WhatsApp communication
│   │   └── user.py          # Basic user routes
│   ├── static/              # React frontend build files
│   ├── database/
│   │   └── app.db          # SQLite database
│   └── main.py             # Flask application entry point
├── venv/                   # Python virtual environment
└── requirements.txt        # Python dependencies
```

## Deployment Steps

### 1. Prepare the Repository

1. **Initialize Git Repository** (if not already done):
   ```bash
   cd altona_village_cms
   git init
   git add .
   git commit -m "Initial commit - Altona Village CMS"
   ```

2. **Create GitHub Repository**:
   - Go to GitHub and create a new repository
   - Push your code:
   ```bash
   git remote add origin https://github.com/yourusername/altona-village-cms.git
   git branch -M main
   git push -u origin main
   ```

### 2. Environment Configuration

Create a `.env` file for production environment variables:

```env
# Database Configuration
DATABASE_URL=sqlite:///app.db

# Security Keys (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# WhatsApp API Configuration (Optional)
WHATSAPP_API_URL=https://api.whatsapp.com
WHATSAPP_API_TOKEN=your-whatsapp-token
```

### 3. Deploy to Render

1. **Connect GitHub Repository**:
   - Log in to Render
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure Build Settings**:
   - **Name**: `altona-village-cms`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python src/main.py`

3. **Set Environment Variables**:
   Add the following environment variables in Render:
   - `SECRET_KEY`: Your secret key
   - `JWT_SECRET_KEY`: Your JWT secret key
   - `FLASK_ENV`: `production`

4. **Deploy**:
   - Click "Create Web Service"
   - Render will automatically build and deploy your application

### 4. Database Setup

For production, consider upgrading to PostgreSQL:

1. **Add PostgreSQL to Render**:
   - Go to your service dashboard
   - Add a PostgreSQL database

2. **Update Database Configuration**:
   ```python
   # In src/main.py, update the database URI
   import os
   
   # Use PostgreSQL in production
   if os.getenv('DATABASE_URL'):
       app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
   else:
       app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
   ```

### 5. Domain Configuration (Optional)

1. **Custom Domain**:
   - In Render dashboard, go to Settings
   - Add your custom domain
   - Configure DNS records as instructed

2. **SSL Certificate**:
   - Render automatically provides SSL certificates
   - Your site will be available at `https://your-domain.com`

## Post-Deployment Setup

### 1. Create Admin Account

The system automatically creates a default admin account:
- **Email**: `admin@altonavillage.com`
- **Password**: `admin123`

**IMPORTANT**: Change this password immediately after deployment!

### 2. Configure Email Service

For production email functionality:

1. **Gmail SMTP** (Simple option):
   - Enable 2-factor authentication
   - Generate an app password
   - Use the app password in SMTP_PASSWORD

2. **SendGrid** (Recommended for production):
   - Sign up for SendGrid
   - Get API key
   - Update communication routes to use SendGrid API

3. **AWS SES** (Enterprise option):
   - Set up AWS SES
   - Configure SMTP credentials
   - Update environment variables

### 3. WhatsApp Integration

For WhatsApp functionality:

1. **WhatsApp Business API**:
   - Apply for WhatsApp Business API access
   - Get API credentials
   - Update communication routes

2. **Twilio WhatsApp API** (Alternative):
   - Sign up for Twilio
   - Enable WhatsApp messaging
   - Update integration code

## Monitoring and Maintenance

### 1. Application Monitoring

- Monitor application logs in Render dashboard
- Set up alerts for errors and downtime
- Monitor database performance

### 2. Database Backups

- Enable automatic backups in Render
- Consider additional backup strategies for critical data
- Test backup restoration procedures

### 3. Security Updates

- Regularly update dependencies
- Monitor for security vulnerabilities
- Keep Flask and other packages up to date

### 4. Performance Optimization

- Monitor response times
- Optimize database queries
- Consider caching for frequently accessed data
- Use CDN for static assets if needed

## Troubleshooting

### Common Issues

1. **Application Won't Start**:
   - Check build logs for errors
   - Verify all dependencies are in requirements.txt
   - Ensure environment variables are set correctly

2. **Database Connection Issues**:
   - Verify DATABASE_URL is correct
   - Check database service status
   - Ensure database migrations are run

3. **Static Files Not Loading**:
   - Verify React build files are in src/static/
   - Check Flask static file configuration
   - Ensure build process completed successfully

### Support

For technical support or questions:
- Check application logs first
- Review this documentation
- Contact the development team

## Security Considerations

1. **Change Default Credentials**: Immediately change the default admin password
2. **Environment Variables**: Never commit secrets to version control
3. **HTTPS**: Always use HTTPS in production
4. **Database Security**: Use strong database passwords and restrict access
5. **Regular Updates**: Keep all dependencies updated
6. **Backup Strategy**: Implement regular backups and test restoration

## Scaling Considerations

As your community grows, consider:

1. **Database Scaling**: Upgrade to a larger PostgreSQL instance
2. **Application Scaling**: Use multiple application instances
3. **CDN**: Implement a CDN for static assets
4. **Caching**: Add Redis for session and data caching
5. **Load Balancing**: Implement load balancing for high availability

This deployment guide ensures your Altona Village Community Management System is properly configured for production use with security, scalability, and maintainability in mind.

