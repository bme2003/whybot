import numpy as np
from typing import List, Tuple

Coord = Tuple[int,int]

def make_memory_grid(width: int, height: int, hazards: List[Coord], decay: float = 0.9) -> np.ndarray:
    """
    Hazard memory: bump spots that 'color' nearby cells with extra cost.
    """
    mem = np.zeros((height,width), dtype=np.float32)
    if not hazards:
        return mem
    for (x,y) in hazards:
        if 0<=x<width and 0<=y<height:
            # radial bump with decay by distance
            for yy in range(height):
                for xx in range(width):
                    d = abs(xx-x) + abs(yy-y)
                    mem[yy,xx] += (decay ** d)
    # normalize 0..1
    if mem.max() > 0:
        mem = mem / mem.max()
    return mem