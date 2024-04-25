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
SLICE_SIZE = 400
EPOCHS = 100
SCORE_COEFFICIENTS = (900, 50, 50)
layout = Layout('./../data/layouts/genetic/step1-max/layout_4_racks.json').reset_item_count().reset_path_count()
item_list = None
check_list = None
check_ids = None
df = None
best = None
str_item = None
selected_categories = [
 'bakery',
 'beverages',
 'breakfast',
 'canned goods',
 'dairy eggs',
 'deli',
 'dry goods pasta',
 'frozen',
 'household',
 'meat seafood',
 'pantry',
 'produce',
 'snacks']

check_config = {
    1: 30,
    2: 50,
    3: 60,
    4: 75,
    5: 75,
    6: 60,
    7: 50,
}

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
    checks = check_list[:SLICE_SIZE]
    random.shuffle(checks)
    # estimation = 1000 - calculate_score(res_dict, processed_layout, checks, SCORE_COEFFICIENTS)
    estimation = res_dict['path']
    return estimation

def run_genome(genome, config):
    _layout = layout.copy()
    net = neat.nn.FeedForwardNetwork.create(genome, config)
    for i in range(_layout.shape[0]):
        for j in range(_layout.shape[1]):
            for level in range(_layout.get_max_rack_level()):
                inputs = create_input_for_genome(_layout, i, j, level)
                if inputs is not None:
                    output = net.activate(inputs)
                    _layout.set_item_to_rack(str(np.argmax(output) + 1), (i, j), level)
    return _layout

def run(config_file):
    global layout
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
    for i in range(15):
        winner = p.run(pe.evaluate, 5)
        l = run_genome(winner, config)
        layout = l.copy()
        l.reset_path_count()
        if i % 10 == 0:
            l.reset_item_count()
        print("Generation: ", i, "Fitness: ", winner.fitness, "Layout saved")
    global best
    best = winner

config_file = './neat_config.cfg'

if __name__ == '__main__':
    df = pd.read_csv('./../data/datasets/ECommerce_consumer behaviour.csv')
    df = df[['order_id', 'user_id', 'order_number', 'department', 'product_id', 'product_name']]
    check_list = []

    df = df[df['department'].isin(selected_categories)]


    def get_order_items(order_id):
        order = df[df['order_id'] == order_id]
        is_in_category = order['department'].apply(lambda x: x in selected_categories)
        return order_id, order[is_in_category]['product_name'].unique().tolist()\

    # Create check list
    check_ids = df['order_id'].unique().tolist()
    check_list = []
    for check_id in tqdm(check_ids[:10000]):
        check = get_order_items(check_id)
        check_list.append(check)

    def get_checks_of_specific_length(check_list, length):
        return [x for x in check_list if len(x[1]) == length]

    def get_checks_of_specific_length_range(check_list, range_dict):
        # range dict: length - n_of_checks
        res = []
        for key in tqdm(range_dict.keys()):
            res += get_checks_of_specific_length(check_list, key)[:range_dict[key]]
        return res

    tuned_checks = get_checks_of_specific_length_range(check_list, check_config)

    # convert tuned checks item names to item ids
    check_list = []
    name_id_df = df[['product_name', 'product_id']].drop_duplicates()
    # ids are not sequential numbers, so we need to map them to sequential numbers
    name_id_df['product_id_norm'] = range(1, len(name_id_df) + 1)
    for check in tuned_checks:
        check_list.append((check[0], [str(name_id_df[name_id_df['product_name'] == x]['product_id_norm'].values[0]) for x in check[1]]))

    #convert layout items to item ids
    str_items = name_id_df['product_id_norm'].unique().tolist()
    str_items = [str(x) for x in str_items]
    layout.set_item_list(str_items, reset_items=False)
    for i in range(layout.shape[0]):
        for j in range(layout.shape[1]):
            if layout[i][j].type.name == 'RACK':
                items = layout[i][j].items
                for level in range(layout.get_max_rack_level()):
                    item = items[level]
                    new_item = name_id_df[name_id_df['product_name'] == item[0]]['product_id_norm'].values[0]
                    layout.set_item_to_rack(str(new_item), (i, j), level=level)

    best = None
    run(config_file)