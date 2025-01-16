from typing import Iterable, Sequence


def _direction(
    p: tuple[float, float],
    q: tuple[float, float],
    r: tuple[float, float],
):
    return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])


def intersect(
    a1: tuple[float, float],
    b1: tuple[float, float],
    a2: tuple[float, float],
    b2: tuple[float, float],
) -> bool:
    """Checks if two line segments a1b1 and a2b2 crosses each other"""

    d1 = _direction(a1, b1, a2)
    d2 = _direction(a1, b1, b2)
    d3 = _direction(a2, b2, a1)
    d4 = _direction(a2, b2, b1)

    if d1 == 0 and d2 == 0:
        if b1[0] < a1[0]: a1, b1 = b1, a1
        if b2[0] < a2[0]: a2, b2 = b2, a2
        if a1[0] <= a2[0] and b1[0] >= b2[0]: return True
        if a1[0] >= a2[0] and b1[0] <= b2[0]: return True
        return False

    if (((d1>=0 and d2<=0) or (d1<=0 and d2>=0)) and
        ((d3>=0 and d4<=0) or (d3<=0 and d4>=0))):
        return True
    return False


def is_proper_tree(children: Sequence[Iterable[int]], root: int) -> bool:
    "Checks if a directed graph is a proper tree"
    vis = [False for _ in children]
    not_cycle = [True]

    def dfs(node: int) -> None:
        if vis[node]:
            not_cycle[0] = False
            return
        vis[node] = True
        for child_node in children[node]:
            dfs(child_node)

    dfs(root)
    return not_cycle[0] and sum(vis) == len(children)
