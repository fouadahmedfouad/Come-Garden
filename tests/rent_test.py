# from flaskr.allotment import Allotment
# from flaskr.plot      import Plot
# from flaskr.member    import Member
#
#
#
# def test_rent():
#
#     allotment = Allotment(120, 80)
#     allotment.plot_maker()
#
#     A = Member("Alice", 100)
#     B = Member("Bob", 100,"premium")
#    
#     ACredits = A.credits
#     BCredits = B.credits
#     
#     plot = allotment.plots[1]
#     
#     regular_price = allotment.calculate_rent(plot,A)
#     premium_price = allotment.calculate_rent(plot,B)
#     
#     ## Add thre rentals to A
#     for i in range(3):
#         A.add_rental(i)
#     
#     regular_tier_price = allotment.calculate_rent(plot,A)
#  
#
#
#     assert regular_price > premium_price
#     assert regular_tier_price == regular_price * allotment.get_member_tier_factor(A)
#
#     rent = allotment.rent_plot(1, A, 1.5)
#     assert "Not enough" in rent
#
#     A_credits = A.credits
#     assert A_credits == ACredits
#
#     rent = allotment.rent_plot(1,A,1.0)
#     assert isinstance(rent,Plot) == True
#
#     A_credit = A.credits
#     assert A_credit < ACredits
#
#
#     owners = plot.get_owners()
#
#     assert A.name in owners
#     assert plot.is_available() is False
#     
#    
#
#
#     C = Member("Cooper", 100)
#     D = Member("Dan", 100,"premium")
#
#     CCredits = C.credits
#     DCredits = D.credits
#     
#     plot2 = allotment.plots[2]
#     plot2.soil_quality = "premium"
#     
#     regular_price2 = allotment.calculate_rent(plot2,C)
#     gold_price2 = allotment.calculate_rent(plot2,D)
#
#     shareC = 0.5
#     shareD = 0.5
#
#     rent = allotment.rent_plot(2,C,shareC)
#     assert isinstance(rent,Plot) == True
#
#     owners = plot2.get_owners()
#
#     assert C.name in owners
#     assert plot2.is_available() is True
#
#     rent = allotment.rent_plot(2,D,shareD)
#     owners = plot2.get_owners()
#
#     assert D.name in owners
#     assert plot2.is_available() is False
#
#
#
# if __name__ == "__main__":
#     test_rent()
#
