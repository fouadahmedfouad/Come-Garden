from datetime import datetime, timedelta
import uuid

from features.marketPlace.market_place_info import (
    Listing,
    Trade,
    Rating,
    Question,
    Answer
)


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
    def create_listing(self, user, item, quantity, listing_type="normal", request=None):
        listing = Listing(user.id, item, quantity, listing_type, request)
        user.listings_ids.append(listing.id) 
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
    def request_trade(self, user, listing_id): 
        listing = self.listings.get(listing_id)

        if not listing or listing.status != "active":
            return None

        if listing.type == "flash" and datetime.now() > listing.expires_at:
            listing.status = "expired"
            return None

        trade = Trade(listing.id, user.id)
        self.trades[trade.id] = trade

        return trade



    
 


    def complete_trade(self, user, trade_id):
        trade = self.trades.get(trade_id)
        listing = self.listings.get(trade.listing_id)
        

        trade.status = "completed"
        listing.status = "completed"

        # Gift → karma
        if listing.type == "gift":
           self.member_karam[user.id] = self.member_karam.get(user.id, 0) + 10

        return trade 

    # Rating
    def rate_user(self, from_user_id, to_user_id, score, comment=""):
        self.ratings.append(Rating(from_user_id, to_user_id, score, comment))

   

 

    # Advice (Q&A)
    def ask_question(self, user, content, bounty=0):
        q = Question(user.id, content, bounty)
        user.questions_ids.append(q.id)
        user.credits -= q.bounty
        self.questions[q.id] = q

        return q

    def answer_question(self, user, question_id, content):
        question = self.questions.get(question_id)

        if not question or question.status != "open":
            return None

        ans = Answer(question_id, user, content)

        question.answers.append(ans.id)
        self.answers[ans.id] = ans

        return ans

    def accept_answer(self,user, question_id, answer_id):
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
        answer.responder.credits += question.bounty
        
        return answer


    def get_listings(self, user):
        return list(self.listings.values())

    def get_trades_by_listing(self, user, listing_id): 
        trades = []
        for trade in self.trades.values():
            if trade.listing_id == listing_id:
                trades.append(trade)
        return trades

    def get_my_trades(self, user):
        trades = []
        for trade in self.trades.values():
            if trade.buyer_id == user.id:
                trades.append(trade)
        return trades

    def get_questions(self, user):
        return list(self.questions.values())

    def get_answers_by_question(self, user, question_id):
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

