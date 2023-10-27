import logging
import math
import copy

# import logging
# from time import time

# Para pruebas
# dist = [[0, 3, 6, 6, 3],
#         [3, 0, 4, 5, 3],
#         [6, 4, 0, 3, 5],
#         [6, 5, 3, 0, 4],
#         [3, 3, 5, 4, 0]]

dist = [[0, 3, 2, 6, 4, 2],
        [3, 0, 2, 5, 4, 2],
        [2, 2, 0, 3, 1, 4],
        [6, 5, 3, 0, 3, 4],
        [4, 4, 1, 3, 0, 1],
        [2, 2, 4, 4, 1, 0]]

import constants
from constants import MaximizeMethod
import duration_constants
from duration_constants import INCREMENT_DURATION
from duration_constants import VARIABLE_DURATION


class Place:
    def __init__(self, number, x, y, score, open_time, close_time, service_time):
        self.number = number
        self.x = x
        self.y = y
        self.score = score
        self.open = open_time
        self.close = close_time
        self.service_time = service_time

    def __eq__(self, place):
        return self.number == place.number

    def __repr__(self):
        return f"P_{self.number}"

    def distance(self, target):
        return math.sqrt(math.pow(self.x - target.x, 2) + math.pow(target.y - self.y, 2))
        #return dist[self.number][target.number]


class Visit:
    def __init__(self, place):
        self.place = place
        self.wait = 0
        self.arrive = 0
        self.shift = 0
        self.maxShift = place.close
        self._service_time = place.service_time
        self._score = place.score

    def __eq__(self, visit):
        return self.place.number == visit.place.number

    def __repr__(self):
        return f"V_{self.number}"

    def __str__(self):
        return f"Node {self.place.number}, arrive {self.arrive}, wait {self.wait}, service_time {self._service_time}, shift {self.shift}, maxshift {self.maxShift}"

    def get_start_service_time(self):
        return max([self.place.open, self.arrive])

    def get_end_service_time(self):
        return self.get_start_service_time() + self.service_time

    def set_wait(self):  # time to wait until the window is open, if it's already closed returns False
        if self.close < self.arrive:
            return False
        self.wait = max([0, self.open - self.arrive])
        return True

    def get_ratio(self):
        if (self.shift == 0):
            return math.pow(self.score, 2)
        else:
            return math.pow(self.score, 2) / self.shift  # compute the correct denominator

    def updateValuesAfterInsert(self, shift):  # retrasa una visita (comienza más tarde)
        self.arrive = self.arrive + shift
        self.shift = max([0, shift - self.wait])
        self.wait = max([0, self.wait - shift])
        self.maxShift = self.maxShift - self.shift

    def updateValuesBringingForward(self, shift):  # adelanta una visita (comienza más pronto)
        self.arrive = self.arrive - shift
        self.set_wait()
        self.shift = max([0, shift - self.wait])
        self.maxShift = self.maxShift + self.shift

    def updateValuesAfterRemove(self, shift):
        old_start = self.arrive + self.wait
        self.arrive = self.arrive - shift
        self.set_wait()
        new_start = self.arrive + self.wait
        self.shift = max([0, (old_start - new_start)])  # max([0, shift-self.wait])
        self.maxShift = self.maxShift + self.shift

    def removeFromRoute(self):
        self.place.is_serviced = False
        self.arrive = 0
        self.wait = 0
        self.shift = 0
        self.maxShift = self.place.close

    def updateValuesAfterOptimization(self, arrive, wait, service_time, post):
        self.arrive = arrive
        if post is None:
            self.setMaxShiftLast()
        else:
            self.wait = wait
            self._service_time = service_time
            self.setMaxShift(post)
        #shift no hace falta

    def setMaxShift(self, post):
        self.maxShift = min([self.place.close - self.get_start_service_time(), post.wait + post.maxShift])

    def setMaxShiftLast(self):
        self.maxShift = (self.place.close - self.get_start_service_time())

    def distance(self, target):
        return self.place.distance(target.place)

    def get_gap_visits(self, before, after):
        # Un hueco será la suma de la distancia entre la visita anterior y la visita self, más el tiempo de espera de self,
        # más el tiempo de servicio de self, más la distancia entre la visita self y la visita posterior
        # Se actualiza cuando llega la visita para poder calcular el tiempo de espera
        self.arrive = before.get_end_service_time() + before.distance(self)
        if self.set_wait():
            antes = before.distance(self)
            despues = self.distance(after)
            return True, before.distance(self) + self.wait + self.service_time + self.distance(after)
        else:
            return False, 0

    def feasibility(self, shift):
        return shift <= (self.wait + self.maxShift)

    @property
    def number(self):
        return self.place.number

    @property
    def x(self):
        return self.place.x

    @property
    def y(self):
        return self.place.y

    @property
    def score(self):
        if duration_constants.VARIABLE_DURATION or constants.MAXIMISATION_METHOD == MaximizeMethod.DurationScore:
            return self.place.score * self._service_time
        else:
            return self.place.score

    @property
    def open(self):
        return self.place.open

    @property
    def close(self):
        return self.place.close

    @property
    def service_time(self):
        return self._service_time

    @service_time.setter
    def service_time(self, value):
        # print("Setting value...")
        if not (self.place.service_time <= value <= self.place.service_time + duration_constants.INCREMENT_DURATION):
            raise ValueError("This service_time is not possible")
        self._service_time = value

    @property
    def max_duration(self):
        return self.place.service_time + duration_constants.INCREMENT_DURATION

    @property
    def best_score_service(self):
        return (min(self.max_duration - self.service_time, self.maxShift)) * self.place.score

    @property
    def less_score_service(self):
        return (self.service_time - self.place.service_time) * self.place.score

    @property
    def ratio_score(self):
        # En este caso se está teniendo en cuenta la duración mínima
        # return self.place.score / self.place.service_time
        # Se podría hacer el mismo ratio con max_duration (pero solo para VARIABLE_DURATION
        # Igual que se hace en el método get_ratio donde se hace score^2/shift, se toma la misma semántica
        return math.pow(self.place.score, 2) / self.place.service_time


class Problem:
    def __init__(self, name, places: list, day_number, day_capacity):
        self.name = name
        self.places = places
        self.day_number = day_number
        self.day_capacity = day_capacity
        self.depot: Place = list(filter(lambda x: x.number == 0, places))[0]
        self.depot.is_serviced = True

    def __repr__(self):
        return f"Instance: {self.name}\n" \
               f"Day number: {self.day_number}\n" \
               f"Day capacity: {self.day_capacity}\n"

    def obj_func(self, routes):
        return sum(map(lambda x: x.total_distance, routes))

    def print_canonical(self, routes):
        return "\n".join(list(map(lambda x: x.canonical_view, routes)))

    def total_score(self, routes):
        return -1 * sum(map(lambda x: x.total_score, routes))


class Route:
    def __init__(self, problem: Problem, visits: list, index: int):
        self.problem: Problem = problem
        # number, x, y, score, open, close, service_time
        if len(visits) > 2:
            l2 = copy.deepcopy(visits[1:-1])
            last = copy.deepcopy(visits[-1])
        else:
            l2 = []
            last = Visit(self.problem.depot)
        self._visits: list = [Visit(self.problem.depot), *l2, last]
        self._index: int = index

    def __repr__(self):
        return " ".join(str(visit.number) for visit in self._visits)

    def __str__(self):
        s = "Route " + str(self._index) + '\r\n'
        return s + "".join(str(visit) + '\r\n' for visit in self._visits)

    def __eq__(self, route):
        if not len(self._visits) == len(route._visits):
            return False
        if not self.total_score == route.total_score:
            return False
        for i in range(len(self._visits)):
            if not self._visits[i] == route._visits[i]:
                return False
        return True

    @property
    def canonical_view(self):
        time = 0
        result = [0, 0.0, 0.0, 0.0, 0.0]
        for source, target in zip(self._visits, self._visits[1:]):
            start_time = max([target.open, time + source.distance(target)])
            time = start_time + target.service_time
            result.append(target.number)
            result.append(source.distance(target))
            result.append(start_time)
            result.append(target.wait)
            result.append(target.service_time)
        return " ".join(str(x) for x in result)

    @property
    def visits(self):
        return self._visits[1:-1]

    @property
    def all_visits(self):
        return self._visits

    @property
    def total_distance(self):
        return sum(a.distance(b) for (a, b) in zip(self._visits, self._visits[1:]))

    @property
    def total_score(self):
        return sum(visit.score for visit in self._visits)

    @property
    def edges(self):
        return list(zip(self._visits, self._visits[1:]))

    @property
    def is_feasible(self):
        time = 0
        capacity = self.problem.day_capacity
        is_feasible = True
        for source, target in zip(self._visits, self._visits[1:]):
            start_service_time = max([target.open, time + source.distance(target)])
            if start_service_time >= target.close:
                is_feasible = False
            time = start_service_time + target.service_time
            capacity -= target.score
        if time >= self.problem.depot.close or capacity < 0:
            is_feasible = False
        return is_feasible

    @property
    def check_feasible(self):
        time = 0
        for source, target in zip(self._visits, self._visits[1:]):
            start_service_time = max([target.open, time + source.distance(target)])
            if start_service_time >= target.close:
                return False
            redondear_start_time = round(start_service_time, 5)
            redondear_target_start_time = round(target.get_start_service_time(), 5)
            if not redondear_start_time == redondear_target_start_time:
                return False
            time = start_service_time + target.service_time
        return True


    def find_position(self, new_visit: Visit):
        pos = 0
        #logging.debug(f"Buscando posicion para {repr(new_visit)}")
        for source, target in zip(self._visits, self._visits[1:]):
            #logging.debug(f"Pareja {repr(source)} y {repr(target)}")
            pos += 1
            if source.get_end_service_time()<new_visit.open and target.get_end_service_time()>new_visit.open:
                # La apertura de la visita nueva es anterior al comienzo de la visita target
                if target.get_start_service_time()>new_visit.open:
                    break
                # Se comprueba si la visita nueva puede empezar después (su cierre es anterior a su posible comienzo)
                elif new_visit.close>(target.get_start_service_time()+target.distance(new_visit)):
                    pos += 1
                    break
        if pos >= len(self._visits):
            pos -= 1
        #logging.debug(f"Posicion {pos}")
        return pos

    def feasibility(self, shift, position):
        node = self._visits[position]
        # print("Node ", node.number, "-wait:", node.wait, "-maxshift:", node.maxShift)
        # return shift <= (node.wait + node.maxShift)
        return node.feasibility(shift)

    def get_visit(self, position):
        return self._visits[position]

    def add(self, node, position):
        self._visits.insert(position, node)
        node.place.is_serviced = True
        nodeI = self.get_visit(position - 1)
        nodeK = self.get_visit(position + 1)
        node.arrive = nodeI.get_start_service_time() + nodeI.service_time + nodeI.distance(node)
        node.set_wait()
        node.shift = nodeI.place.distance(node) + node.wait + node.service_time + node.distance(
            nodeK) - nodeI.distance(nodeK)
        # print(f"{nodeI.distance(node)}+{node.wait}+{node.service_time}+{node.distance(nodeK)}-{nodeI.distance(nodeK)}")
        # print(f"Node {node}, arrive {node.arrive}, wait {node.wait}, shift {node.shift}")

    def remove(self, position):
        node = self._visits.pop(position)
        node.removeFromRoute()
        return node

    def get_available_nodes(self):  # Seleccionamos las visitas que tienen maxShift>0
        return list(filter(lambda x: x.maxShift > 0, self._visits[1:]))

    def get_scalable_visits(self):  # Seleccionamos las visitas que se pueden ampliar
        if duration_constants.VARIABLE_DURATION:
            return list(filter(lambda x: x.best_score_service > 0, self._visits[1:]))
        else:
            return []

    def get_less_score_visits(self):  # Seleccionamos las visitas que pueden reducir su duración y las ordenamos
        if duration_constants.VARIABLE_DURATION:
            return sorted(list(filter(lambda x: x.less_score_service > 0, self._visits[1:])), key=lambda x: x.less_score_service)
        else:
            return []

    def search(self, a_list, node):
        i = 0
        for item in a_list:
            if item == node:
                return i
        return -1

    def get_positions(self):
        positions = []
        nodes = self.get_available_nodes()
        for node in nodes:
            # print(node)
            position = self._visits.index(node, 1)
            positions.append(position)
        return positions

    def updateValuesAfterInsert(self, shift, position, is_positive_shift):
        # Actualiza los atributos de la visita hacia el final
        self.updateValuesTowardsEnd(shift, position, len(self._visits), is_positive_shift)
        # Actualiza el atributo maxShift hasta el principio
        self.updateValuesTowardsBeginning(position)

    def updateValuesTowardsBeginning(self, position):
        if (position + 1) == len(self._visits):
            self._visits[position].setMaxShiftLast()
        else:
            self._visits[position].setMaxShift(self._visits[position + 1])
        for (node, post) in zip(self._visits[position - 1::-1], self._visits[position:0:-1]):
            node.setMaxShift(post)

    def updateValuesTowardsEnd(self, shift, position, end, is_positive_shift):
        fin = True
        for node in self._visits[position + 1:end]:
            if shift == 0:
                fin = False
                break
            if is_positive_shift:
                node.updateValuesAfterInsert(shift)
            else:
                node.updateValuesBringingForward(shift)
            shift = node.shift
        return fin

    def updateValuesAfterRemove(self, shift, position):
        for visit in self._visits[position:]:
            if shift == 0:
                break
            visit.updateValuesAfterRemove(shift)
            shift = visit.shift

    def get_current_gap(self, after_visit: Visit, before_visit: Visit):
        return after_visit.arrive - before_visit.get_end_service_time()

    def updateValuesCheckingFeasibilityOneRoute(self, index_x, index_y, consecutive_visits):
        # index_x e index_y son los indices de las visitas que se están moviendo
        # obtenemos las visitas
        x_visit = self._visits[index_y]  # Visita X, se utiliza el indice Y porque ya ha cambiado de posición
        y_visit = self._visits[index_x]  # Visita Y, se utiliza el indice X porque ya ha cambiado de posición
        before_x_visit = self._visits[index_x - 1]
        after_y_visit = self._visits[index_y + 1]

        if consecutive_visits:
            # El hueco actual será el tiempo transcurrido entre el instante en el que termina el servicio
            # de la visita anterior a la visita X y el instante en que empieza la visita posterior a la visita Y
            current_gap = self.get_current_gap(after_y_visit,
                                               before_x_visit)  # after_y_visit.get_start_service_time() - before_x_visit.get_end_service_time()
            # Se calcula la información de llegada y espera al haber reordenado las visitas
            for (prev, current) in zip(self._visits[index_x - 1:index_y], self._visits[index_x:index_y + 1]):
                current.arrive = prev.get_end_service_time() + prev.distance(current)
                if not current.set_wait():  # Si no se cumple el horario apertura
                    return False
            # El hueco nuevo será el tiempo transcurrido entre el instante en el que termina el servicio
            # de la visita anterior y el instante en que empieza la visita posterior, en este caso el instante
            # en el que empieza la visita posterior será el instante en el que termina el servicio de la visita X
            # en su ubicación definitiva más la distancia entre la visita X y la visita Y+1 menos el instante en que
            # termina el servicio de la visita anterior a la X
            new_gap = x_visit.get_end_service_time() + x_visit.distance(
                after_y_visit) - before_x_visit.get_end_service_time()  # +after_y_visit.wait
            # Se calcula el desplazamiento de las visitas
            shift = new_gap - current_gap
            # Comprobamos que sigue siendo factible
            if not after_y_visit.feasibility(shift):
                return False
            # Si el desplazamiento es positivo no se generará hueco y no se va a mejorar la solución
            if shift >= 0:
                return False
            # Se propaga el desplazamiento hasta el final, y después se recalcula MaxShift hasta el principio
            self.updateValuesAfterInsert(abs(shift), index_y, shift >= 0)
            return True
        else:
            # En este caso hay que calcular el hueco donde estaba la visita X y donde estaba la visita Y
            # Un hueco será desde que termina la visita anterior a la X y llega la posterior a la X
            # el otro hueco será desde que termina la visita anterior a la Y y llega la posterior a la Y
            after_x_visit = self._visits[index_x + 1]
            before_y_visit = self._visits[index_y - 1]
            # current_gap_x = after_x_visit.get_start_service_time() - before_x_visit.get_end_service_time()
            current_gap_x = self.get_current_gap(after_x_visit, before_x_visit)
            # current_gap_y = after_y_visit.get_start_service_time() - before_y_visit.get_end_service_time()
            current_gap_y = self.get_current_gap(after_y_visit, before_y_visit)

            # Se calcula el primer hueco, se actualiza arrive y wait
            is_service_x, new_gap_x = y_visit.get_gap_visits(before_x_visit, after_x_visit)
            if not is_service_x:  # No se puede servir
                return False
            # Se calcula el desplazamiento de las visitas
            shift_x = new_gap_x - current_gap_x
            y_visit.shift = shift_x
            # Se propaga el desplazamiento hasta la visita anterior a la que se ha movido
            actualiza_shift_ultima_visita = self.updateValuesTowardsEnd(abs(shift_x), index_x, index_y,
                                                                        shift_x >= 0)  # se actuaiza desde la visita posterior a la X hasta la anterior a la Y
            if not actualiza_shift_ultima_visita:  # Se actualiza el shift del último nodo porque durante la propagación no se ha hecho
                before_y_visit.shift = 0
            is_service_y, new_gap_y = x_visit.get_gap_visits(before_y_visit, after_y_visit)
            if not is_service_y:  # No se puede servir
                return False
            # Se calcula el desplazamiento de las visitas
            if shift_x >= 0:
                shift_y = new_gap_y - current_gap_y + before_y_visit.shift
            else:
                shift_y = new_gap_y - current_gap_y - before_y_visit.shift
            # Commprobamos que sigue siendo factible
            if not after_y_visit.feasibility(shift_y):
                return False
            # Si los dos desplazamientos son positivos no se han generado huecos y no se va a mejorar la solución
            if shift_x >= 0 and shift_y >= 0:
                return False
            # Se propaga el desplazamiento hasta el final, y después se recalcula MaxShift hasta el principio
            self.updateValuesAfterInsert(abs(shift_y), index_y, shift_y >= 0)
            return True

    def updateValuesCheckingFeasibilityTwoRoutes(self, route, index_x, index_y, move_visit):
        if move_visit:
            return self.updateValuesCheckingFeasibilityMove(route, index_x, index_y)
        else:
            return self.updateValuesCheckingFeasibilitySwap(route, index_x, index_y)

    def updateValuesCheckingFeasibilitySwap(self, route, index_x, index_y):
        # self y route son las rutas desde las que se hacen los movimientos
        # index_x e index_y son los indices de las visitas que se están intercambiando
        # obtenemos las visitas
        x_visit = route._visits[index_y]  # Visita X, se utiliza el indice Y porque ya ha cambiado de posición y de ruta
        y_visit = self._visits[index_x]  # Visita Y, se utiliza el indice X porque ya ha cambiado de posición y de ruta
        before_x_visit = self._visits[index_x - 1]
        after_x_visit = self._visits[index_x + 1]
        before_y_visit = route._visits[index_y - 1]
        after_y_visit = route._visits[index_y + 1]
        # current_gap_x = after_x_visit.get_start_service_time() - before_x_visit.get_end_service_time()
        current_gap_x = self.get_current_gap(after_x_visit, before_x_visit)
        # current_gap_y = after_y_visit.get_start_service_time() - before_y_visit.get_end_service_time()
        current_gap_y = self.get_current_gap(after_y_visit, before_y_visit)
        # En swap2, la visita en la posición index_x de la ruta self se intercambia por la visita de la posición index_y
        # de la ruta route
        # Se calcula el nuevo hueco en la primera ruta, se actualiza arrive y wait
        is_service_x, new_gap_x = y_visit.get_gap_visits(before_x_visit, after_x_visit)
        if not is_service_x:  # No se puede servir
            return False
        # Se calcula el desplazamiento de las visitas
        shift_x = new_gap_x - current_gap_x
        y_visit.shift = shift_x
        # Commprobamos que sigue siendo factible
        if not after_x_visit.feasibility(shift_x):
            return False
        # Se calcula el nuevo hueco en la segunda ruta, se actualiza arrive y wait
        is_service_y, new_gap_y = x_visit.get_gap_visits(before_y_visit, after_y_visit)
        if not is_service_y:  # No se puede servir
            return False
        # Se calcula el desplazamiento de las visitas
        shift_y = new_gap_y - current_gap_y
        # Commprobamos que sigue siendo factible
        if not after_y_visit.feasibility(shift_y):
            return False
        # Si los dos desplazamientos son positivos no se han generado huecos y no se va a mejorar la solución
        if shift_x >= 0 and shift_y >= 0:
            return False
        # Si los desplazamientos no reducen los huecos actuales, no se va a mejorar la solución
        if (shift_x + shift_y) >= 0:
            return False
        # Se propaga el desplazamiento hasta el final, y después se recalcula MaxShift hasta el principio
        self.updateValuesAfterInsert(abs(shift_x), index_x, shift_x >= 0)
        route.updateValuesAfterInsert(abs(shift_y), index_y, shift_y >= 0)
        return True

    def updateValuesCheckingFeasibilityReplace(self, index_x):
        # self es la ruta donde se añade la visita no planificada
        # index_x es el índices de la visita que se quita

        # Visita Y, la visita no planificada que se añade, se utiliza el indice X
        # porque ya ha cambiado de posición y de ruta
        y_visit = self._visits[index_x]

        before_x_visit = self._visits[index_x - 1]
        after_x_visit = self._visits[index_x + 1]

        current_gap_x = self.get_current_gap(after_x_visit, before_x_visit)

        # En replace, la visita en la posición index_x de la ruta self se reemplaza por la visita no planificada

        # Se calcula el nuevo hueco, se actualiza arrive y wait
        is_service_x, new_gap_x = y_visit.get_gap_visits(before_x_visit, after_x_visit)
        if not is_service_x:  # No se puede servir
            return False
        # Se calcula el desplazamiento de las visitas
        shift_x = new_gap_x - current_gap_x
        y_visit.shift = shift_x
        # Commprobamos que sigue siendo factible
        if not after_x_visit.feasibility(shift_x):
            return False
        # Se propaga el desplazamiento hasta el final, y después se recalcula MaxShift hasta el principio
        self.updateValuesAfterInsert(abs(shift_x), index_x, shift_x >= 0)
        return True

    def updateValuesCheckingFeasibilityMove(self, route, index_x, index_y):
        # self y route son las rutas desde la que se hacen los movimientos
        # index_x es el indice de las visita que se mueve a la posición index_y
        # obtenemos las visitas
        x_visit = route._visits[index_y]  # Visita X, se utiliza el indice Y porque ya ha cambiado de posición y de ruta
        y_visit = route._visits[
            index_y + 1]  # Visita Y, se utiliza el indice X porque ya ha cambiado de posición y de ruta
        before_x_visit = self._visits[index_x - 1]
        after_x_visit = self._visits[index_x]
        before_y_visit = route._visits[index_y - 1]

        # current_gap_x = after_x_visit.get_start_service_time() - before_x_visit.get_end_service_time()
        current_gap_x = self.get_current_gap(after_x_visit, before_x_visit)
        # current_gap_y = y_visit.get_start_service_time() - before_y_visit.get_end_service_time()
        current_gap_y = self.get_current_gap(y_visit, before_y_visit)

        # En move, la visita en la posición index_x de la ruta self se mueve a la posición index_y de la ruta route

        # Se calcula el nuevo hueco en la ruta que añade la visita, se actualiza arrive y wait
        is_service_y, new_gap_y = x_visit.get_gap_visits(before_y_visit, y_visit)
        if not is_service_y:  # No se puede servir
            return False
        # Se calcula el desplazamiento de las visitas
        shift_y = new_gap_y - current_gap_y
        x_visit.shift = shift_y
        # Commprobamos que sigue siendo factible
        if not y_visit.feasibility(shift_y):
            return False
        # Se propaga el desplazamiento hasta el final, y después se recalcula MaxShift hasta el principio
        route.updateValuesAfterInsert(abs(shift_y), index_y, shift_y >= 0)
        # Se calcula el desplazamiento al haber quitado la visita y se propoaga hasta el final
        shift_x = current_gap_x - before_x_visit.distance(after_x_visit)
        self.updateValuesAfterRemove(abs(shift_x), index_x)
        # Se propaga hasta el comienzo el valor de MaxShift
        self.updateValuesTowardsBeginning(index_x)
        return True

    def updateBestScore(self, scalable_visits: list):
        # ordenamos las visitas de acuerdo a la que proporcione un mejor score
        # nos quedamos con la primera visita
        #best_visit = sorted(self.visits, key=lambda x: x.best_score_service, reverse=True)[0]
        # Trabajamos solo con las visitas ampliables
        best_visit = sorted(scalable_visits, key=lambda x: x.best_score_service, reverse=True)[0]
        logging.debug("La mejor visita es: " + str(best_visit))
        # calcular shift y la posición a partir de la cual propagar
        shift = min(best_visit.max_duration - best_visit.service_time, best_visit.maxShift)
        logging.debug("Shift de la mejor visita es: " + str(shift))
        # actualizamos la duración de la visita
        best_visit.service_time = best_visit.service_time + shift
        # index() encuentra el indice de la primera ocurrencia y numpy.where() encuentra todos los indices
        position = self._visits.index(best_visit)  # Si no lo encuentra lanza una excepción
        # propagamos la actualización hasta el final y actualizamos hasta el principio
        self.updateValuesAfterInsert(abs(shift), position, shift >= 0)
        logging.debug("Termina la actualización")

    def updateWorstScore(self, scalable_visits: list):
        # las visitas están ordenadas de acuerdo a la que proporcione un menor score
        # nos quedamos con la primera visita
        worst_visit = scalable_visits[0]
        logging.debug("La peor visita es: " + str(worst_visit))
        # calcular shift y la posición a partir de la cual propagar
        shift =  worst_visit.place.service_time - worst_visit.service_time # para que el shift sea negativo y se adelanten las visitas posteriores
        logging.debug("Shift de la peor visita es: " + str(shift))
        # actualizamos la duración de la visita
        worst_visit.service_time = worst_visit.place.service_time #worst_visit.service_time - shift
        # index() encuentra el índice de la primera ocurrencia y numpy.where() encuentra todos los indices
        position = self._visits.index(worst_visit)  # Si no lo encuentra lanza una excepción
        # propagamos la actualización hasta el final y actualizamos hasta el principio
        self.updateValuesAfterInsert(abs(shift), position, shift >= 0)
        logging.debug("Termina la actualización")

    def existsPositiveMaxShift(self):  # Hay nodos con MaxShift y visitas ampliables
        return len(self.get_available_nodes()) > 0 and len(self.get_scalable_visits()) > 0


class Solution:
    def __init__(self, problem: Problem, routes=[]):
        self.problem: Problem = problem
        self.day_number = problem.day_number
        self._routes: list = routes
        if routes == []:
            for i in range(self.day_number):
                self._routes.append(Route(problem, [], i))
        self.problem.depot.is_serviced = True
        self.total_time = 0

    def __str__(self):
        s = ""
        for r in self._routes:
            s += str(r)
        s += "Score: " + str(self.total_score)
        return s

    def __eq__(self, solution):
        if not self.total_visits == solution.total_visits:
            return False
        if not self.total_score == solution.total_score:
            return False
        if not len(self._routes) == len(solution._routes):
            return False
        for i in range(len(self._routes)):
            if not self._routes[i] == solution._routes[i]:
                return False
        return True

    def print_abstract(self):
        return f"Total time: {self.total_time}\n" \
               f"Total visits: {self.total_visits}\n" \
               f"Total score: {self.total_score}\n"

    def get_available_visits(
            self):  # Ver si conviene mas mantener una variable con los places no utilizados en ninguna ruta
        visited = set()
        for route in self._routes:
            visited = visited.union({v.place.number for v in route._visits})
        # logging.debug(f"Visited: {visited}")
        available_places = list(filter(lambda x: x.number not in visited, self.problem.places))
        # logging.debug(f"Available places: {available_places}")
        available_visits = []
        for place in available_places:
            available_visits.append(Visit(place))
        return available_visits

    def get_available_visits_not_checked(self):
        # Ver si conviene mas mantener una variable con los places no utilizados en ninguna ruta
        visited = set()
        for route in self._routes:
            visited = visited.union({v.place.number for v in route._visits})
        # logging.debug(f"Visited: {visited}")
        available_places = list(filter(lambda x: x.number not in visited and
                                                 x.number not in self._checked, self.problem.places))
        # logging.debug(f"Available places: {available_places}")
        available_visits = []
        for place in available_places:
            available_visits.append(Visit(place))
        return available_visits

    def init_checked_list(self):
        self._checked = list()

    def delete_checked_list(self):
        self._checked.clear()

    def add_checked_list(self, value :int):
        self._checked.append(value)

    def get_route(self, index):
        return self._routes[index]

    def set_route(self, index, route: Route):
        self._routes[index] = route

    @property
    def total_visits(self):
        return sum(len(route.visits) for route in self._routes)

    @property
    def total_score(self):
        return sum(route.total_score for route in self._routes)

    @property
    def check_feasible(self):
        for route in self._routes:
            if not route.check_feasible:
                return False
        return True


class Customer:
    def __init__(self, number, x, y, demand, ready_time, due_date, service_time):
        self.number = number
        self.x = x
        self.y = y
        self.demand = demand
        self.ready_time = ready_time
        self.due_date = due_date
        self.service_time = service_time
        self.is_serviced = False
        self.wait = 0
        self.arrive = 0
        self.shift = 0
        self.maxShift = self.due_date

    def __eq__(self, customer):
        return self.number == customer.number

    def __repr__(self):
        return f"C_{self.number}"

    def __str__(self):
        return f"Node {self.number}, arrive {self.arrive}, wait {self.wait}, shift {self.shift}, maxshift {self.maxShift}"

    def get_start_service_time(self):
        return max([self.ready_time, self.arrive])

    def set_wait(self):  # time to wait until the window is open, if it's already closed returns False
        if self.due_date < self.arrive:
            return False
        self.wait = max([0, self.ready_time - self.arrive])
        return True

    def get_ratio(self):
        return math.pow(self.demand, 2) / self.shift  # compute the correct denominator

    def distance(self, target):
        return math.sqrt(math.pow(self.x - target.x, 2) + math.pow(target.y - self.y, 2))

    def updateValuesAfterInsert(self, shift):
        self.arrive = self.arrive + shift
        self.shift = max([0, shift - self.wait])
        self.wait = max([0, self.wait - shift])
        self.maxShift = self.maxShift - self.shift

    def updateValuesAfterRemove(self, shift):
        old_start = self.arrive + self.wait
        self.arrive = self.arrive - shift
        self.set_wait()
        new_start = self.arrive + self.wait
        self.shift = max([0, (old_start - new_start)])  # max([0, shift-self.wait])
        self.maxShift = self.maxShift + self.shift

    def removeFromRoute(self):
        self.is_serviced = False
        self.arrive = 0
        self.wait = 0
        self.shift = 0
        self.maxShift = self.due_date

    def setMaxShift(self, post):
        self.maxShift = min([self.due_date - self.get_start_service_time(), post.wait + post.maxShift])
