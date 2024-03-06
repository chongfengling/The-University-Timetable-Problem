import pandas as pd
import numpy as np
import random
from collections import deque
from random import randrange
import networkx as nx
import itertools
import matplotlib.pyplot as plt

def create_data(uni_info, student, num_course = 4):
    # generate course list for students from compulsory and optional data
    res = pd.DataFrame(columns=[])
    for i in student.keys():
        all_course = uni_info[i]['Compulsory'] + uni_info[i]['Optional']
        df_tmp = pd.DataFrame(columns = all_course)
        for j in range(0, student[i]):
            optional_course = random.sample(uni_info[i]['Optional'], num_course - len(uni_info[i]['Compulsory']))
            single_choice = uni_info[i]['Compulsory'] + optional_course
            single_choice_index = [1 if c in single_choice else 0 for c in all_course]
            df_tmp.loc[len(df_tmp.index)] = single_choice_index
        res = res.append(df_tmp, ignore_index=True).fillna(0)
    return res

def build_constraints(df):
    # generate conflict matrix P, conflict exists if P_ij=1 
    columns = df.columns
    print(columns)
    graph = np.zeros((len(columns), len(columns)))
    for i in range(len(columns)-1):
        c1 = df.loc[:, columns[i]]

        for j in range(i+1, len(columns)):
            c2 = df.loc[:, columns[j]]
            c3 = c2.add(c1)
            if (2 in c3.values):
                graph[i][j] = 1
                graph[j][i] = 1
    return graph, dict(itertools.zip_longest([*range(0,len(columns))], columns))




def tabucol(graph, number_of_colors, tabu_size=7, reps=100, max_iterations=10000, debug=False, statistics=False):
    # graph is assumed to be the adjacency matrix of an undirected graph with no self-loops
    # nodes are represented with indices, [0, 1, ..., n-1]
    # colors are represented by numbers, [0, 1, ..., k-1]
    colors = list(range(number_of_colors))
    # number of iterations of the tabucol algorithm
    iterations = 0
    # initialize tabu as empty queue
    tabu = deque()
    
    # solution is a map of nodes to colors
    # Generate a random solution:
    solution = dict()
    for i in range(len(graph)):
        solution[i] = colors[randrange(0, len(colors))]

    # Aspiration level A(z), represented by a mapping: f(s) -> best f(s') seen so far
    aspiration_level = dict()

    while iterations < max_iterations:
        # Count node pairs (i,j) which are adjacent and have the same color.
        move_candidates = set()  # use a set to avoid duplicates
        conflict_count = 0
        for i in range(len(graph)):
            for j in range(i+1, len(graph)): 
                if graph[i][j] > 0:
                    if solution[i] == solution[j]:  # same color
                        move_candidates.add(i)
                        move_candidates.add(j)
                        conflict_count += 1
        move_candidates = list(move_candidates)  # convert to list for array indexing

        if conflict_count == 0:
            # Found a valid coloring.
            break

        # Generate neighbor solutions.
        new_solution = None
        for r in range(reps):
            # choose a conflicted node to move.
            node = move_candidates[randrange(0, len(move_candidates))]
            
            # Choose color other than current. 
            new_color = colors[randrange(0, len(colors) - 1)]
            if solution[node] == new_color: 
                # swapping last color with current color 
                new_color = colors[-1]

            # Create a neighbor solution
            new_solution = solution.copy()
            new_solution[node] = new_color
            # Count adjacent pairs with the same color in the new solution.
            new_conflicts = 0
            for i in range(len(graph)):
                for j in range(i+1, len(graph)):
                    if graph[i][j] > 0 and new_solution[i] == new_solution[j]:
                        new_conflicts += 1
            if new_conflicts < conflict_count:  # found an improved solution
                # if f(s') <= A(f(s)) [where A(z) defaults to z - 1]
                if new_conflicts <= aspiration_level.setdefault(conflict_count, conflict_count - 1):
                    # set A(f(s) = f(s') - 1
                    aspiration_level[conflict_count] = new_conflicts - 1
 
                    if (node, new_color) in tabu: # permit tabu move if it is better any prior
                        tabu.remove((node, new_color))
                        if debug:
                            print("tabu permitted;", conflict_count, "->", new_conflicts)
                        break
                else:
                    if (node, new_color) in tabu:
                        # tabu move isn't good enough
                        continue
                if debug:
                    print (conflict_count, "->", new_conflicts)
                break

        # At this point, either found a better solution,
        # or ran out of reps, using the last solution generated
        
        # The current node color will become tabu.
        # add to the end of the tabu queue
        tabu.append((node, solution[node]))
        if len(tabu) > tabu_size:  # queue full
            tabu.popleft()  # remove the oldest move

        # Move to next iteration of tabucol with new solution
        solution = new_solution
        iterations += 1
        if debug and iterations % 500 == 0:
            print("iteration:", iterations)

    # At this point, either conflict_count is 0 and a coloring was found,
    # or ran out of iterations with no valid coloring.
    if conflict_count != 0:
        print("No coloring found with {} colors.".format(number_of_colors))
        return None
    elif statistics:
        return iterations
    else:
        print("Found coloring:\n", solution, "in ", iterations, 'iterations')
        return solution

    
def test(graph, k, columns, draw=False):
    ls_graph = graph.astype(int).tolist()
    coloring = tabucol(ls_graph, k, debug=True)
    if draw:
        values = [coloring[node] for node in range(len(ls_graph))]
        nx_graph = nx.from_numpy_matrix(graph)
        # nx_graph.add_nodes_from(columns)
        nx.draw(nx_graph, node_color=values, pos=nx.shell_layout(nx_graph))
        nx.draw_networkx_labels(nx_graph, pos=nx.shell_layout(nx_graph), labels=columns)
        plt.show()

def statistics(graph, k, columns, draw=False, example=10000):
    ls_graph = graph.astype(int).tolist()
    num = 0
    for i in range(example):
        num += tabucol(ls_graph, k, debug=False, statistics=True)

    return num/example


if __name__ == '__main__':
    uni_info = {
        "AM_Y3S2":{"Compulsory": ["MTH301"], "Optional": ["MTH302", "MTH308", "PHY302", "MTH310", "MTH318"]}, 
        "FM_Y3S2":{"Compulsory": ["MTH301","MTH302", "ECO310"], "Optional": ["FIN302", "MTH316"]},
        "AS_Y3S2":{"Compulsory": ["MTH301", "MTH302", "MTH306"], "Optional": ["ECO310", "ECO304"]},

        "AM_Y2S2":{"Compulsory": ["MTH208", "MTH210"], "Optional": ["MTH209", "MTH224", "MTH203"]}, 
        "FM_Y2S2":{"Compulsory": ["MTH203", "FIN202", "CPT206"], "Optional": ["FIN206", "MTH208", "MTH222"]},
        "AS_Y2S2":{"Compulsory": ["MTH202", "MTH214", "MTH223"], "Optional": ["ECO216", "FIN206"]},

        "AM_Y1S2":{"Compulsory": ["MTH106", "MTH108", "MTH118", "MTH122"], "Optional": []}, 
        "FM_Y1S2":{"Compulsory": ["MTH116","MTH106", "ECO120", "FIN104"], "Optional": []},
        "AS_Y1S2":{"Compulsory": ["MTH120", "MTH116", "ECO120", "FIN104"], "Optional": []}
    }
    student = {
        "AM_Y3S2": 150,
        "FM_Y3S2": 200,
        "AS_Y3S2": 80,
        "AM_Y2S2": 300,
        "FM_Y2S2": 400,
        "AS_Y2S2": 100,
        "AM_Y1S2": 300,
        "FM_Y1S2": 400,
        "AS_Y1S2": 100
    }

    res = create_data(uni_info, student)
    graph,columns = build_constraints(res)
    color_num = 6 # available timeslots
    test(graph, color_num, columns, True)


    # for i in range(6,10): # statistic number of iterations
    #     print(statistics(graph, i, columns, True))
        