import networkx as nx

from instance import Instance
from solution import Solution


def plot(solution: Solution):
    instance = solution.instance
    G = nx.Graph()
    for node in instance.nodes: G.add_node(node, pos=instance.position[node])
    pos = nx.get_node_attributes(G, 'pos')
    nx.draw_networkx_nodes(G, pos, nodelist=[0], node_color='#FFA726', node_size=80, node_shape='s')
    nx.draw_networkx_nodes(G, pos, nodelist=instance.nodes[1::], node_color='#BDBDBD', node_size=80)
    nx.draw_networkx_edges(G, pos,
                        edgelist=solution.get_edges(),
                        edge_color=['#3E2723' if solution.node_power[node] <= instance.max_cable_capacity else '#D50000' for node in instance.nodes[1::]],
                        width=[instance.get_cable_index_from_node_power(solution.node_power[node]) + 1 for node in instance.nodes[1::]])
    nx.draw_networkx_labels(G, pos, font_size=8)


def plot_instance(instance: Instance):
    G = nx.Graph()
    for node in instance.nodes: G.add_node(node, pos=instance.position[node])
    pos = nx.get_node_attributes(G, 'pos')
    nx.draw_networkx_nodes(G, pos, nodelist=[0], node_color='#FFA726', node_size=80, node_shape='s')
    nx.draw_networkx_nodes(G, pos, nodelist=instance.nodes[1::], node_color='#BDBDBD', node_size=80)
    nx.draw_networkx_labels(G, pos, font_size=8)
