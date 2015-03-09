__author__ = 'Ivan Dortulov'

import copy

graph1 = {'A': {'name': 'A', 'visited': 0, 'neighbours': [['b_id', 'B', 'id', True]]},
          'B': {'name': 'B', 'visited': 0, 'neighbours': [['c_id', 'C', 'id', False]]},
          'C': {'name': 'C', 'visited': 0, 'neighbours': None}}

graph2 = {'A': {'name': 'A', 'visited': 0, 'neighbours': [['b_id', 'B', 'id', True]]},
          'B': {'name': 'B', 'visited': 0, 'neighbours': [['c_id', 'C', 'id', False], ['d_id', 'D', 'id', True]]},
          'C': {'name': 'C', 'visited': 0, 'neighbours': None},
          'D': {'name': 'D', 'visited': 0, 'neighbours': None}}

graph3 = {'A': {'name': 'A', 'visited': 0, 'neighbours': [['b_id', 'B', 'id', True]]},
          'B': {'name': 'B', 'visited': 0, 'neighbours': [['c_id', 'C', 'id', False], ['d_id', 'D', 'id', True]]},
          'C': {'name': 'C', 'visited': 0, 'neighbours': None},
          'D': {'name': 'D', 'visited': 0, 'neighbours': [['a_id', 'A', 'id', False]]}}


def traverse_graph(g):
    query = "SELECT * FROM A AS _A\n"
    return query + traverse_graph_helper(g, g['A'], '_A', ['A']) + ";"

def traverse_graph_helper(g, cur, prev, path):
    cur['visited'] += 1
    if cur['neighbours'] is None:
        return ""

    query = ""
    #print("cur:", cur['name'], ";prev", prev, ";path:", path)
    for edges in cur['neighbours']:
        path_copy = copy.copy(path)
        neighbour = g[edges[1]]

        # We already have visited this node, check if we are in a cycle
        if neighbour['visited'] > 0:
            #print("\tNeighbour ", edges[1], "already visited ", neighbour['visited'], " times!")
            if len(path) > 1:
                if path[0] == edges[1] or path[-1] == edges[1]:
                    #print("\t\tCycle!")
                    if neighbour['visited'] > 2:
                        return ""

        new = "".join(path) + "_" + edges[1]
        # If it is nullable
        if edges[3]:
            query += "LEFT JOIN " + edges[1] + " AS " + new + "\n"
            query += "   ON " + new + "." + edges[2] + " = " + prev + "." + edges[0] + "\n"
        else:
            query += "JOIN " + edges[1] + " AS " + new + "\n"
            query += "   ON " + new + "." + edges[2] + " = " + prev + "." + edges[0] + "\n"

        path_copy.append(edges[1])
        #print("\t", path_copy, new)
        query += traverse_graph_helper(g, neighbour, new, path_copy)

    return query

print(traverse_graph(graph3))