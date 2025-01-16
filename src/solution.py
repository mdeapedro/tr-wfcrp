from tools import cable_cost, node_power
from utils import intersect
from instance import Instance


# We assume that the solution is always a proper tree. It's possible to
# guarantee this by taking care of it at each step of manipulation.
# If we permit the solution to not be a proper tree, then will be impossible
# to calculate the output power of nodes (since there can be cycles), and,
# therefore, very unfeasable to calculate an overall cost.
class Solution:
    _M1: int
    _M2: int
    _M3: int
    _M4: int
    _children_node: list[set[int]]
    _connections_to_substation: int
    _cost_for_cables: float
    _instance: Instance
    _node_power: list[int]
    _number_of_crossings: int
    _parent_node: list[int]

    @property
    def node_power(self):
        return self._node_power

    @property
    def children_node(self):
        return self._children_node

    @property
    def instance(self):
        return self._instance

    @property
    def parent_node(self):
        return self._parent_node

    def __init__(
        self,
        instance: Instance,
        edges: list[tuple[int, int]],
        M1 = 1_000_000_000,
        M2 = 1_000_000_000,
        M3 = 1_000_000_000,
        M4 = 10_000_000_000,
    ):
        self._M1 = M1
        self._M2 = M2
        self._M3 = M3
        self._M4 = M4
        self._children_node = [set() for _ in instance.nodes]
        self._instance = instance
        self._parent_node = [0 for _ in instance.nodes]
        self.build(edges)

    def build(self, edges: list[tuple[int, int]], ignore_crossings=False):
        for node_set in self._children_node:
            node_set.clear()
        for [node_a, node_b] in edges:
            self._parent_node[node_a] = node_b
            self._children_node[node_b].add(node_a)
        self.cost(ignore_crossings, recalculate=True)

    def get_edges(self) -> list[tuple[int, int]]:
        return [(i, self._parent_node[i]) for i in self._instance.nodes[1::]]

    def recalculate_node_power(self) -> None:
        self._node_power = node_power(self._instance.nodes, self.get_edges())

    def cost_for_cables(self, recalculate=False) -> float:
        if recalculate:
            self.recalculate_node_power()
            cost = 0.0
            for [node_a, node_b] in self.get_edges():
                cost += cable_cost(self._instance, node_a, node_b, self._node_power[node_a], self._M1)
            self._cost_for_cables = cost
        return self._cost_for_cables

    def number_of_crossings(self, recalculate=False) -> int:
        if recalculate:
            edges = self.get_edges()
            ret = 0
            for i in range(len(edges)):
                for j in range(i + 1, len(edges)):
                    if (
                        edges[i][0] != edges[j][0] and
                        edges[i][0] != edges[j][1] and
                        edges[i][1] != edges[j][0] and
                        edges[i][1] != edges[j][1]
                    ): ret += intersect(
                        self._instance.position[edges[i][0]],
                        self._instance.position[edges[i][1]],
                        self._instance.position[edges[j][0]],
                        self._instance.position[edges[j][1]],
                    )
            self._number_of_crossings = ret
        return self._number_of_crossings

    def cost_for_crossings(self, recalculate=False) -> int:
        return self._M3 * self.number_of_crossings(recalculate)

    def connections_to_substation(self, recalculate=False) -> int:
        if recalculate:
            ret = 0
            for node in self._parent_node[1::]:
                if node == 0: ret += 1
            self._connections_to_substation = ret
        return self._connections_to_substation

    def cost_for_connections_to_substation(self, recalculate=False) -> int:
        return max(0, self._M2 * (self.connections_to_substation(recalculate) - self._instance.C))

    def cost(self, ignore_crossings=False, recalculate=False) -> int:
        return int(
            self.cost_for_cables(recalculate) +
            self.cost_for_connections_to_substation(recalculate) +
            (0 if ignore_crossings else self.cost_for_crossings(recalculate))
        )

    def _just_move(self, child_node: int, parent_node: int):
        self._children_node[self._parent_node[child_node]].remove(child_node)
        self._parent_node[child_node] = parent_node
        self._children_node[parent_node].add(child_node)

    def move(self, child_node: int, parent_node: int, save_state=False):
        """Disconnect 'child_node' from its parent node and connect it to 'parent_node'.

        Be careful to not break the tree (creating cycles or disconnecting a branch entirely)."""
        if save_state:
            self._child_node_save = child_node
            self._parent_node_save = self._parent_node[child_node]
            self._node_power_save = self._node_power.copy()
            self._cost_for_cables_save = self._cost_for_cables
            self._connections_to_substation_save = self._connections_to_substation
            self._number_of_crossings_save = self._number_of_crossings

        node = self._parent_node[child_node]
        self._cost_for_cables -= cable_cost(self._instance, child_node, node, self._node_power[child_node], self._M1)
        while node != 0:
            next_node = self._parent_node[node]
            self._cost_for_cables -= cable_cost(self._instance, node, next_node, self._node_power[node], self._M1)
            self._node_power[node] -= self._node_power[child_node]
            self._cost_for_cables += cable_cost(self._instance, node, next_node, self._node_power[node], self._M1)
            node = next_node
        node = parent_node
        self._cost_for_cables += cable_cost(self._instance, child_node, node, self._node_power[child_node], self._M1)
        while node != 0:
            next_node = self._parent_node[node]
            self._cost_for_cables -= cable_cost(self._instance, node, next_node, self._node_power[node], self._M1)
            self._node_power[node] += self._node_power[child_node]
            self._cost_for_cables += cable_cost(self._instance, node, next_node, self._node_power[node], self._M1)
            node = next_node

        self._connections_to_substation -= self._parent_node[child_node] == 0
        self._connections_to_substation += parent_node == 0

        for i in range(1, self._instance.n+1):
            if (
                i == child_node or
                i == self._parent_node[child_node] or
                self._parent_node[i] == child_node or
                self._parent_node[i] == self._parent_node[child_node]
                ): continue
            self._number_of_crossings -= intersect(
                self._instance.position[child_node],
                self._instance.position[self._parent_node[child_node]],
                self._instance.position[i],
                self._instance.position[self._parent_node[i]])

        self._just_move(child_node, parent_node)

        for i in range(1, self._instance.n+1):
            if (
                i == child_node or
                i == self._parent_node[child_node] or
                self._parent_node[i] == child_node or
                self._parent_node[i] == self._parent_node[child_node]
                ): continue
            self._number_of_crossings += intersect(
                self._instance.position[child_node],
                self._instance.position[parent_node],
                self._instance.position[i],
                self._instance.position[self._parent_node[i]])

    def move_back(self):
        """Move back to previous saved state move."""
        self._just_move(self._child_node_save, self._parent_node_save)
        self._cost_for_cables = self._cost_for_cables_save
        self._connections_to_substation = self._connections_to_substation_save
        self._number_of_crossings = self._number_of_crossings_save
        self._node_power = self._node_power_save.copy()

    def is_node_in_branch(self, branch_root: int, node: int):
        if branch_root == node: return True
        for child_node in self._children_node[branch_root]:
            if self.is_node_in_branch(child_node, node): return True
        return False

    def get_branch_nodes(self, branch_root: int):
        branch_nodes: list[int] = []
        def dfs(node: int):
            branch_nodes.append(node)
            for child_node in self._children_node[node]:
                dfs(child_node)
        dfs(branch_root)
        return branch_nodes
