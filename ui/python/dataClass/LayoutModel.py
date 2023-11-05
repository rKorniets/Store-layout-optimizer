from typing import List
from pydantic import BaseModel
from ui.python.dataClass.Sell import Sell


class LayoutModel(BaseModel):
    hideSaveLoadButtons: bool
    items: List[str]
    sells: List[List[Sell]]