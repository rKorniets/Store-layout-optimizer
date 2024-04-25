import os
from pathlib import Path

from ui.python.Layout import Layout

path = "./data/layout 18x25_6.json"

layout = Layout(path)
print(layout.get_layout_name())
print(layout.get_layout())

test_items = ["test7", "test1", "test2", "test3", "test5", "test4"]
layout.set_item_list(test_items)

# test check
test_check = ["test1", "test2", "test3", "test4", "test5"]

# set items to rack
layout.set_item_to_rack("test1", (2, 17), 0)
layout.set_item_to_rack("test2", (6, 8), 3)
layout.set_item_to_rack("test3", (10, 12), 3)
layout.set_item_to_rack("test4", (10, 17), 2)
layout.set_item_to_rack("test5", (13, 8), 1)

# test check
test_path = layout.get_check_optimal_path(test_check)
#test_path = layout.calculate_path_for_single_check(test_check)

print(test_path)


# save layout to json file
with open("./data/layout 18x25_6_1.json", "w") as file:
    file.write(layout.get_layout_json())

layout.display_in_window(str(Path(os.getcwd())))
