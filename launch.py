#!/usr/bin/env python3
"""
IB Interview System Launcher
----------------------------
A simple launcher script that sets up the environment and runs the application.
Just double-click this file to start the application.
"""

import os
import sys
import subprocess
import time
import webbrowser
import platform
import importlib.util

# Terminal colors for better visuals
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print colored header text"""
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")

def print_step(text):
    """Print step information"""
    print(f"{Colors.BLUE}➤ {text}{Colors.ENDC}")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.WARNING}! {text}{Colors.ENDC}")

def run_command(command, shell=True):
    """Run a shell command and return its success status"""
    try:
        subprocess.run(command, shell=shell, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except Exception as e:
        print_error(f"Error running command: {e}")
        return False

def check_python():
    """Check if Python is installed"""
    print_step("Checking Python installation...")
    try:
        # Use the same Python interpreter that's running this script
        version = platform.python_version()
        print_success(f"Python {version} found")
        return True
    except Exception:
        print_error("Python 3.7+ is required but not found")
        print_warning("Please install Python from https://www.python.org/downloads/")
        return False

def setup_environment():
    """Set up virtual environment and install dependencies"""
    # Create virtual environment if it doesn't exist
    if not os.path.exists("venv"):
        print_step("Creating virtual environment...")
        if not run_command([sys.executable, "-m", "venv", "venv"], shell=False):
            print_error("Failed to create virtual environment")
            return False
        print_success("Virtual environment created")
    
    # Activate virtual environment and install requirements
    print_step("Installing dependencies...")
    
    # Determine the pip executable to use based on platform
    if platform.system() == "Windows":
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        pip_path = os.path.join("venv", "bin", "pip")
    
    # Install requirements
    if not run_command(f'"{pip_path}" install -r requirements.txt'):
        print_error("Failed to install dependencies")
        return False
    
    print_success("Dependencies installed successfully")
    return True

def run_application():
    """Run the Flask application"""
    print_header("\nStarting IB Interview System...")
    print("The application will open in your browser shortly.")
    print("Press Ctrl+C to stop the server when done.\n")
    
    # Determine Python executable in virtual environment
    if platform.system() == "Windows":
        python_path = os.path.join("venv", "Scripts", "python")
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:
        python_path = os.path.join("venv", "bin", "python")
        pip_path = os.path.join("venv", "bin", "pip")
    
    # Check if requirements.txt was updated - if so, reinstall requirements
    if os.path.exists(".requirements_updated"):
        print_step("Updating dependencies...")
        run_command(f'"{pip_path}" install -r requirements.txt --upgrade')
        os.remove(".requirements_updated")
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(3)
        webbrowser.open("http://localhost:5001")
    
    # Start browser in a separate thread
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start the Flask application using the virtual environment's Python
    os.environ["PYTHONPATH"] = os.getcwd()
    run_command(f'"{python_path}" app.py')

def main():
    """Main function to run the launcher"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    print_header("\n===========================================")
    print_header("     IB Interview System - Launcher     ")
    print_header("===========================================\n")
    
    # Make sure the uploads directory exists
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    
    # Check requirements
    if not check_python():
        input("Press Enter to exit...")
        return
    
    # Setup environment
    if not setup_environment():
        input("Press Enter to exit...")
        return
    
    # Run the application
    run_application()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nLauncher stopped by user")
    except Exception as e:
        print_error(f"An error occurred: {e}")
        input("Press Enter to exit...") 