import pygame
import random
import sys
import numpy as np

# 1. Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 1500, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Da Boids")
clock = pygame.time.Clock()
obstacle = np.zeros((WIDTH, HEIGHT))
scale = 5

def add_rectangle(screen, obstacle, x1, y1, x2, y2):
    obstacle[x1:x2, y1:y2] = 1
    pygame.draw.rect(
    screen,
    (255,0,0),
    pygame.Rect(x1,y1,x2-x1,y2-y1)
)
    

def add_circle(screen, obstacle, cx, cy, r):

    for x in range(cx-r, cx+r+1):
        for y in range(cy-r, cy+r+1):

            if (x-cx)**2 + (y-cy)**2 <= r**2:

                if 0 <= x < WIDTH and 0 <= y < HEIGHT:
                    obstacle[x,y] = 1
    
    pygame.draw.circle(
    screen,
    (255,0,0),
    (cx,cy),
    r
)

class Zombie:
    '''
    Properties of a Zombie:
    1. Runs away if it meets a group of 5+ civilians
    2. Have a normal view radius
    3. Attacks the nearest Civilian and avoids other Zombies
    '''
    def __init__(self):
        self.x = random.randint(20, WIDTH - 20)
        self.y = random.randint(20, HEIGHT - 20)
        while obstacle[self.x, self.y] == 1:
            self.x = random.randint(20, WIDTH - 20)
            self.y = random.randint(20, HEIGHT - 20)
        self.radius = 100
        self.size = 10
        self.view = 2*np.pi
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-4, 4)
        self.color = (0, 255, 0)
        #self.alpha = random.randint(100, 255)
        self.alpha = 255
        self.nearestciv = []
        self.nearzomb = []
        self.nociv = 0
        self.nearciv = []
    def move(self):
        # Apply velocity vectors
        self.x += self.vx
        self.y += self.vy
        
    def get_triangle(self):
        angle = np.arctan2(self.vy, self.vx)
        self.x = self.size + (self.x-self.size)%(WIDTH - 2*self.size)
        self.y = self.size + (self.y-self.size)%(HEIGHT - 2*self.size)
        x1 = int(self.x + self.size*np.cos(angle))
        y1 = int(self.y + self.size*np.sin(angle))
        x2 = int(self.x + self.size*np.cos(angle + (150*np.pi/180)))
        y2 = int(self.y + self.size*np.sin(angle + (150*np.pi/180)))
        x3 = int(self.x + self.size*np.cos(angle + (210*np.pi/180)))
        y3 = int(self.y + self.size*np.sin(angle + (210*np.pi/180)))
        return (np.array([x1, y1]), np.array([x2, y2]), np.array([x3, y3]))
    
    def draw(self, surface): #Renders the triangle boid
        coords = list(self.get_triangle())
        pygame.draw.polygon(surface, self.color, coords)
        
    def find_neighbours(self, all_civ, all_zomb):
        self.nociv = 0
        self.nearciv = []
        if all_civ:
            self.nearestciv = [(all_civ[0], -1)]
        else:
            self.nearestciv = []
            return
        
        self.nearzomb = []
        distmin = 1500
        
        for civ in all_civ:
            dist2 = (self.x - civ.x)**2 + (self.y - civ.y)**2
            val = np.dot(np.array([civ.x - self.x, civ.y - self.y]), np.array([self.vx, self.vy]))
            
            if (dist2 < self.radius**2) and (dist2 > civ.size): #and (val > (np.cos(self.view/2))*(np.linalg.norm(np.array([boid.x - self.x, boid.y - self.y])))*(np.linalg.norm(np.array([self.vx, self.vy])))):
                if dist2 < distmin**2:
                    self.nearestciv[0] = (civ, dist2)
                    distmin = np.sqrt(dist2)
                self.nociv = self.nociv + 1
                self.nearciv.append((civ, dist2))
                
        a, b = self.nearestciv[0]
        if b == -1:
            self.nearestciv = []
                
        for zomb in all_zomb:
            dist2 = (self.x - zomb.x)**2 + (self.y - zomb.y)**2
            val = np.dot(np.array([zomb.x - self.x, zomb.y - self.y]), np.array([self.vx, self.vy]))
            if (dist2 < self.radius**2) and (dist2 > 0): #and (val > (np.cos(self.view/2))*(np.linalg.norm(np.array([boid.x - self.x, boid.y - self.y])))*(np.linalg.norm(np.array([self.vx, self.vy])))):
                self.nearzomb.append((zomb, dist2))
                
    def collision_avoidance(self): 
        F = np.zeros(2)
        for pair in self.nearzomb:
            zomb, dist2 = pair
            dist = np.sqrt(dist2)
            F = F + np.array([self.x - zomb.x, self.y - zomb.y])*((self.radius - dist))/(dist)
            #F = F + np.array([self.x - boid.x, self.y - boid.y])/(dist*(dist-2*self.size)*(dist-2*self.size)) #--> Coulomb force, does not have enough effect in enough time to prevent collisions
        return F
    
    def hunt_civ(self):
        if not self.nearestciv:
            return np.zeros(2)
        civ, dist2 = self.nearestciv[0]
        dist = np.sqrt(dist2)
        if dist > civ.size*2:
            F = np.array([civ.x - self.x, civ.y - self.y])*((self.radius - dist)/(dist))
        else:
            F = -np.array([self.vx, self.vy])*20
        return F
    
    def flock_fear(self):
        if self.nociv < 4:
            return np.zeros(2)
        ctr = 0
        centroid = np.zeros(2)
        for pair in self.nearciv: 
            civ, dist2 = pair
            centroid = ((centroid*ctr) + np.array([civ.x, civ.y]))/(ctr+1)
            ctr = ctr + 1

        F = -centroid + np.array([self.x, self.y])

        return F
    
    def update_velocity(self):
        k1 = 0.01
        k2 = 0.02
        k3 = 0.04
        F1 = self.collision_avoidance()

        F3 = self.flock_fear()
        if self.nociv < 4:
            F2 = self.hunt_civ()
            acc = k1*F1 + k2*F2 - 0.01*np.array([self.vx, self.vy])
        else:
            F3 = self.flock_fear()
            acc = k1*F1 + k3*F3 - 0.01*np.array([self.vx, self.vy])
        self.vx = self.vx + acc[0]/scale
        self.vy = self.vy + acc[1]/scale
        
    def obstacle_avoidance(self):
        delta_theta = 0.1
        angle = np.arctan2(self.vy, self.vx)
        r1 = 0
        r2 = 0
        flag1 = False
        flag2 = False
        for r in np.arange(self.size, self.radius, 1):
            x1, y1 = (np.clip(int(self.x + r*np.cos(angle + delta_theta)), 0, WIDTH-1), np.clip(int(self.y + r*np.sin(angle + delta_theta)), 0, HEIGHT-1))
            if obstacle[x1, y1] == 1:
                r1 = r
                flag1 = True
                break
        for r in np.arange(self.size, self.radius, 1):
            x2, y2 = (np.clip(int(self.x + r*np.cos(angle - delta_theta)), 0, WIDTH-1), np.clip(int(self.y + r*np.sin(angle - delta_theta)), 0, HEIGHT-1))
            if obstacle[x2, y2] == 1:
                r2 = r
                flag2 = True
                break
        if flag1 and flag2:
            v = np.array([y2 - y1, x1 - x2]) #Normal vector from obstacle surface
            v = v*((2*self.radius - r1 - r2))/(2*np.linalg.norm(v))
            #v = v*4/((np.linalg.norm(v))*((r1+r2)**2))
        else:
            v = np.zeros(2)
        return v
        
        
        
        
class Civilian:
    '''
    Properties of a Civilian:
    1. Lives forever, unless killed by a Zombie
    2. Has a normal view radius when calm, larger view radius when alert
    3. Tries to flock if alert.
    4. Has a probability of getting alerted if nearby civilian is alerted.
    '''
    def __init__(self):
        self.x = random.randint(20, WIDTH - 20)
        self.y = random.randint(20, HEIGHT - 20)
        while obstacle[self.x, self.y] == 1:
            self.x = random.randint(20, WIDTH - 20)
            self.y = random.randint(20, HEIGHT - 20)
        self.radius = 100
        self.size = 10
        self.view = 2*np.pi
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-4, 4)
        self.color = (0, 0, 255)
        #self.alpha = random.randint(100, 255)
        self.alpha = 255
        self.nearciv = []
        self.nearzomb = []
        self.alert = False
        self.nozomb = 0
        self.alert_prob = 1
        self.t_last = pygame.time.get_ticks()
        
    def move(self):
        # Apply velocity vectors
        self.x += self.vx
        self.y += self.vy
        
    def get_triangle(self):
        angle = np.arctan2(self.vy, self.vx)
        self.x = self.size + (self.x-self.size)%(WIDTH - 2*self.size)
        self.y = self.size + (self.y-self.size)%(HEIGHT - 2*self.size)
        x1 = int(self.x + self.size*np.cos(angle))
        y1 = int(self.y + self.size*np.sin(angle))
        x2 = int(self.x + self.size*np.cos(angle + (150*np.pi/180)))
        y2 = int(self.y + self.size*np.sin(angle + (150*np.pi/180)))
        x3 = int(self.x + self.size*np.cos(angle + (210*np.pi/180)))
        y3 = int(self.y + self.size*np.sin(angle + (210*np.pi/180)))
        return (np.array([x1, y1]), np.array([x2, y2]), np.array([x3, y3]))
    
    def draw(self, surface): #Renders the triangle boid
        coords = list(self.get_triangle())
        pygame.draw.polygon(surface, self.color, coords)
        
    def find_neighbours(self, all_civ, all_zomb):
        self.nearciv = []
        self.nearzomb = []
        self.nozomb = 0
        for civ in all_civ:
            dist2 = (self.x - civ.x)**2 + (self.y - civ.y)**2
            val = np.dot(np.array([civ.x - self.x, civ.y - self.y]), np.array([self.vx, self.vy]))
            if (dist2 < self.radius**2) and (dist2 > civ.size): #and (val > (np.cos(self.view/2))*(np.linalg.norm(np.array([boid.x - self.x, boid.y - self.y])))*(np.linalg.norm(np.array([self.vx, self.vy])))):
                self.nearciv.append((civ, dist2))
            
        for zomb in all_zomb:
            dist2 = (self.x - zomb.x)**2 + (self.y - zomb.y)**2
            val = np.dot(np.array([zomb.x - self.x, zomb.y - self.y]), np.array([self.vx, self.vy]))
            if (dist2 < self.radius**2) and (dist2 > 0): #and (val > (np.cos(self.view/2))*(np.linalg.norm(np.array([boid.x - self.x, boid.y - self.y])))*(np.linalg.norm(np.array([self.vx, self.vy])))):
                self.nearzomb.append((zomb, dist2))
                self.nozomb = self.nozomb + 1
                
    def collision_avoidance(self): 
        F = np.zeros(2)
        for pair in self.nearciv:
            civ, dist2 = pair
            dist = np.sqrt(dist2)
            F = F + np.array([self.x - civ.x, self.y - civ.y])*((self.radius - dist))/(dist)
            #F = F + np.array([self.x - boid.x, self.y - boid.y])/(dist*(dist-2*self.size)*(dist-2*self.size)) #--> Coulomb force, does not have enough effect in enough time to prevent collisions
        return F
    
    def zombator_avoidance(self): 
        F = np.zeros(2)
        for pair in self.nearzomb:
            zomb, dist2 = pair
            dist = np.sqrt(dist2)
            F = F + np.array([self.x - zomb.x, self.y - zomb.y])*((self.radius - dist))/(2*dist)
            #F = F + np.array([self.x - boid.x, self.y - boid.y])/(dist*(dist-2*self.size)*(dist-2*self.size)) #--> Coulomb force, does not have enough effect in enough time to prevent collisions
        return F
    
    def velocity_matching(self):
        ctr = 0
        v_avg = np.zeros(2)
        for pair in self.nearciv:
            civ, dist2 = pair
            v_avg = ((v_avg*ctr) + np.array([civ.vx, civ.vy]))/(ctr+1)
            ctr = ctr + 1
        if v_avg[0] == 0 and v_avg[1] == 0: #No neighbours detected
            F = 0
        else:
            F = v_avg - np.array([self.vx, self.vy])
            F = F - 0*np.array([self.vx, self.vy])
        return F
    
    def flock_centering(self):
        ctr = 0
        centroid = np.zeros(2)
        for pair in self.nearciv: 
            civ, dist2 = pair
            centroid = ((centroid*ctr) + np.array([civ.x, civ.y]))/(ctr+1)
            ctr = ctr + 1
        if centroid[0] == 0 and centroid[1] == 0: #No neighbours detected
            F = 0
        else:
            F = centroid - np.array([self.x, self.y])

        return F
    
    def death_check(self, all_civ):
        for pair in self.nearzomb:
            zomb, dist2 = pair
            dist = np.sqrt(dist2)
            if dist <= self.size*2:
                all_civ.remove(self)
            else:
                continue
            
    def alert_check1(self):
        if self.nozomb > 0 or (pygame.time.get_ticks() - self.t_last < 10*1000 and self.alert):
            if self.alert == False:
                self.t_last = pygame.time.get_ticks()
            self.alert = True
            self.radius = 150
            self.color = (255, 0, 0)
        else:
            self.alert = False
            self.radius = 100
            self.color = (0, 0, 255)
            
    def alert_check2(self):
        ctr = 0
        if self.alert:
            return
        for pair in self.nearciv:
            civ, dist2 = pair
            if civ.alert == True:
                ctr = ctr + 1
        n = np.random.randint(1, 101)
        if n <= 100*ctr*self.alert_prob:
            self.alert = True
            self.radius = 150
            self.color = (255, 0, 0)
    
    def update_velocity(self):
        k1 = 0.02
        k2 = 0.02
        k3 = 0.03
        k4 = 0.02
        if self.alert == True:
            F1 = self.collision_avoidance()
            F2 = self.velocity_matching()
            F3 = self.flock_centering()
            F4 = self.zombator_avoidance()
            acc = k1*F1 + k2*F2 + k3*F3 + k4*F4 - 0.01*np.array([self.vx, self.vy])
        else:
            F1 = self.collision_avoidance()
            acc = k1*F1 - 0.01*np.array([self.vx, self.vy])
        self.vx = self.vx + acc[0]/scale
        self.vy = self.vy + acc[1]/scale
        
    def obstacle_avoidance(self):
        delta_theta = 0.1
        angle = np.arctan2(self.vy, self.vx)
        r1 = 0
        r2 = 0
        flag1 = False
        flag2 = False
        for r in np.arange(self.size, self.radius, 1):
            x1, y1 = (np.clip(int(self.x + r*np.cos(angle + delta_theta)), 0, WIDTH-1), np.clip(int(self.y + r*np.sin(angle + delta_theta)), 0, HEIGHT-1))
            if obstacle[x1, y1] == 1:
                r1 = r
                flag1 = True
                break
        for r in np.arange(self.size, self.radius, 1):
            x2, y2 = (np.clip(int(self.x + r*np.cos(angle - delta_theta)), 0, WIDTH-1), np.clip(int(self.y + r*np.sin(angle - delta_theta)), 0, HEIGHT-1))
            if obstacle[x2, y2] == 1:
                r2 = r
                flag2 = True
                break
        if flag1 and flag2:
            v = np.array([y2 - y1, x1 - x2]) #Normal vector from obstacle surface
            v = v*((2*self.radius - r1 - r2))/(2*np.linalg.norm(v))
            #v = v*4/((np.linalg.norm(v))*((r1+r2)**2))
        else:
            v = np.zeros(2)
        return v
        
all_civ = [Civilian() for _ in range(20)]
all_zomb = [Zombie() for _ in range(1)]
running = True
while running:
    # 2. Handle User Input Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    # 3. Update Simulation State Logic
    for civ in all_civ:
        civ.find_neighbours(all_civ, all_zomb)
    for zomb in all_zomb:
        zomb.find_neighbours(all_civ, all_zomb)
    
    for civ in all_civ:
        civ.death_check(all_civ)
        
    for civ in all_civ:
        civ.alert_check1()
    for civ in all_civ:
        civ.alert_check2()
        
        
    for civ in all_civ:
        civ.update_velocity()
        civ.move()
    for zomb in all_zomb:
        zomb.update_velocity()
        zomb.move()

    # 4. Clear Window
    screen.fill((255, 255, 255))
    #add_rectangle(screen, obstacle,500,200,520,500)
    #add_rectangle(screen, obstacle,500,480,800,500)
    #add_rectangle(screen, obstacle,780,200,800,500)
    #add_circle(screen, obstacle, 200, 200, 50)
    # 5. Render New Frame
    for civ in all_civ:
        civ.draw(screen)
    for zomb in all_zomb:
        zomb.draw(screen)
        
    # Refresh window and lock at 60 FPS
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()       




