from typing import Self

from textual.widget import Widget

from queueSim.generators import new_people
from queueSim.model import Model, ModelCashdesk, ModelPerson, ModelSimulation
from queueSim.states import PersonState
from queueSim.view import bla, ViewCashDesk


class ModelView:
    def __init__(self, model: Model, view: Widget, children: None | list[Self] = None):
        self.model = model
        self.view = view
        if children:
            self.children = children

    def view_update(self): ...

    def after_step(self): ...

    def step(self):
        if hasattr(self, "model"):
            self.model.step()

        if hasattr(self, "children"):
            for child in self.children:
                child.step()

        self.view_update()
        self.after_step()


class Person(ModelView):
    def __init__(self, cashdesk: "Cashdesk"):
        self.model = ModelPerson(cashdesk.model)
        self.view = cashdesk.view.create_person()
        self._parent = cashdesk

    def after_step(self):
        if self.model.state == PersonState.leaving:
            self.model.remove()
            self.view.remove()

            self._parent.remove_person(self)

    def view_update(self):
        self.view.done = self.model.done


class Cashdesk(ModelView):
    def __init__(self, model: ModelCashdesk, name: str, initial_persons: int = 0):
        self.model = model
        self.view = ViewCashDesk(name, 0)
        self.children = []

        for _ in range(initial_persons):
            self.add_person()

    def remove_person(self, person: Person):
        self.children.remove(person)
        self.view.remove_person(person.view)

    def add_person(self):
        person = Person(self)
        self.children.append(person)
        self.model.add_person(person.model)

    def view_update(self):
        self.view.closed = self.model.state
        self.view.done = self.model.done

class Counter(ModelView):
    def __init__(self, env: ModelSimulation, app: bla):
        self.env = env
        self.view = app.header.counter

    def view_update(self):
        return super().view_update()
    
    def step(self):
        self.view.step = self.env.step_count
        self.view.done = self.env.done


class Simulation:
    simulation = ModelSimulation()

    def __init__(self,initial_desks: list[int]):
        self.cashdesks: list[Cashdesk] = []

        for index, persons in enumerate(initial_desks):
            self.cashdesks.append(
                Cashdesk(self.simulation.add_cashdesk(), f"cashdesk: {index}", persons)
            )
        self.app = bla([cashdesk.view for cashdesk in self.cashdesks])
        self.counter = Counter(self.simulation,self.app)
        _patch_controls(self)

    def simulation_step(self):
        self.simulation.step_count += 1
        for _ in range(new_people()):
            self._person_spawn()
        for cashdesk in self.cashdesks:
            cashdesk.step()

        self.counter.step()

    def run(self):
        self.app.run()

    def _person_spawn(self):
        min_index = self.simulation.shortest_opened_queue()
        if min_index is not None:
            self.cashdesks[min_index].add_person()

def _patch_controls(sim: Simulation) -> None:
    def key_space(self) -> None:
        sim.simulation_step() #type: ignore  # noqa: F821

    setattr(sim.app, "key_space", key_space)






