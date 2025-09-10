import numpy as np
from typing import List, Tuple

Coord = Tuple[int,int]

def make_risk_grid(width: int, height: int, obstacles: List[Coord]) -> np.ndarray:
    """
    Simple risk: higher near obstacles, lower far away.
    We'll approximate distance-to-obstacle without SciPy:
    risk = exp(-d/sigma), with small d near walls -> high risk.
    """
    grid = np.zeros((height, width), dtype=np.float32)
    if not obstacles:
        return grid
    obs_mask = np.zeros_like(grid, dtype=np.uint8)
    for (x,y) in obstacles:
        if 0<=x<width and 0<=y<height:
            obs_mask[y,x]=1
    # For each cell, compute min manhattan distance to any obstacle (naive but fine for small grids).
    ys, xs = np.indices(grid.shape)
    obs_coords = np.argwhere(obs_mask==1)
    if len(obs_coords)==0:
        return grid
    # naive distance
    dmin = np.full_like(grid, fill_value=9999, dtype=np.int32)
    for oy, ox in obs_coords:
        d = np.abs(xs-ox) + np.abs(ys-oy)
        dmin = np.minimum(dmin, d)
    sigma = 4.0
    risk = np.exp(-dmin / sigma)
    # Obstacles should be impassable; we can still mark high risk on cells adjacent to them.
    risk[obs_mask==1] = 1.0
    return risk

def make_uncertainty_grid(width: int, height: int, seed: int | None = None) -> np.ndarray:
    """
    Toy uncertainty: smooth noise field (0..1).
    """
    rng = np.random.default_rng(seed if seed is not None else 123)
    base = rng.random((height, width), dtype=np.float32)
    # Smooth by simple box filter
    k = 2
    sm = base.copy()
    for _ in range(2):
        tmp = sm.copy()
        for y in range(height):
            for x in range(width):
                y0 = max(0, y-k); y1 = min(height, y+k+1)
                x0 = max(0, x-k); x1 = min(width, x+k+1)
                sm[y,x] = tmp[y0:y1, x0:x1].mean()
    return sm
