import numpy as np


def evaluate_layout(layout, check, start_pos=None, use_item_count=False, reward_type='max'):
    try:
        res = layout.get_check_optimal_path(check, start_point=start_pos, use_product_count=use_item_count)
    except Exception as e:
        #print(e)
        if reward_type == 'max' or reward_type == 'uniformity':
            return 0, True
        else:
            return 999, True
    return len(res), False


def compare_racks(rack1, rack2):
    counter = 0
    for level in range(len(rack1)):
        if rack1[level][0] != rack2[level][0]:
            counter += 1
    return counter


def calculate_uniformity(layout):
    rack_score = 0
    tile_score = 0
    tile_count = 0
    for i in range(layout.shape[0]):
        for j in range(layout.shape[1]):
            if layout[i][j].type.name == 'RACK':
                tile_count += 1
                t_rack = len(set(layout[i][j].items))
                if t_rack > 1:
                    rack_score += 1
                floor_pos = None
                for pos in [(i-1, j), (i+1, j), (i, j-1), (i, j+1)]:
                    if 0 <= pos[0] < layout.shape[0] and 0 <= pos[1] < layout.shape[1]:
                        if layout[pos[0]][pos[1]].type.name == 'FLOOR':
                            floor_pos = pos
                            break
                if floor_pos:
                    diff = (floor_pos[0] - i, floor_pos[1] - j)
                    pos_left = (i - diff[1], j - diff[0])
                    pos_right = (i + diff[1], j + diff[0])
                    if layout[pos_left[0]][pos_left[1]].type.name == 'RACK':
                        rack_score += compare_racks(layout[i][j].items, layout[pos_left[0]][pos_left[1]].items)
                        tile_score += layout[i][j].items != layout[pos_left[0]][pos_left[1]].items
                    if layout[pos_right[0]][pos_right[1]].type.name == 'RACK':
                        rack_score += compare_racks(layout[i][j].items, layout[pos_right[0]][pos_right[1]].items)
                        tile_score += layout[i][j].items != layout[pos_right[0]][pos_right[1]].items
    return rack_score, tile_score


def thread_func(t_layout, t_check_arr, t_start_pos=None, use_item_count=True):
    t_res = (0, 0)
    for check in t_check_arr:
        t = evaluate_layout(t_layout, check[1], t_start_pos, use_item_count=use_item_count)
        inc = 1 if t[1] else 0
        t_res = (t_res[0] + t[0], t_res[1] + inc)
    uni_rack, uni_tile = calculate_uniformity(t_layout)
    res_dict = dict()
    res_dict['path'] = t_res[0]
    res_dict['invalid'] = t_res[1]
    res_dict['rack_uniformity'] = uni_rack
    res_dict['tile_uniformity'] = uni_tile
    return res_dict, t_layout

def calculate_score(res_dict, layout, check_arr, weights=(750, 125, 125)):
    rack_count = layout.get_rack_count()
    invalid_score = res_dict['invalid'] / len(check_arr)
    # each tile has 2 neighbors
    rack_uniformity = res_dict['rack_uniformity'] / (rack_count * 3)
    # each tile has 4 neighbors
    tile_uniformity = res_dict['tile_uniformity'] / (rack_count * 4)
    return weights[0] * invalid_score + weights[1] * rack_uniformity + weights[2] * tile_uniformity

def get_tile_info(layout, i, j):
    tile = layout[i][j]
    if tile.type.name != 'RACK':
        return None

    res = dict()
    res['dist_to_cashier'] = len(layout.calculate_path_to_cashier((i, j)))
    res['dist_to_exit'] = len(layout.calculate_path_to_door((i, j)))
    res['orientation'] = None
    res['left_products'] = []
    res['right_products'] = []

    for pos in [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]:
        if 0 <= pos[0] < layout.shape[0] and 0 <= pos[1] < layout.shape[1]:
            if layout[pos[0]][pos[1]].type.name == 'FLOOR':
                floor_pos = pos
                break
    floor_pos = None
    for pos in [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)]:
        if 0 <= pos[0] < layout.shape[0] and 0 <= pos[1] < layout.shape[1]:
            if layout[pos[0]][pos[1]].type.name == 'FLOOR':
                floor_pos = pos
                break
    if floor_pos:
        diff = (floor_pos[0] - i, floor_pos[1] - j)
        res['orientation'] = diff
        pos_left = (i - diff[1], j - diff[0])
        pos_right = (i + diff[1], j + diff[0])
        if layout[pos_left[0]][pos_left[1]].type.name == 'RACK':
            res['left_products'] = layout[pos_left[0]][pos_left[1]].items
        if layout[pos_right[0]][pos_right[1]].type.name == 'RACK':
            res['right_products'] = layout[pos_right[0]][pos_right[1]].items
    else:
        print('WARNING: No floor found for rack at position', i, j)
    return res
