import json
import os
import PyPDF2
from datetime import datetime, timedelta, timezone
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib
import email
import time
import requests
from config import *
from zoneinfo import ZoneInfo
import re
import logging
from typing import Optional, Dict, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CustomZoomClient:
    def __init__(self, account_id, client_id, client_secret):
        self.account_id = account_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.secret_token = os.getenv('ZOOM_SECRET_TOKEN')
        self.verification_token = os.getenv('ZOOM_VERIFICATION_TOKEN')
        self.base_url = "https://api.zoom.us/v2"
        self.access_token = None
        self.token_expiry = 0

    def _get_access_token(self):
        if self.access_token and time.time() < self.token_expiry:
            return self.access_token
        
        print("Getting new Zoom access token...")  # Debug print
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {self.secret_token}'
        }
        
        data = {
            'grant_type': 'account_credentials',
            'account_id': self.account_id,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'token': self.verification_token
        }
        
        print(f"Zoom OAuth request data: {data}")  # Debug print
        
        try:
            response = requests.post(
                'https://zoom.us/oauth/token?grant_type=account_credentials',
                headers=headers,
                params={'account_id': self.account_id},
                auth=(self.client_id, self.client_secret)
            )
            
            print(f"Zoom OAuth response: {response.text}")  # Debug print
            
            if response.ok:
                token_data = response.json()
                self.access_token = token_data['access_token']
                self.token_expiry = time.time() + token_data['expires_in'] - 300
                return self.access_token
            else:
                raise Exception(f"Failed to get access token: {response.text}")
        except Exception as e:
            print(f"Exception in _get_access_token: {str(e)}")  # Debug print
            raise

    def create_meeting(self, start_time=None):
        headers = {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Content-Type': 'application/json'
        }
        
        # Format start_time to UTC ISO format
        if start_time:
            start_time = start_time.astimezone(timezone.utc)
        
        data = {
            'topic': 'IB Interview Prep Session',
            'type': 2,  # Scheduled meeting
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%SZ') if start_time else None,
            'duration': 60,  # 60 minutes
            'settings': {
                'host_video': True,
                'participant_video': True,
                'join_before_host': False,
                'mute_upon_entry': True,
                'waiting_room': True,
                'auto_recording': 'none',
                'use_pmi': False,
                'timezone': 'America/New_York'
            }
        }

        try:
            response = requests.post(
                f"{self.base_url}/users/{ZOOM_USER_ID}/meetings",
                headers=headers,
                json=data
            )
            
            if response.ok:
                meeting_data = response.json()
                return {
                    'url': meeting_data.get('join_url'),
                    'meeting_id': str(meeting_data.get('id')),
                    'password': meeting_data.get('password', '')
                }
            else:
                error_msg = response.json() if response.content else response.text
                print(f"Zoom API Error Response: {error_msg}")  # Debug print
                raise Exception(f"Failed to create meeting: {response.text}")
        except Exception as e:
            print(f"Error in create_meeting: {str(e)}")  # Debug print
            raise

    def delete_meeting(self, meeting_id):
        headers = {
            'Authorization': f'Bearer {self._get_access_token()}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.delete(
                f"{self.base_url}/meetings/{meeting_id}",
                headers=headers
            )
            
            if not response.ok:
                raise Exception(f"Failed to delete meeting: {response.text}")
        except Exception as e:
            print(f"Error in delete_meeting: {str(e)}")
            raise

class InterviewSystem:
    """
    Manages interview scheduling, resume analysis, and communication.
    
    Attributes:
        bookings_file (str): Path to JSON file storing bookings
        zoom_client (CustomZoomClient): Client for Zoom meeting management
    """
    
    def __init__(self):
        self.bookings_file = "bookings.json"
        self.zoom_client = CustomZoomClient(
            account_id=ZOOM_ACCOUNT_ID,
            client_id=ZOOM_CLIENT_ID,
            client_secret=ZOOM_CLIENT_SECRET
        )
        try:
            self._load_bookings()
            logger.info("Interview system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize interview system: {e}")
            raise

    def _load_bookings(self) -> None:
        """Load bookings from JSON file or initialize empty dict."""
        try:
            with open(self.bookings_file, 'r') as f:
                self.bookings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.bookings = {}

    def _save_bookings(self) -> None:
        """Save current bookings to JSON file."""
        with open(self.bookings_file, 'w') as f:
            json.dump(self.bookings, f, indent=4)

    def analyze_resume(self, resume_path: str, bank: str, coverage: str) -> str:
        """
        Analyze resume content and provide tailored feedback.
        
        Args:
            resume_path: Path to uploaded resume file
            bank: Target investment bank
            coverage: Coverage area
            
        Returns:
            str: Detailed feedback on resume
            
        Raises:
            Exception: If resume analysis fails
        """
        try:
            # Extract text from resume
            if resume_path.lower().endswith('.pdf'):
                text = self._extract_text_from_pdf(resume_path)
            else:
                with open(resume_path, 'r', encoding='utf-8') as file:
                    text = file.read()

            original_text = text  # Keep original case for display
            text = text.lower()  # Convert to lowercase for analysis
            
            feedback = []
            improvements = []  # Define improvements list at the beginning
            
            # 1. Format and Presentation
            words = text.split()
            word_count = len(words)
            feedback.append("Format and Presentation:")
            if word_count < 200:
                feedback.append(f"- Resume is quite brief at approximately {word_count} words. Consider adding more detail about your experiences.")
            elif word_count > 1000:
                feedback.append(f"- Resume is lengthy at {word_count} words. Consider condensing to highlight key achievements.")
            
            # Extract and analyze sections
            sections_found = []
            if "education" in text:
                sections_found.append("Education")
                # Look for key education elements
                education_keywords = ["gpa", "major", "university", "college", "bachelor", "master", "mba"]
                missing_edu = [k for k in education_keywords if k not in text]
                if missing_edu:
                    feedback.append(f"- Consider adding these to your Education section: {', '.join(missing_edu)}")
                
                # Check education details (moved here to combine with other education checks)
                if "gpa" not in text:
                    improvements.append("Add GPA if above 3.5")
                if not any(course in text for course in ["finance", "accounting", "economics"]):
                    improvements.append("Include relevant coursework")
            
            if "experience" in text:
                sections_found.append("Experience")
                # Check for action verbs
                action_verbs = ["led", "managed", "developed", "created", "analyzed", "implemented"]
                if not any(verb in text for verb in action_verbs):
                    feedback.append("- Use more action verbs to describe your experiences")
            
            if "skills" in text or "technical skills" in text:
                sections_found.append("Skills")
            
            missing_sections = [s for s in ["Education", "Experience", "Skills"] if s not in sections_found]
            if missing_sections:
                feedback.append(f"- Add these key sections: {', '.join(missing_sections)}")

            # 2. Technical Skills for Coverage Area
            feedback.append(f"\nTechnical Skills (Relevant to {coverage}):")
            industry_keywords = COVERAGE_KEYWORDS.get(coverage, [])
            found_keywords = [word for word in industry_keywords if word.lower() in text]
            
            if found_keywords:
                feedback.append(f"- Strong alignment with {coverage}: {', '.join(found_keywords)}")
                # Extract context around keywords
                for keyword in found_keywords[:2]:  # Show context for top 2 matches
                    idx = text.find(keyword.lower())
                    if idx != -1:
                        context = text[max(0, idx-50):min(len(text), idx+50)].strip()
                        feedback.append(f"  • Context: \"...{context}...\"")
            else:
                feedback.append(f"- Limited {coverage}-specific experience shown")
                feedback.append(f"- Consider adding these keywords: {', '.join(industry_keywords[:3])}")

            # 3. Banking Experience
            feedback.append("\nBanking Experience:")
            banking_terms = {
                "deal experience": ["transaction", "deal", "m&a", "merger", "acquisition"],
                "financial modeling": ["model", "valuation", "dcf", "lbo", "comps"],
                "market analysis": ["market research", "industry analysis", "competitor analysis"],
                "technical skills": ["excel", "powerpoint", "bloomberg", "capital iq"]
            }
            
            for category, terms in banking_terms.items():
                found_terms = [term for term in terms if term in text]
                if found_terms:
                    feedback.append(f"- Strong {category}: {', '.join(found_terms)}")
                else:
                    feedback.append(f"- Consider adding {category} examples")

            # 4. Quantitative Achievements
            feedback.append("\nQuantitative Achievements:")
            # Updated regex to better match actual metrics and exclude contact info
            quant_matches = re.finditer(
                r'(?:(?:\$|USD|EUR)?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|k|m|b|%))|'
                r'(?:increased|decreased|improved|reduced|grew|raised|managed|led|oversaw)(?:\s+\w+){0,5}\s+'
                r'(?:by\s+)?(?:\$|USD|EUR)?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|k|m|b|%))?)',
                text,
                re.IGNORECASE
            )
            
            matches_found = []
            contact_patterns = ['@', 'phone', 'tel', '+1', 'linkedin', '.com', '.net', '.org']
            achievement_words = ['increased', 'decreased', 'improved', 'reduced', 'grew', 
                               'raised', 'managed', 'led', 'oversaw', 'achieved', 'delivered']
            
            for match in quant_matches:
                # Skip if it looks like contact info (phone numbers, emails, etc.)
                if any(pattern in match.group().lower() for pattern in contact_patterns):
                    continue
                    
                # Get surrounding context
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                
                # Skip if context suggests it's not an achievement
                if not any(word in context.lower() for word in achievement_words):
                    continue
                    
                matches_found.append(context)

            if matches_found:
                feedback.append("- Good use of metrics:")
                for context in matches_found[:3]:  # Show top 3 metrics
                    feedback.append(f"  • \"{context}\"")
            else:
                feedback.append("- Add specific metrics to quantify your achievements")
                feedback.append("- Example: deal sizes, percentage improvements, team size")
            
            # Check formatting
            if not re.search(r'\d{4}', text):  # Look for years
                improvements.append("Add dates to experiences")
            if not re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', text):
                improvements.append("Include contact information")
            
            if improvements:
                feedback.append("Additional improvements:")
                for improvement in improvements:
                    feedback.append(f"- {improvement}")

            # 6. Bank-Specific Recommendations
            feedback.append(f"\nRecommendations for {bank}'s {coverage} group:")
            feedback.append(f"- Research recent {bank} deals in {coverage}")
            feedback.append("- Network with alumni at the bank")
            feedback.append(f"- Focus on {coverage}-specific technical skills")
            feedback.append("- Prepare deal discussions relevant to the group")

            # Create tailored summary
            strengths = []
            if found_keywords:
                strengths.append(f"{coverage} experience")
            if matches_found:
                strengths.append("quantitative achievements")
            if any(term in text for term in banking_terms["deal experience"]):
                strengths.append("deal experience")
            
            summary = f"Your profile shows {len(strengths)} key strengths for {bank}'s {coverage} group: "
            summary += ", ".join(strengths) if strengths else "potential for development"
            summary += ". Focus on " + (improvements[0].lower() if improvements else "gaining relevant experience") + "."

            return f"Executive Summary:\n{summary}\n\nDetailed Feedback:\n" + "\n".join(feedback)

        except Exception as e:
            print(f"Error in resume analysis: {str(e)}")
            return f"Error analyzing resume: {str(e)}"

    @staticmethod
    def _extract_text_from_pdf(pdf_path: str) -> str:
        """Extract text content from PDF file."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return ' '.join(page.extract_text() for page in reader.pages)

    def schedule_interview(self, email: str, date: str, time: str, 
                         bank: str, coverage: str, interview_type: str) -> tuple:
        """
        Schedule a new interview and create Zoom meeting.
        
        Args:
            email: Candidate's email
            date: Interview date (YYYY-MM-DD)
            time: Interview time (HH:MM AM/PM ET)
            bank: Target bank
            coverage: Coverage area
            interview_type: Type of interview
            
        Returns:
            tuple: (datetime, str, dict) - Interview date, time, and Zoom details
            
        Raises:
            ValueError: If time slot is already booked
        """
        print(f"Scheduling interview for date: {date}")
        
        if date and time:
            ny_tz = ZoneInfo('America/New_York')
            # Convert string to datetime
            selected_date = datetime.strptime(date, '%Y-%m-%d')
            print(f"Parsed date: {selected_date}")
            
            # Explicitly set timezone without conversion
            selected_date = selected_date.replace(tzinfo=ny_tz)
            print(f"Date with timezone: {selected_date}")
            
            date_str = selected_date.strftime('%Y-%m-%d')
            print(f"Final date string to be saved: {date_str}")
            
            # Convert time string to datetime
            time_format = "%I:%M %p ET"  # Format for "9:00 AM ET"
            time_obj = datetime.strptime(time, time_format).time()
            meeting_datetime = datetime.combine(selected_date.date(), time_obj).replace(tzinfo=ny_tz)
            
            zoom_details = self._generate_zoom_meeting(meeting_datetime)
            
            # Check if slot is available
            if date_str in self.bookings and time in self.bookings[date_str]:
                raise Exception("This time slot is already booked")
            
            if date_str not in self.bookings:
                self.bookings[date_str] = {}
            
            self.bookings[date_str][time] = {
                'email': email,
                'zoom_link': zoom_details
            }
            
            self._save_bookings()
            return selected_date, time, zoom_details
        else:
            raise Exception("Date and time must be selected")

    def _get_available_dates(self):
        dates = []
        current_date = datetime.now()
        while len(dates) < 5:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
                dates.append(current_date)
        return dates

    def _generate_zoom_meeting(self, meeting_datetime=None):
        try:
            return self.zoom_client.create_meeting(start_time=meeting_datetime)
        except Exception as e:
            # Re-raise the exception to be handled by the caller
            raise

    def generate_topics(self, bank, coverage, interview_type):
        try:
            topics = INTERVIEW_TOPICS.get(interview_type, [])
            if not topics:
                return "No topics available."
                
            # Create a clean bulleted list
            formatted_topics = []
            for topic in topics:
                if isinstance(topic, str) and topic.strip():
                    formatted_topics.append(f"• {topic.strip()}")
            
            # Return the formatted list with proper line breaks
            return "\n".join(formatted_topics)
            
        except Exception as e:
            print(f"Error generating topics: {str(e)}")
            return "Error generating interview topics."

    def send_interview_details(self, recipient_email, bank, coverage, interview_type,
                             resume_feedback, interview_topics, 
                             interview_date, interview_time, zoom_details):
        try:
            subject = f"Your {interview_type} Interview Details - {bank} {coverage}"
            
            # Create the email body
            body = f"""
Dear Candidate,

Your interview has been scheduled:

Date: {interview_date.strftime('%A, %B %d, %Y')}
Time: {interview_time} (Eastern Time)

Zoom Details:
Join URL: {zoom_details['url']}
Meeting ID: {zoom_details['meeting_id']}
Password: {zoom_details['password']}

Resume Feedback:
{resume_feedback}

Interview Topics to Prepare:
{interview_topics}

Need to Cancel or Reschedule?
----------------------------
To cancel your interview, please send an email to {EMAIL_ADDRESS} with:
Subject: CANCEL INTERVIEW
Date: {interview_date.strftime('%Y-%m-%d')}
Time: {interview_time}

Best regards,
IB Interview Prep Team
"""
            
            # Create the calendar event (using a simpler approach)
            time_format = "%I:%M %p"  # Format for "9:00 AM"
            time_str = interview_time.replace(" ET", "")  # Remove ET
            time_obj = datetime.strptime(time_str, time_format).time()
            start_datetime = datetime.combine(interview_date.date(), time_obj)
            end_datetime = start_datetime + timedelta(hours=1)
            
            # Get timezone
            local_tz = ZoneInfo('America/New_York')
            
            # Format dates in iCalendar format
            start = start_datetime.replace(tzinfo=local_tz).strftime("%Y%m%dT%H%M%S")
            end = end_datetime.replace(tzinfo=local_tz).strftime("%Y%m%dT%H%M%S")
            dtstamp = datetime.now(local_tz).strftime("%Y%m%dT%H%M%S")
            
            # Create a unique identifier
            uid = f'ibinterview-{interview_date.strftime("%Y%m%d")}-{time_str.replace(" ", "").replace(":", "")}@ibinterviewprep.com'
            
            # Create the iCalendar content manually
            ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//IB Interview System//NONSGML v1.0//EN
METHOD:REQUEST
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}Z
DTSTART;TZID=America/New_York:{start}
DTEND;TZID=America/New_York:{end}
SUMMARY:IB {interview_type} Interview - {bank} {coverage}
LOCATION:{zoom_details['url']}
DESCRIPTION:IB Interview Prep Session\\nBank: {bank}\\nCoverage: {coverage}\\nType: {interview_type}\\n\\nZoom Meeting Details:\\nJoin URL: {zoom_details['url']}\\nMeeting ID: {zoom_details['meeting_id']}\\nPassword: {zoom_details['password']}\\n\\nPlease join 5 minutes early.
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:Reminder: Interview in 30 minutes
TRIGGER:-PT30M
END:VALARM
END:VEVENT
END:VCALENDAR
"""
            
            # Create email message with multipart/mixed
            msg = MIMEMultipart("mixed")
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = recipient_email
            msg["Subject"] = subject
            
            # Add a plain text part for the body
            msg.attach(MIMEText(body, "plain"))
            
            # Create the calendar attachment
            calendar_part = MIMEText(ical_content, "calendar", "utf-8")
            calendar_part["Content-Class"] = "urn:content-classes:calendarmessage"
            calendar_part["Content-Type"] = "text/calendar; charset=UTF-8; method=REQUEST"
            calendar_part["Content-Disposition"] = "attachment; filename=invitation.ics"
            msg.attach(calendar_part)
            
            # Also attach as a regular .ics file for clients that don't recognize the calendar part
            ics_attachment = MIMEText(ical_content)
            ics_attachment["Content-Type"] = "text/calendar; name=invite.ics"
            ics_attachment["Content-Disposition"] = "attachment; filename=invite.ics"
            msg.attach(ics_attachment)
            
            # Connect to SMTP server and send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                try:
                    password = ''.join(EMAIL_PASSWORD.split())
                    server.login(EMAIL_ADDRESS, password)
                    server.send_message(msg)
                except Exception as e:
                    print(f"Email error: {str(e)}")
                    raise Exception(f"Failed to send email: {str(e)}")
                
        except Exception as e:
            print(f"Email Error Details: {str(e)}")
            raise Exception(f"Failed to send interview details: {str(e)}")

    def check_cancellations(self):
        try:
            # Use SSL connection
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            
            try:
                # Remove spaces from password if present
                password = EMAIL_PASSWORD.replace(" ", "")
                # Login with error handling
                mail.login(EMAIL_ADDRESS, password)
            except imaplib.IMAP4.error as e:
                print(f"Login failed: {str(e)}")
                return
            
            # Select inbox
            mail.select("inbox")
            
            # Search for cancellation emails
            _, message_numbers = mail.search(None, '(SUBJECT "CANCEL INTERVIEW" UNSEEN)')
            
            if not message_numbers[0]:
                # No new cancellation requests - this is normal
                mail.logout()
                return
            
            for num in message_numbers[0].split():
                try:
                    _, msg_data = mail.fetch(num, '(RFC822)')
                    email_body = msg_data[0][1]
                    message = email.message_from_bytes(email_body)
                    
                    sender_email = email.utils.parseaddr(message['from'])[1]
                    print(f"Processing cancellation request from {sender_email}")
                    
                    # Get email body
                    if message.is_multipart():
                        body = ''
                        for part in message.walk():
                            if part.get_content_type() == 'text/plain':
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = message.get_payload(decode=True).decode()
                    
                    # Parse date and time from email body
                    date_str = None
                    time_slot = None
                    
                    for line in body.split('\n'):
                        line = line.strip()
                        if line.lower().startswith('date:'):
                            date_str = line.split(':', 1)[1].strip()
                        elif line.lower().startswith('time:'):
                            time_slot = line.split(':', 1)[1].strip()
                    
                    if date_str and time_slot:
                        # Try to cancel the booking
                        if date_str in self.bookings:
                            if time_slot in self.bookings[date_str]:
                                booking = self.bookings[date_str][time_slot]
                                if booking['email'].lower() == sender_email.lower():
                                    # Delete the Zoom meeting
                                    try:
                                        meeting_id = booking['zoom_link']['meeting_id']
                                        self.zoom_client.delete_meeting(meeting_id)
                                    except Exception as e:
                                        print(f"Warning: Could not delete Zoom meeting: {e}")
                                    
                                    # Remove the booking
                                    del self.bookings[date_str][time_slot]
                                    if not self.bookings[date_str]:  # If no more bookings for this date
                                        del self.bookings[date_str]
                                    self._save_bookings()
                                    
                                    print(f"Successfully cancelled booking for {sender_email}")
                                    
                                    # Send cancellation confirmation with calendar update
                                    try:
                                        self._send_cancellation_confirmation(sender_email, date_str, time_slot)
                                    except Exception as e:
                                        print(f"Warning: Could not send cancellation confirmation: {e}")
                                
                            else:
                                # Send a response email explaining the time slot wasn't found
                                self._send_invalid_cancellation_response(
                                    sender_email,
                                    date_str,
                                    time_slot,
                                    "No booking found for this time slot."
                                )
                        else:
                            # Send a response email explaining the date wasn't found
                            self._send_invalid_cancellation_response(
                                sender_email,
                                date_str,
                                time_slot,
                                "No booking found for this date."
                            )
                    else:
                        # Send a response email explaining the format issue
                        self._send_invalid_cancellation_response(
                            sender_email,
                            None,
                            None,
                            "Could not find date and time in your email. Please ensure you include both Date: and Time: lines."
                        )
                    
                    # Mark email as processed
                    mail.store(num, '+FLAGS', '\\Seen')
                    
                except Exception as e:
                    print(f"Error processing cancellation email: {e}")
                    continue
                
            mail.logout()
            
        except Exception as e:
            print(f"Error checking cancellations: {str(e)}")
        finally:
            try:
                mail.logout()
            except:
                pass

    def _send_cancellation_confirmation(self, recipient_email, date_str, time_slot):
        """Send confirmation email with calendar cancellation"""
        try:
            subject = "Interview Cancellation Confirmation"
            
            # Create the body
            body = f"""
Dear Candidate,

Your interview scheduled for {date_str} at {time_slot} has been successfully cancelled.

If you would like to reschedule, please visit our scheduling system again.

Best regards,
IB Interview Prep Team
"""
            
            # Convert date and time strings to datetime
            time_format = "%I:%M %p"
            time_str = time_slot.replace(" ET", "")  # Remove ET
            time_obj = datetime.strptime(time_str, time_format).time()
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_datetime = datetime.combine(date_obj, time_obj)
            end_datetime = start_datetime + timedelta(hours=1)
            
            # Get timezone
            local_tz = ZoneInfo('America/New_York')
            
            # Format dates in iCalendar format
            start = start_datetime.replace(tzinfo=local_tz).strftime("%Y%m%dT%H%M%S")
            end = end_datetime.replace(tzinfo=local_tz).strftime("%Y%m%dT%H%M%S")
            dtstamp = datetime.now(local_tz).strftime("%Y%m%dT%H%M%S")
            
            # Create a unique identifier - must match the original UID
            uid = f'ibinterview-{date_str.replace("-", "")}-{time_str.replace(" ", "").replace(":", "")}@ibinterviewprep.com'
            
            # Create the iCalendar cancellation content manually
            ical_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//IB Interview System//NONSGML v1.0//EN
METHOD:CANCEL
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}Z
DTSTART;TZID=America/New_York:{start}
DTEND;TZID=America/New_York:{end}
SUMMARY:IB Interview Prep Session (CANCELLED)
STATUS:CANCELLED
SEQUENCE:1
END:VEVENT
END:VCALENDAR
"""
            
            # Create email message with multipart/mixed
            msg = MIMEMultipart("mixed")
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = recipient_email
            msg["Subject"] = subject
            
            # Add a plain text part for the body
            msg.attach(MIMEText(body, "plain"))
            
            # Create the calendar attachment
            calendar_part = MIMEText(ical_content, "calendar", "utf-8")
            calendar_part["Content-Class"] = "urn:content-classes:calendarmessage"
            calendar_part["Content-Type"] = "text/calendar; charset=UTF-8; method=CANCEL"
            calendar_part["Content-Disposition"] = "attachment; filename=cancellation.ics"
            msg.attach(calendar_part)
            
            # Also attach as a regular .ics file
            ics_attachment = MIMEText(ical_content)
            ics_attachment["Content-Type"] = "text/calendar; name=cancel.ics" 
            ics_attachment["Content-Disposition"] = "attachment; filename=cancel.ics"
            msg.attach(ics_attachment)
            
            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                password = ''.join(EMAIL_PASSWORD.split())
                server.login(EMAIL_ADDRESS, password)
                server.send_message(msg)
            
            print(f"Sent cancellation confirmation to {recipient_email}")
            
        except Exception as e:
            print(f"Error sending cancellation confirmation: {str(e)}")
            raise Exception(f"Failed to send cancellation confirmation: {str(e)}")

    def _send_invalid_cancellation_response(self, recipient_email, date_str, time_slot, reason):
        """Send an email explaining why the cancellation couldn't be processed"""
        try:
            subject = "Unable to Process Interview Cancellation"
            
            body = f"""
Dear Candidate,

We were unable to process your interview cancellation request.

Reason: {reason}

"""
            if date_str and time_slot:
                body += f"""
Details provided:
Date: {date_str}
Time: {time_slot}
"""
            
            body += """
If you need to cancel an interview, please ensure:
1. The date format is YYYY-MM-DD
2. The time includes "ET" (e.g., "9:00 AM ET")
3. You are using the same email address used to schedule the interview

Best regards,
IB Interview Prep Team
"""
            
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                password = ''.join(EMAIL_PASSWORD.split())
                server.login(EMAIL_ADDRESS, password)
                server.send_message(msg)
                
            print(f"Sent invalid cancellation response to {recipient_email}")
            
        except Exception as e:
            print(f"Error sending invalid cancellation response: {str(e)}")

    def view_bookings(self):
        if not self.bookings:
            print("\nNo interviews currently scheduled.")
            return
        
        print("\nCurrently Scheduled Interviews:")
        print("-------------------------------")
        
        # Convert bookings to a sorted list of (date, bookings) tuples
        sorted_bookings = []
        for date_str, times in self.bookings.items():
            # Convert string date to datetime for proper sorting
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            sorted_bookings.append((date_obj, times))
        
        # Sort by date
        sorted_bookings.sort(key=lambda x: x[0])
        
        for date_obj, times in sorted_bookings:
            # Format the date
            formatted_date = date_obj.strftime('%A, %B %d, %Y')
            print(f"\nDate: {formatted_date}")
            
            # Sort times and display bookings
            for time, booking in sorted(times.items()):
                print(f"  Time: {time}")
                print(f"  Email: {booking['email']}")
                print(f"  Meeting ID: {booking['zoom_link']['meeting_id']}")
                print("  ---------------")

    def delete_all_meetings(self):
        try:
            # Delete all Zoom meetings
            for date, times in self.bookings.items():
                for time, booking in times.items():
                    try:
                        meeting_id = booking['zoom_link']['meeting_id']
                        self.zoom_client.delete_meeting(meeting_id)
                    except Exception as e:
                        print(f"Warning: Could not delete Zoom meeting {meeting_id}: {e}")

            # Clear bookings
            self.bookings = {}
            self._save_bookings()
        except Exception as e:
            raise Exception(f"Error deleting all meetings: {str(e)}") 