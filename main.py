from ui.python.Layout import Layout

path = "./data/layout 18x252.json"

layout = Layout(path)
print(layout.get_layout_name())
print(layout.get_layout())

res1 = layout.get_sell_to_item_path("test1", (17, 13))[0]
res2 = layout.get_sell_to_item_path("test2", res1[-2])[0]
res3 = layout.get_sell_to_item_path("test3", res2[-2])[0]
res4 = layout.get_sell_to_item_path("test4", res3[-2])[0]
res5 = layout.get_sell_to_item_path("test5", res4[-2])[0]

print(res1, res2, res3, res4, sep="\n")

# save layout to json file
with open("./data/layout 18x25_3.json", "w") as file:
    file.write(layout.get_layout_json())