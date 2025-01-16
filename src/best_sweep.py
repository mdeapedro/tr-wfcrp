from instance import Instance
from solution import Solution
from tools import sweep


def best_sweep(instance: Instance):
    """Iterate over all possible sweeps and return the best"""
    current_cost = 1e18
    current_edges: list[tuple[int, int]] = []
    S = Solution(instance, [])

    for starting_turbine in instance.nodes[1::]:
        for clockwise in (False, True):
            for tpg in range(instance.n // instance.C, instance.max_cable_capacity + 1):
                edges = sweep(instance, starting_turbine, clockwise, tpg)
                S.build(edges, ignore_crossings=True)
                cost = S.cost()
                if cost < current_cost:
                    current_cost = cost
                    current_edges = edges

    return current_edges
