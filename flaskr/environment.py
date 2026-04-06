from datetime import datetime, timezone

class Season:
    def __init__(self, name, start_date, end_date):
        self.name = name
        self.start_date = start_date
        self.end_date = end_date

    def contains(self, date):
        return self.start_date <= date <= self.end_date

    def first_day(self):
        return self.start_date
    def last_day(self):
        return self.end_date


class TimeProvider:
    def now(self):
        return datetime.now().date()


class EnvService:
    def __init__(self, time_provider=None, region=None):
        self.time_provider = time_provider or TimeProvider()
        self.region = region  # future use (e.g. "EG", "EU", etc.)

        self.seasons = []
        self.current_season = None

    def initialize(self, year=None):
        today = self.time_provider.now()
        year = year or today.year

        self.seasons = self.build_seasons(year)
        self.update_current_season()

    def build_seasons(self, year):
        # Default logic (can later switch by region)
        return [
            Season("Spring", datetime(year, 3, 1).date(), datetime(year, 5, 31).date()),
            Season("Summer", datetime(year, 6, 1).date(), datetime(year, 8, 31).date()),
            Season("Fall", datetime(year, 9, 1).date(), datetime(year, 11, 30).date()),
            Season("Winter", datetime(year, 12, 1).date(), datetime(year + 1, 2, 28).date()),
        ]

    def update_current_season(self):
        today = self.time_provider.now()

        for season in self.seasons:
            if season.contains(today):
                self.current_season = season
                return

        self.current_season = None

    def get_current_season(self):
        return self.current_season

    def get_next_season(self):
        today = self.time_provider.now()

        for season in self.seasons:
            if season.start_date > today:
                return season

        return None  

