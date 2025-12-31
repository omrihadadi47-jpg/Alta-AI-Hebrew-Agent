import os.path
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from pathlib import Path

# Google APIs
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# --- Configuration ---
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

SENDER_EMAIL = os.getenv("SENDER_EMAIL")  
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Handles Google authentication and returns the Calendar service."""
    creds = None
    # The file token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Requires credentials.json from Google Cloud Console
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def get_available_slots(date_str):
    """
    Checks availability (Currently static, can be upgraded to real logic).
    """
    print(f"[Tool] Checking availability for: {date_str}")
    # Future upgrade: Use service.events().list to check for conflicts
    return ["10:00", "14:00", "16:30"]

def book_meeting(date_str, time_str, customer_email, customer_name="Customer"):
    """
    Creates a Google Calendar event and sends a confirmation email.
    """
    print(f"[Tool] Booking meeting for {customer_name} at {date_str} {time_str}")
    
    try:
        # 1. Create Google Calendar Event
        service = get_calendar_service()
        
        # Format date and time for Google (ISO format)
        # Assuming input is YYYY-MM-DD and HH:MM
        start_datetime_str = f"{date_str}T{time_str}:00"
        
        # Calculate end time (assuming 45 minutes duration)
        try:
            start_dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            # Fallback for different date formats if necessary
             start_dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%d/%m/%Y %H:%M")

        end_dt = start_dt + datetime.timedelta(minutes=45)
        end_datetime_str = end_dt.strftime("%Y-%m-%dT%H:%M:%00")

        # Event details (Hebrew content as requested)
        event = {
            'summary': f'פגישת היכרות - Alta AI עם {customer_name}',
            'location': 'Zoom Meeting',
            'description': f'פגישת דמו עם קטי.\nפרטי לקוח: {customer_name} ({customer_email})',
            'start': {
                'dateTime': start_datetime_str,
                'timeZone': 'Asia/Jerusalem',
            },
            'end': {
                'dateTime': end_datetime_str,
                'timeZone': 'Asia/Jerusalem',
            },
            'attendees': [
                {'email': customer_email},
                {'email': SENDER_EMAIL},
            ],
        }

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        calendar_link = created_event.get('htmlLink')
        print(f"[Google Calendar] Event created: {calendar_link}")

        # 2. Send Confirmation Email
        send_confirmation_email(customer_email, customer_name, f"{date_str} at {time_str}", calendar_link)

        return {"status": "success", "message": "Meeting booked and email sent."}

    except Exception as e:
        print(f"[Error] Failed to book meeting: {e}")
        return {"status": "error", "message": f"Failed to book meeting: {str(e)}"}

def send_confirmation_email(to_email, name, slot, calendar_link):
    """Sends an email via Gmail SMTP."""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email
    msg['Subject'] = f"אישור פגישה: Alta AI - {name}"

    # Email Body (Hebrew content as requested)
    body = f"""
    <div dir="rtl" style="font-family: Arial, sans-serif;">
        <h2>היי {name},</h2>
        <p>שמחים לאשר את פגישת הדמו שלך עם קטי מחברת Alta AI.</p>
        <p><strong>מועד הפגישה:</strong> {slot}</p>
        <p>קישור לפגישה (זום) יישלח בסמוך למועד, וכבר מופיע בזימון ביומן המצורף.</p>
        <br>
        <a href="{calendar_link}" style="background-color: #6c5ce7; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">צפה באירוע ביומן</a>
        <br><br>
        בברכה,<br>
        צוות Alta AI
    </div>
    """
    
    msg.attach(MIMEText(body, 'html'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, EMAIL_APP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()
        print(f"[Email] Confirmation sent to {to_email}")
    except Exception as e:
        print(f"[Email Error] Could not send email: {e}")