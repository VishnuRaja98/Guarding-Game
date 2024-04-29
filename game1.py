import pygame
import random

class Point:
    def __init__(self, screen_width=None, screen_height=None, x=None, y=None):
        if x is None or y is None:
            self.pos = pygame.Vector2(random.randint(10, screen_width-10), random.randint(60, screen_height-10))    # 60 => 50 extra for the top bar
        else:
            self.pos = pygame.Vector2(x,y)

    # def __init__(self, click_pos):
    #     self.pos = click_pos

    def draw(self, screen, color="red", size=5):
        pygame.draw.circle(screen, color, self.pos, size)

class Line:
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

    def set_start(self, start_pos):
        self.start = start_pos

    def set_end(self, end_pos):
        self.end = end_pos

    def draw(self, screen, color="white", size=2):
        if self.start and self.end:
            pygame.draw.line(screen, color, self.start, self.end, size)

    def check_any_intersection(self, other_lines):
        for line in other_lines:
            if self.intersection(line):
                print(f"current line: ({self.start},{self.end}) intersects old line: ({line.start},{line.end})")
                return True
        return False
    
    def intersection(self, other_line):
        # Get the points
        x1, y1 = self.start
        x2, y2 = self.end
        x3, y3 = other_line.start
        x4, y4 = other_line.end

        # Calculate the denominator
        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)

        # Check if lines are parallel (denominator is 0)
        if denom == 0:
            return False

        # Calculate intersection point
        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom

        # Check if intersection point lies within the segments
        if 0 < ua <= 1 and 0 < ub <= 1: # only greater than 0 and not greater than equal to considered as its going to intersect in the starting anyways
            return True
        else:
            return False
        

class Game:
    def __init__(self, customPoints=False, total_points = 10):
        pygame.init()
        self.screen = pygame.display.set_mode((600, 480))
        self.clock = pygame.time.Clock()
        self.customPoints = customPoints
        # a = Point(250,250,x=100,y=100)
        # b = Point(250,250,x=200,y=100)
        # c = Point(250,250,x=150,y=0)
        # d = Point(250,250,x=150,y=200)
        # e = Point(250,250,x=130,y=110)
        # f = Point(250,250,x=250,y=110)
        # a = Point(x=0,y=200)
        # b = Point(x=100,y=150)
        # c = Point(x=150,y=50)
        # d = Point(x=200,y=150)
        # e = Point(x=300,y=200)
        # f = Point(x=200,y=250)
        # g = Point(x=150,y=300)
        # h = Point(x=100,y=250)
        if not self.customPoints:
            self.points = [Point(self.screen.get_width(), self.screen.get_height()) for _ in range(total_points)]
        else:
            self.points = []
        self.lines = [Line()]
        self.running = True
        
        self.poly_points = []
        self.total_points = total_points
        self.total_guard_points = int(self.total_points/4)
        self.guard_points = set()
        self.guarded_points = set()
        self.guard_lines = []
        self.mode = "polygonize" if not self.customPoints else "choose points" # change to "guard" after polygonizer is done and "calculating" after that
        self.top_section_surface = pygame.Surface((self.screen.get_width(), 50))    # this section will have title and player
        self.game_font = pygame.font.SysFont(None, 36)
        
        self.reset_button = pygame.Rect(self.top_section_surface.get_width() - 90, 10, 80, 30)
        self.reset_font = pygame.font.SysFont(None, 24)
        self.reset_text = self.reset_font.render("Reset", True, pygame.Color("white"))


        
    def reset_game(self):
        # Reset the game state
        if not self.customPoints:
            self.points = [Point(self.screen.get_width(), self.screen.get_height()) for _ in range(self.total_points)]
        else:
            self.points = []
        self.lines = [Line()]
        self.poly_points = []
        self.guard_points = set()
        self.guarded_points = set()
        self.guard_lines = []
        self.mode = "choose points" if self.customPoints else "polygonize"
        self.top_section_surface.fill((30, 30, 30))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_click_event(event)

    def mouse_click_event(self, event):
        # For Mode = polygonizer:
        # Left click -> select next point of polygon
        # Right click -> Go back one point while building polygon
        # Mode = guard:
        # Left Click -> select/unselect a point guard
        # Right Click -> Unselect last point selection
        if self.reset_button.collidepoint(event.pos):
            self.reset_game()

        elif self.mode=="choose points":
            if event.button == 1:
                click_pos = pygame.mouse.get_pos()
                self.points.append(Point(x=click_pos[0], y=click_pos[1]))
                if len(self.points)==self.total_points:
                    self.mode="polygonize"
            elif event.button == 3:
                del self.points[-1]
        elif self.mode == "polygonize":
            if event.button == 1:
                # get mouse click position if clicked in vicinity of a point
                click_pos = pygame.mouse.get_pos()
                clicked_points = [point for point in self.points if pygame.Vector2(point.pos - click_pos).length() < 5]
                # call the function only if a point is selected
                if len(clicked_points) == 1:
                    self.polygonize_m1(click_pos = clicked_points[0].pos)   # further checks for points are done inside this function only
            elif event.button == 3:
                self.polygonize_m3()
        elif self.mode == "guard":
            if event.button == 1:
                # get mouse click position if clicked in vicinity of a point
                click_pos = pygame.mouse.get_pos()
                clicked_points_idx = [idx for idx in range(len(self.poly_points)) if pygame.Vector2(self.poly_points[idx].pos - click_pos).length() < 5]
                # call the function only if a point is selected
                if len(clicked_points_idx) == 1:
                    self.guard_m1(click_idx = clicked_points_idx[0])


    def polygonize_m1(self, click_pos):
        """Mouse 1 functionionality during polygonize phase"""
        # if point is already selected i dont want to join it
        if click_pos in self.poly_points:
            #if its the first point and all other points have been selected, then ok -> join and complete
            #else
            if not (click_pos==self.poly_points[0] and len(self.poly_points)==self.total_points):
                print(f"Cant join {click_pos} as its already selected")
                return
        if self.lines[-1].start is None:    # this case will only occur for the first line
            self.lines[-1].set_start(click_pos)
            self.poly_points.append(click_pos)
            print("start point = ", self.lines[-1].start)
        elif self.lines[-1].start != click_pos: # if clicked point is not same as current point
            self.lines[-1].set_end(click_pos)   # setting this to check intersection. IF there is intersection, ill reset it
            if not self.lines[-1].check_any_intersection(self.lines[:-1]):  # check intersections with all previous points
                print(f"line created:({self.lines[-1].start},{self.lines[-1].end})")
                if len(self.lines) == self.total_points and self.lines[-1].end == self.poly_points[0]:
                    self.mode = "guard" # polygonize over
                    print("Converting self.poly_points to all objects of call Point")
                    self.convert_poly_points()
                else:   # start a new line only if process not yet over
                    self.lines.append(Line(start=click_pos))    # adds new line with current line ending point as start
                    self.poly_points.append(click_pos)
            else:
                self.lines[-1].set_end(None)    # remove the line end that was added
        return
    
    def polygonize_m3(self):
        """Mouse 3 functionionality during polygonize phase"""
        if self.poly_points and self.lines:    # can go back only if there is somewhere to go back to (wow deep)
            print(f"removing {self.poly_points[-1]}")
            del self.poly_points[-1]
            # while removing line object, need to remove the current line which has its start point set and the previous lines end point
            del self.lines[-1]
            # can delete the previous end only if its not the first point
            if self.lines: 
                self.lines[-1].set_end(None)
            else:   # keep the first line object as first point now need to to be set
                print(f"start point was unset!")
                self.lines = [Line()]
            return
        return  

    def guard_m1(self, click_idx):
        """Mouse 1 functionionality during polygonize phase"""
        # the click_pos being an existing point is already checked when identifying click_pos. If req got to change that later
        if click_idx in self.guard_points:
            self.guard_points.remove(click_idx)
            print(f"guards reduced to - {self.guard_points}")
        else:
            self.guard_points.add(click_idx)
            print(f"guards updated to - {self.guard_points}")
            if len(self.guard_points) == self.total_guard_points:
                self.mode="calculate"
                self.check_guards()
        return

    def check_guards(self):
        for pointid in range(len(self.poly_points)):
            print(f"For point {pointid}")
            this_point_guarded = self.check_guard_pointpos(pointid)

            # if not self.check_guard_pointpos(point):
            #     return False
        print(f"self.guarded_points = {self.guarded_points}")
        print(f"self.guard_points = {self.guard_points}")
        print(f"self.total_points = ",self.total_points)
        if len(self.guarded_points)==self.total_points:
            self.mode="Guarder Wins!!!"
        else:
            self.mode="Polygonizer Wins!!!"
        return True 

    def check_guard_pointpos(self, pointid):
        guarded = False
        for idx in self.guard_points:
            guarded = self.Diagonal(idx,pointid)
            if guarded:
                self.guarded_points.add(pointid)
            print(f"Diagonal on point {pointid},{idx} = {guarded}")
            if guarded:
                return True
        return guarded



    # to check diagonal use InCone(a,b)&&InCone(b,a)&&Diagonalie(a,b).
    # Check the module. Its near PSLG and DCEL and before triangulation.
    # Every algorithm from Module 11
    def Area2(self,a:Point,b:Point,c:Point):
        """
        Returns twice the area of triangle abc
        """
        # Returning minus this because all answers are coming opposite for inCOne
        return (b.pos.x - a.pos.x)*(c.pos.y - a.pos.y)-(c.pos.x-a.pos.x)*(b.pos.y-a.pos.y)
        # return (c.pos.x-a.pos.x)*(b.pos.y-a.pos.y)-(b.pos.x - a.pos.x)*(c.pos.y - a.pos.y)

    def Left(self,a:Point,b:Point,c:Point):
        """
        Is c STRICTLY left of the oriented line ab?
        """
        return self.Area2(a,b,c) > 0

    def LeftOn(self,a:Point,b:Point,c:Point):
        """
        Is c left of or on the oriented line ab?
        """
        return self.Area2(a,b,c) >= 0

    def Collinear(self,a:Point,b:Point,c:Point):
        """
        Are a, b, c collinear points?
        """
        return self.Area2(a,b,c) == 0
    
    def intersectProp(self,a:Point,b:Point,c:Point,d:Point):
        """
        Return if ab and cd properly intersect
        ab and cd properly intersect if and only if 
        1. points a and b are on opposite sides of line cd,
        2. c and d are on opposite sides of line ab
        """
        # Eliminate imporper collinear cases - 
        if self.Collinear(a,b,c) or self.Collinear(a,b,d) or self.Collinear(c,d,a) or self.Collinear(c,d,b):
            return False    # collinear means they only touch. We consider that as not an intersection
        return self.Left(a,b,c)^self.Left(a,b,d) and self.Left(c,d,a)^self.Left(c,d,b)  # Returns False only if c,d are on same side of ab and a,b are on same side of cd

    def Between(self,a:Point,b:Point,c:Point):
        """
        Returns whether c is between a and b when collinear
        """
        if not self.Collinear(a,b,c):
            return False    # no further checks required if points are not collinear
        
        # if ab not vertical check betweenness on x. Else check on y
        if a.pos.x != b.pos.x:
            return (a.pos.x<=c.pos.x and c.pos.x<=b.pos.x) or (a.pos.x>=c.pos.x and c.pos.x>=b.pos.x)
        else:
            return (a.pos.y<=c.pos.y and c.pos.y<=b.pos.y) or (a.pos.y>=c.pos.y and c.pos.y>=b.pos.y)

    def Intersect(self,a:Point,b:Point,c:Point,d:Point):
        """
        IntersectProp Does not return and intersection if 3 points are collinear. So Do a betweenness check
        If the third collinear point is between the other segment, then the intersection should return True
        """
        # DOUBT: For guarding we can probably ignore this as we dont stop guarding if a vertex is hit, we can go evne further till we hit a proper edge
        if self.intersectProp(a,b,c,d):
            return True
        elif self.Between(a,b,c) or self.Between(a,b,d) or self.Between(c,d,a) or self.Between(c,d,b):
            return True
        else:
            return False
        
    def Diagonalie(self,ai:int,bi:int):
        """
        Returns True is no segment of the polygon intersects diagonal joining vertices at index ai,bi
        """
        # ai, bi are the indexes of ther vertices in poly_points
        a = self.poly_points[ai]
        b = self.poly_points[bi]
        for i in range(len(self.poly_points)):
            if i==len(self.poly_points)-1:   # for last point, the next point will the first point
                i_next = 0
            else:
                i_next = i+1
            # skip edges adjacent to ai or bi
            if i != ai and i_next != ai and i != bi and i_next != bi and self.Intersect(a,b,self.poly_points[i],self.poly_points[i_next]):
                return False    # an intersection is found
            # DOUBT: Change the Intersect function above to IntersectProp? Will not require Between function also if replaced
        return True
    
    def inCone(self,ai:int,bi:int):
        """ 
        Returns wheter the diagonal joining vertices at ai,bi in poly_points is inside the polygone Cone or outside
        """
        # get previous and next vertices of ai
        a_prev = ai-1 if ai>0 else len(self.poly_points)-1   # extra handling for ai being 0
        a_next = ai+1 if ai+1<len(self.poly_points) else 0   # extra handling for ai being last element
        if a_next == bi or a_prev == bi:
            return True # inCone test returns false for cosequetive vertices. I want it to return True as it is visible from the guard
        a=self.poly_points[ai]
        b=self.poly_points[bi]
        a0 = self.poly_points[a_prev]
        a1 = self.poly_points[a_next]
        # Case 1: a is a convex vertex - 
        if self.LeftOn(a,a1,a0):
            return self.Left(a,b,a0) and self.Left(b,a,a1)
        # Case 2: Else a is a reflex vertex
        return not(self.LeftOn(a,b,a1) and self.LeftOn(b,a,a0))
    
    def Diagonal(self,ai:int,bi:int):
        """ 
        Returns whether vertex joining ai and bi is a diagonal. DOUBT: For our guarding condition, we might need to change our concept of diagonal a little bit
        """
        # return inCone(ai,bi) and inCone(bi,ai) and Diagonalie(ai,bi)
        if ai==bi: return True  # because duh...
        is_diagonal = self.inCone(ai,bi) and self.Diagonalie(ai,bi)
        if is_diagonal:
            self.guard_lines.append(Line(self.poly_points[ai].pos, self.poly_points[bi].pos))
        return is_diagonal  # one of the inCone tests can be removed (Slide 25 module 11)

    def areas_under_segment(self,p1:Point,p2:Point):
        return (p2.pos.y+p1.pos.y)*(p2.pos.x-p1.pos.x)

    def convert_poly_points(self):
        self.poly_points = [Point(x=pos.x, y=pos.y) for pos in self.poly_points]
        # Check if polygoin is clockwise or anticlockwise
        # ref - https://stackoverflow.com/questions/1165647/how-to-determine-if-a-list-of-polygon-points-are-in-clockwise-order
        # uses the areas under segments.
        area_sum = self.areas_under_segment(self.poly_points[0],self.poly_points[-1])
        for i in range(len(self.poly_points)-1):
            area_sum += self.areas_under_segment(self.poly_points[i+1],self.poly_points[i])
        print("Area = ", area_sum)
        if area_sum<0:
            print("Reversed because anticlockwise")
            self.poly_points.reverse()


    def update(self):
        pass

    def draw(self):
        # Create a separate surface for the top section
        
        self.top_section_surface.fill((30, 30, 30))  # Fill the top section with a dark color
        player_text = self.game_font.render(f"{self.mode}", True, pygame.Color("white"))
        player_text_rect = player_text.get_rect(center=(self.top_section_surface.get_width() // 2, self.top_section_surface.get_height() // 2))
        self.top_section_surface.blit(player_text, player_text_rect)
        
        # Draw reset button
        pygame.draw.rect(self.top_section_surface, pygame.Color("gray"), self.reset_button)
        self.top_section_surface.blit(self.reset_text, (self.reset_button.x + 5, self.reset_button.y + 5))


        self.screen.fill("purple")
        self.screen.blit(self.top_section_surface, (0, 0))  # Position the top section at the top left corner of the screen

        for point in self.points:
            point.draw(self.screen)
        for id in self.guard_points:
            self.poly_points[id].draw(self.screen, color="green", size=8)
        if self.mode != "guard":
            for line in self.lines:
                line.draw(self.screen)
        if self.mode != "guard" and self.mode !='polygonize':
            for line in self.guard_lines:
                line.draw(self.screen, color="yellow", size=4)
            for idx in self.guarded_points:
                if idx not in self.guard_points:
                    self.poly_points[idx].draw(self.screen, color="yellow", size=8)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Game(customPoints=True, total_points=8)
    game.run()