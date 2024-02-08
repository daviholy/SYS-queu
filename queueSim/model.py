from typing import TypeVar

from queueSim import limits
from queueSim.generators import done
from queueSim.states import CashState, PersonState


class Model:
    def __init__(self):
        self.hooked = False

    def step(self): ...


model = TypeVar("model", bound=Model)


class ModelPerson(Model):
    def __init__(self, casdesk_model: "ModelCashdesk") -> None:
        super().__init__()
        self.done = 0.0
        self.state = PersonState.waiting
        self.parent = casdesk_model

    def step(self):
        if self.state == PersonState.cashing:
            self.done += done()

            if self.done >= 1.0:
                self.done = 1.0
                self.state = PersonState.leaving
                self.parent.env.done += 1
                self.parent.done +=1

    def remove(self):
        self.parent.remove_person(self)


class ModelCashdesk(Model):
    def __init__(self, env: "ModelSimulation") -> None:
        super().__init__()
        self.env = env
        self.state = CashState.opened
        self.duration = 0
        self.done = 0

        self.queue: list[ModelPerson] = []

    def remove_person(self, person: ModelPerson):
        self.queue.remove(person)
        if len(self.queue) > 0:
            self.queue[0].state = PersonState.cashing

    def add_person(self, person: ModelPerson):
        self.queue.append(person)
        if len(self.queue) == 1:
            person.state = PersonState.cashing

    def step(self):
        if not self.state == CashState.opened:
            return
        if (
            len(self.queue) <= limits.MIN_QUEUE_LENGTH
            and self.env.length_longest_opened_queue() <= limits.MAXIMAL_LONGEST_QUEUE
        ):
            if self.duration == limits.MIN_QUEUE_DURATION and self.env.opened_desks > 1:
                self.state = CashState.closed
                self.duration = 0
                self.env.opened_desks -= 1
            else:
                self.duration += 1

        elif len(self.queue) > limits.MAX_QUEUE_LENGTH:
            if self.duration > limits.MAX_QUEUE_DURATION:
                self.env.open_desk()
                self.duration = 0
            else:
                self.duration += 1
        else:
            self.duration = 0


class ModelSimulation:
    def __init__(self):
        self.cashdesks: list[ModelCashdesk] = []
        self.opened_desks = 0
        self.step_count = 0
        self.opened_step = 0
        self.done = 0

    def add_cashdesk(self) -> ModelCashdesk:
        cashdesk = ModelCashdesk(self)
        self.cashdesks.append(cashdesk)
        self.opened_desks += 1
        return cashdesk

    def shortest_opened_queue(self) -> int | None:
        index = None
        length = None
        for current_index, cashdesk in enumerate(self.cashdesks):
            if cashdesk.state == CashState.opened and (
                length is None or len(cashdesk.queue) < length
            ):
                index = current_index
                length = len(cashdesk.queue)
        return index

    def open_desk(self) -> None:
        if self.step_count - self.opened_step <= limits.MINIMAL_OPENING_SPAN:
            return
        for cashdesk in self.cashdesks:
            if cashdesk.state == CashState.closed:
                cashdesk.state = CashState.opened
                self.opened_step = self.step_count
                self.opened_desks += 1
                return

    def length_longest_opened_queue(self) -> int:
        length = 0
        for cashdesk in self.cashdesks:
            if cashdesk.state == CashState.opened and (
                not length or len(cashdesk.queue) > length
            ):
                length = len(cashdesk.queue)
        return length
