from typing import List
from pydantic import BaseModel
from ui.python.dataClass.Sell import Sell


class LayoutModel(BaseModel):
    hideSaveLoadButtons: bool
    rackLevels: int
    items: List[str]
    sells: List[List[Sell]]