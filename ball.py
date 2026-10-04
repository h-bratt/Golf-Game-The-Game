import pygame
from pygame.math import Vector2
import pymunk
from pymunk import Vec2d
import math

class Ball():
    def __init__(self,position,s):
        self.body = pymunk.Body() #creates pymunk body
        self.body.position = position
        self.previousPosition = position #for water hazard
        self.shape = pymunk.Circle(self.body, 0.5) # Create a circle shape and attach to body
        self.shape.mass = 10
        self.shape.elasticity = 0.6
        self.shape.collision_type = 0
        s.add(self.body,self.shape)
        self.image = pygame.image.load("ball.png")
        self.clubImage = pygame.image.load("club.png")
        self.clubPosition = Vector2(0,0) #pixels
        self.maxRadius = 320 #max distance of ball from club in pixels
        self.minRadius = 32 #min distance of ball from club in pixels
        self.lineColour = (255,0,0,255)
        self.Vmax = 15
        self.inRough = 0 #number of roughs in
        self.holed = False #game over?
        self.strokeCount = 0

    def updateClub(self,mouseX,mouseY): #updates club position and rotation
        self.clubPosition = Vector2(mouseX-32,mouseY-32) #set club position
        theta = math.atan((self.clubPosition.x-608)/(self.clubPosition.y-368+0.00000000000001)) #angle of club
        self.clubImage = pygame.image.load("club.png")#reorients club each frame
        if self.clubPosition.y < 368: #flips angle if should be > 180 degrees
            theta += math.pi
        if (self.clubPosition.x-608) **2 + (self.clubPosition.y-368) **2 > self.maxRadius **2:
            self.clubPosition = Vector2(608+self.maxRadius*math.sin(theta),368+self.maxRadius*math.cos(theta))
        elif (self.clubPosition.x-608) **2 + (self.clubPosition.y-368) **2 < self.minRadius **2:
            self.clubPosition = Vector2(608+self.minRadius*math.sin(theta),368+self.minRadius*math.cos(theta))
        theta = 360*theta/(2*math.pi) #convert to degrees
        self.clubImage = pygame.transform.rotate(self.clubImage,theta) #rotate club to face ball
    
    def updateLine(self): #changes line colour based on absolute clubPosition / maxRadius
        g = 255 * (1-(math.sqrt((self.clubPosition.x-608) **2 + (self.clubPosition.y-368) **2)/self.maxRadius)) 
        self.lineColour = (255,g,0,255)
        return(self.lineColour)
    
    def voila(self,screen): #draws ball club and line to screen
        if self.holed == False: #if not in hole
            if abs(self.body.velocity.x) <= 0.04 and abs(self.body.velocity.y) <= 0.04: #if not visually moving
                pygame.draw.line(screen,self.updateLine(),(640,400),(self.clubPosition.x+32,self.clubPosition.y+32),16)
            screen.blit(self.image,(608,368)) #puts ball at screen's center
            if abs(self.body.velocity.x) <= 0.04 and abs(self.body.velocity.y) <= 0.04: #if not visually moving
                screen.blit(self.clubImage,self.clubPosition)
    
    def hit(self): #hits ball 
        if abs(self.body.velocity.x) <= 0.04 and abs(self.body.velocity.y) <= 0.04 and self.holed == False: #if not visually moving
            self.body.velocity = (-self.Vmax*(self.clubPosition.x-608)/self.maxRadius,-self.Vmax*(self.clubPosition.y-368)/self.maxRadius)
            self.previousPosition = self.body.position
            self.strokeCount += 1