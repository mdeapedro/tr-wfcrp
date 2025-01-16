from os import path

import numpy as np
from nptyping import Float, Int, NDArray, Shape, Structure


class Instance:
    _C: int
    _Cmin: int
    _cable_indices: NDArray[Shape["*"], Int]
    _cables: NDArray[Shape["*"], Structure["[capacity, cost_per_meter, availability]: Int"]]
    _delta: NDArray[Shape["1, 2"], Float]
    _distance: NDArray[Shape["Nodes, Nodes"], Float]
    _max_cable_capacity: int
    _name: str
    _nodes: NDArray[Shape["Nodes"], Int]
    _position: NDArray[Shape["Nodes, 2"], Float]

    @property
    def C(self):
        """Substation's capacity"""
        return self._C

    @property
    def Cmin(self):
        """Minimum substation's capacity defined by instance"""
        return self._Cmin

    @property
    def cables(self):
        """List of cables"""
        return self._cables

    @property
    def delta(self):
        """Substation's original position"""
        return self._delta

    @property
    def distance(self):
        """Distance between node i to j for each i, j from 0 to n"""
        return self._distance

    @property
    def max_cable_capacity(self):
        """Maximum capacity among all cables"""
        return self._max_cable_capacity

    @property
    def name(self):
        """Instance file name"""
        return self._name

    @property
    def n(self):
        """Number of turbines"""
        return len(self._position)-1

    @property
    def nodes(self):
        """Indices of nodes. This is basically range(n + 1)"""
        return self._nodes

    @property
    def position(self):
        """Positions of nodes from 0 to n"""
        return self._position

    def get_cable_index_from_node_power(self, node_power: int) -> int:
        """Return the appropriate cable for a given turbine's power"""
        node_power = min(node_power, self._max_cable_capacity)
        return self._cable_indices[node_power]

    def __init__(
        self,
        instance_dir: str,
        instance: str,
        C: int = 0
    ):
        self._name = instance
        with open(f"{path.join(instance_dir, instance)}.turb") as file:
            first_line = file.readline().split()

            self._Cmin = -int(first_line[2]) - 1

            self._delta = np.array((float(first_line[0]), float(first_line[1])))

            nodes = [[0.0, 0.0]]
            for line in file:
                words = line.split()
                nodes.append([
                    float(words[0]) - self._delta[0],
                    float(words[1]) - self._delta[1],
                ])

        if C == 0:
            self._C = self._Cmin + 1
        elif self._Cmin > C:
            message = f"C ({C}) cannot be lower than the instance's Cmin ({self._Cmin})"
            raise ValueError(message)
        else:
            self._C = C

        self._position = np.array(nodes)

        # Sort turbines by clockwise order relative to the substation.
        # This way, each turbine will be uniquely identified by its index after sort.
        clockwise_order = []
        h = np.array([1, 0])
        for turb in self._position[1::]:
            t = turb / np.linalg.norm(turb)
            d = np.dot(h, t)
            angle = np.arccos(d)
            clockwise_order.append(angle)
        self._position[1::] = self._position[1::][np.argsort(clockwise_order)]

        # Create the matrix of distances between each node i to each node j.
        self._distance = np.empty((len(self._position), len(self._position)))
        for i in range(len(self._position)):
            self._distance[i][i] = 0.0
            for j in range(i+1, len(self._position)):
                self._distance[i][j] = np.linalg.norm(self._position[i] - self._position[j])
                self._distance[j][i] = self._distance[i][j]

        cables: list[tuple[int, int, int]] = []
        with open(f"{path.join(instance_dir, instance)}.cable") as file:
            for line in file:
                words = line.split()
                cables.append((
                    int(words[0]), # capacity
                    int(words[1]), # cost_per_meter
                    int(words[2]), # availability
                ))

        cables.sort()

        self._cables = np.array(cables, dtype=[("capacity", "i4"), ("cost_per_meter", "i4"), ("availability", "i4")])

        self._max_cable_capacity = self._cables[-1]["capacity"]

        # Aux list for getting cable index from node_power
        cable_indices = list(range(self._max_cable_capacity+1))
        i = 0
        j = 1
        while j < len(cable_indices):
            if j > self._cables[i]["capacity"]:
                i += 1
            else:
                cable_indices[j] = i
                j += 1

        self._cable_indices = np.array(cable_indices)

        self._nodes = np.array(range(len(self._position)))
