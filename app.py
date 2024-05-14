from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import os

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def authenticate_google_api():
    if os.path.exists("credentials.json"):
        print("Here")
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)

    creds = flow.run_local_server(port=0)

    service = build("calendar", "v3", credentials=creds)
    return service


def create_event(
    service, summary, location, description, start_time, end_time, attendees_emails
):
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


def schedule_meeting(service):
    summary = "Team Sync Meeting"
    location = "Virtual Meeting Room"
    description = "Discuss project updates and next steps"
    start_time = "2024-05-14T16:00:00-04:00"
    end_time = "2024-05-14T17:00:00-04:00"
    attendees_emails = ["rkrall@linkedin.com", "tamotowndrow@outlook.com"]

    create_event(
        service, summary, location, description, start_time, end_time, attendees_emails
    )


def main():
    service = authenticate_google_api()
    schedule_meeting(service)


if __name__ == "__main__":
    main()
