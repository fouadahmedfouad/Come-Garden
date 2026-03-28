from datetime import datetime, timezone
class TimeProvider:
    def now(self):
        return datetime.now(timezone.utc).date()



