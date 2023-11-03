from typing import List
from pydantic import BaseModel
from ui.python.dataClass.TileType import TileType


class Sell(BaseModel):
    type: TileType
    items: List[str]
    pathCount: int