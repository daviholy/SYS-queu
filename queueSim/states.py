from enum import Enum


class PersonState(Enum):
    waiting = 0
    cashing = 1
    leaving = 2


class CashState(Enum):
    opened = 0
    closed = 1
