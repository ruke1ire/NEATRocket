#!/usr/bin/python3

import numpy as np 
import pymunk
import pyglet
from pymunk.pyglet_util import DrawOptions
import neat
import os
import random
import pickle
import glob
import sys
import math
import visualize
import graphviz

from rocket import Rocket, RocketImage
from base import Base

if len(sys.argv) == 2:
    NETWORK_DIR = sys.argv[1]
elif len(sys.argv) > 2:
    raise "Too many directories to write to"
else:
    NETWORK_DIR = 'networksTest/'

#setup the window
window_width = 1920
window_height = 1080
window = pyglet.window.Window(window_width,window_height)
#window = pyglet.window.Window(fullscreen = True)
window_width = window.width
window_height = window.height
window.set_caption("NEATLanding")
fps_display = pyglet.window.FPSDisplay(window=window)

batch = pyglet.graphics.Batch()

#create drawoptions object
options = DrawOptions()

#setup space
space = pymunk.Space()
space.gravity = (0,-1000)

#insert base
BASE_MARGIN = 100
NOT_BASE_MARGIN = 500
base = Base(x_pos = window_width//2,y_pos = window_height//2)
base.insert(space)
base.iterate_position(reset=True,window_width = window_width, window_height = window_height)

#state scale
CARTESIAN_SCALE = 200.0
ANGULAR_SCALE = 1.0/2.0

#global variables for simulation and training
genomess = []
nets = []
rockets = []
step_count = 0
dead_rockets = []
generation = 1
best_fitness = -float('inf')
GENERATIONS = 50

generation_number = pyglet.text.Label('',
                          font_name='Arial',
                          font_size=15,
                          x = 100, y=window_height-30,
                          anchor_x='center', anchor_y='center',batch=batch)

rocket_image = RocketImage(batch=batch)

#on_draw window event
@window.event
def on_draw():
    window.clear()
    space.debug_draw(options)
    batch.draw()
    fps_display.draw()
    #rocket_image.rocket_sprite.draw()

@window.event
def on_mouse_press(x,y,button,modifier):
    pass

def get_states(rocket):
    #get rocket's current position and velocity
    x = float(rocket.body.position[0])/CARTESIAN_SCALE
    y = float(rocket.body.position[1])/CARTESIAN_SCALE
    a = float(rocket.body.angle)/ANGULAR_SCALE
    vx = float(rocket.body.velocity[0])/CARTESIAN_SCALE
    vy = float(rocket.body.velocity[1])/CARTESIAN_SCALE
    va = float(rocket.body.angular_velocity)

    #get base position
    bx = float(base.body.position[0])/CARTESIAN_SCALE
    by = float(base.body.position[1])/CARTESIAN_SCALE

    #calculate rocket state as mentioned in README
    ex = x-bx
    ey = y-by
    ea = a
    evx = vx
    evy = vy
    eva = va

    return [ex,ey,ea,evx,evy,eva]

def get_fitness(states):
    state_weights = [1,1,0,0,0,0]
    s = 0
    for i, (state,state_weights) in enumerate(zip(states,state_weights)):
        s += state_weights*(state**2)
    return s

def get_fitness2(states):
    state_weights = [1,1,1,0,0,0]
    s = 0
    for i, (state,state_weights) in enumerate(zip(states,state_weights)):
        s += state_weights*(abs(state))
    return s

def get_fitness3(states):
    state_weights = [1,1,1,0,0,0]
    sigma = 10.0
    s = 0
    for i, (state,state_weights) in enumerate(zip(states,state_weights)):
        s += state_weights*(abs(state))
    s = -math.exp(-s/sigma)
    return s

def get_fitness4(states):
    state_weights = [1,1,0,0,0,0]
    intercept = 1.0
    s = 0
    for i, (state,state_weights) in enumerate(zip(states,state_weights)):
        s += state_weights*(max(-abs(state) + intercept,0.0))
    return -s

def eval_genomes(genomes, config):
    #this function runs once a generation
    global genomess
    global rockets
    global nets
    global dead_rockets

    dead_rockets = []
    rockets = []
    nets = []

    for i, (genome_id, genome) in enumerate(genomes):
        genomess.append(genome)
        current_fitness = genome.fitness
        if current_fitness is None:
            current_fitness = -float('inf')
        genomess[-1].fitness = 0
        rockets.append(Rocket(x_pos = window.width//2, y_pos = window.height//2,batch=batch,_id=round(current_fitness,1)))

        rockets[-1].insert(space)

        dead_rockets.append(0)
        nets.append(neat.nn.FeedForwardNetwork.create(genome, config))

    generation_number.text = f"Generation: {generation}"

    pyglet.app.run()

    base.iterate_position(reset=True,window_width = window_width, window_height = window_height)

def update(dt):
    global nets
    global step_count
    global genomess
    global rockets
    global dead_rockets
    global generation
    global best_fitness

    current_best_fitness = -float('inf')
    current_best_idx = -1

    for i,genome in enumerate(genomess):
        if current_best_fitness < genome.fitness:
            current_best_fitness = genome.fitness
            current_best_fitness_idx = i

    #print(current_best_fitness)

    rocket_image.attach(rockets[current_best_fitness_idx])
#    rocket_image.rocket_sprite.update(rockets[current_best_fitness_idx].body.position.x, rockets[current_best_fitness_idx].body.position.y, -float(rockets[current_best_fitness_idx].body.angle) * 180 / 3.1416)
#    rocket_image.attach(rockets[current_best_fitness_idx])
    step_count += 1

    if(((step_count) >= 60*30) or (sum(dead_rockets) >= 0.95*300)):
        best_fitness_idx = -1
        best_fitness = -float('inf')
        for i,genome in enumerate(genomess):
            genome.fitness -= (60*30-step_count)*5
            if best_fitness < genome.fitness:
                best_fitness = genome.fitness
                best_fitness_idx = i

        print(best_fitness)
        
        if best_fitness_idx != -1:
            print("Saving Network")
            pickle.dump(nets[best_fitness_idx],open(f"{NETWORK_DIR}/Net_{generation}.p","wb"))

        for rocket in rockets:
            rocket.remove(space)

        pyglet.app.exit()
        generation += 1
        nets = []
        step_count = 0
        genomess = []
        rockets = []

    if((step_count % 300 == 0)):
        base.iterate_position(reset=False,window_width = window_width, window_height = window_height)
#        base.random_position([BASE_MARGIN,window_width-BASE_MARGIN],
#                [BASE_MARGIN,window_height-BASE_MARGIN],
#                [window_width//2-NOT_BASE_MARGIN//2,window_width//2+NOT_BASE_MARGIN//2],
#                [window_height//2-NOT_BASE_MARGIN//2,window_height//2+NOT_BASE_MARGIN//2])

    # apply force to every rocket
    for i, net in enumerate(nets):
        states = get_states(rockets[i])
        output = net.activate(states)

       # output_fitness = 0
       # 
       # for value in output:
       #     output_fitness += value**2

        genomess[i].fitness = genomess[i].fitness - get_fitness2(states)
        rockets[i].propel(output)
        rockets[i].update()
        if i == current_best_fitness_idx:
            rockets[i].visibility(False)
        else:
            rockets[i].visibility(True)

        if ((rockets[i].body.position.y < -100) or 
                (rockets[i].body.position.y > window_height+100) or
                (rockets[i].body.position.x < -100) or
                (rockets[i].body.position.x > window_width+100)):
            dead_rockets[i] = 1
            #rockets[i].remove(space)
            #genomess[i].fitness = genomess[i].fitness - 10

    space.step(1.0/60.0)


def run(config_file):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    p = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    node_names = {-1: 'x', -2:'y', -3:'angle', -4:'xdot', -5:'ydot', -6:'angledot',0:'Main Jet',1:'Upper Jet',2:'Lower Jet'}

    for gen in range(1,GENERATIONS+1):
        winner = p.run(eval_genomes, 1)

        # Display the winning genome.
        print('\nBest genome:\n{!s}'.format(winner))

        visualize.draw_net(config, winner, node_names=node_names,view=False,filename=f"{NETWORK_DIR}diagraph_{gen}",fmt='png')
        visualize.plot_stats(stats, ylog=False, view=False,filename=f"{NETWORK_DIR}fitness_{gen}.png")
        visualize.plot_species(stats, view=False,filename=f"{NETWORK_DIR}speciation_{gen}.png")

#Set pyglet update interval
pyglet.clock.schedule(update)

local_dir = os.path.dirname(__file__)
config_path = os.path.join(local_dir, 'config')

if not os.path.exists(os.path.dirname(NETWORK_DIR)):
    os.makedirs(os.path.dirname(NETWORK_DIR))
else:
    net_paths = glob.glob(f"{NETWORK_DIR}Net*")
    for paths in net_paths:
        os.remove(paths)

run(config_path)
