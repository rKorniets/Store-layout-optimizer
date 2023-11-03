from typing import List
from pydantic import BaseModel
from ui.python.dataClass.Sell import Sell


class LayoutModel(BaseModel):
    sells: List[List[Sell]]