from datetime import datetime, timedelta
import uuid
# Listing
class Listing:
    def __init__(self, owner_id, item, quantity, listing_type="normal", request=None, duration_hours=24):
        self.id = str(uuid.uuid4())
        self.owner_id = owner_id
        self.item = item
        self.quantity = quantity

        self.type = listing_type  # normal, flash, gift
        self.request = request

        self.created_at = datetime.now()
        self.expires_at = None

        if listing_type == "flash":
            self.expires_at = self.created_at + timedelta(hours=duration_hours)
        
        self.status = "active"
        self.flags = []  # allergy flags


# Trade
class Trade:
    def __init__(self, listing_id, buyer_id):
        self.id = str(uuid.uuid4())
        self.listing_id = listing_id
        self.buyer_id = buyer_id
        self.status = "pending"


# Rating
class Rating:
    def __init__(self, from_user_id, to_user_id, score, comment=""):
        self.from_user = from_user_id
        self.to_user = to_user_id
        self.score = score
        self.comment = comment


# Advice Q&A
class Question:
    def __init__(self, asker_id, content, bounty=0):
        self.id = str(uuid.uuid4())
        self.asker_id = asker_id
        self.content = content
        self.bounty = bounty

        self.answers = []
        self.accepted_answer_id = None
        self.status = "open"


class Answer:
    def __init__(self, question_id, responder, content):
        self.id = str(uuid.uuid4())
        self.question_id = question_id
        self.responder = responder
        self.content = content
        self.accepted = False

