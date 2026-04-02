from flaskr.plot import Plot

# Note:
## Be realsitc
## Put constraints
## automate


class Allotment():

    def __init__(self,width,height,road):
        self.allotment_width = width
        self.allotment_height = height
        self.road = road 
        self.plots = []
    
    PLOTS = {
        "large": {"w": 20, "h": 10},
        "small": {"w": 6.3, "h": 3.3}
    }
    
    def generate_points(self,start_x, start_y, step_x, step_y, count_x, count_y):
        return [
            (start_x + i * step_x, start_y + j * step_y)
            for i in range(count_x)
            for j in range(count_y)
        ]
  
    def create_plot(self,plot_id,plot_size,x,y,w,h):
        center = (round(x,2),round(y,2))
        area = w * h
        
        boundary = {
            "x_min": x - w/2,
            "x_max": x + w/2,
            "y_min": y - h/2,
            "y_max": y + h/2,
        }

        return Plot(plot_id,plot_size,center,w,h,area,boundary,"available")

    def cad_render(self,large_pts,small_pts,lw,lh,sw,sh):
        try: 
            import cadquery as cq
            from ocp_vscode import show
        except ImportError:
            raise RuntimeError("cad_render requires cadquery and ocp_vscode installed")
      
        alt_w = self.allotment_width
        alt_h = self.allotment_height
        alt_thickness = 1
        plt_thickness = 3
        
        allotment = cq.Workplane("front").rect(alt_w,alt_h).extrude(alt_thickness)
        if large_pts:
            allotment = allotment.pushPoints(large_pts).rect(lw, lh).extrude(plt_thickness)
        if small_pts:
            allotment = allotment.pushPoints(small_pts).rect(sw, sh).extrude(plt_thickness)

        show(allotment, reset_camera=True)

    def plotMaker(self):
    
        alt_w = self.allotment_width
        alt_h = self.allotment_height
        road  = self.road
        
        lw, lh = self.PLOTS["large"]["w"], self.PLOTS["large"]["h"]
    
        # LARGE PLOTS (GREEDY FIRST)
    
        stepLx = lw + road
        stepLy = lh + road
        
        nlp_W = int((alt_w - road) // stepLx)
        nlp_H = int((alt_h - road) // stepLy)
        
        used_width = nlp_W * stepLx
        used_height = nlp_H * stepLy
        
        startLx = -(alt_w / 2) + road + lw / 2
        startLy = -(alt_h / 2) + road + lh / 2
        
        large_pts = self.generate_points(startLx, startLy, stepLx, stepLy, nlp_W, nlp_H)

        plot_id = 1 
        for (x,y) in large_pts:
            plot = self.create_plot(plot_id,"large",x,y,lw,lh) 
            self.plots.append(plot)
            plot_id += 1
        
        remaining_width  = alt_w - used_width
        remaining_height = alt_h - used_height
        
        sw, sh = self.PLOTS["small"]["w"], self.PLOTS["small"]["h"]
        stepSx = sw + road
        stepSy = sh + road
        
        small_pts = []
        # RIGHT STRIP
        if remaining_width >= sw:
            nsp_W_right = int(remaining_width // stepSx)
            nsp_H_right = int((alt_h - road) // stepSy)
        
            right_edge_large = -(alt_w / 2) + used_width + road
    
            startRx = right_edge_large + sw / 2
            startRy = -(alt_h / 2) + road + sh / 2
    
            small_pts += self.generate_points(startRx, startRy, stepSx, stepSy, nsp_W_right, nsp_H_right)
        
        
        # TOP STRIP
        if remaining_height >= sh:
            nsp_W_top = int((used_width) // stepSx)
            nsp_H_top = int(remaining_height // stepSy)
        
            top_edge_large = -(alt_h / 2) + used_height + road
        
            startTx = -(alt_w / 2) + road + sw / 2
            startTy = top_edge_large + sh / 2
        
            small_pts += self.generate_points(startTx, startTy, stepSx, stepSy, nsp_W_top, nsp_H_top)
        
        if small_pts:
            for (x,y) in small_pts:
                plot = self.create_plot(plot_id,"small",x,y,sw,sh) 
                self.plots.append(plot)
                plot_id += 1
        
        self.totalLargePlots = len(large_pts)
        self.totalSmallPlots = len(small_pts)
        self.totalPlots = len(large_pts) + len(small_pts)
        
        print("Total plots:", self.totalPlots)        
        print("Large plots:", self.totalLargePlots)
        print("Small plots:", self.totalSmallPlots)

        self.cad_render(large_pts,small_pts,lw,lh,sw,sh)


allot = Allotment(100,50,2)
allot.plotMaker()
