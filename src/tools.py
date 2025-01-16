from nptyping import Float, Int, NDArray, Shape

from instance import Instance


def cable_cost(
    instance: Instance,
    node_a: int,
    node_b: int,
    node_power: int,
    M1: int
) -> float:
    """Get the cost for a cable connected in node_a and node_b"""

    cable_index = instance.get_cable_index_from_node_power(node_power)
    length_cost = instance.distance[node_a][node_b] * instance.cables[cable_index]['cost_per_meter']
    overflow_cost = M1 * max(0, node_power - instance.max_cable_capacity)

    return length_cost + overflow_cost


def node_power(
    nodes: NDArray[Shape["*"], Int],
    edges: list[tuple[int, int]]
) -> list[int]:
    """Return the power each node outputs"""

    tree: list[list[int]] = [[] for _ in nodes]
    for [u, v] in edges:
        tree[u].append(v)
        tree[v].append(u)

    # We assume each turbine produces 1 of power
    power = [1 for _ in nodes]
    vis = [False for _ in nodes]

    def calculate_power(node: int):
        vis[node] = True
        for child_node in tree[node]:
            if vis[child_node]: continue
            power[node] += calculate_power(child_node)
        return power[node]
    calculate_power(0)

    return power


def node_power_branch(
    nodes: list[int] | NDArray[Shape["*"], Int],
    edges: list[tuple[int, int]],
    root: int
) -> list[int]:
    """Return the power each node outputs for a branch"""

    mapping: dict[int, int] = {}
    for i in range(len(nodes)):
        mapping[nodes[i]] = i

    tree: list[list[int]] = [[] for _ in nodes]
    for [u, v] in edges:
        tree[mapping[u]].append(v)
        tree[mapping[v]].append(u)

    # We assume each turbine produces 1 of power
    power = [1 for _ in nodes]
    vis = [False for _ in nodes]

    def calculate_power(node: int):
        node = mapping[node]
        vis[node] = True
        for child_node in tree[node]:
            if vis[mapping[child_node]]: continue
            power[node] += calculate_power(child_node)
        return power[node]
    calculate_power(root)

    return power


def prim(
    nodes: list[int],
    distance: NDArray[Shape["Nodes, Nodes"], Float],
    starting_node: int,
    size: int = -1
) -> list[tuple[int, int]]:
    """Directed Minimum Spanning Tree with weights as distances between nodes"""

    if size < 0: size = len(nodes)

    minimum_spanning_tree_nodes = [ starting_node ]

    fringe_nodes = set(nodes)
    fringe_nodes.remove(starting_node)

    next_mnode: int
    next_fnode: int
    edges: list[tuple[int, int]] = []

    while len(fringe_nodes) > 0 and len(minimum_spanning_tree_nodes) < size:
        min_dist = 1e18

        for mnode in minimum_spanning_tree_nodes:
            for fnode in fringe_nodes:
                if distance[mnode][fnode] < min_dist:
                    next_mnode = mnode
                    next_fnode = fnode
                    min_dist = distance[mnode][fnode]

        fringe_nodes.remove(next_fnode)
        minimum_spanning_tree_nodes.append(next_fnode)

        edges.append((next_fnode, next_mnode))

    return edges


def _sort_turbines_by_distance_to_substation(
    turbines: list[int],
    distance: NDArray[Shape["Nodes, Nodes"], Float]
) -> list[int]:
    distance_to_substation = [distance[turbine][0] for turbine in turbines]
    order = sorted(range(len(distance_to_substation)), key=lambda x: distance_to_substation[x])
    return [turbines[i] for i in order]


def _sweep_groups(
    n: int,
    starting_turbine: int,
    clockwise: bool,
    tpg: int
) -> list[list[int]]:
    groups: list[list[int]] = []
    i = starting_turbine
    j = 0
    k = 0

    while i <= n if clockwise else i >= 1:
        groups.append([])
        while j < tpg and (i <= n if clockwise else i >= 1):
            groups[k].append(i)
            i += 1 if clockwise else -1
            j += 1
        j %= tpg
        k += 1

    i = 1 if clockwise else n
    while i < starting_turbine if clockwise else i > starting_turbine:
        groups.append([])
        while j < tpg and (i < starting_turbine if clockwise else i > starting_turbine):
            groups[k].append(i)
            i += 1 if clockwise else -1
            j += 1
        j %= tpg
        k += 1

    i = 0
    while 1 not in groups[i]:
        i += 1
    groups = groups[i:] + groups[:i]

    return groups


def sweep(
    instance: Instance,
    starting_turbine: int,
    clockwise: bool,
    tpg: int
) -> list[tuple[int, int]]:
    groups = _sweep_groups(instance.n, starting_turbine, clockwise, tpg)
    groups = [_sort_turbines_by_distance_to_substation(turbines, instance.distance) for turbines in groups]
    edges_groups = [[(turbines[0], 0)] + prim(turbines, instance.distance, turbines[0]) for turbines in groups]
    return [edge for edges in edges_groups for edge in edges]
