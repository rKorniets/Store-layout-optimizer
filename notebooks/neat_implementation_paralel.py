import random
import os

import neat
from neat import DistributedEvaluator, ParallelEvaluator
from tqdm.notebook import tqdm, trange
from pathlib import Path
from random import randint
from ui.python.Layout import Layout
import numpy as np

from helpers.estimation_helpers import *
import helpers.visualize as visualize

import pandas as pd

MAX_WORKERS = 10
SLICE_SIZE = 1000
EPOCHS = 300
SCORE_COEFFICIENTS = (1000, 0, 0)
layout = None
item_list = None
check_list = None
check_ids = None
df = None
best = None
str_item = None

def get_order_items(order_id):
    return order_id, list(map(str, df[df['order_id'] == order_id]['product_id'].tolist()))

def random_layout():
    layout = Layout('./../data/layout 18x25_6.json')
    layout.set_item_list(df['product_id'].unique().tolist())
    for row in range(layout.shape[0]):
        for col in range(layout.shape[1]):
            if layout[row][col].type.name == 'RACK':
                for lev in range(layout.get_max_rack_level()):
                    layout.set_item_to_rack(random.choice(layout.get_item_list()), (row, col), level=lev)
    return layout


def create_input_for_genome(layout, i, j, level):
    def tile_enum_to_int(tile):
        if tile.type.value == 'wall':
            return 0
        if tile.type.value == 'floor':
            return 1
        if tile.type.value == 'rack':
            return 2
        if tile.type.value == 'door':
            return 3
        if tile.type.value == 'cashier':
            return 4
        return 0

    def convert_items_to_int(items):
        ids = []
        if len(items) == 0:
            return [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]
        for item in items:
            if item[0] == '':
                ids.append((-1, 0))
            else:
                ids.append((int(item[0]), int(item[1])))
        return ids

    tile_info = get_tile_info(layout, i, j)
    if tile_info is None:
        return None

    left_products = convert_items_to_int(tile_info['left_products'])
    right_products = convert_items_to_int(tile_info['right_products'])

    return [
        level,
        tile_info['dist_to_cashier'],
        tile_info['dist_to_exit'],
        tile_info['orientation'][0],
        tile_info['orientation'][1],
        left_products[0][0],
        left_products[0][1],
        left_products[1][0],
        left_products[1][1],
        left_products[2][0],
        left_products[2][1],
        left_products[3][0],
        left_products[3][1],
        right_products[0][0],
        right_products[0][1],
        right_products[1][0],
        right_products[1][1],
        right_products[2][0],
        right_products[2][1],
        right_products[3][0],
        right_products[3][1],
        tile_enum_to_int(layout[i - 1][j]),
        tile_enum_to_int(layout[i + 1][j]),
        tile_enum_to_int(layout[i][j - 1]),
        tile_enum_to_int(layout[i][j + 1]),
        tile_enum_to_int(layout[i - 1][j - 1]),
        tile_enum_to_int(layout[i + 1][j + 1]),
        tile_enum_to_int(layout[i - 1][j + 1]),
        tile_enum_to_int(layout[i + 1][j - 1]),
    ]

def eval_genome(genome, config):
    _layout = layout.copy()
    genome.fitness = 0
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    for i in range(_layout.shape[0]):
        for j in range(_layout.shape[1]):
            for level in range(_layout.get_max_rack_level()):
                inputs = create_input_for_genome(_layout, i, j, level)
                if inputs is not None:
                    output = net.activate(inputs)
                    _layout.set_item_to_rack(str(np.argmax(output)+1), (i, j), level)
    res_dict, processed_layout = thread_func(_layout, check_list[:SLICE_SIZE], use_item_count=True)
    estimation = calculate_score(res_dict, processed_layout, check_list[:SLICE_SIZE], SCORE_COEFFICIENTS)
    return estimation

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
    p.add_reporter(neat.Checkpointer(10))

    pe = ParallelEvaluator(MAX_WORKERS, eval_genome)

    # Run for up to 300 generations.
    winner = p.run(pe.evaluate, EPOCHS)
    global best
    best = winner

config_file = './neat_config.cfg'

if __name__ == '__main__':
    df = pd.read_csv('./../data/datasets/ECommerce_consumer behaviour.csv')
    df = df[['order_id', 'user_id', 'order_number', 'department', 'product_id', 'product_name']]
    item_list = df['product_id'].unique().tolist()
    check_ids = df['order_id'].unique().tolist()
    check_list = []

    # add some dummy check data to make neat add different items to the layout
    for i in range(100):
        check_list.append((i, [str(randint(1, 100)) for _ in range(randint(1,4))]))

    for check_id in tqdm(check_ids[:2000]):
        check_list.append(get_order_items(check_id))

    layout = Layout('./../data/layout 18x25_6.json').get_empty_rack_layout()
    items = df['product_id'].unique().tolist()
    str_item = [str(i) for i in items]
    layout.set_item_list(str_item)
    best = None
    run(config_file)