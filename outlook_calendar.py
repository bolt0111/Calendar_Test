from O365 import Account, MSGraphProtocol
from datetime import datetime, timedelta
from dateutil import tz
from zoneinfo import ZoneInfo
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SCOPES = ["Calendars.Read", "Calendars.ReadWrite", "MailboxSettings.ReadWrite"]


def authenticate_account(client_id, client_secret, scopes):
    credentials = (client_id, client_secret)
    protocol = MSGraphProtocol()
    account = Account(credentials, protocol=protocol, auth_flow_type="authorization")
    if account.authenticate(scopes=scopes):
        print("Authenticated!")
        return account
    else:
        print("Authentication failed")
        return None


def get_account_timezone(account):
    mailbox_settings = account.mailbox().get_settings()
    return tz.gettz(mailbox_settings.timezone)


def fetch_free_slots(account, start, end, interval_minutes=60):
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()
    query = calendar.new_query("start").greater_equal(start)
    query.chain("and").on_attribute("end").less_equal(end)
    events = calendar.get_events(limit=100, query=query)
    events = sorted(events, key=lambda x: x.start)

    potential_slots = []
    current_time = start
    while current_time + timedelta(minutes=interval_minutes) <= end:
        potential_slots.append(
            (current_time, current_time + timedelta(minutes=interval_minutes))
        )
        current_time += timedelta(minutes=interval_minutes)

    free_slots = []
    for potential_start, potential_end in potential_slots:
        if all(
            potential_start >= event.end or potential_end <= event.start
            for event in events
        ):
            free_slots.append((potential_start, potential_end))

    return free_slots


def print_free_slots(free_slots):
    for start, end in free_slots:
        print(f"Free slot from {start.isoformat()} to {end.isoformat()}")


def schedule_meeting(account, start, end, subject, attendees, timezone_str):
    schedule = account.schedule()
    calendar = schedule.get_default_calendar()
    event = calendar.new_event()
    event.subject = subject

    tzinfo = ZoneInfo(timezone_str)
    event.start = start.replace(tzinfo=tzinfo)
    event.end = end.replace(tzinfo=tzinfo)

    for attendee in attendees:
        event.attendees.add(attendee)

    event.reminder = 15
    return event.save()


def main():
    account = authenticate_account(CLIENT_ID, CLIENT_SECRET, SCOPES)
    if account:
        tzinfo = get_account_timezone(account)
        start = datetime(2024, 5, 29, 9, 0, 0, tzinfo=tzinfo)
        end = datetime(2024, 5, 29, 18, 0, 0, tzinfo=tzinfo)
        free_slots = fetch_free_slots(account, start, end, interval_minutes=60)
        print_free_slots(free_slots)
        #  Specify the timezone you want to use
        # timezone_str = 'America/New_York'

        # start = datetime(2024, 5, 12, 11, 0, 0)
        # end = datetime(2024, 5, 12, 12, 0, 0)

        # meeting_scheduled = schedule_meeting(
        #     account,
        #     start,
        #     end,
        #     "Team Sync",
        #     ["tamotowndrow@outlook.com", "ericcroxe@outlook.com"],
        #     timezone_str
        # )

        # if meeting_scheduled:
        #     print("Meeting scheduled successfully!")
        # else:
        #     print("Failed to schedule meeting.")


if __name__ == "__main__":
    main()
