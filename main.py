import pygame
from pygame.math import Vector2
import pymunk
from pymunk import Vec2d
from ball import Ball
from elements import * 
import json

def toIMG(cords,ball): #converts from grid cords to pixels relative to ball
    b = ball.body.position 
    return((64*((cords.x-b.x+10)-0.5),64*((cords.y-b.y+6.25)-0.5)))

def roughBegin(arbiter, space, data):
    ball = data
    if ball.inRough == 0:
        ball.body.velocity *= 0.5
    ball.inRough +=1
def roughEnd(arbiter, space, data):
    ball=data
    ball.inRough -=1
def bunkerPreSolve(arbiter, space, data): #repeatedly reduces velocity until near 0
    ball = data
    if abs(ball.body.velocity.x) + abs(ball.body.velocity.y) > 0.01:
        ball.body.velocity *= 0.9 
def waterBegin(arbiter, space, data): #returns ball to previous position
    ball = data
    ball.body.position = ball.previousPosition
    ball.body.velocity = Vec2d(0,0)
def holeBegin(arbiter, space, data):
    ball = data[0]
    par = data[1]
    strokeCount = ball.strokeCount
    ball.holed = True
    ball.body.velocity = Vec2d(0,0)
    term[0] = "Hole Cleared!"
    if strokeCount == 1:
        term[1] = "Hole in One"
    elif strokeCount == par -4:
        term[1] = "Condor"
    elif strokeCount == par -3:
        term[1] = "Albatross"
    elif strokeCount == par -2:
        term[1] = "Eagle"
    elif strokeCount == par -1:
        term[1] = "Birdie"
    elif strokeCount == par:
        term[1] = "Par"
    elif strokeCount == par + 1:
        term[1] = "Bogey"
    elif strokeCount == par + 2:
        term[1] = "Double Bogey"
    elif strokeCount == par + 3:
        term[1] = "Triple Bogey"
    elif strokeCount == par + 4:
        term[1] = "Quadruple Bogey"

def elementDraw(elements,screen,ball): #draws course elements to screen 
    for e in elements:
        cords = toIMG(Vec2d(e.body.position.x,e.body.position.y),ball) 
        if cords[0] >= -64 and cords[0] <= 1344 and cords[1] >= -64 and cords[1] <= 864: 
            screen.blit(e.image,cords) 

def loadCourse(c): #loads course passed
    s = pymunk.Space() # Create a Space which contains the simulation
    s.damping = 0.5 #multiplied with velocity each second

    b = Ball(Vec2d(c["TeePosX"],c["TeePosY"]),s) #ball starts on tee

    p = c["Par"] #course par
    t =["",""] #score term

    s.on_collision(0,1,begin=roughBegin,separate=roughEnd,data=b) #collision between ball and rough
    s.on_collision(0,2,pre_solve=bunkerPreSolve,data=b) #collision between ball and bunker
    s.on_collision(0,3,begin=waterBegin,data=b) #collision between ball and water hazard
    s.on_collision(0,4,begin=holeBegin,data=[b,p]) #collision between ball and hole

    e = [] #list of elements in course
    g = c["Grid"] 
    for x in range(len(g)): #loop through grid
        for y in range(len(g[x])):
            if g[x][y] == 1: #tee
                e.append(Tee(Vec2d(x,y),s))
            elif g[x][y] == 2: #hole
                e.append(Hole(Vec2d(x,y),s))
            elif g[x][y] == 3: #rough
                e.append(Rough(Vec2d(x,y),s))
            elif g[x][y] == 4: #bunker
                e.append(Bunker(Vec2d(x,y),s))
            elif g[x][y] == 5: #water
                e.append(WaterHazard(Vec2d(x,y),s))
            elif g[x][y] == 6: #wall
                e.append(Wall(Vec2d(x,y),s))

    return b, s, p, e, t

def placeElement(mouse): #places element in grid
    x = int((mouse.x-192)//16) #grid cords
    y = int(mouse.y //16) 
    if mouse.x > 192 and mouse.y < 672 and grid[x][y] != currentElement:
        if currentElement == 1: #tee if no tee
            if TeeHolePos[0] != None:
                return None #can't place if already a tee in course
            TeeHolePos[0] = Vec2d(x,y)
        if currentElement == 2: #hole if no hole
            if TeeHolePos[1] != None:
                return None #can't place if already a hole
            TeeHolePos[1] = Vec2d(x,y)
        if grid[x][y] == 1: #
            TeeHolePos[0] = None
        elif grid[x][y] == 2:
            TeeHolePos[1] = None

        grid[x][y] = currentElement
        return isPossible()

def isPossible():#checks if course is possible
    teePos = TeeHolePos[0] #grid cords of tee
    holePos = TeeHolePos[1] #grid cords of hole
    if teePos == None or holePos == None: #tee and hole needed for valid path
        return False
    
    gGrid = [] #travel cost from tee
    hGrid = [] #heuristic travel cost to hole
    fGrid = [] #total cost of every node (also used to discount obstacles and discovered nodes)
    for i in range(68): #makes grids same size as main grid (gCost + hCost)
        gGrid.append([None] * 42)
        hGrid.append([None] * 42)
        fGrid.append([None] * 42)
    gGrid[teePos.x][teePos.y] = 0 #start so no distance from start
    hGrid[teePos.x][teePos.y] = abs(holePos.x-teePos.x) + abs(holePos.y-teePos.y)
    fGrid[teePos.x][teePos.y] = gGrid[teePos.x][teePos.y] + hGrid[teePos.x][teePos.y]

    openList = [teePos]#nodes discovered but not yet visited

    while len(openList) > 0:#whilst there are discovered nodes to visit
        nodeToVisit = None #node to be visited
        fCost = 100000000 #stupidly high so a first node is always selected
        for n in openList:
            if fGrid[n.x][n.y] < fCost: #finds node with lowest fCost
                fCost = fGrid[n.x][n.y]
                nodeToVisit = n
        x = nodeToVisit.x #short variable names for ease of use
        y = nodeToVisit.y
        fGrid[x][y] = False #has already been visited
        openList.remove(nodeToVisit)

        checkXList = [x-1,x+1,x,x] #cords of nodes to be checked
        checkYList = [y,y,y-1,y+1]
        for j in range(4): #checks all adjacent nodes to nodeToVisit
            X,Y = checkXList[j], checkYList[j]
            if X >= 0 and X < 68 and Y >= 0 and Y < 42: #checks node to be checked is within the array
                if fGrid[X][Y] == None: #if not discovered
                    if grid[X][Y] == 2: #is hole
                        return True #found
                    if grid[X][Y] > 4: #if impassible obstacle
                        fGrid[X][Y] = False #can't be pathed
                    else:
                        gGrid[X][Y] = gGrid[x][y] + 1 #1 futher from tee than nodeToVisit
                        hGrid[X][Y] = abs(holePos.x-X) + abs(holePos.y-Y) #distance from hole
                        fGrid[X][Y] = gGrid[X][Y] + hGrid[X][Y] #total cost
                        openList.append(Vec2d(X,Y)) #discovered
                elif fGrid[X][Y] == False: #ignore since visited or obstacle
                    pass
                elif gGrid[X][Y] > gGrid[x][y] + 1: #node discovered but now has shorter path
                    fGrid[X][Y] -= gGrid[X][Y] #subs old gCost
                    gGrid[X][Y] = gGrid[x][y] + 1 #updates gCost
                    fGrid[X][Y]+= gGrid[X][Y] #adds new gCost

    return False #every node checked but no path

pygame.init()#pygame stuff
screen = pygame.display.set_mode((1280, 800)) #fullscreen
running = True

just = False #allows one input from mouse press

f = open("save.json","r") #open save file
courseList = json.loads(f.read()) #get course list
f.close() 

mode = 0 #menu, htp, course list, game, editor, save
page = 0 #for course list

currentElement = 0 #for course editor grass, tee , hole, rough, bunker, water, wall
elementImages = ["grass.png","tee.png","hole.png","rough.png","bunker.png","water.png","wall.png"]#for editor
elementInfo = [{"Name":"Grass","Info":"The basic element","Info2":""},
               {"Name":"Tee","Info":"Ball starts here","Info2":"Must be 1"},
               {"Name":"Hole","Info":"Game ends on impact","Info2":"Must be 1"},
               {"Name":"Rough","Info":"Slows the ball on entry","Info2":""},
               {"Name":"Bunker","Info":"Slows the ball rapidly","Info2":""},
               {"Name":"Water Hazard","Info":"Resets the ball to the","Info2":"position before the shot"},
               {"Name":"Wall","Info":"Ball bounces off","Info2":""}]

box = 0 #for save screen

while running:
    for event in pygame.event.get():#events
        if event.type == pygame.KEYDOWN: #if type 
            if box == 1: #if in text box
                if event.key == pygame.K_BACKSPACE:
                    TeeHolePos[2] = TeeHolePos[2][:-1] #remove last character
                elif len(TeeHolePos[2]) < 19:
                    TeeHolePos[2] += event.unicode
            elif box == 2: #if in par box
                if event.key == pygame.K_BACKSPACE:
                    TeeHolePos[3] = TeeHolePos[3][:-1] #remove last character
                elif len(str(TeeHolePos[3])) < 5 and event.key >= 48 and event.key <= 57: #if number
                    TeeHolePos[3] += event.unicode
    if pygame.key.get_pressed()[pygame.K_ESCAPE]: #exits game
        running = False

    if mode == 0: #main menu / start screen
        if event.type == pygame.MOUSEBUTTONDOWN and event.button  == 1 and just == False:
            just = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button  == 1 and just == True:
            just = False
            if pygame.mouse.get_pos()[0] >= 548 and pygame.mouse.get_pos()[0] <= 724 and pygame.mouse.get_pos()[1] >= 280 and pygame.mouse.get_pos()[1] <= 376:
                mode = 2 #course list
            elif pygame.mouse.get_pos()[0] >= 464 and pygame.mouse.get_pos()[0] <= 824 and pygame.mouse.get_pos()[1] >= 412 and pygame.mouse.get_pos()[1] <= 528:
                mode = 1
            elif pygame.mouse.get_pos()[0] >= 548 and pygame.mouse.get_pos()[0] <= 724 and pygame.mouse.get_pos()[1] >= 568 and pygame.mouse.get_pos()[1] <= 664:
                running = False
        
        screen.blit(pygame.font.SysFont("impact",64).render("Golf Game: The Game",True,(255,255,255)),Vector2(368,96))#title

        screen.blit(pygame.font.SysFont("impact",60).render("Play",True,(255,255,255)),Vector2(584,288))#play
        pygame.draw.ellipse(screen,(0,200,0,255),((548,278),(176,96)),10)

        screen.blit(pygame.font.SysFont("impact",60).render("How to Play",True,(255,255,255)),Vector2(504,432))#htp
        pygame.draw.ellipse(screen,(0,200,0,255),((464,412),(360,116)),10)

        screen.blit(pygame.font.SysFont("impact",60).render("Quit",True,(255,255,255)),Vector2(584,578))#quit
        pygame.draw.ellipse(screen,(0,200,0,255),((548,568),(176,96)),10)

    elif mode == 1: #how to play
        if pygame.mouse.get_pressed()[pygame.BUTTON_LEFT-1]:
            if pygame.mouse.get_pos()[0] >= 64 and pygame.mouse.get_pos()[0] <= 128 and pygame.mouse.get_pos()[1] >= 48 and pygame.mouse.get_pos()[1] <= 112:
                mode = 0

        screen.blit(pygame.font.SysFont("impact",64).render("How to Play",True,(255,255,255)),Vector2(496,96))#title
        screen.blit(pygame.image.load("htp.png"),(224,192)) #how to play 
        screen.blit(pygame.image.load("exit.png"),(64,48)) #back to previous menu

    elif mode == 2: #course list
        if event.type == pygame.MOUSEBUTTONDOWN and event.button  == 1 and just == False:
            just = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button  == 1 and just == True:
            just = False
            if pygame.mouse.get_pos()[0] >= 64 and pygame.mouse.get_pos()[0] <= 128 and pygame.mouse.get_pos()[1] >= 48 and pygame.mouse.get_pos()[1] <= 112:
                mode = 0
            elif pygame.mouse.get_pos()[0] >= 64 and pygame.mouse.get_pos()[0] <= 128 and pygame.mouse.get_pos()[1] >= 134 and pygame.mouse.get_pos()[1] <= 198:
                possible = False
                TeeHolePos = [None,None,"","",None] #teepos holepos name par course
                grid = []
                for x in range(68):
                    grid.append([0] * 42)
                mode = 4
            elif pygame.mouse.get_pos()[0] >= 1152 and pygame.mouse.get_pos()[0] <= 1216 and pygame.mouse.get_pos()[1] >= 198 and pygame.mouse.get_pos()[1] <= 262 and page > 0:    
                page -= 1
            elif pygame.mouse.get_pos()[0] >= 1152 and pygame.mouse.get_pos()[0] <= 1216 and pygame.mouse.get_pos()[1] >= 626 and pygame.mouse.get_pos()[1] <= 690 and 3 * (page+1) < len(courseList):    
                page += 1
            elif pygame.mouse.get_pos()[0] >= 192 and pygame.mouse.get_pos()[0] <= 488:#play
                for x in range(3):
                    if pygame.mouse.get_pos()[1] >= (198 + 212*x) and pygame.mouse.get_pos()[1] <= (326 + 212*x) and len(courseList) - 3*page -x > 0:
                        currentCourse = courseList[3*page+x] #get selected course's data
                        ball, space, par, elements, term = loadCourse(currentCourse)
                        mode = 3 #game
            elif pygame.mouse.get_pos()[0] >= 489 and pygame.mouse.get_pos()[0] <= 783:#edit
                for x in range(3):
                    if pygame.mouse.get_pos()[1] >= (198 + 212*x) and pygame.mouse.get_pos()[1] <= (326 + 212*x) and len(courseList) - 3*page -x > 0:
                        currentCourse = courseList[3*page+x] #get selected course's data
                        possible = True
                        TeeHolePos = [Vec2d(currentCourse["TeePosX"],currentCourse["TeePosY"]),
                                      Vec2d(currentCourse["HolePosX"],currentCourse["HolePosY"]),
                                      currentCourse["Name"],
                                      str(currentCourse["Par"]),
                                      currentCourse] #teepos holepos name par course
                        grid = currentCourse["Grid"]
                        mode = 4 #editor
            elif pygame.mouse.get_pos()[0] >= 784 and pygame.mouse.get_pos()[0] <= 1080:#delete 
                for x in range(3):
                    if pygame.mouse.get_pos()[1] >= (198 + 212*x) and pygame.mouse.get_pos()[1] <= (326 + 212*x) and len(courseList) - 3*page -x > 0:
                        courseList.pop(3*page+x) #delete
                        f = open("save.json","w") #open save file
                        f.write(json.dumps(courseList)) #updates file
                        f.close() 


        screen.blit(pygame.image.load("exit.png"),(64,48)) #back to previous menu
        screen.blit(pygame.image.load("new.png"),(64,134)) #makes new course
        if page > 0: #if previous page
            screen.blit(pygame.image.load("up.png"),(1152,198)) #up arrow
        if 3 * (page+1) < len(courseList): #if next page
            screen.blit(pygame.image.load("down.png"),(1152,626)) #down arrow

        for x in range(len(courseList)-(3*page)): #draws course info based on number of courses in a page
            if x < 3:
                screen.blit(pygame.image.load("courseInfo.png"),(192,212*x+134))  
                screen.blit(pygame.font.SysFont("impact",48).render(courseList[3*page+x]["Name"],True,(255,255,255)),Vector2(368,212*x+136))
                screen.blit(pygame.font.SysFont("impact",48).render(str(courseList[3*page+x]["Par"]),True,(255,255,255)),Vector2(944,212*x+136))

    elif mode == 3: #game game
        space.step(1/60)#moves sim forward each frame
        ball.updateClub(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1])
        
        if pygame.mouse.get_pressed()[pygame.BUTTON_LEFT-1]:
            if pygame.mouse.get_pos()[0] >= 1152 and pygame.mouse.get_pos()[0] <= 1216:
                if pygame.mouse.get_pos()[1] >= 48 and pygame.mouse.get_pos()[1] <= 112:#replay
                    ball, space, par, elements, term = loadCourse(currentCourse) #reloads course
                    ball.updateClub(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1]) #updates club so can be drawn
                elif pygame.mouse.get_pos()[1] >= 128 and pygame.mouse.get_pos()[1] <= 192:#quit
                    mode = 2
            else: #not button clicked
                ball.hit()

        elementDraw(elements,screen,ball)

        ball.voila(screen) #draws ball club and line to screen

        screen.blit(pygame.image.load("restart.png"),Vector2(1152,48)) #retry button and ui
        screen.blit(pygame.image.load("exit.png"),(1152,128)) #exit button
        screen.blit(pygame.font.SysFont("impact",64).render("Par: "+str(par),True,(255,255,255)),Vector2(32,32)) #par
        screen.blit(pygame.font.SysFont("impact",64).render("Stroke: "+str(ball.strokeCount),True,(255,255,255)),Vector2(32,96)) #stroke count

        screen.blit(pygame.font.SysFont("impact",64).render(term[0],True,(255,255,255)),Vector2(460,160)) #hole cleared
        screen.blit(pygame.font.SysFont("impact",64).render(term[1],True,(255,255,255)),Vector2(460,224)) #score output

    elif mode == 4: #course editor
        if event.type == pygame.MOUSEBUTTONDOWN and event.button  == 1 and just == False:
            just = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button  == 1 and just == True:
            just = False
            if pygame.mouse.get_pos()[0] >= 108 and pygame.mouse.get_pos()[0] <= 172 and pygame.mouse.get_pos()[1] >= 20 and pygame.mouse.get_pos()[1] <= 84 and possible == True:
                mode = 5 #save screen
            elif pygame.mouse.get_pos()[0] >= 20 and pygame.mouse.get_pos()[0] <= 84 and pygame.mouse.get_pos()[1] >= 20 and pygame.mouse.get_pos()[1] <= 84:
                mode = 2 #back to course list
            elif pygame.mouse.get_pos()[1] >= 720 and pygame.mouse.get_pos()[1] <= 784:
                for x in range(7):
                    if pygame.mouse.get_pos()[0] >= 224 + 128*x and pygame.mouse.get_pos()[0] <= 288 + 128*x:
                        currentElement = x
        if pygame.mouse.get_pressed()[pygame.BUTTON_LEFT-1]:
            p = placeElement(Vector2(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1]))
            if p != None:
                possible = p
        
        for x in range(len(grid)):
            for y in range(len(grid[x])):
                if grid[x][y] != 0: #no lag pretty please
                    screen.blit(pygame.transform.scale(pygame.image.load(elementImages[grid[x][y]]),(16,16)),Vector2(16*x+192,16*y))#mini element

        screen.blit(pygame.image.load("editor.png"),Vector2(0,0)) #editor ui
        if possible == True:
            screen.blit(pygame.image.load("save.png"),Vector2(108,20)) #save button
        screen.blit(pygame.image.load("select.png"),Vector2(224+128*currentElement,720)) #current element ring
        screen.blit(pygame.font.SysFont("impact",32).render(elementInfo[currentElement]["Name"],True,(255,255,255)),Vector2(8,100)) #Element Name
        screen.blit(pygame.font.SysFont("impact",16).render(elementInfo[currentElement]["Info"],True,(255,255,255)),Vector2(8,132)) #Element Info 1
        screen.blit(pygame.font.SysFont("impact",16).render(elementInfo[currentElement]["Info2"],True,(255,255,255)),Vector2(8,148)) #Element Info 2
        if TeeHolePos[0] == None: 
            screen.blit(pygame.font.SysFont("impact",16).render("Tee Needed",True,(255,0,0)),Vector2(8,622)) #No Tee Error
        if TeeHolePos[1] == None:
            screen.blit(pygame.font.SysFont("impact",16).render("Hole Needed",True,(255,0,0)),Vector2(8,638)) #No Hole Error
        screen.blit(pygame.transform.scale(pygame.image.load(elementImages[currentElement]),(12,12)),Vector2(pygame.mouse.get_pos()[0]-6,pygame.mouse.get_pos()[1]-6))#mini element
        if possible == False: #if error
            screen.blit(pygame.font.SysFont("impact",16).render("Course Impossible",True,(255,0,0)),Vector2(8,654)) #Imposiible
            redScreen = pygame.Surface((1280,800), pygame.SRCALPHA) 
            redScreen.fill((255,0,0,128)) 
            screen.blit(redScreen, (0,0))
            
    elif mode == 5: #save screen
        if event.type == pygame.MOUSEBUTTONDOWN and event.button  == 1 and just == False:
            just = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button  == 1 and just == True:
            just = False
            if pygame.mouse.get_pos()[0] >= 64 and pygame.mouse.get_pos()[0] <= 128 and pygame.mouse.get_pos()[1] >= 48 and pygame.mouse.get_pos()[1] <= 112:
                box = 0
                mode = 4
            elif pygame.mouse.get_pos()[0] >= 192 and pygame.mouse.get_pos()[0] <= 1088 and pygame.mouse.get_pos()[1] >= 144 and pygame.mouse.get_pos()[1] <= 336:
                box = 1
            elif pygame.mouse.get_pos()[0] >= 192 and pygame.mouse.get_pos()[0] <= 1088 and pygame.mouse.get_pos()[1] >= 368 and pygame.mouse.get_pos()[1] <= 560:
                box = 2
            elif pygame.mouse.get_pos()[0] >= 192 and pygame.mouse.get_pos()[0] <= 1088 and pygame.mouse.get_pos()[1] >= 592 and pygame.mouse.get_pos()[1] <= 784:
                box = 0
                if TeeHolePos[2] != "" and TeeHolePos[3] != "": #if name and par exist
                    if TeeHolePos[4] != None:
                        courseList.remove(TeeHolePos[4])
                    courseList.append({"Name": TeeHolePos[2], "Par": int(TeeHolePos[3]), "TeePosX": TeeHolePos[0].x,"TeePosY": TeeHolePos[0].y, "Grid" : grid, "HolePosX": TeeHolePos[1].x,"HolePosY": TeeHolePos[1].y})
                    f = open("save.json","w") #open save file
                    f.write(json.dumps(courseList)) #updates file
                    f.close()
                    mode = 2 #course list
            else:
                box = 0
        

        screen.blit(pygame.image.load("exit.png"),(64,48)) #back to previous menu
        screen.blit(pygame.image.load("namer.png"),(192,144)) #name box
        screen.blit(pygame.image.load("parer.png"),(192,368)) #par box
        screen.blit(pygame.image.load("saver.png"),(192,592)) #save box
        if TeeHolePos[2] == "" and box != 1: #if no entry and not selected
            screen.blit(pygame.font.SysFont("impact",60).render("Click Here To Enter Name",True,(200,200,200,128)),Vector2(448,202)) #text in name box
        else:
            screen.blit(pygame.font.SysFont("impact",64).render(TeeHolePos[2],True,(255,255,255)),Vector2(448,200)) #text in name box
        if TeeHolePos[3] == "" and box != 2: #if no entry and not selected
            screen.blit(pygame.font.SysFont("impact",60).render("Click Here To Enter Par",True,(200,200,200,128)),Vector2(384,426)) #text in par box
        else:
            screen.blit(pygame.font.SysFont("impact",64).render(str(TeeHolePos[3]),True,(255,255,255)),Vector2(384,424)) #text in par box

    pygame.display.flip()#updates display
    pygame.time.Clock().tick(60)  # limits FPS to 60
    screen.fill((161, 240, 19))#fill screen to override last frame

pygame.quit()