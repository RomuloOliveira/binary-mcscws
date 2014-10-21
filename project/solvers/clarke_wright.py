#!/bin/env python
# -*- coding: utf-8 -*-

import operator
from project.solvers.base_solution import BaseSolution
from project import models

class ClarkeWrightSolution(BaseSolution):
    pass

def can_add(data, node_list, current):
    """Returns true if a vehicle with demand `current` has capacity to serve `node_list`"""
    demand = sum([data['DEMAND'][i] for i in node_list])
    capacity = data['CAPACITY']

    if current + demand <= capacity:
        return True

    return False

def add_node(data, allocation, i, vehicle, vehicles_run, vehicles_demand, append=True):
    """Adds node `i` to vehicle `vehicle`

    Takes care of removing demand for one vehicle to another
    """
    demand = data['DEMAND'][i]

    #
    # Removes demand from old vehicle
    #
    if i in allocation:
        old_vehicle = allocation[i]

        vehicles_demand[old_vehicle] = vehicles_demand[old_vehicle] - demand
        vehicles_run[old_vehicle].remove(i)

    vehicles_demand[vehicle] = vehicles_demand[vehicle] + demand
    allocation[i] = vehicle

    if append: # append
        vehicles_run[vehicle].append(i)
    else: # prepend
        vehicles_run[vehicle].insert(0, i)

    return True

def is_interior(route, allocations, node):
    """Return True if `node` is interior, i.e., not adjascent to depot"""
    return (route[allocations[node]].index(node) != 0 and
            route[allocations[node]].index(node) != len(route[allocations[node]]) - 1)

def compute_savings_list(data):
    """Compute Clarke and Wright savings list

    A saving list is a matrix containing the saving amount S between i and j

    S is calculated by S = d(0,i) + d(0,j) - d(i,j) (CLARKE; WRIGHT, 1964)
    """

    savings_list = {}

    for i, j in data.edges():
        t = (i, j)

        if i == data.depot() or j == data.depot():
            continue

        savings_list[t] = data.distance(data.depot(), i) + data.distance(data.depot(), j) - data.distance(i, j)

    sorted_savings_list = sorted(savings_list.items(), key=operator.itemgetter(1), reverse=True)

    return [nodes for nodes, saving in sorted_savings_list]

def solve(data, vehicles):
    """Solves the CVRP problem using Clarke and Wright Savings methods"""
    nodes = list(data.nodes())

    savings_list = compute_savings_list(data)

    routes = [models.Route(data.capacity()) for _ in range(vehicles)]

    allocated = 0
    for i, j in savings_list:
        if allocated == len(nodes) - 1: # All nodes in a route
            break

        # Neither points are in a route
        if i.route_allocation() is None and j.route_allocation() is None:
            # Try to add the two nodes to a route
            for route in routes:
                if route.can_allocate([i, j]):
                    route.allocate([i, j])
                    allocated = allocated + 2
                    break
        # either i or j is allocated
        elif (i.route_allocation() is not None and j.route_allocation() is None) or (j.route_allocation() is not None and i.route_allocation() is None):
            inserted = None
            to_insert = None

            if i.route_allocation() is not None:
                inserted = i
                to_insert = j
            else:
                inserted = j
                to_insert = i

            route = inserted.route_allocation()

            # inserted not interior
            if not route.is_interior(inserted):
                if route.can_allocate([to_insert]):
                    append = False

                    if route.last(inserted):
                        append = True

                    route.allocate([to_insert], append)
                    allocated = allocated + 1

    return routes, savings_list
