from flaskr.allotment import Allotment, Season
from flaskr.plot      import Plot
from flaskr.member    import Member
from datetime import datetime, timedelta



def test_rent_plot_empty_waitlist():
    alt = Allotment(100, 100)
    alt.plot_maker()

    result = alt.rent_plot(1)

    assert result == 1


def test_renew_before_rent():
    alt = Allotment(100, 100)
    alt.plot_maker()

    spring = Season(
    "Spring 2026",
    datetime(2026, 3, 1),
    datetime(2026, 3, 27)
    )

    summer = Season(
    "Summer 2026",
    datetime(2026, 7, 1),
    datetime(2026, 10, 31)
    )

    custome_season = Season(
    "custom 2026",
    datetime(2026,3, 26),
    datetime(2026,3, 27) 
    )

    alt.add_season(spring)
    alt.add_season(summer)
    alt.add_season(custome_season)

    memberId1 = alt.join_member("Fouad Ahmed")
    memberId2 = alt.join_member("Dan Alex")
 
    plot = alt.plots[1]
    member = alt.members[memberId1]
    member2 = alt.members[memberId2]
    
   
    member.credits = 200
    member2.credits = 200


    alt.apply(1,1,0.5)
    alt.apply(1,2,0.3)

    alt.renew_rental(plot,plot.rental)
    alt.rent_plot(1)

# def test_renew_before_rent():
#     alt = Allotment(100,50).build()
#     plot = alt.plots[1]
#     
#     member_id  = alt.join_member("Fouad ahmed fouad")  
#     member_id2 = alt.join_member("Ahmed fouad")
#     member_id3 = alt.join_member("Alice marchel")
#     member_id4 = alt.join_member("Dan alex")
#
#     member = alt.members[member_id]
#     member2 = alt.members[member_id2]
#     member3 = alt.members[member_id3]
#     member4 = alt.members[member_id4]
#
#     member.credits = 200
#     member2.credits = 200
#     member3.credits = 200
#     member4.credits = 200
#     
#
#
#     alt.apply(1,member_id,0.1)   
#     alt.apply(1,member_id2,0.1)
#     alt.apply(1,member_id3,0.1)
#     alt.apply(1,member_id4,0.1)
#     # print("Wait",plot.waitlist)
#
#     # Season 1 starts
#     alt.audit_rental_end()
#     alt.audit_rent_plots()
#
#     print("Season 1 members")
#     for p in plot.rental.participants:
#         print(p.member.name, p.share)
#
#     ## set auto_renew for current participant for the member 
#     # i = 0
#     # for p in plot.rental.participants:
#     #     p.auto_renew = True
#     #     i += 1
#     #     if i == 2:
#     #         break
#  
#
#     member_id5 = alt.join_member("New Member")
#     member = alt.members[member_id5]
#     member.credits = 200
#     
#     ## Accepting applications during season 1
#     alt.apply(1,member_id5,0.2)
#     alt.apply(1,member_id4,0.2)
#      ## if the plot is available we allow rent (considering it will end by the end of the season no matter how late you are)
#     alt.audit_rental_end()
#     alt.audit_rent_plots()
#
#     print("Season 1 members")
#     for p in plot.rental.participants:
#         print(p.member.name, p.share)
#
#
#     print("Season 2 members")
#     for p in plot.rental.participants:
#         print(p.member.name, p.share)
#
#     print(plot.rental.end_date)    
#     member_id6 = alt.join_member("New Member2")
#     member = alt.members[member_id6]
#     member.credits = 200

 
    # ## Accepting applications during season 2

    # alt.apply(1, member_id6, 0.1)
    # alt.apply(1, member_id4, 0.1)
    #     ## if the plot is available we can allow rent (considering it will end by the end of the season)
    # alt.audit_rent_plots()


    # alt.audit_rental_end() 
    # alt.audit_rent_plots()
    
    # print("Season 3 members")
    # for p in plot.rental.participants:
    #     print(p.member.name)

    # # End of season 1, and Start of Season 2
    # alt.renew_rental(plot,plot.rental)
    # alt.rent_plot(1)

    # print("Season 2 members")
    # for p in plot.rental.participants:
    #     print(p.member.name)


    # ## auto-renew got it, new member got it over the resident (because rentals are added to the history after it ends, and the season wasn't yet ended when new member applied)
  

    # ## set auto_renew for current participant for the member 
    # i = 0
    # for p in plot.rental.participants:
    #     p.auto_renew = True
    #     i += 1
    #     if i == 2:
    #         break


     
    # member_id6 = alt.join_member("New Member2")
    # member = alt.members[member_id6]
    # member.credits = 200

 
    # ## Accepting applications during season 2
    # alt.apply(1, member_id6, 0.2)
    # alt.apply(1, member_id4, 0.2)
    #     ## if the plot is available we can allow rent (considering it will end by the end of the season)

    # print("Wait",plot.waitlist)

    # ## End of season 2, and Start of Season 3
    # alt.renew_rental(plot,plot.rental)
    # alt.rent_plot(1)

    # print("Season 3 members")
    # for p in plot.rental.participants:
    #     print(p.member.name)

    # ## auto-renew got it, member_id4 got it for his residency priority over the new member.

    # ## end of another season
    # alt.renew_rental(plot,plot.rental)
    # alt.rent_plot(1)
    #

