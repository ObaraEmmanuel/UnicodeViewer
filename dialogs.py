from tkinter import Toplevel, Label, Frame, ttk, filedialog
from widgets import KeyValueLabel, ScrolledGridHolder, Grid, ContextMenu
import components as Components
from PIL import ImageGrab
import os
import shelve


def center_window(parent, child):
    """
    Center a window(child) within its parent on opening
    :param parent:
    :param child:
    :return:
    """
    child.update_idletasks()
    x = int((parent.winfo_width() - child.winfo_width()) / 2) + parent.winfo_x()
    y = int((parent.winfo_height() - child.winfo_height()) / 2) + parent.winfo_y()
    child.geometry("+{}+{}".format(x, y))


def local_picture_location():
    return os.path.join(os.environ['HOMEDRIVE'], os.environ["HOMEPATH"], "Pictures")


class BaseDialog(Toplevel):

    def __init__(self, app):
        super().__init__(app)
        self.wm_transient(app)
        self.config(bg='#5a5a5a')
        self.resizable(0, 0)
        self.grab_set()
        self.focus_force()
        self.app = app
        self.grid = app.active_grid
        self.body = Frame(self, bg='#f7f7f7')
        self.body.pack(side='top', fill="x", expand=True)
        self.button_holder = Frame(self)
        self.button_holder.pack(side='top', fill='x', expand=True)
        self.centered = False
        self.bind('<Configure>', lambda _: self.center())

    def center(self):
        if not self.centered:
            center_window(self.app, self)
            self.centered = True if self.winfo_width() != 1 else False


class UnicodeInfo(BaseDialog):

    def __init__(self, app):
        super().__init__(app)
        data = self.grid.data
        Label(self.body, font=(self.grid.font, 28), bg="#5a5a5a", text=self.grid['text'],
              width=5, height=2, fg='#f7f7f7').grid(row=0, column=0, rowspan=len(data), sticky='nesw', padx=5, pady=5)
        # Render the grids data
        row = 1
        for key in data:
            KeyValueLabel(self.body, key, data[key],
                          width=100, height=10).grid(row=row, column=2, sticky='ew')
            row += 1

        close = ttk.Button(self.button_holder, text="Close", command=self.destroy)
        close.pack(side='top', pady=5)

        self.title("Info for {}".format(self.grid.text.replace("0x", "")))


class SaveAsImage(BaseDialog):

    def __init__(self, app):
        super().__init__(app)
        self.image_label = Label(self.body, font=(self.grid.font, 60), fg="#5a5a5a", bg="#f7f7f7",
                                 width=4, height=2, text=self.grid['text'])
        self.image_label.pack(side='top', padx=5, pady=5)

        ttk.Button(self.button_holder, text="copy").pack(side='left', padx=5, pady=5)
        ttk.Button(self.button_holder, text="Save", command=self.save).pack(side='left', padx=5, pady=5)
        ttk.Button(self.button_holder, text="Cancel", command=self.destroy).pack(side='left', padx=5, pady=5)
        self.image = None

    def snip_img(self):
        self.update_idletasks()
        self.body.update_idletasks()
        self.image_label.update_idletasks()
        x1 = self.image_label.winfo_rootx()
        y1 = self.image_label.winfo_rooty()
        x2 = self.image_label.winfo_width() + x1
        y2 = self.image_label.winfo_height() + y1
        image = ImageGrab.grab((x1, y1, x2, y2))
        return image

    def save(self):
        if self.image is None:
            self.image = self.snip_img()
        path = filedialog.asksaveasfilename(parent=self, initialfile="unicd.png",
                                            filetypes=[("Portable Network Graphics", "*.png")],
                                            initialdir=local_picture_location())
        if path:
            self.image.save(path)
            self.destroy()


class ManageFavourites(BaseDialog):

    def __init__(self, app):
        super().__init__(app)
        self.nav = Frame(self.body, bg="#5a5a5a", height=40)
        self.nav.pack(side='top', fill='x', expand=True)
        self.body = ScrolledGridHolder(self.body, height=230, width=400, bg='#f7f7f7')
        self.body.pack(side='top')
        self.body = self.body.body
        self.body.bind('<Leave>', lambda ev: self.deactivate_grid())
        self.grids = []
        self.active_grid = None
        self.load_favourites()
        self.title("Favourites")
        self.context_menu = ContextMenu()
        self.context_menu.load_actions(("\ue923", "Copy unicode", lambda: self.active_grid.copy(0)),
                                       ("\ue923", "Copy code point", lambda: self.active_grid.copy(2)),
                                       ("\ue923", "Copy hexadecimal scalar", lambda: self.active_grid.copy(1)),
                                       ('separator',),
                                       ("\ue7a9", "Save as image", lambda: SaveAsImage(self)),
                                       ("\ue735", "remove from favorites", self.remove),
                                       ("\ue946", "unicode info", lambda: UnicodeInfo(self))
                                       )
        self.components = [
            Components.GridTracker(self)
        ]

        ttk.Button(self.button_holder, text="Clear all", command=self.clear_favourites).pack(side='left', padx=5,
                                                                                             pady=5)
        ttk.Button(self.button_holder, text="Close", command=self.destroy).pack(side='right', padx=5, pady=5)

    def request_context_menu(self, event=None):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def activate_grid(self, grid: Grid):
        for component in self.components:
            component.receive_grid(grid)

    def deactivate_grid(self):
        for component in self.components:
            component.receive_grid(self.active_grid)

    def remove(self):
        with shelve.open("data") as data:
            if "favourites" in data:
                fav = data["favourites"]
                fav.remove((int(self.active_grid.text, 16), self.active_grid.font))
                data["favourites"] = fav
        self.active_grid.grid_forget()
        self.grids.remove(self.active_grid)
        self.active_grid = None

    def clear_favourites(self):
        with shelve.open("data") as data:
            if "favourites" in data:
                data["favourites"] = []
        for grid in self.grids:
            grid.grid_forget()
        self.grids = []

    def load_favourites(self):
        with shelve.open("data") as data:
            if "favourites" in data:
                row, column = 0, 0
                for grid_config in data["favourites"]:
                    grid = Grid(self, font=(grid_config[1], 12))
                    grid.set(grid_config[0])
                    self.grids.append(grid)
                    grid.grid(row=row, column=column)
                    if row == 5:
                        column += 1
                        row = 0
                    else:
                        row += 1
