import kivy
kivy.require('1.8.0')

from kivy.config import Config
Config.set('graphics','width','1280')
Config.set('graphics','height','720')

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, ObjectProperty, ListProperty
from kivy.properties import ReferenceListProperty, DictProperty
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.core.audio import SoundLoader
from kivy.vector import Vector
from random import uniform, randint
from math import log10

'''
---Square Pond, an ecology game---

Square Pond - Version 0.91
Copyright (C) 2014 Kris Shamloo

Made with Kivy.

Music and sound by Wes Shamloo
http://braincat.bandcamp.com/

Game by Kris Shamloo
http://explorevulcan.com

TODO
balance teeth
adjust big and drifter colors
more organisms
more complexity
extend game border
'''

########## Organism Classes ####################################################

#--------- Plant --------------------------------------------------------------#
class Plant(Widget):

    mass = NumericProperty(20.0)
    bal = NumericProperty(1.0)
    
    neighbors = 0
    growth = 0.2
    clock = 0
    bound = True
    leaving = False
    cangrow = True
    
    type = 'Plant'
 
    def grow(self):
        g = self.growth
        self.mass += g
        self.x -= g/2
        self.y -= g/2
    
    def touchgrow(self):
        if self.cangrow:
            self.mass += 2.0
            self.x -= 1.0
            self.y -= 1.0

    def shrink(self, bite):
        self.mass -= bite
        self.x += bite/2
        self.y += bite/2

#--------- Base Square --------------------------------------------------------#
class Square(Widget):

    mass = NumericProperty(20.0)
    bal = NumericProperty(1.0)
    dx = NumericProperty(1.0)
    dy = NumericProperty(1.0)
    v = ReferenceListProperty(dx, dy)    
    
    clock = 0
    decay = 0.01
    bound = True
    leaving = False
    caneat = True

    type = 'Square'

    def move(self):
        self.pos = Vector(*self.v) + self.pos
        
    def eat(self, target, t):
        bite = self.mass
        g = (bite * self.bal)/2
        self.x -= g/2
        self.y -= g/2
        self.mass += g
        self.caneat = False
        self.clock = t + 4

        # try to swim in the direction of discovered food
        if target.center_x > self.center_x:
            self.dx = uniform(.05, .1)
        else:
            self.dx = uniform(-.05, -.1)        
        if target.center_y > self.center_y:
            self.dy = uniform(.05, .1)
        else:
            self.dy = uniform(-.05, -.1)        

        target.shrink(bite)

    def resume(self):
        self.dx = uniform(-1.5, 1.5)
        self.dy = uniform(-1.5, 1.5)
        self.caneat = True
        
    def shrink(self):
        d = self.decay * self.bal
        self.mass -= d
        self.x += d/2
        self.y += d/2

    def flee(self, attacker, t):
        self.clock = t + 1
        jx = attacker.center_x - self.center_x
        jy = attacker.center_y - self.center_y
        
        if (abs(jx) >= abs(jy)):
            if jx >= 0:
                self.dx = -1.5
                self.dy = (-1.5*jy)/abs(jx)
            else:
                self.dx = 1.5
                self.dy = (-1.5*jy)/abs(jx)
        elif (abs(jy) > abs(jx)):
            if jy >= 0:
                self.dy = -1.5
                self.dx = (-1.5*jx)/abs(jy)
            else:
                self.dy = 1.5
                self.dx = (-1.5*jx)/abs(jy)
        else:
            pass

#--------- Tooth --------------------------------------------------------------#
class Tooth(Widget):

    mass = NumericProperty(30.0)
    bal = NumericProperty(1.0)
    dx = NumericProperty(2.0)
    dy = NumericProperty(2.0)
    v = ReferenceListProperty(dx, dy)

    clock = 0
    huntclock = 0
    decay = 0.005
    bound = False
    leaving = False
    caneat = True
    frozen = False

    type = 'Tooth'

    def move(self):
        self.pos = Vector(*self.v) + self.pos
        
    def eat(self, target, t):
        bite = self.mass
        g = (bite * self.bal)/2
        self.dx = uniform(-.1, .1)
        self.dy = uniform(-.1, .1)
        self.x -= g/2
        self.y -= g/2
        self.mass += g
        self.caneat = False
        self.clock = t + 4
        
    def resume(self):
        self.dx = uniform(-2.0, 2.0)
        self.dy = uniform(-2.0, 2.0)
        self.caneat = True
        
    def shrink(self):
        d = self.decay * self.bal
        self.mass -= d
        self.x += d/2
        self.y += d/2
            
    def freeze(self):
        if(not self.frozen):
            self.dx = 0
            self.dy = 0
            self.frozen = True
        elif(self.frozen):
            self.resume()
            self.frozen = False

    def hunt(self, target, t):
        self.huntclock = t + 15*(1/self.bal)
        jx = target.center_x - self.center_x
        jy = target.center_y - self.center_y
        
        # which value is bigger, maintain ratio with respect to max speed (2.0)
        if (abs(jx) >= abs(jy)):
            # dx should be positive, my if zero edge-case handling here is meh
            if jx >= 0:
                self.dx = 2.0
                self.dy = (2.0*jy)/abs(jx)
            # dx should be negative
            else:
                self.dx = -2.0
                self.dy = (2.0*jy)/abs(jx)
        elif (abs(jy) > abs(jx)):
            if jy >= 0:
                self.dy = 2.0
                self.dx = (2.0*jx)/abs(jy)
            else:
                self.dy = -2.0
                self.dx = (2.0*jx)/abs(jy)
        else:
            pass
            
    def flee(self, attacker, t):
        self.clock = t + 1
        jx = attacker.center_x - self.center_x
        jy = attacker.center_y - self.center_y
        
        # same as hunt but with +/- signs reversed
        if (abs(jx) >= abs(jy)):
            if jx >= 0:
                self.dx = -2.0
                self.dy = (-2.0*jy)/abs(jx)
            else:
                self.dx = 2.0
                self.dy = (-2.0*jy)/abs(jx)
        elif (abs(jy) > abs(jx)):
            if jy >= 0:
                self.dy = -2.0
                self.dx = (-2.0*jx)/abs(jy)
            else:
                self.dy = 2.0
                self.dx = (-2.0*jx)/abs(jy)
        else:
            pass

#--------- Big ----------------------------------------------------------------#
class Big(Widget):

    mass = NumericProperty(40.0)
    bal = NumericProperty(1.0)
    dx = NumericProperty(1.0)
    dy = NumericProperty(1.0)
    v = ReferenceListProperty(dx, dy)    
    
    clock = 0
    decay = 0.005
    bound = False
    leaving = False
    caneat = True

    type = 'Big'

    def move(self):
        self.pos = Vector(*self.v) + self.pos
        
    def eat(self, target, t):
        bite = (self.mass * self.bal)/5
        self.x -= bite/2
        self.y -= bite/2
        self.mass += bite
        self.caneat = False
        self.clock = t + 4

        if target.center_x > self.center_x:
            self.dx = uniform(.05, .1)
        else:
            self.dx = uniform(-.05, -.1)        
        if target.center_y > self.center_y:
            self.dy = uniform(.05, .1)
        else:
            self.dy = uniform(-.05, -.1)        
        
        target.shrink(bite)

    def resume(self):
        self.dx = uniform(-1.5, 1.5)
        self.dy = uniform(-0.5, 0.5)
        self.caneat = True
        
    def shrink(self):
        d = self.decay * self.bal
        self.mass -= d
        self.x += d/2
        self.y += d/2
        
    def leave(self):
        self.bound = False
        self.caneat = False
        self.leaving = True
        self.dy = uniform(-1, -0.5)
        self.dx = uniform(-0.5, 0.5)
      
    def flee(self, attacker, t):
        self.clock = t + 1
        jx = attacker.center_x - self.center_x
        jy = attacker.center_y - self.center_y
        
        if (abs(jx) >= abs(jy)):
            if jx >= 0:
                self.dx = -1.0
                self.dy = (-1.0*jy)/abs(jx)
            else:
                self.dx = 1.0
                self.dy = (-1.0*jy)/abs(jx)
        elif (abs(jy) > abs(jx)):
            if jy >= 0:
                self.dy = -1.0
                self.dx = (-1.0*jx)/abs(jy)
            else:
                self.dy = 1.0
                self.dx = (-1.0*jx)/abs(jy)
        else:
            pass

    def touchflee(self, touch, t):
        self.clock = t + 1
        jx = touch.x - self.center_x
        jy = touch.y - self.center_y
        
        if (abs(jx) >= abs(jy)):
            if jx >= 0:
                self.dx = -1.0
                self.dy = (-1.0*jy)/abs(jx)
            else:
                self.dx = 1.0
                self.dy = (-1.0*jy)/abs(jx)
        elif (abs(jy) > abs(jx)):
            if jy >= 0:
                self.dy = -1.0
                self.dx = (-1.0*jx)/abs(jy)
            else:
                self.dy = 1.0
                self.dx = (-1.0*jx)/abs(jy)
        else:
            pass
        
#--------- Drifter ------------------------------------------------------------#
class Drifter(Widget):

    mass = NumericProperty(60.0)
    bal = NumericProperty(1.0)
    dx = NumericProperty(1.0)
    dy = NumericProperty(1.0)
    v = ReferenceListProperty(dx, dy)    
    
    clock = 0
    decay = 0.005
    bound = False
    leaving = True
    caneat = False
    goslow = True

    type = 'Drifter'

    def move(self):
        self.pos = Vector(*self.v) + self.pos
        
    def leave_fast(self):
        self.dy = uniform(-.5, -0.25)
        self.goslow = True
        
    def leave_slow(self):
        self.dy = uniform(-.1, -0.05)
        self.goslow = False
        
    def reverse(self):
        if self.top < root.height:
            self.dy = .5

#--------- Apex ---------------------------------------------------------------#
class Apex(Widget):

    mass = NumericProperty(80.0)
    bal = NumericProperty(1.0)
    dx = NumericProperty(2.0)
    dy = NumericProperty(2.0)
    v = ReferenceListProperty(dx, dy)

    clock = 0
    huntclock = 0
    decay = 0.005
    bound = False
    leaving = False
    caneat = False
    doresume = False
    leaving = False
    
    type = 'Apex'

    def move(self):
        self.pos = Vector(*self.v) + self.pos
        
    def eat(self, target, t):
        bite = self.mass
        g = (bite * self.bal)/3
        self.dx = uniform(-.1, .1)
        self.dy = uniform(-.1, .1)
        self.x -= g/2
        self.y -= g/2
        self.mass += g
        self.caneat = False
        self.clock = t + 8
        self.doresume = True
        
    def resume(self):
        self.dx = uniform(-1.0, 1.0)
        self.dy = uniform(-1.0, 1.0)
        self.caneat = False
        self.doresume = False
        
    def shrink(self):
        d = self.decay * self.bal
        self.mass -= d
        self.x += d/2
        self.y += d/2
            
    def leave(self, t):
        self.bound = False
        self.caneat = False
        self.doresume = False
        self.leaving = True
        self.dy = uniform(-1, -0.5)
        self.dx = uniform(-0.5, 0.5)
        self.huntclock = t + 100000

    def hunt(self, target,t):
        self.caneat = True
        self.doresume = True
        self.huntclock = t + 10
        self.clock = t + 2
        jx = target.center_x - self.center_x
        jy = target.center_y - self.center_y
        
        # which value is bigger, maintain ratio with respect to max speed (4.0)
        if (abs(jx) >= abs(jy)):
            # dx should be positive, my if zero edge-case handling here is meh
            if jx >= 0:
                self.dx = 4.0
                self.dy = (4.0*jy)/abs(jx)
            # dx should be negative
            else:
                self.dx = -4.0
                self.dy = (4.0*jy)/abs(jx)
        elif (abs(jy) > abs(jx)):
            if jy >= 0:
                self.dy = 4.0
                self.dx = (4.0*jx)/abs(jy)
            else:
                self.dy = -4.0
                self.dx = (4.0*jx)/abs(jy)
        else:
            pass
            
#--------- Menu --------------------------------------------------------------#
class Menu(Widget):

    mass = NumericProperty(400.0)
    bal = NumericProperty(1)
    dx = NumericProperty(1.0)
    dy = NumericProperty(1.0)
    v = ReferenceListProperty(dx, dy)
    clock = 0
    bound = True
    leaving = False
    cangrow = True
    
    type = 'Menu'
    def move(self):
        self.pos = Vector(*self.v) + self.pos 

#--------- End ----------------------------------------------------------------#
class End(Widget):

    mass = NumericProperty(400.0)
    bal = NumericProperty(1)
    dx = NumericProperty(1.0)
    dy = NumericProperty(1.0)
    v = ReferenceListProperty(dx, dy)
    clock = 0
    bound = True
    leaving = False
    cangrow = True
    a_score = NumericProperty(0)
    p_score = NumericProperty(0)

    type = 'End'
    def move(self):
        self.pos = Vector(*self.v) + self.pos

########## Game Class ##########################################################

class Game(Widget):
    cl = ListProperty([])
    toothclock = 0
    bigclock = 0
    drifterclock = 0
    apexclock = 0
    canhide = False
    canseed = False
    squaresound = True
    plantlimit = 16    
    ticks = 0
    a_score = 0
    p_score = 0
    
    start_sound = SoundLoader.load('media/Start_Button.mp3')
    game_music = SoundLoader.load('media/ecomusic.mp3')
    eat1 = SoundLoader.load('media/Eat_1.mp3')
    eat2 = SoundLoader.load('media/Eat_2.mp3')
    eat3 = SoundLoader.load('media/Eat_3.mp3')
    eat4 = SoundLoader.load('media/Eat_4.mp3')
    eat5 = SoundLoader.load('media/Eat_5.mp3')
    eat6 = SoundLoader.load('media/Eat_6.mp3')
    eat7 = SoundLoader.load('media/Eat_7.mp3')
    # track 8 is for teeth
    eat8 = SoundLoader.load('media/Eat_8.mp3')
    eat9 = SoundLoader.load('media/Eat_9.mp3')
    
    eatsfx = [eat1,eat2,eat3,eat4,eat5,eat6,eat7,eat9,eat8]
    
    for i in range(len(eatsfx)):
        eatsfx[i].volume = 0.4

    # create a plant
    def on_touch_up(self, touch):
        
        for child in self.children:
            if child.collide_point(*touch.pos):
                if child.type == 'Menu' or child.type == 'End':
                    self.remove_widget(child)
                    self.cl.remove(child)
                    Clock.schedule_once(root.first_square)
                    Clock.schedule_interval(root.balance, 1.0)
                    self.canseed = True
                    self.a_score = 0
                    self.p_score = 0
                    self.plantlimit = 16
                    
                    if self.start_sound:
                        #self.start_sound.play()
                        pass
                        
                    if self.game_music:
                        #self.game_music.play()
                        #self.game_music.loop = True
                        pass

                elif child.type == 'Tooth':
                    child.freeze()
                elif child.type == 'Big':
                    t = Clock.get_boottime()
                    child.touchflee(touch, t)    
                elif child.type == 'Drifter':
                    child.reverse()

                return
                
        if self.canseed:    
            p = Plant(pos=(touch.x-10, touch.y-10))
            p.clock = Clock.get_boottime()
            self.add_widget(p)
            self.cl.append(p)
       
    def on_touch_move(self, touch):
        for child in self.children:
            if child.collide_point(*touch.pos):
                if child.type == 'Square':
                    child.center_x = touch.x
                    child.center_y = touch.y
                    
                elif child.type == 'Plant':
                    child.touchgrow()
                    
    # create the start menu
    def open_menu(self, dt):
        m = Menu()
        m.x = randint(0, self.width-m.mass)
        m.y = randint(0, self.height-m.mass)
        m.clock = Clock.get_boottime()
        m.dx = uniform(-0.3,0.3)
        m.dy = uniform(-0.3,0.3)
        self.add_widget(m)
        self.cl.append(m)

    # create the end menu
    def open_end(self, dt):
        e = End()
        e.x = randint(0, self.width-e.mass)
        e.y = randint(0, self.height-e.mass)
        e.clock = Clock.get_boottime()
        e.dx = uniform(-0.3,0.3)
        e.dy = uniform(-0.3,0.3)
        e.a_score = self.a_score
        e.p_score = self.p_score
        self.add_widget(e)
        self.cl.append(e)

    # create the first square
    def first_square(self, dt):
        s = Square()
        s.x = randint(0, self.width-s.mass)
        s.y = randint(0, self.height-s.mass)
        s.clock = Clock.get_boottime()
        s.dx = uniform(-1.5,1.5)
        s.dy = uniform(-1.5,1.5)
        self.add_widget(s)
        self.cl.append(s)
        
    # create a child square    
    def new_square(self, x, y):
        s = Square()
        s.center_x = x
        s.center_y = y
        s.clock = Clock.get_boottime()
        s.dx = uniform(-1.5,1.5)
        s.dy = uniform(-1.5,1.5)
        
        self.add_widget(s)
        self.cl.append(s)
        
    # create the first tooth
    def first_tooth(self, dt):
        t = Tooth()
        t.x = randint(self.width/4, 3*self.width/4)
        t.y = randint(self.height+25,self.height+125)
        t.clock = Clock.get_boottime()
        t.huntclock = Clock.get_boottime() + 3
        t.dx = uniform(-2.0, 2.0)
        t.dy = uniform(-2.0, -1.0)
        t.mass = 35.0
        self.add_widget(t)
        self.cl.append(t)    
        
    # create a child tooth    
    def new_tooth(self, x, y):
        t = Tooth()
        t.center_x = x
        t.center_y = y
        t.clock = Clock.get_boottime()
        t.dx = uniform(-2.0, 2.0)
        t.dy = uniform(-2.0, 2.0)
        
        self.add_widget(t)
        self.cl.append(t)

    # create the first big
    def first_big(self, dt):
        b = Big()
        b.x = randint(self.width/4, 3*self.width/4)
        b.y = randint(self.height+40,self.height+140)
        b.clock = Clock.get_boottime()
        b.dx = uniform(-1.0, 1.0)
        b.dy = uniform(-.75, -.5)

        self.add_widget(b)
        self.cl.append(b)

    # create the first drifter
    def first_drifter(self, dt):
        d = Drifter()
        d.x = randint(self.width/4, 3*self.width/4)
        d.y = randint(self.height,self.height+40)
        d.clock = Clock.get_boottime()
        d.dx = uniform(-0.1, 0.1)
        d.dy = uniform(-.75, -.5)

        self.add_widget(d)
        self.cl.append(d)

    # create the first apex
    def first_apex(self, dt):
        a = Apex()
        a.x = randint(self.width/4, 3*self.width/4)
        a.y = randint(self.height+25,self.height+125)
        a.clock = Clock.get_boottime()
        a.huntclock = Clock.get_boottime() + 10
        a.dx = uniform(-1.0, 1.0)
        a.dy = uniform(-1.5, -.5)

        self.add_widget(a)
        self.cl.append(a)        

#--------- Fast Update Cycle --------------------------------------------------#

    def update(self, dt):

        t = Clock.get_boottime()
        kill = []
        create = []
        squares = []
        
        for i in range(len(self.cl)):
            
            # collision behavior ----------------------------------------------#
            for j in range(len(self.cl)):

                if (i != j and self.cl[i].type != 'Plant' and self.cl[i].collide_widget(self.cl[j])):
                    if (self.cl[i].type == 'Big'):                      
                        # bigs eat plants
                        if (self.cl[j].type == 'Plant' and self.cl[i].caneat):
                            self.cl[i].eat(self.cl[j], t)

                    if (self.cl[i].type == 'Square'):
                        # squares eat plants           
                        if (self.cl[j].type == 'Plant' and self.cl[i].caneat):
                            self.cl[i].eat(self.cl[j], t)
                            track = randint(0,7)
                            if self.eatsfx[track] and self.squaresound:
                                self.eatsfx[track].play()
                                self.squaresound = False

                        # teeth eat squares    
                        if (self.cl[j].type == 'Tooth'):
                            self.cl[i].flee(self.cl[j], t)
                            if (self.cl[j].mass >= self.cl[i].mass and self.cl[j].caneat):
                                self.cl[j].eat(self.cl[i], t)
                                kill.append(i)
                                if self.eatsfx[8]:
                                    self.eatsfx[8].play()
                    
                    # apexes eat teeth and bigs (only during a hunting attack)               
                    if (self.cl[i].type == 'Apex'):
                        if (self.cl[j].type == 'Tooth' and self.cl[i].caneat):
                            self.cl[i].eat(self.cl[j], t)
                            kill.append(j)
                        if (self.cl[j].type == 'Big' and self.cl[i].caneat):
                            self.cl[i].eat(self.cl[j], t)
                            kill.append(j)
                        if (self.cl[j].type == 'Square'):
                            self.cl[j].flee(self.cl[i], t)
                            
                    # bounce off of drifters
                    if (self.cl[i].type == 'Drifter'):
                        if (self.cl[j].type != 'Plant' and self.cl[j].type != 'Apex' and self.cl[j].type != 'Drifter' and self.cl[j].bound):
                            self.cl[j].flee(self.cl[i], t)

                # Apex hunting and prey fleeing, can hunt any tooth          
                if (i != j and self.cl[i].type == 'Apex' and self.cl[j].type == 'Tooth'):
                    d = Vector(self.cl[i].center).distance(self.cl[j].center)
                    if (d < 300 and t > self.cl[i].huntclock and self.cl[i].bound):
                        self.cl[i].hunt(self.cl[j], t)
                    if (d < 150 and self.cl[j].bound):
                        self.cl[j].flee(self.cl[i], t)

                # can hunt smaller bigs
                if (i != j and self.cl[i].type == 'Apex' and self.cl[j].type == 'Big'):
                    if (self.cl[i].mass-20 > self.cl[j].mass):
                        d = Vector(self.cl[i].center).distance(self.cl[j].center)
                        if (d < 300 and t > self.cl[i].huntclock and self.cl[i].bound):
                            self.cl[i].hunt(self.cl[j], t)
                        if (d < 200 and self.cl[j].bound):
                            self.cl[j].flee(self.cl[i], t)
                            
            # non collision behavior ------------------------------------------#

            # Plant
            if self.cl[i].type == 'Plant':    
                # plants grow if less than max size
                if self.cl[i].cangrow:
                    self.cl[i].grow()
                
                # die if too small
                if self.cl[i].mass < 5:
                    kill.append(i)
                
                # allow plant to grow if less than max size
                if (not self.cl[i].cangrow and self.cl[i].mass <= self.height/2):
                    self.cl[i].cangrow = True
                    self.canhide = False    

                # limit max size of plants, allow Hides to appear
                elif self.cl[i].mass > self.height/2:
                    self.cl[i].cangrow = False
                    self.canhide = True

            # Square
            if (self.cl[i].type == 'Square'):
                # tally up squares for targeting
                squares.append(i)
                
                # shrink squares
                self.cl[i].shrink()
                
                # resume wandering after eating
                if (not self.cl[i].caneat and t > self.cl[i].clock):
                    self.cl[i].resume()
                
                # die if too small    
                if (self.cl[i].mass < 10):
                    kill.append(i)
                    
                # reproduce if large enough
                if (self.cl[i].caneat and self.cl[i].mass > 40):
                    x1 = self.cl[i].center_x + randint(-15,-5)
                    y1 = self.cl[i].center_y + randint(-15,15)
                    x2 = self.cl[i].center_x + randint(5,15)
                    y2 = self.cl[i].center_y + randint(-15,15)
                    
                    kill.append(i)
                    create.append(['Square',x1,y1])
                    create.append(['Square',x2,y2])

            # Big
            if (self.cl[i].type == 'Big'):
                # shrink bigs
                self.cl[i].shrink()
                
                # resume wandering after eating or fleeing            
                if (not self.cl[i].caneat and t > self.cl[i].clock and self.cl[i].bound):
                    self.cl[i].resume()    
                
                # die if too small
                if (self.cl[i].mass < 20):
                    kill.append(i)
                
                # leave if large enough                    
                if (self.cl[i].mass > 120 and not self.cl[i].leaving):
                    self.cl[i].leave()
            
            # Drifter
            if (self.cl[i].type == 'Drifter'):
                # oscillate fast and slow
                if (t > self.cl[i].clock):
                    if (not self.cl[i].goslow):
                        self.cl[i].leave_fast()
                        self.cl[i].clock = t + 2
                    elif (self.cl[i].goslow):
                        self.cl[i].leave_slow()
                        self.cl[i].clock = t + 8

            # Tooth
            if (self.cl[i].type == 'Tooth'):
                # shrink teeth
                self.cl[i].shrink()
                
                # resume wandering after eating
                if (not self.cl[i].caneat and t > self.cl[i].clock):
                    self.cl[i].resume()
                
                # die if too small    
                if (self.cl[i].mass < 15):
                    kill.append(i)
                    
                # reproduce if large enough
                if (self.cl[i].caneat and self.cl[i].mass > 80):
                    x1 = self.cl[i].center_x + randint(-15,5)
                    y1 = self.cl[i].center_y + randint(-15,15)
                    x2 = self.cl[i].center_x + randint(5,15)
                    y2 = self.cl[i].center_y + randint(-15,15)                   

                    kill.append(i)
                    create.append(['Tooth',x1,y1])
                    create.append(['Tooth',x2,y2])
                    
                # hunt squares, randomly target a square
                if (self.cl[i].caneat and t > self.cl[i].huntclock):
                    if (len(squares) > 0):
                        tgt = randint(0,len(squares))
                        try:
                            self.cl[i].hunt(self.cl[squares[tgt]], t)
                        except:
                            pass
                
            # Apex
            if (self.cl[i].type == 'Apex'):
                # shrink apexes
                self.cl[i].shrink()
                
                # resume wandering if needed
                if (t > self.cl[i].clock and self.cl[i].doresume):
                    self.cl[i].resume()
           
                # leave if large enough or if too small
                if (self.cl[i].mass > 140 or self.cl[i].mass < 40):
                    if (not self.cl[i].leaving):
                        self.cl[i].leave(t)          
            
            # move organisms that can move ------------------------------------#
            if (self.cl[i].type != 'Plant' and self.cl[i].bound):

                # bounce off left
                if (self.cl[i].x <= 0):
                    self.cl[i].x = 0
                    self.cl[i].dx *= -1

                # bounce off right   
                elif (self.cl[i].right >= self.width):
                    self.cl[i].right = self.width
                    self.cl[i].dx *= -1
                    
                # bounce off bottom
                if (self.cl[i].y <= 0):
                    self.cl[i].y = 0
                    self.cl[i].dy *= -1
                    
                # bounce off top
                if (self.cl[i].top >= self.height):
                    self.cl[i].top = self.height
                    self.cl[i].dy *= -1
                
                # move organism
                self.cl[i].move()
            
            # unbound organisms move into game space --------------------------#    
            if (not self.cl[i].bound and not self.cl[i].leaving):
                if (self.cl[i].top < self.height):
                    self.cl[i].bound = True
                self.cl[i].move()
            
            # unbound organisms move out of game space ------------------------#    
            if (not self.cl[i].bound and self.cl[i].leaving):
                if (self.cl[i].top < -10):
                    kill.append(i)
                self.cl[i].move()
                
        # kill, start from the end of the creature list to preserve order -----#        
        for i in range(len(kill)-1, -1, -1):
            try:
                self.remove_widget(self.cl[kill[i]])
                self.cl.remove(self.cl[kill[i]])
            except:
                pass

        # create, ['type',pos(x),pos(y)] --------------------------------------#        
        for i in range(len(create)):
            if (create[i][0] == 'Square'):
                self.new_square(create[i][1], create[i][2])
            elif (create[i][0] == 'Tooth'):
                self.new_tooth(create[i][1], create[i][2])
            else:
                pass

#--------- Slow Update Cycle --------------------------------------------------#                
    def balance(self, dt):
        
        self.ticks += 1
        plants = 0
        squares = 0
        teeth = 0
        bigs = 0
        drifters = 0
        apexes = 0
        species = 0
        t = Clock.get_boottime()
        
        for i in range(len(self.cl)):
            if self.cl[i].type == 'Plant':
                plants += 1
            elif self.cl[i].type == 'Square':
                squares += 1                
            elif self.cl[i].type == 'Tooth':
                teeth += 1
            elif self.cl[i].type == 'Big':
                bigs += 1
            elif self.cl[i].type == 'Drifter':
                drifters += 1
            elif self.cl[i].type == 'Apex':
                apexes += 1
        
        # create a tooth if conditions allow      
        if (teeth < 1 and squares > 10 and t > self.toothclock):
            self.toothclock = t + 20
            Clock.schedule_once(self.first_tooth)
            
        # create a big if conditions allow
        if (teeth > 3 and squares > 20 and plants > 3 and t > self.bigclock):
            self.bigclock = t + 20
            Clock.schedule_once(self.first_big)

        # create a drifter if conditions allow
        if (bigs > 2 and drifters < 2 and t > self.drifterclock):
            self.drifterclock = t + 30                        
            Clock.schedule_once(self.first_drifter)
            
        # create an apex if conditions allow
        if (teeth > 4 and apexes < teeth/3 and t > self.apexclock):
            self.apexclock = t + 40
            Clock.schedule_once(self.first_apex)

        # slow down square growth and decay
        if (squares > 0 and Square.bal > 0.01):        
            Square.bal = 1.0 - log10(squares)/2      
        
        # slow down tooth growth and decay
        if (teeth > 0 and Tooth.bal > 0.2):
            Tooth.bal = 1.0 - (teeth * .1)

        # limit total plants            
        if (plants >= self.plantlimit):
            self.canseed = False
        elif (plants < self.plantlimit):
            self.canseed = True            

        # calculate score
        if plants > 0:
            species += 1
        if squares > 0:
            species += 1
        if teeth > 0:
            species += 1
        if bigs > 0:
            species += 1
        if drifters > 0:
            species += 1
        if apexes > 0:
            species += 1
            
        temp_peak = (plants + squares*3 + teeth*6 + bigs*9 + drifters*12 + apexes*15) * species
        if (temp_peak > self.p_score):
            self.p_score = temp_peak
            
        self.a_score += temp_peak
            
        # limit square sfx to once per second
        if not self.squaresound:
            self.squaresound = True
        
        # reduce available seeds
        if self.ticks > 60 and self.ticks % 20 == 0 and self.plantlimit > 0:
            self.plantlimit -= 1
            
        # check lose-state
        if (squares < 1):
            print("You lost dude.")
            Clock.unschedule(self.update)
            Clock.unschedule(self.balance)
            self.canseed = False
            self.cl = []
            self.clear_widgets(self.children)
            
            self.a_score = self.a_score/self.ticks    
            Clock.schedule_interval(self.update, 1.0/60.0)
            self.open_end(self)

        # debugging data
        '''
        print("Total plants:",plants)
        print("Total squares:",squares)
        print("Total teeth:",teeth)
        print("Total bigs:",bigs)
        print("list should be",plants+squares+teeth+bigs+drifters+apexes)
        print("list length is", len(self.cl))
        print("FPS:", Clock.get_rfps())
        '''

########## App Class ###########################################################        

root = ObjectProperty(None)

class SquarePond(App):

    def build(self):
        global root
        root = Game()
        Clock.schedule_once(root.open_menu)
        Clock.schedule_interval(root.update, 1.0/60.0)
        return root
        
########## Giddyup #############################################################   
if __name__ == '__main__':
    SquarePond().run()
