import os
from math import inf

from pydantic import BaseModel
from ui.python.dataClass.LayoutModel import LayoutModel


class Layout:
    _layout = None
    _layout_name = None

    def load_layout(self):
        with open(self.path_to_json) as file:
            raw_layout = file.read()

        layout = LayoutModel.parse_raw(raw_layout)
        return layout

    def __init__(self, path_to_json):
        self.path_to_json = path_to_json
        self._layout = self.load_layout()
        self._layout_name = os.path.basename(path_to_json)

    def get_layout_name(self):
        return self._layout_name

    def get_layout(self):
        return self._layout

    def get_layout_json(self):
        return self._layout.model_dump_json()

    """
    Used for finding the shortest path from start_point to item_name
    """
    def get_sell_to_item_path(self, item_name: str, start_point: tuple, add_path_to_layout: bool = True):
        visited = [[False] * len(self._layout.sells[0]) for _ in range(len(self._layout.sells))]

        queue = [start_point]
        visited[start_point[0]][start_point[1]] = (inf, inf)

        item_coordinates = None

        while queue:
            s = queue.pop(0)
            for i, j in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if s[0]+i < 0 or s[0]+i >= len(self._layout.sells) or s[1]+j < 0 or s[1]+j >= len(self._layout.sells[0]):
                    continue
                if self._layout.sells[s[0]+i][s[1]+j].type.name == "FLOOR" and visited[s[0]+i][s[1]+j] == False:
                    queue.append((s[0]+i, s[1]+j))
                    visited[s[0]+i][s[1]+j] = (s[0], s[1])
                elif self._layout.sells[s[0]+i][s[1]+j].type.name == "RACK" and self._layout.sells[s[0]+i][s[1]+j].items.count(item_name) > 0:
                    item_coordinates = (s[0]+i, s[1]+j)
                    visited[s[0]+i][s[1]+j] = (s[0], s[1])
                    break

        if item_coordinates is not None:
            # restore path
            path = []
            coords = item_coordinates
            while coords != (inf, inf):
                path.append(coords)
                self._layout.sells[coords[0]][coords[1]].pathCount += 1
                coords = visited[coords[0]][coords[1]]

            path.reverse()

            return path, item_coordinates
