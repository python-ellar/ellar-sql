from dataclasses import dataclass


@dataclass
class CroppingDetails:
    x: int
    y: int
    height: int
    width: int
