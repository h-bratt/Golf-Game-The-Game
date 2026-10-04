import pygame
from pygame.math import Vector2
import pymunk
from pymunk import Vec2d

class Element():
    def __init__(self,position,s):
        self.body = pymunk.Body() #creates pymunk body
        self.body.position = position
        self.body.body_type = pymunk.Body.STATIC #non moving
        self.image = pygame.image.load("testIMG.png")
        self.shape = pymunk.Poly(self.body,[(0.5,0.5),(0.5,-0.5),(-0.5,-0.5),(-0.5,0.5)])
        
class Tee(Element):
    def __init__(self, position, s):
        super().__init__(position, s)
        self.image = pygame.image.load("tee.png")

class Wall(Element):
    def __init__(self, position, s):
        super().__init__(position, s)
        self.image = pygame.image.load("wall.png")
        self.shape.elasticity = 0.6
        s.add(self.body,self.shape)

class SensorElement(Element):
    def __init__(self, position, s):
        super().__init__(position, s)
        self.shape.sensor = True #doesn't collide
        s.add(self.body,self.shape)

class Rough(SensorElement):
    def __init__(self, position, s):
        super().__init__(position, s)
        self.image = pygame.image.load("rough.png")
        self.shape.collision_type = 1

class Bunker(SensorElement):
    def __init__(self, position, s):
        super().__init__(position, s)
        self.image = pygame.image.load("bunker.png")
        self.shape.collision_type = 2

class WaterHazard(SensorElement):
    def __init__(self, position, s):
        super().__init__(position, s)
        self.image = pygame.image.load("water.png")
        self.shape.collision_type = 3

class Hole(SensorElement):
    def __init__(self, position, s):
        super().__init__(position, s)
        self.image = pygame.image.load("hole.png")
        self.shape.collision_type = 4