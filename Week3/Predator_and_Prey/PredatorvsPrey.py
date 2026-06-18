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

class Predator:
    '''
    Properties of a Predator:
    1. Live for a limited timespan, which resets when they eat a Prey.
    2. Have a larger view radius
    3. Attacks the nearest Prey and avoids other Predators
    '''
    def __init__(self):
        self.x = random.randint(20, WIDTH - 20)
        self.y = random.randint(20, HEIGHT - 20)
        while obstacle[self.x, self.y] == 1:
            self.x = random.randint(20, WIDTH - 20)
            self.y = random.randint(20, HEIGHT - 20)
        self.radius = 150
        self.size = 10
        self.view = 2*np.pi
        self.vx = random.uniform(-10, 10)
        self.vy = random.uniform(-10, 10)
        self.color = (255, 0, 0)
        #self.alpha = random.randint(100, 255)
        self.alpha = 255
        self.nearestprey = []
        self.nearpred = []
        self.last_ate = pygame.time.get_ticks()
        
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
        
    def find_neighbours(self, all_prey, all_pred):
        self.nearestprey = [(all_prey[0], -1)]
        self.nearpred = []
        distmin = 1500
        for prey in all_prey:
            dist2 = (self.x - prey.x)**2 + (self.y - prey.y)**2
            val = np.dot(np.array([prey.x - self.x, prey.y - self.y]), np.array([self.vx, self.vy]))
            if (dist2 < self.radius**2) and (dist2 > prey.size): #and (val > (np.cos(self.view/2))*(np.linalg.norm(np.array([boid.x - self.x, boid.y - self.y])))*(np.linalg.norm(np.array([self.vx, self.vy])))):
                if dist2 < distmin**2:
                    self.nearestprey[0] = (prey, dist2)
                    distmin = np.sqrt(dist2)
        a, b = self.nearestprey[0]
        if b == -1:
            self.nearestprey = []
                
        for pred in all_pred:
            dist2 = (self.x - pred.x)**2 + (self.y - pred.y)**2
            val = np.dot(np.array([pred.x - self.x, pred.y - self.y]), np.array([self.vx, self.vy]))
            if (dist2 < self.radius**2) and (dist2 > 0): #and (val > (np.cos(self.view/2))*(np.linalg.norm(np.array([boid.x - self.x, boid.y - self.y])))*(np.linalg.norm(np.array([self.vx, self.vy])))):
                self.nearpred.append((pred, dist2))
                
    def collision_avoidance(self): 
        F = np.zeros(2)
        for pair in self.nearpred:
            pred, dist2 = pair
            dist = np.sqrt(dist2)
            F = F + np.array([self.x - pred.x, self.y - pred.y])*((self.radius - dist))/(dist)
            #F = F + np.array([self.x - boid.x, self.y - boid.y])/(dist*(dist-2*self.size)*(dist-2*self.size)) #--> Coulomb force, does not have enough effect in enough time to prevent collisions
        return F
    
    def hunt_prey(self):
        if not self.nearestprey:
            return np.zeros(2)
        prey, dist2 = self.nearestprey[0]
        dist = np.sqrt(dist2)
        if dist > prey.size*2:
            F = np.array([prey.x - self.x, prey.y - self.y])*((self.radius - dist)/(3*dist))
        else:
            F = -np.array([self.vx, self.vy])*20
            self.last_ate = pygame.time.get_ticks()
        return F
    
    def death_check(self, all_pred):
        if pygame.time.get_ticks() - self.last_ate > 10000:
            all_pred.remove(self)
    
    def update_velocity(self):
        k1 = 0.02
        k2 = 0.02
        k3 = 0.01
        F1 = self.collision_avoidance()
        F2 = self.hunt_prey()
        #F3 = self.obstacle_avoidance()
        acc = k1*F1 + k2*F2 #+ k3*F3 #Not normalizing it even though that is what is mentioned in the paper
        self.vx = self.vx + acc[0]
        self.vy = self.vy + acc[1]
        
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
        
        
        
        
class Prey:
    '''
    Properties of a Prey:
    1. Lives forever, unless killed by a Predator
    2. Has a smaller view radius
    3. Tries to flock with other Prey, and fears Predators
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
        self.vx = random.uniform(-10, 10)
        self.vy = random.uniform(-10, 10)
        self.color = (0, 255, 0)
        #self.alpha = random.randint(100, 255)
        self.alpha = 255
        self.nearprey = []
        self.nearpred = []
        
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
        
    def find_neighbours(self, all_prey, all_pred):
        self.nearprey = []
        self.nearpred = []
        for prey in all_prey:
            dist2 = (self.x - prey.x)**2 + (self.y - prey.y)**2
            val = np.dot(np.array([prey.x - self.x, prey.y - self.y]), np.array([self.vx, self.vy]))
            if (dist2 < self.radius**2) and (dist2 > prey.size): #and (val > (np.cos(self.view/2))*(np.linalg.norm(np.array([boid.x - self.x, boid.y - self.y])))*(np.linalg.norm(np.array([self.vx, self.vy])))):
                self.nearprey.append((prey, dist2))
                
        for pred in all_pred:
            dist2 = (self.x - pred.x)**2 + (self.y - pred.y)**2
            val = np.dot(np.array([pred.x - self.x, pred.y - self.y]), np.array([self.vx, self.vy]))
            if (dist2 < self.radius**2) and (dist2 > 0): #and (val > (np.cos(self.view/2))*(np.linalg.norm(np.array([boid.x - self.x, boid.y - self.y])))*(np.linalg.norm(np.array([self.vx, self.vy])))):
                self.nearpred.append((pred, dist2))
                
    def collision_avoidance(self): 
        F = np.zeros(2)
        for pair in self.nearprey:
            prey, dist2 = pair
            dist = np.sqrt(dist2)
            F = F + np.array([self.x - prey.x, self.y - prey.y])*((self.radius - dist))/(dist)
            #F = F + np.array([self.x - boid.x, self.y - boid.y])/(dist*(dist-2*self.size)*(dist-2*self.size)) #--> Coulomb force, does not have enough effect in enough time to prevent collisions
        return F
    
    def predator_avoidance(self): 
        F = np.zeros(2)
        for pair in self.nearpred:
            pred, dist2 = pair
            dist = np.sqrt(dist2)
            F = F + np.array([self.x - pred.x, self.y - pred.y])*((self.radius - dist))/(dist)
            #F = F + np.array([self.x - boid.x, self.y - boid.y])/(dist*(dist-2*self.size)*(dist-2*self.size)) #--> Coulomb force, does not have enough effect in enough time to prevent collisions
        return F
    
    def velocity_matching(self):
        ctr = 0
        v_avg = np.zeros(2)
        for pair in self.nearprey:
            prey, dist2 = pair
            v_avg = ((v_avg*ctr) + np.array([prey.vx, prey.vy]))/(ctr+1)
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
        for pair in self.nearprey: 
            prey, dist2 = pair
            centroid = ((centroid*ctr) + np.array([prey.x, prey.y]))/(ctr+1)
            ctr = ctr + 1
        if centroid[0] == 0 and centroid[1] == 0: #No neighbours detected
            F = 0
        else:
            F = centroid - np.array([self.x, self.y])

        return F
    
    def death_check(self, all_prey):
        for pair in self.nearpred:
            pred, dist2 = pair
            dist = np.sqrt(dist2)
            if dist <= self.size*2:
                all_prey.remove(self)
            else:
                continue
    
    def update_velocity(self):
        k1 = 0.01
        k2 = 0.015
        k3 = 0.015
        k4 = 0.03
        k5 = 0.02
        F1 = self.collision_avoidance()
        F2 = self.velocity_matching()
        F3 = self.flock_centering()
        #F4 = self.obstacle_avoidance()
        F5 = self.predator_avoidance()
        acc = k1*F1 + k2*F2 + k3*F3 + k5*F5 #+ k4*F4 #Not normalizing it even though that is what is mentioned in the paper
        self.vx = self.vx + acc[0]
        self.vy = self.vy + acc[1]
        
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
        
all_prey = [Prey() for _ in range(50)]
all_pred = [Predator() for _ in range(2)]
running = True
while running:
    # 2. Handle User Input Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    # 3. Update Simulation State Logic
    for prey in all_prey:
        prey.find_neighbours(all_prey, all_pred)
    for pred in all_pred:
        pred.find_neighbours(all_prey, all_pred)
    
    for prey in all_prey:
        prey.update_velocity()
        prey.move()
    for pred in all_pred:
        pred.update_velocity()
        pred.move()

    # 4. Clear Window
    screen.fill((255, 255, 255))
    #add_rectangle(screen, obstacle,500,200,520,500)
    #add_rectangle(screen, obstacle,500,480,800,500)
    #add_rectangle(screen, obstacle,780,200,800,500)
    #add_circle(screen, obstacle, 200, 200, 50)
    # 5. Render New Frame
    for prey in all_prey:
        prey.draw(screen)
    for pred in all_pred:
        pred.draw(screen)
        
    for prey in all_prey:
        prey.death_check(all_prey)
    for pred in all_pred:
        pred.death_check(all_pred)
    # Refresh window and lock at 60 FPS
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()       
