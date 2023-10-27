import os
from VRPTW.structure import Problem, Customer, Place

class SolomonFormatParser:
    """Parsing file in Solomon format
    https://www.sintef.no/projectweb/top/vrptw/solomon-benchmark/documentation/
    """
    def __init__(self, problem_file, num_nodes):
        self.problem_file = problem_file
        self.num_nodes = num_nodes

    def get_problem(self) -> Problem:
        with open(self.problem_file, 'r') as f:
            lines = list(map(lambda l: l.replace('\n', '').split(), f.readlines()))
        name = lines[0][0]
        vehicle_number, vehicle_capacity = list(map(int, lines[4]))
        customers = []
        for line in lines[9:]:
            customers.append(Customer(*list(map(int, line))))
        return Problem(name, customers, vehicle_number, vehicle_capacity)

    def get_problem_places(self) -> Problem:
        with open(self.problem_file, 'r') as f:
            lines = list(map(lambda l: l.replace('\n', '').split(), f.readlines()))
        name = lines[0][0]
        vehicle_number, vehicle_capacity = list(map(int, lines[4]))
        places = []
        for line in lines[9:]:
            places.append(Place(*list(map(int, line))))
        if self.num_nodes>0:
            return Problem(name, places[:self.num_nodes], vehicle_number, vehicle_capacity)
        return Problem(name, places, vehicle_number, vehicle_capacity)

class GeneralFormatParser:
    def __init__(self, problem_file, format, num_nodes):
        self.problem_file = problem_file
        self.format = format
        self.num_nodes = num_nodes

    def get_problem_places(self) -> Problem:
        with open(self.problem_file, 'r') as f:
            lines = list(map(lambda l: l.replace('\n', '').split(), f.readlines()))
        if self.format is None:
            name = self.problem_file.split(os.sep)[-1].split(".")[0]
            vehicle_number, vehicle_capacity = list(map(int, lines[1]))
            places = []
            for line in lines[2:]:
                l = list(line)
                places.append(Place(int(l[0]), float(l[1]), float(l[2]), int(l[4]), int(l[-2]), int(l[-1]), int(l[3])))
            if self.num_nodes>0:
                return Problem(name, places[:self.num_nodes], vehicle_number, vehicle_capacity)
            return Problem(name, places, vehicle_number, vehicle_capacity)
        else:
            s=SolomonFormatParser(self.problem_file, self.num_nodes)
            return s.get_problem_places()