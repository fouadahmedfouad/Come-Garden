# from flaskr.allotment import Allotment
# from flaskr.plot      import Plot
#
# def test_sunlight():
#     allotment = Allotment(120,100)
#     allotment.plotMaker()
#
#     allotment.calculate_sunlight()
#    
#     for i in range(1,len(allotment.plots)):
#         plot = allotment.plots[i]
#         sunlight_level = plot.sunlight_level
#         
#         _,y = plot.center
#         ## Top 30%
#         if y < allotment.allotment_height * 0.3:
#             assert sunlight_level == "high"
#         ## Above the bottom 30% and below the top 30%
#         elif y < allotment.allotment_height * 0.7:
#             assert sunlight_level == "medium"
#         ## Bottom 30% 
#         else:
#             assert sunlight_level == "low"
#
# if __name__ == "__main__":
#     test_sunlight()
#
