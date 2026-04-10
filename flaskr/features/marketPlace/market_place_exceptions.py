class MarketplaceError(Exception):
    pass


class InvalidUserError(MarketplaceError):
    def __init__(self, user):
        super().__init__(f"Invalid user: {user}")


class ListingNotFoundError(MarketplaceError):
    def __init__(self, listing_id):
        super().__init__(f"Listing not found: {listing_id}")


class InvalidListingError(MarketplaceError):
    def __init__(self, message):
        super().__init__(message)


class TradeError(MarketplaceError):
    def __init__(self, message):
        super().__init__(message)


class QuestionError(MarketplaceError):
    def __init__(self, message):
        super().__init__(message)


class AnswerError(MarketplaceError):
    def __init__(self, message):
        super().__init__(message)
