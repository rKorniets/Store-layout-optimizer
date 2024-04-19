class NoItemInLayoutError(Exception):
    def __init__(self, item_array):
        self.item_name = item_array
        super().__init__(f"No items from array is found in layout: {item_array}")