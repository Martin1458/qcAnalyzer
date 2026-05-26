import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class ChartFrame(ttk.Frame):
    def __init__(self, parent, figsize=(8, 4)):
        super().__init__(parent)
        self.fig = Figure(figsize=figsize, dpi=96)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def clear(self):
        self.fig.clf()

    def draw(self):
        self.canvas.draw()
