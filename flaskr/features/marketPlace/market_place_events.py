from datetime import datetime

class MakretEvent:
    def __init__(self, event_type, user_id=None, **data):
        self.type = event_type
        self.user_id = user_id
        self.timestamp = datetime.utcnow()
        self.data = data

class ListingCreated(MakretEvent):
    def __init__(self, user_id, listing_id, item, quantity):
        super().__init__(
            "listing_created",
            user_id,
            listing_id=listing_id,
            item=item,
            quantity=quantity
        )


class TradeRequested(MakretEvent):
    def __init__(self, user_id, listing_id, trade_id):
        super().__init__(
            "trade_requested",
            user_id,
            listing_id=listing_id,
            trade_id=trade_id
        )


class TradeCompleted(MakretEvent):
    def __init__(self, user_id, listing_id, trade_id):
        super().__init__(
            "trade_completed",
            user_id,
            listing_id=listing_id,
            trade_id=trade_id
        )


class QuestionAsked(MakretEvent):
    def __init__(self, user_id, question_id, bounty):
        super().__init__(
            "question_asked",
            user_id,
            question_id=question_id,
            bounty=bounty
        )


class AnswerAccepted(MakretEvent):
    def __init__(self, user_id, answer_id, bounty):
        super().__init__(
            "answer_accepted",
            user_id,
            answer_id=answer_id,
            bounty=bounty
        )
