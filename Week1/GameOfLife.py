import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

s = 50

people = np.zeros((s, s), dtype = int)

glider = np.array([
    [0,1,0],
    [0,0,1],
    [1,1,1]
])
blinker = np.array([
    [1,1,1]
])
toad = np.array([
    [0,1,1,1],
    [1,1,1,0]
])
gun = np.array([
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
[0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,1,1],
[1,1,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[1,1,0,0,0,0,0,0,0,0,1,0,0,0,1,0,1,1,0,0,0,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
[0,0,0,0,0,0,0,0,0,0,0,0,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
])

#people[5:14,5:41] = gun
X = np.array([
    [1, 0, 1],
    [0, 1, 0],
    [1, 0, 1]
])
#people[24:27, 24:27] = X
#people[75:77,20:24] = toad

#people[20:21,20:23] = blinker

people[2:5,2:5] = glider
#people[10:13,10:13] = glider
many_people = [people]
tim = 1
num_frames = 3000
fig, ax = plt.subplots(figsize=(20, 20))
im = ax.imshow(people, cmap='binary', interpolation = 'nearest', origin='lower')
title = ax.set_title("Game Of Life: Frame 0")

def update_people(people):
    people1 = np.zeros((s, s), dtype = int)
    for i in range(s):
        for j in range(s):
            list1 = []
            list2 = []
            ctr = 0
            #Filtering the possible index values for boundary conditions
            for k in [-1, 0, 1]:
                if (i+k)>=0 and (i+k)<s:
                    list1.append(i+k)
                if (j+k)>=0 and (j+k)<s:
                    list2.append(j+k)
            for a in list1:
                for b in list2:
                    if((a,b) != (i, j)):
                        ctr = ctr + people[a, b]
            if people[i, j] == 0 and ctr == 3:
                people1[i, j] = 1  #Birth Rule
            elif people[i, j] == 1 and (ctr == 2 or ctr == 3):
                people1[i, j] = 1  #Survival Rule
            else:
                people1[i, j] = 0 #Death Rule
                
    return people1

def update(tim):
    many_people.append(update_people(many_people[-1]))
    im.set_data(many_people[-1])
    title.set_text(f"Game Of Life: Frame {tim}")
    return (im, title)

ani = FuncAnimation(
fig, update, frames=num_frames, interval=110, blit=True)

# 5. Display or Save the animation
plt.show()