from tkinter import Widget
from typing import TypeVar

from textual.app import App
from textual.reactive import reactive
from textual.widgets import Label, Static
from textual.widgets._header import HeaderTitle

from queueSim.model import CashState

view = TypeVar("view", bound=Widget)


class ViewPerson(Static):
    done = reactive(0.0, init=False)

    def __init__(self):
        super().__init__()

    def compose(self):
        yield Label(f"%{self.done}")

    def watch_done(self, new_value: float):
        for label in self.query(Label):
            label.update(str(new_value))


class ViewCashDeskHeader(Static):

    queue_length = reactive(0)
    cashier_name = reactive("", always_update=True)
    closed = reactive(False)
    done = reactive(0, init=False)

    def __init__(self, name: str, length: int, disabled: bool = False):
        super().__init__()
        self._name = Label()
        self._length = Static()
        self.disabled = disabled

        self.queue_length = length
        self.cashier_name = name

    def compose(self):
        if not self.disabled:
            yield Static()
            yield self._name
            yield self._length
        else:
            yield Label("closed")

    def watch_queue_length(self, new_length: int):
        self._length.update(f"{str(new_length)}  done: {self.done}")

    def watch_done(self, new_done: int):
        self._length.update(f"{str(self.queue_length)}  done: {new_done}")

    def watch_cashier_name(self, new_name: str):
        self._name.update(new_name)



class Viewqueue(Static):

    queue = reactive([])

    def __init__(self):
        super().__init__()

    def __getitem__(self, key) -> ViewPerson:
        return self.queue[key]

    def __len__(self) -> int:
        return len(self.queue)


class ViewCashDesk(Static):

    closed = reactive(CashState.opened)
    done = reactive(0, init=False)

    def __init__(self, name: str, len: int = 0):
        super().__init__()
        self._header = ViewCashDeskHeader(name, len)
        self._queue = Viewqueue()
        self._name = name

    def compose(self):
        yield self._header
        yield self._queue

    def create_person(self) -> ViewPerson:
        person = ViewPerson()
        self._queue.queue.append(person)
        if self.is_running:
            self._queue.mount(person)
        else:
            self._queue.compose_add_child(person)
        self._header.queue_length += 1
        return person

    def remove_person(self, person: ViewPerson) -> None:
        self._queue.queue.remove(person)
        self._header.queue_length -= 1

    def watch_closed(self, closed: CashState):
        if closed == CashState.closed:
            self._header.cashier_name = "CLOSED"
            self._header.disabled = True
        else:
            self._header.cashier_name = self._name
            self._header.disabled = False
    
    def watch_done(self, new_value: int):
        self._header.done = new_value

class ViewCounter(Static):
    step = reactive(0, init=False)
    done = reactive(0, init=False)

    def compose(self):
        yield Label(f"steps: {self.step}   done: {self.done}", id="testing")
    
    def watch_step(self):
        self.query_one(Label).update(f"steps: {self.step}   done: {self.done}")

    def watch_done(self):
        self.query_one(Label).update(f"steps: {self.step}   done: {self.done}")

class Header(Static):
    def __init__(self):
        super().__init__()
        self.counter = ViewCounter()

    def compose(self):
        yield Static()

        title =  HeaderTitle()
        title.text = "Cash desks simulator"
        yield title
        yield self.counter


class bla(App):
    CSS_PATH = "style.tcss"

    def __init__(self, desks: list[ViewCashDesk]):
        super().__init__()
        self.header = Header()
        self.desks = desks

    def compose(self):
        for desk in self.desks:
            yield desk
        yield self.header