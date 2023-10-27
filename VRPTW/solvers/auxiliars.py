# -*- coding: utf-8 -*-
"""
Created on Tue Jul 14 18:41:48 2020

@author: emarzal
"""
import copy
import itertools
import random
from VRPTW.structure import Problem, Route, Solution
from time import time
import logging
import duration_constants
from duration_constants import INCREMENT_DURATION
from duration_constants import METHOD, VARIABLE_DURATION
from duration_constants import DurationMethod

from ortools.linear_solver import pywraplp

class FeasibleInsertion:
    def __init__(self, node, position, route, ratio, service_time):
        self.node = node
        self.position = position
        self.route = route
        self.ratio = ratio
        self.service_time = service_time
        self.prob = 0


def two_opt(a, i, j):
    if i == 0:
        return a[j:i:-1] + [a[i]] + a[j + 1:]
    return a[:i] + a[j:i - 1:-1] + a[j + 1:]


def swap1(a, i, j):
    # print(a, b, i, j)
    a = a.copy()
    a[i], a[j] = a[j], a[i]
    return a


def move(a, b, i, j):
    # print(a, b, i, j)
    if len(a) == 0:
        return a, b
    while i >= len(a):
        i -= len(a)
    return a[:i] + a[i + 1:], b[:j] + [a[i]] + b[j:]


def replace(a, b, i, j):
    # print(a, b, i, j)
    if len(b) == 0:
        return a
    while j >= len(b):
        j -= len(b)
    return a[:i] + [b[j]] + a[i + 1:]


def swap2(a, b, i, j):
    # print(a, b, i, j)
    if i >= len(a) or j >= len(b):
        return a, b
    a, b = a.copy(), b.copy()
    a[i], b[j] = b[j], a[i]
    return a, b


def create_example(number, solution: Solution):
    if number == 1:  # swap1 y two_ops
        visit_order = [1, 3, 2, 5, 4]
        position_order = [1, 2, 2, 1, 5]
        route_order = [0, 0, 0, 1, 1]
        # for (visit_id, position, route_id) in zip(visit_order[0:], position_order[0:], route_order[0:]):
        #     route = solution._routes[route_id]
        #     visit = list(filter(lambda x: x.number == visit_id, solution.get_available_visits()))[0]
        #     route.add(visit, position)
        #     route.updateValuesAfterInsert(visit.shift, position, True)
        #     logging.debug(solution)
    if number == 2:  # swap2
        visit_order = [5, 3, 2, 4, 1]
        position_order = [1, 2, 3, 1, 2]
        route_order = [0, 0, 0, 1, 1]
        # for (visit_id, position, route_id) in zip(visit_order[0:], position_order[0:], route_order[0:]):
        #     route = solution._routes[route_id]
        #     visit = list(filter(lambda x: x.number == visit_id, solution.get_available_visits()))[0]
        #     route.add(visit, position)
        #     route.updateValuesAfterInsert(visit.shift, position, True)
        #     logging.debug(solution)
    if number == 3:  # move
        visit_order = [5, 2, 3, 4, 1]
        position_order = [1, 2, 3, 1, 2]
        route_order = [1, 1, 1, 0, 0]
        # for (visit_id, position, route_id) in zip(visit_order[0:], position_order[0:], route_order[0:]):
        #     route = solution._routes[route_id]
        #     visit = list(filter(lambda x: x.number == visit_id, solution.get_available_visits()))[0]
        #     route.add(visit, position)
        #     route.updateValuesAfterInsert(visit.shift, position, True)
        #     logging.debug(solution)
    if number == 4:  # replace
        visit_order = [1, 3, 4]
        position_order = [1, 2, 3]
        route_order = [0, 0, 0]
        # for (visit_id, position, route_id) in zip(visit_order[0:], position_order[0:], route_order[0:]):
        #     route = solution._routes[route_id]
        #     visit = list(filter(lambda x: x.number == visit_id, solution.get_available_visits()))[0]
        #     route.add(visit, position)
        #     route.updateValuesAfterInsert(visit.shift, position, True)
        #     logging.debug(solution)
    if number == 5:  # move limits
        visit_order = [3, 1, 2, 4, 5]
        position_order = [1, 2, 1, 2, 3]
        route_order = [0, 0, 1, 1, 1]
        # for (visit_id, position, route_id) in zip(visit_order[0:], position_order[0:], route_order[0:]):
        #     route = solution._routes[route_id]
        #     visit = list(filter(lambda x: x.number == visit_id, solution.get_available_visits()))[0]
        #     route.add(visit, position)
        #     route.updateValuesAfterInsert(visit.shift, position, True)
        #     logging.debug(solution)
    if number == 6:  # primera solución rc202
        visit_order = [94, 91, 36, 26, 23, 12, 11, 19, 22, 18, 86, 57, 83, 84, 34, 31, 50, 96, 56, 66, 54, 4, 60, 7, 3,
                       1, 2, 5, 70]
        position_order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
                          27, 28, 29]
        route_order = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    if number == 7:  # increase duration
        visit_order = [2, 4, 5, 1]
        position_order = [1, 2, 3, 4]
        route_order = [0, 0, 0, 0]

    for (visit_id, position, route_id) in zip(visit_order[0:], position_order[0:], route_order[0:]):
        route = solution._routes[route_id]
        visit = list(filter(lambda x: x.number == visit_id, solution.get_available_visits()))[0]
        if duration_constants.VARIABLE_DURATION:
            visit.service_time = 2
        route.add(visit, position)
        route.updateValuesAfterInsert(visit.shift, position, True)
        logging.debug(solution)
    return solution


def elapsed_time(initial_time, total_time=None):
    if not total_time:
        return time() - initial_time
    else:
        return total_time - initial_time


class IteratedLocalSearchV2:
    def __init__(self, problem: Problem, obj_func=None):
        # super().__init__(problem)
        self.problem: Problem = problem
        if not obj_func:
            obj_func = self.problem.obj_func
        self.obj_func = obj_func
        # Para local search
        self.noimpr = 0
        self.threshold1 = 10  # segun paper
        self.timelimit = 10  # 300  # En segundos
        # Para perturbation
        self.threshold2 = 20  # segun paper
        self.threshold3 = 3  # segun paper
        self.cons = 1
        self.post = 1
        self.primera_vez = True
        self.fast_construction = False
        self.initial_time = 0
        self.decrease_dv = False
        self.duration_optimize = False

    def updateFeasibleList(self, solution: Solution):  # ALGORITHM 2
        feasibleList = []
        # nodes = self.get_available_nodes(route)
        nodes = solution.get_available_visits()
        # print(nodes)
        for node in nodes:
            for route in solution._routes:
                positions = route.get_positions()
                # print("NUM_POSITIONS:", len(positions))
                for position in positions:
                    # logging.debug(f"CHECK {node} at position {position} of route {route._index}")
                    nodeI = route.get_visit(position - 1)
                    # print(f"Node i {nodeI}")
                    nodeK = route.get_visit(position)
                    # print(f"Node k {nodeK}")
                    # logging.debug(nodeI.distance(node))
                    node.arrive = nodeI.get_start_service_time() + nodeI.service_time + nodeI.distance(node)
                    # logging.debug(f"-- arrive {node.arrive}")
                    if node.set_wait():
                        # logging.debug(f"-- wait {node.wait}")
                        if duration_constants.VARIABLE_DURATION:
                            if duration_constants.METHOD == DurationMethod.Max:
                                node.service_time = node.place.service_time + duration_constants.INCREMENT_DURATION
                            if duration_constants.METHOD == DurationMethod.MaxShift:
                                # El valor debe estar entre el service_time del place y su incremento
                                # Si el valor del maxShift es mayor que service_time+incremento habrá gap
                                # Si el valor de maxShift es menor que service_time el nodo no será factible (se podía pasar al siguiente)
                                maxShift = nodeK.wait + nodeK.maxShift - nodeI.distance(
                                    node) - node.wait - node.distance(
                                    nodeK) + nodeI.distance(nodeK)
                                min_maxShift = min(maxShift, node.place.service_time + duration_constants.INCREMENT_DURATION)
                                node.service_time = max(node.place.service_time, min_maxShift)
                            if duration_constants.METHOD == DurationMethod.Random:
                                node.service_time = random.uniform(0, 1) * duration_constants.INCREMENT_DURATION + node.place.service_time

                        node.shift = nodeI.distance(node) + node.wait + node.service_time + node.distance(
                            nodeK) - nodeI.distance(nodeK)
                        # print(
                        #   f"-- shift = {node.shift} = {nodeI.distance(node)}+{node.wait}+{node.service_time}+{node.distance(nodeK)}-{nodeI.distance(nodeK)}")
                        # print(f"node {node} shift {node.shift}")
                        if route.feasibility(node.shift, position):
                            feasibleItem = FeasibleInsertion(node, position, route, node.get_ratio(), node.service_time)
                            feasibleList.append(feasibleItem)
                            # logging.debug("Node added")
                        # else:
                        #    logging.debug("Node not feasible (invalidates a subsequent node)")
                    # else:
                    #    logging.debug("Node not feasible (window already closed)")
        return sorted(feasibleList, key=lambda x: x.ratio, reverse=True)

    def updateFastFeasibleList(self, solution: Solution):  # ALGORITHM 2
        feasibleList = []
        # nodes = self.get_available_nodes(route)
        nodes = solution.get_available_visits_not_checked()
        # Lista de visitas ordenadas por ratio score/duración
        sorted_visit = sorted(nodes, key=lambda x: x.ratio_score, reverse=True)
        #logging.debug(f"Lista Visitas: {sorted_visit}")
        #node = sorted_visit[0]
        for node in sorted_visit:
            # Buscar la posición donde añadir la mejor visita (node es la mejor visita)
            # Si no cabe se pasa a la siguiente ruta, cuando se consigue colocar se termina
            for route in solution._routes:
                position = route.find_position(node)
                #logging.debug(f"CHECK {node} at position {position} of route {route._index}")
                nodeI = route.get_visit(position - 1)
                #logging.debug(f"Node i {repr(nodeI)}")
                nodeK = route.get_visit(position)
                # print(f"Node k {nodeK}")
                #logging.debug(f"Node k {repr(nodeK)}")
                # logging.debug(nodeI.distance(node))
                node.arrive = nodeI.get_start_service_time() + nodeI.service_time + nodeI.distance(node)
                #logging.debug(f"-- arrive {node.arrive}")
                if node.set_wait():
                    # logging.debug(f"-- wait {node.wait}")
                    if duration_constants.VARIABLE_DURATION:
                        if duration_constants.METHOD == DurationMethod.Max:
                            node.service_time = node.place.service_time + duration_constants.INCREMENT_DURATION
                        if duration_constants.METHOD == DurationMethod.MaxShift:
                            # El valor debe estar entre el service_time del place y su incremento
                            # Si el valor del maxShift es mayor que service_time+incremento habrá gap
                            # Si el valor de maxShift es menor que service_time el nodo no será factible (se podía pasar al siguiente)
                            maxShift = nodeK.wait + nodeK.maxShift - nodeI.distance(
                                node) - node.wait - node.distance(
                                nodeK) + nodeI.distance(nodeK)
                            min_maxShift = min(maxShift, node.place.service_time + duration_constants.INCREMENT_DURATION)
                            node.service_time = max(node.place.service_time, min_maxShift)
                        if duration_constants.METHOD == DurationMethod.Random:
                            node.service_time = random.uniform(0, 1) * duration_constants.INCREMENT_DURATION + node.place.service_time

                    node.shift = nodeI.distance(node) + node.wait + node.service_time + node.distance(
                        nodeK) - nodeI.distance(nodeK)
                    # print(
                    #   f"-- shift = {node.shift} = {nodeI.distance(node)}+{node.wait}+{node.service_time}+{node.distance(nodeK)}-{nodeI.distance(nodeK)}")
                    # print(f"node {node} shift {node.shift}")
                    if route.feasibility(node.shift, position):
                        feasibleItem = FeasibleInsertion(node, position, route, node.get_ratio(), node.service_time)
                        feasibleList.append(feasibleItem)
                        break
            # Añadir el elemento a una lista para no tenerlo en cuenta la proxima vez
            if len(feasibleList) > 0:
                break
            else:
                #logging.debug("Node added to checked")
                solution.add_checked_list(node.place.number)
                    # logging.debug("Node added")
                # else:
                #    logging.debug("Node not feasible (invalidates a subsequent node)")
        return feasibleList #sorted(feasibleList, key=lambda x: x.ratio, reverse=True)

    def selectBestFeasible(self, feasibleList):
        sumRatio = sum(a.ratio for a in feasibleList)
        for feasibleItem in feasibleList:
            feasibleItem.prob = feasibleItem.ratio / sumRatio
        U = random.uniform(0, 1)  # 0.5  # DEBUG-LAURA: random.uniform(0, 1)
        AccumProb = 0
        # logging.debug(f"U={U}, SELECT BEST:")
        # for item in feasibleList:
        #    logging.debug(
        #        f"{item.node}, route {item.route._index}, position {item.position}, ratio {item.ratio}, prob {item.prob}\n")
        for feasibleItem in feasibleList:
            AccumProb += feasibleItem.prob
            if U <= AccumProb:
                return feasibleItem

    # Se hace de esta forma porque en varios sitios del código se llama al método para construir la solución
    def construction(self, routes=[]):
        if self.fast_construction:
            best = self._fast_construction(routes)
        else:
            best = self._old_construction(routes)
        return best

    def _old_construction(self, routes=[]):
        logging.debug("Under construction:")
        solution = Solution(self.problem, routes)
        logging.debug(solution)
        # if self.primera_vez:
        #     self.primera_vez = False
        #     print(solution)
        #     return create_example(7, solution)

        feasibleList = self.updateFeasibleList(solution)
        while len(feasibleList) > 0:
            # for item in feasibleList:
            #    print(f"node {item.node}, position {item.position}, ratio {item.ratio}\n")
            bestNode = self.selectBestFeasible(feasibleList)
            # logging.debug(f"BESTNODE {bestNode.node}, route {bestNode.route._index}, position {bestNode.position}, ratio {bestNode.ratio}\n")
            if duration_constants.VARIABLE_DURATION:
                bestNode.node.service_time = bestNode.service_time
            route = solution._routes[bestNode.route._index]
            route.add(bestNode.node, bestNode.position)
            # print(solution)
            route.updateValuesAfterInsert(bestNode.node.shift, bestNode.position, True)
            # print(solution)
            feasibleList = self.updateFeasibleList(solution)
        logging.debug("After construction:")
        logging.debug(solution)
        solution.total_time = time()
        return solution


    def _fast_construction(self, routes=[]):
        logging.debug("Under fast construction:")
        solution = Solution(self.problem, routes)
        solution.init_checked_list()
        logging.debug(solution)
        # if self.primera_vez:
        #     self.primera_vez = False
        #     print(solution)
        #     return create_example(7, solution)

        feasibleList = self.updateFastFeasibleList(solution)
        while len(feasibleList) > 0:
            # for item in feasibleList:
            #    print(f"node {item.node}, position {item.position}, ratio {item.ratio}\n")
            bestNode = feasibleList[0]  # El primer elemento de la lista es el mejor
            # logging.debug(f"BESTNODE {bestNode.node}, route {bestNode.route._index}, position {bestNode.position}, ratio {bestNode.ratio}\n")
            if duration_constants.VARIABLE_DURATION:
                bestNode.node.service_time = bestNode.service_time
            route = solution._routes[bestNode.route._index]
            route.add(bestNode.node, bestNode.position)
            # print(solution)
            route.updateValuesAfterInsert(bestNode.node.shift, bestNode.position, True)
            # print(solution)
            feasibleList = self.updateFastFeasibleList(solution)
        logging.debug("After fast construction:")
        logging.debug(solution)
        solution.total_time = time()
        solution.delete_checked_list()
        return solution

    def perturbation(self, solution):
        if self.noimpr > self.threshold2 and (self.noimpr + 1) % self.threshold3 == 0:
            solution = self.exchangeRoute(solution)
        else:
            solution = self.shake(solution)
        return solution

    def exchangeRoute(self, solution):
        p1 = int(random.uniform(0, solution.day_number))
        p2 = int(random.uniform(0, solution.day_number))
        if p1 == p2:
            p2 += 1
            if p2 > solution.day_number - 1:
                p2 = 0
        solution._routes[p1]._visits, solution._routes[p2]._visits = \
            solution._routes[p2]._visits, solution._routes[p1]._visits
        logging.debug("Solution after exchangeRoute:\r\n")
        logging.debug(solution)
        return solution

    def shake(self, solution):
        logging.debug("Shake with post=" + str(self.post) + "and cons=" + str(self.cons))
        for route_0 in solution._routes:
            # No hace falta hacer copia
            # route_0 = Route(route.problem, route._visits)
            logging.debug("Ruta inicial:")
            logging.debug(route_0)
            # Check whether the nodes to remove are consecutive or not
            # Recall that the first and the last nodes cannot be removed (so there is always self.post-1 or j-1)
            if len(route_0._visits) == 2:  # Route is empty
                continue
            if self.post >= len(route_0._visits) - 1:
                self.post = 1
            if self.post + self.cons < len(route_0._visits):  # Nodes to remove are consecutive
                logging.debug("Consecutive nodes")
                for i in range(self.cons):
                    logging.debug("Nodo eliminado:" + str(route_0._visits[self.post]))
                    route_0.remove(self.post)
                    if len(route_0._visits) == 2:
                        break
                index_first_after = self.post
                index_first_before = self.post - 1
                self.updatePosteriorNodes(route_0, index_first_before, index_first_after)
            else:  # Nodes to remove are not consecutive
                logging.debug("No consecutive nodes")
                j = self.post
                for i in range(self.cons):
                    logging.debug("Nodo eliminado:" + str(route_0._visits[j]))
                    route_0.remove(j)
                    if j == len(route_0._visits) - 1:
                        index_first_after = j  # self.post
                        index_first_before = j - 1  # self.post - 1
                        self.updatePosteriorNodes(route_0, index_first_before, index_first_after)
                        j = 1
                    if len(route_0._visits) == 2:
                        break
                # update nodes from beginning to first removed node
                self.updatePosteriorNodes(route_0, 0, 1)
                # update last node
                self.updatePosteriorNodes(route_0, len(route_0._visits) - 2, len(route_0._visits) - 1)
            logging.debug("Nueva ruta:")
            logging.debug(route_0)

        # Update post and cons
        self.post += self.cons
        if self.primera_vez:
            self.primera_vez = False
        else:
            self.cons += 1
            self.primera_vez = True
        # smallest = min(len(x._visits) for x in solution._routes if len(x._visits)>2) - 2 do not take into account empty routes
        smallest = min(len(x._visits) for x in solution._routes) - 2
        if self.post > smallest:
            if smallest == 0:
                self.post = 1
            else:
                self.post -= smallest
        if self.cons > max(len(x._visits) for x in solution._routes):
            self.cons = 1

        # Add nodes until possible --> function construction but starting with a given route
        solution = self.construction(solution._routes)

        return solution

    def updatePosteriorNodes(self, route_0, index_first_before, index_first_after):
        # Modify arrive, wait, maxshift of nodes after the removed nodes
        first_after = route_0._visits[index_first_after]
        first_before = route_0._visits[index_first_before]
        # print(first_before)
        # print(first_after)
        shift = first_after.arrive - (first_before.arrive + first_before.wait + first_before.service_time) \
                - first_after.distance(first_before)
        first_before.shift = shift
        # print("Intervalo:", shift)

        for i in range(index_first_after, len(route_0._visits)):
            n = route_0._visits[i]
            n.updateValuesAfterRemove(route_0._visits[i - 1].shift)
            # print(i,"--",n)

        # Modify max_shift of nodes before the removed nodes
        for i in range(index_first_before, 0, -1):
            n = route_0._visits[i]
            n.setMaxShift(route_0._visits[i + 1])
            # print(n)

        # print(route_0)

    # Método con la estructura del Algoritmo 4
    def execute(self):
        self.initial_time = time()
        routes = []
        # Construcción inicial
        best = self.construction(routes)
        logging.debug("\r\nINITIAL SOLUTION:\r\n")
        logging.debug(best)
        logging.debug("Total distance" + str(self.obj_func(best._routes)))
        logging.debug("Time:" + str(elapsed_time(self.initial_time)))
        #best.total_time = elapsed_time(self.initial_time, best.total_time)
        # Devuelve la solución inicial
        #return best

        # Llamada a local searh
        best = self.local_search(best)
        logging.debug("Local search solution:")
        logging.debug(self.problem.print_canonical(best._routes))
        logging.debug(best)
        logging.debug("Total distance")
        logging.debug(self.obj_func(best._routes))
        logging.debug("Time:" + str(elapsed_time(self.initial_time)))
        new_solution = copy.deepcopy(
            best)  # Se copia para que los cambios de la perturbación no afecten a la mejor solución
        # num_iter = 0
        while elapsed_time(self.initial_time) <= self.timelimit:
            # num_iter += 1
            logging.debug("Elapsed time : " + str(elapsed_time(self.initial_time)))
            input_solution = copy.deepcopy(new_solution)
            new_solution = self.perturbation(new_solution)
            if not input_solution == new_solution:
                new_solution = self.local_search(new_solution)
            logging.debug("Time:" + str(elapsed_time(self.initial_time)))
            if self.obj_func(new_solution._routes) < self.obj_func(best._routes):
                best = copy.deepcopy(
                    new_solution)  # Se copia para que los cambios de la perturbación no afecten a la mejor solución
                self.noimpr = 0
                logging.debug("ILS step")
                logging.debug(self.problem.print_canonical(best._routes))
                logging.debug("Total distance" + str(self.obj_func(best._routes)))
            else:
                self.noimpr += 1
            if (self.noimpr + 1) % self.threshold1 == 0:
                new_solution = copy.deepcopy(
                    best)  # Se copia para que los cambios de la perturbación no afecten a la mejor solución
        best.total_time = elapsed_time(self.initial_time, best.total_time)
        # print("Num iterations:", num_iter)
        return best

    def local_search(self, solution: Solution) -> Solution:
        logging.debug("Entrando en local search...")
        any_change = False
        new_solution = solution
        any_change, new_solution = self.change_one_route(new_solution, swap1)
        logging.debug("After swap1 - Time:" + str(elapsed_time(self.initial_time)))
        logging.debug(new_solution)
        # logging.debug("Distance" + str(self.obj_func(new_solution._routes)))
        any_change, new_solution = self.change_two_routes(new_solution, swap2)
        logging.debug("After swap2 - Time:" + str(elapsed_time(self.initial_time)))
        logging.debug(new_solution)
        # logging.debug("Distance" + str(self.obj_func(new_solution._routes)))
        any_change, new_solution = self.change_one_route(new_solution, two_opt)
        logging.debug("After two_opt - Time:" + str(elapsed_time(self.initial_time)))
        logging.debug(new_solution)
        # logging.debug("Distance" + str(self.obj_func(new_solution._routes)))
        any_change, new_solution = self.change_two_routes(new_solution, move)
        logging.debug("After move - Time:" + str(elapsed_time(self.initial_time)))
        logging.debug(new_solution)
        # logging.debug("Distance" + str(self.obj_func(new_solution._routes)))
        if duration_constants.VARIABLE_DURATION:
            if self.duration_optimize:
                new_solution = self.increase_duration_optimize(new_solution)
                logging.debug("After increase duration optimize - Time:" + str(elapsed_time(self.initial_time)))
            else:
                if self.decrease_dv:
                    new_solution = self.decrease_duration_less_score(new_solution)
                    logging.debug("After decrease duration - Time:" + str(elapsed_time(self.initial_time)))
                new_solution = self.increase_duration_max_shift(new_solution)
                logging.debug("After increase duration - Time:" + str(elapsed_time(self.initial_time)))
            logging.debug(new_solution)
        if any_change:
            new_solution = self.construction(new_solution._routes)
            logging.debug("After insert - Time:" + str(elapsed_time(self.initial_time)))
            logging.debug(new_solution)
            # logging.debug("Distance" + str(self.obj_func(new_solution._routes)))
        else:
            logging.debug("No insert because no change - Time:" + str(elapsed_time(self.initial_time)))
        new_solution = self.replace_one_route(new_solution)
        logging.debug("After replace - Time:" + str(elapsed_time(self.initial_time)))
        logging.debug(new_solution)
        # logging.debug("Distance" + str(self.obj_func(new_solution._routes)))
        return new_solution

    def change_one_route(self, solution: Solution, change_func) -> Solution:
        any_change = False
        new_solution = solution
        # logging.debug("Time 1:" + str(elapsed_time(self.initial_time)))
        for i in range(len(new_solution._routes)):  # Hay una lista de rutas
            is_stucked = False
            # logging.debug("Time 2:" + str(elapsed_time(self.initial_time)))
            while not is_stucked:
                route = new_solution.get_route(i)
                best_distance = route.total_distance
                is_stucked = True
                # logging.debug("Time 3:" + str(elapsed_time(self.initial_time)))
                for k, j in itertools.combinations(range(len(route.visits)), 2):
                    # k = 1
                    # j = 3
                    # if k == 3 and j == 14:
                    #     logging.debug(new_solution)
                    # logging.debug("Time 4:" + str(elapsed_time(self.initial_time)))
                    reordered_list: list = [route._visits[0], *change_func(route.visits, k, j), route._visits[-1]]
                    new_route = Route(self.problem, reordered_list, route._index)
                    # logging.debug("Time 5:" + str(elapsed_time(self.initial_time)))
                    # Se suma +1 porque se añade el depot al principio
                    if new_route.updateValuesCheckingFeasibilityOneRoute(k + 1, j + 1,
                                                                         change_func == two_opt):  # is_feasible:
                        # new_solution.set_route(i, new_route)
                        # return new_solution
                        # logging.debug("Time 6:" + str(elapsed_time(self.initial_time)))
                        if new_route.total_distance < best_distance:
                            new_solution.set_route(i, new_route)
                            new_solution.total_time = time()
                            best_distance = new_route.total_distance
                            any_change = True
                            # if not new_solution.check_feasible:
                            #     logging.debug(new_solution)
                            is_stucked = False
                            # logging.debug("Time 7:" + str(elapsed_time(self.initial_time)))
        # logging.debug("Time 8:" + str(elapsed_time(self.initial_time)))
        return any_change, new_solution

    def change_two_routes(self, solution: Solution, change_func) -> Solution:
        best = solution
        any_change = False
        is_stucked = False
        while not is_stucked:
            is_stucked = True
            # Para todos los pares de rutas posibles
            for i, j in itertools.combinations(range(len(best._routes)), 2):
                # Para todos los índices posibles en las dos rutas
                if change_func == move and len(best.get_route(i).visits) == 0:
                    continue
                if change_func == swap2 and (len(best.get_route(i).visits) == 0 or len(best.get_route(j).visits)) == 0:
                    continue
                for k, l in itertools.product(range(len(best.get_route(i).visits)),
                                              range(len(best.get_route(j).visits))):
                    # print(change_func, i, j, k, l)
                    if k >= len(best.get_route(i).visits) or l >= len(best.get_route(j).visits):
                        continue
                    c1, c2 = change_func(best.get_route(i).visits, best.get_route(j).visits, k, l)
                    r1, r2 = Route(self.problem, [best.get_route(i).get_visit(0), *c1, best.get_route(i).get_visit(-1)],
                                   best.get_route(i)._index), Route(self.problem, [best.get_route(j).get_visit(0), *c2,
                                                                                   best.get_route(i).get_visit(-1)],
                                                                    best.get_route(j)._index)
                    if r1.updateValuesCheckingFeasibilityTwoRoutes(r2, k + 1, l + 1,
                                                                   change_func == move):  # r1.is_feasible and r2.is_feasible:
                        if r1.total_distance + r2.total_distance < best.get_route(i).total_distance + \
                                best.get_route(j).total_distance:
                            best.set_route(i, r1)
                            best.set_route(j, r2)
                            best.total_time = time()
                            any_change = True
                            # return best
                            is_stucked = False
            # best = list(filter(lambda x: len(x.visits) != 0, best))
        return any_change, best

    def replace_one_route(self, solution: Solution) -> Solution:
        new_solution = solution
        unscheduled_visits = new_solution.get_available_visits()
        # Si no hay visitas sin planificar no hacemos nada
        if len(unscheduled_visits) == 0:
            return new_solution
        for i in range(len(new_solution._routes)):  # Hay una lista de rutas
            is_stucked = False
            while not is_stucked:
                unscheduled_visits = new_solution.get_available_visits()
                route = new_solution.get_route(i)
                best_score = route.total_score
                is_stucked = True
                for k, j in itertools.product(range(len(route.visits)), range(len(unscheduled_visits))):
                    # k = 1
                    # j = 0
                    reordered_list: list = [route._visits[0], *replace(route.visits, unscheduled_visits, k, j),
                                            route._visits[-1]]
                    new_route = Route(self.problem, reordered_list, route._index)
                    # Se suma +1 porque se añade el depot al principio
                    if new_route.updateValuesCheckingFeasibilityReplace(k + 1):
                        # new_solution.set_route(i, new_route)
                        # return new_solution
                        if new_route.total_score > best_score:
                            new_solution.set_route(i, new_route)
                            new_solution.total_time = time()
                            best_score = new_route.total_score
                            is_stucked = False
        return new_solution

    def increase_duration_max_shift(self, solution: Solution) -> Solution:
        new_solution = solution
        # Para cada ruta
        for i in range(len(new_solution._routes)):  # Hay una lista de rutas
            route = new_solution.get_route(i)
            scalable_visits = route.get_scalable_visits()
            num_scalable = 0
            #while route.existsPositiveMaxShift():
            while len(scalable_visits) > 0 and len(scalable_visits) != num_scalable:
                num_scalable = len(scalable_visits)
                logging.debug("Hay visitas ampliables: " + str(num_scalable))
                # aumentar la duración para la visita que más incremente el score
                route.updateBestScore(scalable_visits)
                scalable_visits = route.get_scalable_visits()
                # repetir mientras se pueda incrementar el score
                # en cada iteración una visita debe mejorar
                # si entre dos iteraciones, ninguna visita mejora, se para
        return new_solution

    def decrease_duration_less_score(self, solution: Solution) -> Solution:
        new_solution = solution
        # Para cada ruta
        for i in range(len(new_solution._routes)):  # Hay una lista de rutas
            route = new_solution.get_route(i)
            decrease_visits = route.get_less_score_visits()
            if len(decrease_visits) > 0:
                logging.debug("Hay visitas decrementables " )
                # reducir la duración de la visita que menos score consigue
                route.updateWorstScore(decrease_visits)
                # solo se quita una visita por cada ruta
        return new_solution

    def increase_duration_optimize(self, solution: Solution) -> Solution:
        #print(solution)
        new_solution = solution
        # Para cada ruta, resolver un problema de LP
        for i in range(len(new_solution._routes)):  # Hay una lista de rutas
            route = new_solution.get_route(i)
            scalable_visits = route.get_scalable_visits()
            if len(scalable_visits) == 0:
                #print("No hay visitas a incrementar")
                return solution

            # solver = pywraplp.Solver.CreateSolver('SAT_INTEGER_PROGRAMMING')
            solver = pywraplp.Solver.CreateSolver('GLOP')
            if not solver:
                return
            # Crear problema para route
            visits = route.all_visits
            num_visits = len(visits)
            start = {}
            arrive = {}
            wait = {}
            duration = {}
            for i in range(num_visits):
                arrive[i] = solver.NumVar(0, visits[0].place.close, 'a'+str(i)) #todo el intervalo del problema
                wait[i] = solver.NumVar(0, visits[0].place.close, 'w'+str(i))
                start[i] = solver.NumVar(visits[i].place.open, visits[i].place.close, 's'+str(i))
                duration[i] = solver.NumVar(visits[i].service_time, visits[i].max_duration, 'd'+str(i))
            #print("Number of variables:", solver.NumVariables())
            for i in range(num_visits-1):
                solver.Add(arrive[i] + wait[i] == start[i])
                solver.Add(start[i] + duration[i] + visits[i].place.distance(visits[i+1].place) == arrive[i+1] )
            #print("Number of constraints:", solver.NumConstraints())
            solver.Maximize(solver.Sum([duration[i]*visits[i].place.score for i in range(num_visits)]))  #score constante

            status = solver.Solve()

            # Update solution
            if status == pywraplp.Solver.FEASIBLE or status == pywraplp.Solver.OPTIMAL:
                #print("Solution:")
                #print("Objective function=", solver.Objective().Value())
                for j in range(num_visits-1, -1, -1): #we start from the end to update maxshift
                    #print(j)
                    #print('Arrive ' + str(visits[j].number) + ':', arrive[j].solution_value())
                    #print('Wait ' + str(visits[j].number) + ':', wait[j].solution_value())
                    #print('Start ' + str(visits[j].number) + ':', start[j].solution_value())
                    #print('Duration ' + str(visits[j].number) + ':', duration[j].solution_value())

                    if j==num_visits-1:
                        visits[j].updateValuesAfterOptimization(arrive[j].solution_value(), wait[j].solution_value(),
                                                                duration[j].solution_value(), None)
                    else:
                        visits[j].updateValuesAfterOptimization(arrive[j].solution_value(), wait[j].solution_value(),
                                                                duration[j].solution_value(), visits[j+1])
                #print(new_solution) #si imprimo solution, también sale modificado!!
            #else:
                #print("No solution")

            #sys.exit(0)

        return new_solution