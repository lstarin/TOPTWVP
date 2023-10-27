import os
import glob
import argparse

import constants
#from VRPTW import *
import duration_constants
from VRPTW.parser import GeneralFormatParser
from VRPTW.solvers.auxiliars import IteratedLocalSearchV2
from VRPTW.structure import Solution

import logging
import datetime
from constants import MAXIMISATION_METHOD, MaximizeMethod
# import enum
#
# class DurationMethod(enum.Enum):
#
#     Max = 1
#     MaxShift = 2
#     Random = 3
#     Optimize = 4
#
# #Constantes para trabajar con duración variable
# INCREMENT_DURATION = 30
# STEP_DURATION = 15
# VARIABLE_DURATION = True
# METHOD = DurationMethod.MaxShift



filename="VRPTW.log"
logging.basicConfig(filename=filename, filemode='w', format='%(levelname)s:%(message)s', level=logging.DEBUG)
now = datetime.datetime.now()
logging.debug('EXECUTION TIME:'+now.strftime("%Y-%m-%d %H:%M:%S"))

def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Solving VRPTW with heuristics')
    parser.add_argument('problem_file', type=str, help='Problem file or instances folder (in Solomon format)')
    parser.add_argument('-b', '--benchmark', action='store_true', help="Run solvers on all files in instances folder")
    parser.add_argument('-r', '--routes', type=int, help='Number of routes available')
    parser.add_argument('-s', '--solution_folder', type=str, help='Folder to store the solution files')
    parser.add_argument('-t', '--total_time', type=int, help='Total time execution in seconds')
    parser.add_argument('-i', '--iterations', type=int, help='Number of iterations for each problem')
    parser.add_argument('-m', '--maximize', type=str, help='Set the maximisation method')
    parser.add_argument('-f', '--format', type=str, help='Problem file format')
    parser.add_argument('-fc', '--fast_construction', action='store_true', help="Fast initial construction")
    parser.add_argument('-vd', '--vble_duration', type=str, help='Activate variable duration with one method')
    parser.add_argument('-vi', '--vble_interval', type=int, help='Set the variable interval')
    parser.add_argument('-n', '--num_nodes', type=int, help='Num nodes to use from the problem')
    parser.add_argument('-dd', '--decrease_duration', action='store_true', help="Execute decrease duration method")
    parser.add_argument('-do', '--duration_optimize', action='store_true', help="Execute increase duration optimize method")
    parser.add_argument('-d', '--debug', action='store_true', help="Information for debugging is written to the log file")
    return parser.parse_args()


def execute_problem(file, args: argparse.Namespace):
    # global problem, problem
    num_iterations = 1
    num_nodes = -1
    if args.num_nodes is not None:
        num_nodes = args.num_nodes
    if args.iterations is not None:
        num_iterations = args.iterations
    for iteration in range(num_iterations):
        problem = GeneralFormatParser(file, args.format, num_nodes).get_problem_places()
        print(problem.places)
        #problem = SolomonFormatParser(file).get_problem_places()
        if args.routes is not None:
            problem.day_number = args.routes
        logging.debug(problem)
        ils: IteratedLocalSearchV2 = IteratedLocalSearchV2(problem, problem.total_score)
        if args.total_time is not None:
            ils.timelimit = args.total_time
        if args.fast_construction:
            ils.fast_construction = True
        if args.decrease_duration:
            ils.decrease_dv = True
        if args.duration_optimize:
            ils.duration_optimize = True
        solution: Solution = ils.execute()
        logging.debug("\r\nSOLUTION:\r\n")
        logging.debug(solution)
        iteration_str = ""
        if args.iterations is not None:
            iteration_str = f"_{iteration}"  # s = "Route " + str(self._index) + '\r\n'
        with open(f"""{solution_folder}{file.split(os.sep)[-1].split(".")[0]}{iteration_str}_v2.sol""", 'w') as f:
            print(file.split(os.sep)[-1].split(".")[0], problem.obj_func(solution._routes), solution.total_score, solution.total_time)
            f.write(solution.print_abstract())
            #visit_node distance start_time wait service_time
            f.write(problem.print_canonical(solution._routes))
            f.close()


if __name__ == '__main__':
    args = arguments()
    level_str = "INFO"
    if args.debug:
        level_str = "DEBUG"
    numeric_level = getattr(logging, level_str, None)
    filename = "VRPTW.log"
    logging.basicConfig(filename=filename, filemode='w', format='%(levelname)s:%(message)s', level=numeric_level)
    now = datetime.datetime.now()
    logging.debug('EXECUTION TIME:' + now.strftime("%Y-%m-%d %H:%M:%S"))
    solution_folder = 'solutions'
    if args.solution_folder is not None:
        if not args.solution_folder.startswith(os.sep):
            solution_folder += os.sep
        solution_folder += args.solution_folder
    if not solution_folder.endswith(os.sep):
        solution_folder += os.sep
    # if not os.path.exists('solutions'):
    #     os.mkdir('solutions')
    if not os.path.exists(solution_folder):
        os.mkdir(solution_folder)
    if args.maximize is not None:
        if args.maximize == "DurationScore":
            constants.MAXIMISATION_METHOD = MaximizeMethod.DurationScore
    if args.vble_duration is not None:
        duration_constants.VARIABLE_DURATION = True
        # De momento no se utiliza porque solo se trabaja con ese método
        # if args.vble_duration == "MaxShift":
        #     duration_constants.METHOD = duration_constants.DurationMethod.MaxShift
    if args.vble_interval is not None:
        duration_constants.INCREMENT_DURATION = args.vble_interval

    if args.benchmark:
        assert os.path.isdir(args.problem_file), "Folder doesn't exist"
        folder = args.problem_file
        if not folder.endswith(os.sep):
            folder += os.sep
        folder += '*.txt'

        for file in glob.glob(folder):  # ('instances/*.txt'):
            # problem = SolomonFormatParser(file).get_problem_places()
            # if args.routes is not None:
            #     problem.day_number = args.routes
            # solution = IteratedLocalSearchV2(problem).execute()
            # # with open(f"""solutions/{file.split(os.sep)[-1].split(".")[0]}.sol""", 'w') as f:
            # with open(f"""{solution_folder}{file.split(os.sep)[-1].split(".")[0]}.sol""", 'w') as f:
            #     print(file.split(os.sep)[-1].split(".")[0], problem.obj_func(solution._routes))
            #     f.write(solution.print_abstract())
            #     f.write(problem.print_canonical(solution._routes))
            execute_problem(file, args)
    else:
        assert os.path.isfile(args.problem_file), "Problem file doesn't exist"
        # # problem = SolomonFormatParser(args.problem_file).get_problem()
        # problem = SolomonFormatParser(args.problem_file).get_problem_places()
        # if args.routes is not None:
        #     problem.day_number = args.routes
        # print(problem)
        # # solution = IteratedLocalSearch(problem).execute()
        # solution = IteratedLocalSearchV2(problem).execute()
        # # solution = IteratedLocalSearchV2(problem).construction()
        # # print("\r\nINITIAL SOLUTION:\r\n",solution)
        # # solution = IteratedLocalSearchV2(problem).perturbation(solution)
        # print("\r\nSOLUTION:\r\n", solution)
        # # with open(f"""solutions/{args.problem_file.split(os.sep)[-1].split(".")[0]}.sol""", 'w') as f:
        # with open(f"""{solution_folder}{args.problem_file.split(os.sep)[-1].split(".")[0]}.sol""", 'w') as f:
        #     f.write(problem.print_canonical(solution._routes))
        # # solution = GuidedLocalSearch(problem).execute()
        execute_problem(args.problem_file, args)
