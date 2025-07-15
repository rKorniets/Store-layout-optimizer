from typing import List, Optional, Tuple
from pydantic import BaseModel
from ui.python.dataClass.TileType import TileType


class Sell(BaseModel):
    type: TileType
    items: Optional[List[Optional[Tuple[str, int]]]]
    pathCount: int
    category: Optional[str] = None