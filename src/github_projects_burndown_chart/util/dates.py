from datetime import datetime, timedelta, timezone
from dateutil import parser
from dateutil import tz
from typing import List

def parse_to_utc(date_string: str) -> datetime:
    """
    Parse a date string to UTC time.

    If the input has no timezone, interpret it in local time for that date
    before converting to UTC.
    """
    raw_datetime = parser.parse(date_string)
    if raw_datetime.tzinfo is None:
        raw_datetime = raw_datetime.replace(tzinfo=tz.tzlocal())
    return raw_datetime.astimezone(timezone.utc)


def parse_to_local(datetime_utc: datetime) -> datetime:
    """
    Parse a datetime object to local time.
    """
    return datetime_utc.astimezone()


def date_range(start_date: datetime, end_date: datetime) -> List[datetime]:
    # The +1 includes the end_date in the list
    num_days = (end_date - start_date).days + 1
    return [start_date + timedelta(days=x) for x in range(0, num_days)]


TODAY_UTC: datetime = parse_to_utc(datetime.today().strftime('%Y-%m-%d'))
