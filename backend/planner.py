from typing import Dict, List, Tuple, Optional
import heapq
import numpy as np
from .utils import neighbors_4, manhattan
from .risk import make_risk_grid, make_uncertainty_grid
from .memory import make_memory_grid

Coord = Tuple[int,int]

class MultiCostPlanner:
    def __init__(self, width: int, height: int, obstacles: List[Coord],
                 hazards: List[Coord], weights: Dict[str,float], seed: Optional[int]=None):
        self.w = width
        self.h = height
        self.obstacles = set(obstacles)
        self.weights = weights
        self.risk = make_risk_grid(width, height, obstacles)
        self.unc = make_uncertainty_grid(width, height, seed)
        self.mem = make_memory_grid(width, height, hazards)
        # quick block mask
        self.blocked = np.zeros((height,width), dtype=np.uint8)
        for (x,y) in self.obstacles:
            if 0<=x<width and 0<=y<height:
                self.blocked[y,x]=1

    def passable(self, p: Coord) -> bool:
        x,y = p
        return (0<=x<self.w) and (0<=y<self.h) and (self.blocked[y,x]==0)

    def step_cost_terms(self, prev: Coord, curr: Coord, nxt: Coord, prev_dir: Optional[Coord]) -> Dict[str,float]:
        """
        Compute per-term costs of stepping into nxt.
        - time: 1 per move
        - risk: risk grid at nxt
        - energy: turning penalty if direction changes
        - uncertainty: unc grid at nxt
        - memory: mem grid at nxt
        """
        terms = {
            "time": 1.0,
            "risk": float(self.risk[nxt[1], nxt[0]]),
            "uncertainty": float(self.unc[nxt[1], nxt[0]]),
            "memory": float(self.mem[nxt[1], nxt[0]]),
            "energy": 0.0
        }
        if prev_dir is not None:
            new_dir = (nxt[0]-curr[0], nxt[1]-curr[1])
            if new_dir != prev_dir:
                terms["energy"] = 0.2  # small turning penalty
        return terms

    def combine_cost(self, terms: Dict[str,float]) -> float:
        w = self.weights
        return (w["time"]*terms["time"] +
                w["risk"]*terms["risk"] +
                w["energy"]*terms["energy"] +
                w["uncertainty"]*terms["uncertainty"] +
                w["memory"]*terms["memory"])

    def a_star(self, start: Coord, goal: Coord):
        if not self.passable(start) or not self.passable(goal):
            return [], False, 0.0, {"time":0,"risk":0,"energy":0,"uncertainty":0,"memory":0}
        # Each node: f, g, (x,y), parent, prev_dir, term_sums
        openh = []
        start_node = (0.0, 0.0, start, None, None, {"time":0.0,"risk":0.0,"energy":0.0,"uncertainty":0.0,"memory":0.0})
        heapq.heappush(openh, start_node)
        gbest = {start: 0.0}
        parent = {}
        prevdir = {start: None}
        termsums = {start: {"time":0.0,"risk":0.0,"energy":0.0,"uncertainty":0.0,"memory":0.0}}

        while openh:
            f, g, curr, par, pdir, tsum = heapq.heappop(openh)
            if curr == goal:
                # reconstruct
                path = [curr]
                node = curr
                while node in parent:
                    node = parent[node]
                    path.append(node)
                path.reverse()
                return path, True, g, tsum
            for nxt in neighbors_4(curr, self.w, self.h):
                if not self.passable(nxt):
                    continue
                # compute terms using prev=current's prevdir, curr, nxt
                terms = self.step_cost_terms(par, curr, nxt, pdir)
                step_c = self.combine_cost(terms)
                g2 = g + step_c
                if nxt not in gbest or g2 < gbest[nxt]:
                    gbest[nxt] = g2
                    parent[nxt] = curr
                    newdir = (nxt[0]-curr[0], nxt[1]-curr[1])
                    prevdir[nxt] = newdir
                    tsum2 = {
                        "time": tsum["time"] + terms["time"],
                        "risk": tsum["risk"] + terms["risk"],
                        "energy": tsum["energy"] + terms["energy"],
                        "uncertainty": tsum["uncertainty"] + terms["uncertainty"],
                        "memory": tsum["memory"] + terms["memory"],
                    }
                    h = manhattan(nxt, goal)  # time-ish heuristic
                    f2 = g2 + (self.weights["time"] * h)  # keep heuristic simple
                    heapq.heappush(openh, (f2, g2, nxt, curr, newdir, tsum2))
        return [], False, 0.0, {"time":0,"risk":0,"energy":0,"uncertainty":0,"memory":0}

    def plan(self, start: Coord, goal: Coord):
        path, ok, total, sums = self.a_star(start, goal)
        return path, ok, total, sums
