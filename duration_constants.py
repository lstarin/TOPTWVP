import enum

class DurationMethod(enum.Enum):

    Max = 1
    MaxShift = 2
    Random = 3
    Optimize = 4

#Constantes para trabajar con duración variable
INCREMENT_DURATION = 30
STEP_DURATION = 15
VARIABLE_DURATION = False
METHOD = DurationMethod.MaxShift
