import os
from random import randint
from copy import deepcopy
from typing import Tuple

import webview
from math import inf

from pydantic import BaseModel
from ui.python.dataClass.LayoutModel import LayoutModel
from ui.python.exceptions.NoItemInLayoutError import NoItemInLayoutError


class Layout:

    shape = None

    def load_layout(self):
        with open(self.path_to_json) as file:
            raw_layout = file.read()

        layout = LayoutModel.parse_raw(raw_layout)
        return layout

    def __init__(self, path_to_json):
        self._window = None
        self.path_to_json = path_to_json
        self._layout = self.load_layout()
        self._layout_name = os.path.basename(path_to_json)
        self._doors = []
        self._cashiers = []
        self._default_item_count = 10

        for i in range(len(self._layout.sells)):
            for j in range(len(self._layout.sells[i])):
                if self._layout.sells[i][j].type.name == "DOOR":
                    self._doors.append((i, j))
                elif self._layout.sells[i][j].type.name == "CASHIER":
                    self._cashiers.append((i, j))
                elif self._layout.sells[i][j].type.name == "RACK":
                    if len(self._layout.sells[i][j].items) <= self._layout.rackLevels:
                        self._layout.sells[i][j].items += [("", self._default_item_count)] * (self._layout.rackLevels - len(self._layout.sells[i][j].items))
                    elif len(self._layout.sells[i][j].items) > self._layout.rackLevels:
                        raise Exception(f"Too many levels for rack at {i}, {j}")
        if len(self._doors) == 0:
            raise Exception("No doors in layout")
        if len(self._cashiers) == 0:
            raise Exception("No cashiers in layout")

        self.shape = (len(self._layout.sells), len(self._layout.sells[0]))

    def __copy__(self):
        new_layout = Layout(self.path_to_json)
        new_layout._layout = deepcopy(self._layout)
        for i in range(len(self._layout.sells)):
            for j in range(len(self._layout.sells[i])):
                if self._layout.sells[i][j].type.name == "RACK":
                    new_layout._layout.sells[i][j].items = [(item_copy[0], self._default_item_count) for item_copy in self._layout.sells[i][j].items.copy()]
                if self._layout.sells[i][j].type.name in ["RACK", "CASHIER"]:
                    new_layout._layout.sells[i][j].pathCount = self._layout.sells[i][j].pathCount
        return new_layout

    def copy(self):
        return self.__copy__()

    def __getitem__(self, item):
        return self._layout.sells[item]

    def __setitem__(self, key, value):
        self._layout.sells[key] = value

    def save_to_json(self, path_to_json):
        with open(path_to_json, "w") as file:
            file.write(self._layout.model_dump_json())

    def get_empty_rack_layout(self):
        new_layout = Layout(self.path_to_json)
        for i in range(len(self._layout.sells)):
            for j in range(len(self._layout.sells[i])):
                if self._layout.sells[i][j].type.name == "RACK":
                    new_layout._layout.sells[i][j].items = [("", self._default_item_count)] * self._layout.rackLevels
                if self._layout.sells[i][j].type.name in ["RACK", "CASHIER"]:
                    new_layout._layout.sells[i][j].pathCount = 0
        return new_layout

    def reset_items(self):
        for i in range(len(self._layout.sells)):
            for j in range(len(self._layout.sells[i])):
                if self._layout.sells[i][j].type.name == "RACK":
                    self._layout.sells[i][j].items = [("", self._default_item_count)] * self._layout.rackLevels
                if self._layout.sells[i][j].type.name in ["RACK", "CASHIER"]:
                    self._layout.sells[i][j].pathCount = 0
        return self

    def reset_path_count(self):
        for i in range(len(self._layout.sells)):
            for j in range(len(self._layout.sells[i])):
                if self._layout.sells[i][j].type.name in ["RACK", "CASHIER", "FLOOR", "DOOR"]:
                    self._layout.sells[i][j].pathCount = 0
        return self

    def reset_item_count(self):
        for i in range(len(self._layout.sells)):
            for j in range(len(self._layout.sells[i])):
                if self._layout.sells[i][j].type.name == "RACK":
                    for item in range(self.get_max_rack_level()):
                        self._layout.sells[i][j].items[item] = (self._layout.sells[i][j].items[item][0], self._default_item_count)
        return self

    def get_layout_name(self):
        return self._layout_name

    def get_layout(self):
        return self._layout

    def get_layout_json(self):
        return self._layout.model_dump_json()

    def set_layout(self, layout: LayoutModel):
        self._layout = layout

    def set_item_list(self, items: list, reset_items: bool = True):
        if reset_items is True:
            self.reset_items()
        self._layout.items = items

    def get_item_list(self):
        return self._layout.items

    def get_rack_count(self):
        return len([1 for i in range(len(self._layout.sells)) for j in range(len(self._layout.sells[i])) if self._layout.sells[i][j].type.name == "RACK"])

    def set_item_to_rack(self, item_name: str, coord: tuple, level: int):
        if self._layout.sells[coord[0]][coord[1]].type.name != "RACK":
            raise Exception("Sell type must be RACK")
        if item_name not in self._layout.items:
            raise Exception(f"Item {item_name} ({type(item_name)}) not found in _layout. Items: {self._layout.items}")
        self._layout.sells[coord[0]][coord[1]].items[level] = (item_name, self._default_item_count)

    def get_max_rack_level(self):
        return self._layout.rackLevels

    def set_max_rack_level(self, level: int):
        self._layout.rackLevels = level

    """
    Used for finding the shortest path from start_point to item_name
    """
    def get_sell_to_item_path(self, item_name: str = None, coord_target: tuple = None, start_point: tuple = None, add_path_to_layout: bool = True):
        if start_point is None and coord_target is None:
            raise Exception("start_point or coord_target must have values")

        visited = [[False] * len(self._layout.sells[0]) for _ in range(len(self._layout.sells))]

        queue = [start_point]
        visited[start_point[0]][start_point[1]] = (inf, inf)

        item_coordinates = None
        break_flag = False

        while queue and break_flag is False:
            s = queue.pop(0)
            for i, j in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if s[0]+i < 0 or s[0]+i >= len(self._layout.sells) or s[1]+j < 0 or s[1]+j >= len(self._layout.sells[0]):
                    continue
                if coord_target is not None and (s[0]+i, s[1]+j) == coord_target:
                    item_coordinates = (s[0]+i, s[1]+j)
                    visited[s[0]+i][s[1]+j] = (s[0], s[1])
                    break_flag = True
                    break
                if self._layout.sells[s[0]+i][s[1]+j].type.name in ["FLOOR", "CASHIER"] and visited[s[0]+i][s[1]+j] == False:
                    queue.append((s[0]+i, s[1]+j))
                    visited[s[0]+i][s[1]+j] = (s[0], s[1])
                elif self._layout.sells[s[0]+i][s[1]+j].type.name == "RACK" and item_name is not None and self._layout.sells[s[0]+i][s[1]+j].items.count(item_name) > 0:
                    item_coordinates = (s[0]+i, s[1]+j)
                    visited[s[0]+i][s[1]+j] = (s[0], s[1])
                    break_flag = True
                    break

        if item_coordinates is not None:
            # restore path
            path = []
            coords = item_coordinates
            while coords != (inf, inf):
                path.append(coords)
                if add_path_to_layout is True:
                    self._layout.sells[coords[0]][coords[1]].pathCount += 1
                coords = visited[coords[0]][coords[1]]

            path.reverse()

            return path, item_coordinates

        return None, None

    def get_check_optimal_path(self, transaction_list: list, start_point: tuple = None, add_path_to_layout: bool = True, use_product_count: bool = False, debug: bool = False):
        if start_point is None:
            start_point = self._doors[randint(0, len(self._doors)-1)]

        def remove_found_items(items: list, check_list: list):
            items_list = [item[0] for item in items if item[1] > 0]
            return [c_item for c_item in check_list if c_item not in items_list]


        def check_item_in_rack(items: list, check_list: list):
            for item, count in items:
                if item in check_list and (use_product_count is False or count > 0):
                    return True
            return False

        def update_rack_items(rack_coords: Tuple[int, int], check_list: list):
            for item in range(self.get_max_rack_level()):
                item_tuple = self._layout.sells[rack_coords[0]][rack_coords[1]].items[item]
                if item_tuple[0] in check_list and item_tuple[1] > 0:
                    self._layout.sells[rack_coords[0]][rack_coords[1]].items[item] = \
                        (self._layout.sells[rack_coords[0]][rack_coords[1]].items[item][0], self._layout.sells[rack_coords[0]][rack_coords[1]].items[item][1] - 1)
                    break

        fullPath = []
        transaction_list_copy = transaction_list.copy()
        while len(transaction_list_copy) > 0:
            if debug:
                print(f"Path: {fullPath}, List = {transaction_list_copy}")
            visited = [[False] * len(self._layout.sells[0]) for _ in range(len(self._layout.sells))]

            queue = [start_point]
            visited[start_point[0]][start_point[1]] = (inf, inf)

            item_coordinates = None
            break_flag = False

            while queue and break_flag is False:
                s = queue.pop(0)
                for i, j in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if s[0]+i < 0 or s[0]+i >= len(self._layout.sells) or s[1]+j < 0 or s[1]+j >= len(self._layout.sells[0]):
                        continue
                    if self._layout.sells[s[0]+i][s[1]+j].type.name in ["FLOOR", "CASHIER"] and visited[s[0]+i][s[1]+j] == False:
                        queue.append((s[0]+i, s[1]+j))
                        visited[s[0]+i][s[1]+j] = (s[0], s[1])
                    elif self._layout.sells[s[0]+i][s[1]+j].type.name == "RACK" and check_item_in_rack(self._layout.sells[s[0]+i][s[1]+j].items, transaction_list_copy):
                        item_coordinates = (s[0]+i, s[1]+j)
                        visited[s[0]+i][s[1]+j] = (s[0], s[1])
                        break_flag = True
                        update_rack_items((s[0] + i, s[1] + j), transaction_list_copy)
                        transaction_list_copy = remove_found_items(self._layout.sells[s[0]+i][s[1]+j].items, transaction_list_copy)
                        break

            if item_coordinates is not None:
                # restore path
                path = []
                coords = item_coordinates
                start_point = coords
                while coords != (inf, inf):
                    path.append(coords)
                    if add_path_to_layout is True:
                        self._layout.sells[coords[0]][coords[1]].pathCount += 1
                    coords = visited[coords[0]][coords[1]]

                path.reverse()

                fullPath += path

            else:
                raise NoItemInLayoutError (transaction_list_copy)

        fullPath += self.get_sell_to_item_path(coord_target=self._cashiers[randint(0, len(self._cashiers)-1)], start_point=fullPath[-1])[0]
        return fullPath

    #with provided item order
    def calculate_path_for_single_check(self, check: list, add_to_layout: bool = True):
        start_point = self._doors[randint(0, len(self._doors)-1)]
        path, _ = self.get_sell_to_item_path(check[0], start_point=start_point, add_path_to_layout=add_to_layout)
        for item in check[1:]:
            path += self.get_sell_to_item_path(item, start_point=path[-2], add_path_to_layout=add_to_layout)[0]
        path += self.get_sell_to_item_path(coord_target=self._cashiers[randint(0, len(self._cashiers)-1)], start_point=path[-2], add_path_to_layout=add_to_layout)[0]
        return path

    def calculate_path_to_cashier(self, start_point: tuple, add_to_layout: bool = False):
        # path to the closest cashier
        main_path = self.get_sell_to_item_path(coord_target=self._cashiers[0], start_point=start_point, add_path_to_layout=add_to_layout)[0]
        for i in range(1, len(self._cashiers)):
            path = self.get_sell_to_item_path(coord_target=self._cashiers[i], start_point=start_point, add_path_to_layout=add_to_layout)[0]
            if len(path) < len(main_path):
                main_path = path
        return main_path

    def calculate_path_to_door(self, start_point: tuple, add_to_layout: bool = False):
        # path to the closest door
        main_path = self.get_sell_to_item_path(coord_target=self._doors[0], start_point=start_point, add_path_to_layout=add_to_layout)[0]
        for i in range(1, len(self._doors)):
            path = self.get_sell_to_item_path(coord_target=self._doors[i], start_point=start_point, add_path_to_layout=add_to_layout)[0]
            if len(path) < len(main_path):
                main_path = path
        return main_path

    def calculate_check_score(self, check: list, add_to_layout: bool = True):
        path = self.calculate_path_for_single_check(check, add_to_layout=add_to_layout)
        return path, len(path)

    def display_in_window(self, home_dir = "", debug: bool = False):
        url = 'file:///' + home_dir + '\\ui\\template\\store.html'
        # pass html template as file to webview
        self._window = webview.create_window(title=self._layout_name, url=url, width=50+len(self._layout.sells[0])*40, height=150+len(self._layout.sells)*40, js_api=self)
        def send_config_callback(result):
            print(result)
        def send_config_to_js(window):
            result = window.evaluate_js(
                f"""
                    //$.getScript("./js/store.js")
                    console.log("creating layout");
                    var cfg = JSON.parse(`{self.get_layout_json()}`);
                    console.log(cfg);
                    var layout = new StoreLayout(cfg);
                    console.log("layout created");
                """, send_config_callback)
            return result

        webview.start(send_config_to_js, self._window, debug=debug)
