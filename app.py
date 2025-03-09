from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, Response
from werkzeug.utils import secure_filename
import os
from interview_system import InterviewSystem
from config import *
import threading
import time
from datetime import datetime
import json
from typing import Dict, List, Optional, Union

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize interview system
interview_system = InterviewSystem()

# Background task for checking cancellations
def check_cancellations_background():
    while True:
        try:
            interview_system.check_cancellations()
            time.sleep(30)
        except Exception as e:
            print(f"Error in cancellation checker: {e}")
            time.sleep(30)

# Start cancellation checker in background
cancellation_thread = threading.Thread(target=check_cancellations_background, daemon=True)
cancellation_thread.start()

@app.route('/')
def index() -> str:
    """Render the interview scheduling page."""
    # Get available dates from interview system
    available_dates = interview_system._get_available_dates()
    return render_template('index.html', 
                         banks=BANKS,
                         coverage_areas=COVERAGE_AREAS,
                         interview_types=INTERVIEW_TYPES,
                         available_dates=available_dates)

@app.route('/schedule', methods=['POST'])
def schedule() -> Union[str, tuple]:
    """
    Handle interview scheduling form submission.
    
    Returns:
        Union[str, tuple]: Redirect response or error message
    """
    try:
        # Get form data
        email = request.form['email']
        bank = request.form['bank']
        coverage = request.form['coverage']
        interview_type = request.form['interview_type']
        date = request.form['interview_date']
        time = request.form['interview_time']
        
        # Validate required fields
        if not all([email, bank, coverage, interview_type, date, time]):
            flash('All fields are required')
            return redirect(url_for('index'))
        
        # Handle resume upload
        if 'resume' not in request.files or request.files['resume'].filename == '':
            flash('Resume file is required')
            return redirect(url_for('index'))
            
        resume_file = request.files['resume']
        if not resume_file.filename.lower().endswith(('.pdf', '.txt')):
            flash('Invalid file type. Please upload a PDF or TXT file.')
            return redirect(url_for('index'))
        
        # Save and process resume
        filename = secure_filename(resume_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            resume_file.save(filepath)
            
            # Unified error handling block for the entire process
            try:
                # Analyze resume
                resume_feedback = interview_system.analyze_resume(filepath, bank, coverage)
                
                # Schedule interview
                interview_date, interview_time, zoom_details = interview_system.schedule_interview(
                    email=email,
                    date=date,
                    time=time,
                    bank=bank,
                    coverage=coverage,
                    interview_type=interview_type
                )
                
                # Generate topics
                interview_topics = interview_system.generate_topics(bank, coverage, interview_type)
                
                # Send email
                interview_system.send_interview_details(
                    recipient_email=email,
                    bank=bank,
                    coverage=coverage,
                    interview_type=interview_type,
                    resume_feedback=resume_feedback,
                    interview_topics=interview_topics,
                    interview_date=interview_date,
                    interview_time=interview_time,
                    zoom_details=zoom_details
                )
                
                flash('Interview scheduled successfully! Check your email for details.', 'success')
                
            except Exception as process_error:
                error_message = str(process_error)
                
                # Handle specific errors with more user-friendly messages
                if "already booked" in error_message.lower():
                    flash('This time slot is already booked. Please select another time.')
                elif "zoom meeting" in error_message.lower():
                    flash(f'Error creating Zoom meeting: {error_message}')
                    if "zoom_details" in locals():
                        flash(f'Your Zoom link is: {zoom_details["url"]}', 'warning')
                elif "email" in error_message.lower():
                    flash(f'Interview scheduled but email failed: {error_message}')
                    if "zoom_details" in locals():
                        flash(f'Your Zoom link is: {zoom_details["url"]}', 'warning')
                else:
                    flash(f'Error scheduling interview: {error_message}')
                    
                print(f"Error details: {error_message}")  # Log the error
                    
            return redirect(url_for('index'))
                
        finally:
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            
    except Exception as e:
        print(f"General error: {str(e)}")  # Log the error
        flash(f'Error: {str(e)}')
        return redirect(url_for('index'))

@app.route('/view_bookings')
def view_bookings():
    # Debug print to see what's in the bookings
    print("Current bookings:", interview_system.bookings)
    return render_template('bookings.html', bookings=interview_system.bookings)

@app.route('/delete_all_meetings', methods=['POST'])
def delete_all_meetings():
    interview_system.delete_all_meetings()
    flash('All meetings have been deleted.')
    return redirect(url_for('view_bookings'))

@app.route('/get_booked_slots')
def get_booked_slots() -> jsonify:
    """Return list of booked interview slots."""
    try:
        # Get bookings from the interview system
        bookings = interview_system.bookings
        
        # Format the bookings into a list of date/time slots
        booked_slots = []
        for date_str, times in bookings.items():
            for time_str in times.keys():
                booked_slots.append({
                    'date': date_str,  # Format: "2025-03-14"
                    'time': time_str   # Format: "3:00 PM ET"
                })
        
        return jsonify(booked_slots)
    except Exception as e:
        print(f"Error getting booked slots: {str(e)}")
        return jsonify([])  # Return empty list on error

@app.template_filter('datetime_format')
def datetime_format(value):
    date = datetime.strptime(value, '%Y-%m-%d')
    return date.strftime('%A, %B %d, %Y')

@app.template_filter('strptime')
def strptime_filter(date_str, format):
    return datetime.strptime(date_str, format)

@app.template_filter('strftime')
def strftime_filter(date_obj, format):
    return date_obj.strftime(format)

if __name__ == '__main__':
    app.run(debug=True, port=5001) 