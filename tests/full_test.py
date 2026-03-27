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





#
#
# def test_renew_only_auto_members():
#          alt = Allotment(100, 100)
#
#          member = type("M", (), {"id": 1})
#
#
#          spring = Season(
#              "Spring 2026",
#              datetime(2026, 3, 1),
#              datetime(2026, 3, 27)
#          )
#
#          summer = Season(
#              "Summer 2026",
#              datetime(2026, 7, 1),
#              datetime(2026, 10, 31)
#          )
#
#          custome_season = Season(
#              "custom 2026",
#              datetime(2026,3, 26),
#              datetime(2026,3, 27) 
#          )
#
#          alt.add_season(spring)
#          alt.add_season(summer)
#          alt.add_season(custome_season)
#
#
#          participant = type("P", (), {
#             "member": member,
#             "share": 1.0,
#             "auto_renew": True,
#             "status": None
#          })
#
#          old_rental = type("R", (), {
#             "participants": [participant],
#             "total_price": 100,
#             "status": "Active"
#          })
#
#          plot = type("Plot", (), {"id": 1,"size":"small", "rental": old_rental})
#
#          alt.calculate_rent = lambda x,y: 50
#          alt.add_participant_to_rental = lambda *args: True
#
#          new = alt.renew_rental(plot, old_rental)
#         
#          assert old_rental.status == "Expired"
#          assert participant.status == "Active"
#
#
#
