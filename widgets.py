from tkinter import Label, Entry, StringVar
import re

UNICODE_HEXADECIMAL = re.compile(r'[0-9a-f]{0,4}$')


class NavControl(Label):

    def __init__(self, master=None, **cnf):
        super().__init__(master, **cnf)
        self["bg"] = initial_bg = "#5a5a5a"
        self["fg"] = initial_fg = "#f7f7f7"
        self.config(height=3, width=5, cursor="hand2")
        self.bind('<Enter>', lambda ev: self.config(bg="#f7f7f7", fg="#5a5a5a"))
        self.bind('<Leave>', lambda ev: self.config(bg=initial_bg, fg=initial_fg))
        self.bind('<Button-1>', lambda ev: self.on_click())
        self.run = None

    def on_click(self):
        if self.run:
            self.run()


class HexadecimalIntegerControl(Entry):

    def __init__(self, master=None, **cnf):
        super().__init__(master, **cnf)
        self._data = StringVar()
        self["textvariable"] = self._data
        self.config(
            validate='all',
            validatecommand=(
                self.register(self.validator), '%P'
            )
        )

    def get(self) -> int:
        val = super().get()
        if val.isdigit():
            return int(val)
        if re.match(UNICODE_HEXADECIMAL, val):
            return int(val, 16)
        return 0

    def set(self, value: str):
        if self.validator(value):
            self._data.set(value)

    def validator(self, value: str) -> bool:
        if value.isdigit():
            if int(value) <= 0xffff:
                return True
        if re.match(UNICODE_HEXADECIMAL, value):
            return True
        return False


class Grid(Label):

    def __init__(self, app, **cnf):
        super().__init__(app.body, **cnf)
        self.app = app
        self.config(height=2, width=4, font='Arial 12', bg="#f7f7f7")
        self.bind('<Enter>', lambda ev: self.hover(True))
        self.bind('<Leave>', lambda ev: self.hover(False))
        self.bind('<Button-1>', lambda ev: self.lock())
        self.bind('<Button-3>', lambda ev: self.request_menu(ev))
        self.text = ""
        self.is_locked = False

    def assert_is_active(self, func):
        text = self.text

        def wrap(*args):
            if not text:
                pass
            else:
                return func(*args)

        wrap.__name__ = func.__name__
        wrap.__doc__ = func.__doc__
        return wrap

    def copy(self, flag: int):
        self.clipboard_clear()
        if flag == 0:
            self.clipboard_append(self["text"])
        elif flag == 1:
            self.clipboard_append(self.text.replace("0x", ""))
        elif flag == 2:
            self.clipboard_append(str(int(self.text, 16)))

    def set(self, value: int):
        if value is None:
            self["text"] = self.text = ""
            return
        self["text"] = chr(value)
        self.text = str(hex(value))

    def hover(self, flag=True):
        if not self.text:
            return
        if flag:
            self["bg"] = "#bbb"
            self.app.activate_grid(self)
        elif not self.is_locked:
            self["bg"] = "#f7f7f7"

    def unlock(self):
        self.is_locked = False
        self.app.active_grid = None
        self['bg'] = "#f7f7f7"

    def request_menu(self, event=None):
        if not self.text:
            return
        self.lock()
        self.app.request_context_menu(self, event)

    def lock(self):
        if not self.text:
            return
        if self.app.active_grid:
            self.app.active_grid.unlock()
        self.is_locked = True
        self.app.active_grid = self
        self["bg"] = "#bbb"
