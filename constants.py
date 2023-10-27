
import enum


class MaximizeMethod(enum.Enum):
    Score = 1
    DurationScore = 2


#Constante para modificar la función de maximización
MAXIMISATION_METHOD = MaximizeMethod.Score

