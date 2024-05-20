from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime, timedelta, timezone
import os


SCOPES = ["https://www.googleapis.com/auth/calendar"]


def authenticate_google_api():
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    service = build("calendar", "v3", credentials=creds)
    return service


def convert_utc_timezone(time):
    time_utc = time.replace(tzinfo=timezone.utc)
    formatted_time_utc = time_utc.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    return formatted_time_utc


def get_available_slots(calendar_id, start_time, end_time, duration_minutes):
    service = authenticate_google_api()

    time_min = convert_utc_timezone(start_time)
    time_max = convert_utc_timezone(end_time)

    request_body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": calendar_id}],
        "timeZone": "America/New_York",
    }

    response = service.freebusy().query(body=request_body).execute()
    busy_slots = response["calendars"][calendar_id]["busy"]

    available_slots = []
    current_time = start_time

    while current_time < end_time:
        slot_end = current_time + timedelta(minutes=duration_minutes)

        current_time_utc = convert_utc_timezone(current_time)
        slot_end_utc = convert_utc_timezone(slot_end)

        if all(
            slot_end_utc <= busy_slot["start"] or current_time_utc >= busy_slot["end"]
            for busy_slot in busy_slots
        ):
            available_slots.append((current_time, slot_end))

        current_time += timedelta(minutes=duration_minutes)

    return available_slots


def create_event(
    summary, location, description, start_time, end_time, attendees_emails
):
    service = authenticate_google_api()

    event = {
        "summary": summary,
        "location": location,
        "description": description,
        "start": {"dateTime": start_time, "timeZone": "America/New_York"},
        "end": {
            "dateTime": end_time,
            "timeZone": "America/New_York",
        },
        "attendees": [{"email": email} for email in attendees_emails],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},
                {"method": "popup", "minutes": 10},
            ],
        },
    }
    event = (
        service.events()
        .insert(calendarId="primary", body=event, sendUpdates="all")
        .execute()
    )


def schedule_meeting():
    summary = "Team Sync Meeting"
    location = "Virtual Meeting Room"
    description = "Discuss project updates and next steps"
    start_time = "2024-05-14T16:00:00-04:00"
    end_time = "2024-05-14T17:00:00-04:00"
    attendees_emails = ["rkrall@linkedin.com", "tamotowndrow@outlook.com"]

    create_event(summary, location, description, start_time, end_time, attendees_emails)


calendar_id = "9wperfect@gmail.com"
start_time = datetime(2024, 5, 21, 9, 0)
end_time = datetime(2024, 5, 21, 18, 0)
duration_minutes = 60
available_slots = get_available_slots(
    calendar_id, start_time, end_time, duration_minutes
)
