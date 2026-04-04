from datetime import datetime, timedelta
from member import Member
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
    def __init__(self, question_id, responder_id, content):
        self.id = str(uuid.uuid4())
        self.question_id = question_id
        self.responder_id = responder_id
        self.content = content
        self.accepted = False


# Marketplace
class Marketplace:
    def __init__(self):
        self.listings = {}
        self.trades = {}
        self.ratings = []

        self.questions = {}
        self.answers = {}

        self.member_karam = {}
        self.member_credits = {}

    # Listing
    def create_listing(self, member_id, item, quantity, listing_type="normal", request=None):
        listing = Listing(member_id, item, quantity, listing_type, request)
        self.apply_allergy_flags(listing)
        self.listings[listing.id] = listing

        return listing

    def apply_allergy_flags(self, listing):
        allergens = {
            "tomato": "nightshade",
            "potato": "nightshade",
            "peanut": "allergen"
        }

        if listing.item.lower() in allergens:
            listing.flags.append(allergens[listing.item.lower()])

    # Trade
    def request_trade(self, listing_id, buyer_id): 
        listing = self.listings.get(listing_id)

        if not listing or listing.status != "active":
            return None

        if listing.type == "flash" and datetime.now() > listing.expires_at:
            listing.status = "expired"
            return None

        trade = Trade(listing.id, buyer_id)
        self.trades[trade.id] = trade

        return trade

    def complete_trade(self, trade_id, owner_id):
        trade = self.trades.get(trade_id)
        listing = self.listings.get(trade.listing_id)
        

        trade.status = "completed"
        listing.status = "completed"

        # Gift → karma
        if listing.type == "gift":
           self.member_karam[owner_id] = self.member_karam.get(owner_id, 0) + 10

    # Rating
    def rate_user(self, from_user_id, to_user_id, score, comment=""):
        self.ratings.append(Rating(from_user_id, to_user_id, score, comment))

    # Advice (Q&A)
    def ask_question(self, member_id, content, bounty=0):
        q = Question(member_id, content, bounty)
        self.questions[q.id] = q

        return q

    def answer_question(self, member_id, question_id, content):
        question = self.questions.get(question_id)

        if not question or question.status != "open":
            return None

        ans = Answer(question_id, member_id, content)

        question.answers.append(ans.id)
        self.answers[ans.id] = ans

        return ans

    def accept_answer(self, question_id, answer_id):
        question = self.questions.get(question_id)
        answer = self.answers.get(answer_id)

        if not question or not answer:
            return False

        # mark answer as accepted
        answer.accepted = True
        question.accepted_answer_id = answer_id

        # # credit the responder
        # self.member_credits[answer.responder_id] = self.member_credits.get(answer.responder_id,0) + question.bounty

        # mark question as resolved
        question.status = "resolved"
        
        return answer


    def get_listings(self):
        return list(self.listings.values())

    def get_trades_by_listing(self, listing_id): 
        trades = []
        for trade in self.trades.values():
            if trade.listing_id == listing_id:
                trades.append(trade)
        return trades

    def get_my_trades(self, owner_id):
        trades = []
        for trade in self.trades.values():
            if trade.buyer_id == owner_id:
                trades.append(trade)
        return trades

    def get_questions(self):
        return list(self.questions.values())

    def get_answers_by_question(self, question_id):
        q = self.questions.get(question_id)
        result = []
        for ans_id in q.answers:
           result.append(self.answers[ans_id]) 
        return result

    # def get_listings(self, status=None, listing_type=None, item=None):
    #     results = self.listings.values()
    
    #     if status:
    #         results = filter(lambda l: l.status == status, results)
    
    #     if listing_type:
    #         results = filter(lambda l: l.type == listing_type, results)
    
    #     if item:
    #         results = filter(lambda l: l.item.lower() == item.lower(), results)
    
    #     return list(results)

#     # Surplus Prediction
# def predict_surplus(plot):
#     if plot.size == "large" and plot.sun_profile.get("12pm", 0) == 1.0:
#         return ["tomato", "zucchini"]
#     return []


# # TEST
# if __name__ == "__main__":
#     market = Marketplace()

#     # Members
#     m1 = Member("M1", "Alice")
#     m2 = Member("M2", "Bob")
#     members = {"M1": m1, "M2": m2}

#     m1.credits = 20

#     print("\n--- Flash Listing ---")
#     l1 = market.create_listing(m1, "Tomato", 5, listing_type="flash")
#     print(vars(l1))

#     print("\n--- Trade ---")
#     t1 = market.request_trade(l1.id, "M2")
#     market.complete_trade(t1, members)

#     print("\n--- Gift Listing ---")
#     l2 = market.create_listing(m1, "Zucchini", 3, listing_type="gift")
#     t2 = market.request_trade(l2.id, "M2")
#     market.complete_trade(t2, members)
    
#     print("Alice karma:", m1.credits)

#     print("\n--- Rating ---")
#     market.rate_user("M2", "M1", 5, "Great quality!")
#     print(market.ratings)

#     print("\n--- Allergy Flags ---")
#     print(l1.flags)

#     print("\n--- Q&A ---")
#     print("Alice credits before asking:", m1.credits)
#     q = market.ask_question(m1, "Why are leaves yellow?", bounty=10)
#     print("Alice credits after asking:", m1.credits)

#     a = market.answer_question(q.id, m2, "Nitrogen deficiency.")
#     market.accept_answer(q.id, a.id, members)

#     print("Bob credits:", m2.credits)
#     print("Bob contribution:", m2.contribution_points)

#     print("\n--- Surplus Prediction ---")
#     class DummyPlot:
#         size = "large"
#         sun_profile = {"12pm": 1.0}

#     print(predict_surplus(DummyPlot()))
