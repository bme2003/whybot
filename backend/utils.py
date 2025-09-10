from typing import Tuple, Iterable

def manhattan(a: Tuple[int,int], b: Tuple[int,int]) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def neighbors_4(p: Tuple[int,int], w: int, h: int) -> Iterable[Tuple[int,int]]:
    x,y = p
    if x>0: yield (x-1,y)
    if x<w-1: yield (x+1,y)
    if y>0: yield (x,y-1)
    if y<h-1: yield (x,y+1)

def clamp01(x: float) -> float:
    return 0.0 if x<0 else (1.0 if x>1 else x)
