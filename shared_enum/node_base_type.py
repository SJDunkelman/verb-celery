from enum import Enum


class NodeBaseType(str, Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    PROCESS = "PROCESS"
