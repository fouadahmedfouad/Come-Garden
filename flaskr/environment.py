from datetime import datetime, timezone

class Season():
    def __init__(self, name, start_date, end_date):
        self.name = name
        self.start_date = start_date
        self.end_date   = end_date


class TimeProvider:
    def now(self):
        return datetime.now(timezone.utc).date()



