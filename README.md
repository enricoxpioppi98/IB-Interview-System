# IB Interview System

A professional web application for scheduling and preparing for investment banking interviews, featuring automated resume analysis, Zoom integration, and email notifications.

![IB Interview System](https://img.shields.io/badge/IB%20Interview-System-blue)
![Python 3.7+](https://img.shields.io/badge/Python-3.7+-green)
![Flask](https://img.shields.io/badge/Flask-2.0.1-red)

## Features

- **Interview Scheduling** - Select banks, coverage areas, and interview types
- **Zoom Integration** - Automatic meeting creation with calendar invites
- **Resume Analysis** - Instant feedback tailored to investment banking
- **Email Notifications** - Automated confirmations with interview details
- **Calendar Integration** - Receive calendar invites with Zoom details
- **Modern UI** - Clean, glass-like design for easy navigation

## Quick Start - Single-Click Launch

1. **Prerequisites**
   - Python 3.7 or newer installed on your system
   - Internet connection for Zoom API and email functionality

2. **Setup and Run**
   ```bash
   # Clone the repository
   git clone https://github.com/enricoxpioppi98/IB-Interview-System.git
   cd IB-Interview-System
   
   # Run the application
   python launch.py
   ```

3. **That's it!** The launcher will:
   - Set up a virtual environment
   - Install all dependencies
   - Launch the application
   - Open your web browser automatically
   - Access the system at http://localhost:5001

## Using the Application

1. **Schedule an Interview**
   - Select your target bank and coverage area
   - Choose an interview type (Coffee Chat, First Round, Superday)
   - Pick an available date and time
   - Upload your resume (PDF format)
   - Submit and receive instant feedback

2. **View Bookings**
   - Access `/view_bookings` to see all scheduled interviews
   - Manage existing bookings

3. **Cancellations**
   - Cancel by emailing with subject "CANCEL INTERVIEW"
   - Include date and time in the email body

## Project Structure

- `app.py` - Main Flask application with routes and controllers
- `interview_system.py` - Core business logic for interview management
- `config.py` - Configuration settings and constants
- `launch.py` - One-click launcher script for easy setup and execution
- `templates/` - HTML templates for the web interface
- `uploads/` - Temporary storage for resume uploads

## How It Works

1. **Resume Analysis**
   - Extracts text from uploaded PDF
   - Analyzes content for banking-specific keywords
   - Provides tailored feedback based on target bank and coverage

2. **Zoom Integration**
   - Creates custom Zoom meetings for each interview
   - Generates secure meeting links and passwords
   - Includes meeting details in confirmation emails

3. **Email Notifications**
   - Sends detailed interview confirmations
   - Includes resume feedback and preparation tips
   - Attaches calendar invites with Zoom details

## Advanced Setup Options

### Manual Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Docker Setup (if available)
```bash
docker compose up --build
```

## Troubleshooting

If you encounter issues:

1. **Application Won't Start**
   - Ensure Python 3.7+ is installed (`python --version`)
   - Check internet connectivity for API access
   - Verify port 5001 is not in use by another application

2. **Email Issues**
   - Check your spam folder for notifications
   - Ensure the .env file contains valid credentials

3. **Interface Not Loading**
   - If the browser doesn't open automatically, navigate to http://localhost:5001
   - Try a different browser if pages don't render correctly

## Security Note

This repository includes demonstration API keys and credentials for immediate usage. For extended or production use, replace with your own credentials in the `.env` file.

## License

MIT License - See license file for details.