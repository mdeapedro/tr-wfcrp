import random
from time import time

from best_sweep import best_sweep
from instance import Instance
from solution import Solution
from tools import prim, sweep


def cut_branch(solution: Solution, branch_root: int) -> list[tuple[int, int]]:
    edges: list[tuple[int, int]] = []
    def dfs(parent_node: int):
        for child_node in solution.children_node[parent_node]:
            edges.append((child_node, parent_node))
            dfs(child_node)
    dfs(branch_root)
    return edges


def generate_population(instance: Instance, pop_size: int) -> list[Solution]:
    sweep_list: list[list[tuple[int, int]]] = []
    # Add all sweeps
    for starting_turbine in instance.nodes[1::]:
        for clockwise in (False, True):
            for tpg in range(instance.n // instance.C, instance.max_cable_capacity + 1):
                edges = sweep(instance, starting_turbine, clockwise, tpg)
                edges.sort()
                if edges not in sweep_list:
                    sweep_list.append(edges)
    population = [Solution(instance, edges) for edges in sweep_list]
    population.sort(key=lambda solution: solution.cost())
    population = population[0:pop_size-2]
    # Add prim
    population.append(Solution(instance, prim(instance.nodes, instance.distance, 0)))
    # Add all-turbines-to-substation solution
    population.append(Solution(instance, Solution(instance, []).get_edges()))
    return population[0:pop_size]


def initialize_host_repository(instance: Instance, minimum_spanning_tree_branch_size: int) -> list[list[tuple[int, int]]]:
    host_repository_list: list[list[tuple[int, int]]] = []

    for node in instance.nodes:
        edges = prim(instance.nodes, instance.distance, node, minimum_spanning_tree_branch_size)
        edges.sort()
        if edges not in host_repository_list:
            host_repository_list.append(edges)

    best_sweep_solution = Solution(instance, best_sweep(instance))
    first_layer_nodes = best_sweep_solution.children_node[0]

    for node in first_layer_nodes:
        edges = cut_branch(best_sweep_solution, node)
        if edges not in host_repository_list:
            host_repository_list.append(edges)

    return host_repository_list


def single_branch_transposon(solution: Solution):
    first_layer_nodes = list(solution.children_node[0])

    best_solution_edges = solution.get_edges()
    best_cost = solution.cost()

    while len(first_layer_nodes) > 0:
        root_node = first_layer_nodes.pop()
        branch_nodes = solution.get_branch_nodes(root_node)
        for node_a in branch_nodes:
            for node_b in branch_nodes:
                if solution.is_node_in_branch(node_a, node_b): continue
                parent_node_a = solution.parent_node[node_a]
                solution.move(node_a, node_b)
                if solution.cost() < best_cost:
                    best_cost = solution.cost()
                    best_solution_edges = solution.get_edges()
                solution.move(node_a, parent_node_a)
    solution.build(best_solution_edges)


def between_branches_transposon(solution: Solution):
    first_layer_nodes = list(solution.children_node[0])

    best_solution_edges = solution.get_edges()
    best_cost = solution.cost()

    while len(first_layer_nodes) > 0:
        root_node = first_layer_nodes.pop()
        branch_nodes = solution.get_branch_nodes(root_node)
        for node_a in branch_nodes:
            for node_b in solution.instance.nodes:
                if solution.is_node_in_branch(root_node, node_b): continue
                solution.move(node_a, node_b, save_state=True)
                cost = solution.cost()
                if cost < best_cost:
                    best_cost = cost
                    best_solution_edges = solution.get_edges()
                solution.move_back()
    solution.build(best_solution_edges)


def move_to_better_trasposon(solution: Solution):
    best_move: tuple[int, int] | None = None
    best_cost = solution.cost()
    for node_a in solution.instance.nodes[1::]:
        for node_b in solution.instance.nodes:
            if not solution.is_node_in_branch(node_a, node_b):
                solution.move(node_a, node_b, save_state=True)
                if solution.cost() < best_cost:
                    best_move = (node_a, node_b)
                    best_cost = solution.cost()
                solution.move_back()
    if best_move is None:
        return False
    else:
        solution.move(best_move[0], best_move[1])
        return True


def plasmid(solution: Solution, edges: list[tuple[int, int]]):
    solution_edges = solution.get_edges()
    for node in solution.instance.nodes[1::]:
        solution.move(node, 0)
    for [node_a, node_b] in edges:
        solution.move(node_a, node_b)
    edges_set = set()
    for [node_a, node_b] in edges:
        edges_set.add(node_a)
        edges_set.add(node_b)
    for [node_a, node_b] in solution_edges:
        if not solution.is_node_in_branch(node_a, node_b) and node_a not in edges_set:
            solution.move(node_a, node_b)


def transgenetic(
    instance: Instance,
    pop_size: int,
    minimum_spanning_tree_branch_size: int,
    prob_plasmid: float,
    prob_sb_transposon: float,
    number_of_generations: int,
    seed: int=0
):
    random.seed(seed)

    population = generate_population(instance, pop_size)
    host_repository = initialize_host_repository(instance, minimum_spanning_tree_branch_size)
    overall_best_cost = min([solution.cost() for solution in population])
    count_number_of_generations = 0

    while count_number_of_generations < number_of_generations:
        for solution in population:
            cost = solution.cost()
            edges = solution.get_edges()
            prob = random.random()
            if prob < prob_plasmid:
                plasmid(solution, random.choice(host_repository))
            else:
                prob = random.random()
                if prob < prob_sb_transposon:
                    single_branch_transposon(solution)
                else:
                    between_branches_transposon(solution)
            new_cost = solution.cost()
            if cost < new_cost:
                solution.build(edges)

            if new_cost <= overall_best_cost:
                overall_best_cost = new_cost
                host_repository.append(cut_branch(solution, random.choice(list(solution.children_node[0]))))
        count_number_of_generations += 1

    for solution in population:
        while move_to_better_trasposon(solution):
            pass

    solution = population[0]
    for individual in population:
        if individual.cost() < solution.cost():
            solution = individual
    return solution


def transgenetic_debug(
    instance: Instance,
    pop_size: int,
    minimum_spanning_tree_branch_size: int,
    prob_plasmid: float,
    prob_sb_transposon: float,
    number_of_generations: int,
    seed: int=0
):
    print(f"Started Transgenetic Algorithm for instance {instance.name}.")
    print(f"Initializing seed '{seed}'...")
    random.seed(seed)
    print("seed initialized.")

    print(f"Generating initial population with size {pop_size}...")
    population = generate_population(instance, pop_size)
    print(f"Population initialized with size {len(population)}.")
    print(f"Maximum cost: {max([solution.cost() for solution in population])}.")
    print(f"Medium cost: {sum([solution.cost() for solution in population])/len(population):.0f}.")
    print(f"Minimum cost: {min([solution.cost() for solution in population])}.")
    overall_best_cost = min([solution.cost() for solution in population])
    print(f"Overall best cost: {overall_best_cost}.")
    print("Initializing host_repository...")
    host_repository = initialize_host_repository(instance, minimum_spanning_tree_branch_size)
    print(f"Host repository initialized with size {len(host_repository)}.")
    count_number_of_generations = 0
    print("Starting generations...")
    while count_number_of_generations < number_of_generations:
        print(f"Generation {count_number_of_generations + 1}:")
        _time = time()
        _count_plasmids = 0
        _count_sb_transp = 0
        _count_bb_transp = 0
        _updates = 0
        _count_obc = 0
        for solution in population:
            print(".",end="")
            cost = solution.cost()
            edges = solution.get_edges()
            prob = random.random()
            if prob < prob_plasmid:
                plasmid(solution, random.choice(host_repository))
                _count_plasmids += 1
            else:
                prob = random.random()
                if prob < prob_sb_transposon:
                    single_branch_transposon(solution)
                    _count_sb_transp += 1
                else:
                    between_branches_transposon(solution)
                    _count_bb_transp += 1
            new_cost = solution.cost()
            if cost < new_cost:
                solution.build(edges)
            elif new_cost < cost:
                _updates += 1

            if new_cost <= overall_best_cost:
                _count_obc += 1
                overall_best_cost = new_cost
                host_repository.append(cut_branch(solution, random.choice(list(solution.children_node[0]))))
        count_number_of_generations += 1
        print()
        print(
            f"    Execution Time: {time() - _time:.0f} seconds\n"
            f"    Plasmids runned: {_count_plasmids}\n"
            f"    SB Transp runeed: {_count_sb_transp}\n"
            f"    BB Transp runned: {_count_bb_transp}\n"
            f"    Number of updates: {_updates}\n"
            f"    Number of times new overall best cost was found: {_count_obc}\n"
            f"    New maximum cost: {max([solution.cost() for solution in population])}\n"
            f"    New medium cost: {sum([solution.cost() for solution in population])/len(population):.0f}\n"
            f"    New minimum cost: {min([solution.cost() for solution in population])}"
        )

    print("Generations finished.")
    print("Applying final optimization...")
    _time = time()
    for solution in population:
        while move_to_better_trasposon(solution):
            pass
    print(f"Final optimization applied. Took {time() - _time} seconds.")
    print(f"New maximum cost: {max([solution.cost() for solution in population])}.")
    print(f"New medium cost: {sum([solution.cost() for solution in population])/len(population):.0f}.")
    print(f"New minimum cost: {min([solution.cost() for solution in population])}.")
    print("Transgenetic Algorithm Finished.")

    return population
