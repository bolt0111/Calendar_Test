from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime, timedelta, timezone
import os
import pytz
from dateutil import parser

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


def convert_time_to_timezone(time, timezone):
    return time.astimezone(pytz.timezone(timezone))


def get_available_slots(calendar_id, start_time, end_time, duration_minutes):
    service = authenticate_google_api()

    calendar = service.calendars().get(calendarId="09straight@gmail.com").execute()
    calendar_timezone = calendar.get("timeZone")

    start_time = convert_time_to_timezone(start_time, calendar_timezone)
    end_time = convert_time_to_timezone(end_time, calendar_timezone)

    request_body = {
        "timeMin": start_time.isoformat(),
        "timeMax": end_time.isoformat(),
        "items": [{"id": calendar_id}],
        "timeZone": calendar_timezone,
    }

    response = service.freebusy().query(body=request_body).execute()
    busy_slots = response["calendars"][calendar_id]["busy"]

    available_slots = []
    current_time = start_time

    while current_time < end_time:
        slot_end = current_time + timedelta(minutes=duration_minutes)

        current_time_utc = convert_time_to_timezone(current_time, "UTC")
        slot_end_utc = convert_time_to_timezone(slot_end, "UTC")

        if all(
            slot_end_utc <= parser.parse(busy_slot["start"])
            or current_time_utc >= parser.parse(busy_slot["end"])
            for busy_slot in busy_slots
        ):
            available_slots.append((current_time, slot_end))

        current_time += timedelta(minutes=duration_minutes)

    return available_slots


calendar_id = "09straight@gmail.com"
start_time = datetime(2024, 5, 19, 9, 0)
end_time = datetime(2024, 5, 19, 15, 0)
duration_minutes = 60
available_slots = get_available_slots(
    calendar_id, start_time, end_time, duration_minutes
)
print(available_slots)


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
