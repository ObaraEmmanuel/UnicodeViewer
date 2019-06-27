from tkinter import *
import tkinter.ttk as ttk
import components as Components
from widgets import Grid
from threading import Thread
from copy import copy

MAX_GRID_WIDTH, MAX_GRID_HEIGHT = 20, 10


# noinspection PyArgumentList
class App(Tk):

    def __init__(self, ):
        super().__init__()
        self.geometry('800x500')
        self.config(bg='#5a5a5a')
        self.title("Unicode viewer")
        self.resizable(0, 0)
        self.nav = Frame(self, bg="#5a5a5a")
        self.nav.place(x=0, y=0, relwidth=1, relheight=0.1)
        self.body = Frame(self)
        self.body.place(rely=0.101, x=0, relwidth=1, relheight=0.9)
        self.body.bind('<Leave>', lambda ev: self.deactivate_grid())
        self.body.bind('<Button-3>', lambda ev: print('context menu requested.'))
        self.context_menu = Menu(bg="#5a5a5a", tearoff=0, fg="#f7f7f7", activebackground="#f7f7f7",
                                 activeforeground="#5a5a5a", bd=0, relief='flat', font='calibri 12')
        self.context_menu.add_command(label="\ue923   Copy unicode",
                                      command=lambda: self.active_grid.copy(0))
        self.context_menu.add_command(label="\ue923   Copy code point",
                                      command=lambda: self.active_grid.copy(2))
        self.context_menu.add_command(label="\ue923   Copy hexadecimal scalar",
                                      command=lambda: self.active_grid.copy(1))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="\ue7a9   Save as image")
        self.context_menu.add_command(label="\ue735   add to favorites")
        self.context_menu.add_command(label="\ue946   unicode info")
        self._size = (MAX_GRID_WIDTH, MAX_GRID_HEIGHT)
        self.grids = []
        self.grid_cluster = []
        self.init_grids()
        self.active_grid = None
        # Plugin components here. Your component has to inherit the Component class
        self.components = [
            Components.Swipe(self),
            Components.InputBox(self),
            Components.GridTracker(self),
            Components.RenderSizeControl(self),
        ]
        self._from = 0
        self.render_thread = None
        self.render(59422)
        self.size = (10, 5)
        self.style = ttk.Style()
        self.style.configure('Horizontal.TScale', background='#5a5a5a')

    @property
    def size(self) -> (int, int):
        return self._size

    @size.setter
    def size(self, value: (int, int)):
        if self.size == value:
            return
        self._size = value
        w_lower_bound = (MAX_GRID_WIDTH - value[0]) // 2
        h_lower_bound = (MAX_GRID_HEIGHT - value[1]) // 2
        self.grid_cluster = []
        for column in self.grids[w_lower_bound: w_lower_bound + value[0]]:
            for grid in column[h_lower_bound: h_lower_bound + value[1]]:
                self.grid_cluster.append(grid)
        self.clear_grids()
        self.render(self._from)
        for component in self.components:
            component.size_changed()

    def clear_grids(self):
        for column in self.grids:
            for grid in column:
                grid.set(None)

    def init_grids(self):
        for i in range(self.size[0]):
            column = []
            for j in range(self.size[1]):
                grid = Grid(self, font='calibri 12')
                column.append(grid)
                self.grid_cluster.append(grid)
                grid.grid(row=j, column=i)
            self.grids.append(column)

    @property
    def current_range(self) -> [int, int]:
        return [self._from, self._from + self.size[0] * self.size[1]]

    def _render(self, from_: int, prev_thread: Thread) -> None:
        if from_ > 0xffff:
            return
        if prev_thread:
            prev_thread.join()
        self._from = from_
        self.propagate_change()
        cluster = copy(self.grid_cluster)
        if self.active_grid:
            self.active_grid.unlock()
        to = from_ + self.size[0] * self.size[1]
        # Check whether value is above
        to = to if to <= 0xffff else 0xffff
        for i in range(from_, to):
            cluster[i - from_].set(i)
        if to == 0xffff:
            fracture_point = 0xffff - from_
            for j in range(fracture_point, self.size[0] * self.size[1]):
                cluster[j].set(None)

    def propagate_change(self):
        for component in self.components:
            component.receive_range()

    def activate_grid(self, grid: Grid):
        for component in self.components:
            component.receive_grid(grid)

    def deactivate_grid(self):
        for component in self.components:
            component.receive_grid(self.active_grid)

    def render(self, from_: int) -> None:
        self.render_thread = Thread(target=self._render, args=(from_, self.render_thread))
        self.render_thread.start()

    def request_context_menu(self, grid: Grid, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
