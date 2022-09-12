from datetime import datetime
from dateutil import parser

# parse string using ISO 8601
def str_to_time(s: str) -> datetime | None:
    try:
        return parser.parse(s)
    except parser.ParserError:
        return None



# convert date to string using ISO 8601
def time_to_str(date: datetime) -> str:
    return date.strftime("%Y-%m-%dT%H:%M:%SZ")
