#!/usr/bin/env python3

import tkinter as tk
import os
import pathlib
import logging


class App(tk.Tk):

    def __init__(self) -> None:
        super().__init__()

        self.geometry("1200x900")

        self.frame1 = tk.Frame(master=self, width=200, bg="grey")
        self.frame1.grid(row=0, column=0)



        self.tex = tk.Text(master=self, width=200, height=50, bg="black", fg="white")
        self.tex.grid( row=0, column=1)

        activate = tk.Button(self.frame1, width=13,text='Activate', command=self.cbc('Activate', self.tex))
        activate.grid(row=0, column=0, padx=50, pady=20)

        measure = tk.Button(self.frame1, width=13,text='Start measurement', command=self.cbc('Start measurement', self.tex))
        measure.grid(row=1, column=0, padx=50, pady=20)

        turn_on = tk.Button(self.frame1, width=13, text='Turn on', command=self.cbc('Turn on', self.tex))
        turn_on.grid(row=2, column=0, padx=100, pady=20)

        options = ['millisecond', 'nanoseconds']
        self.variable = tk.StringVar(self)
        self.variable.set(options[0])
        integration_time = tk.OptionMenu(self.frame1, self.variable, *options, command=lambda x: self.display_selected(x,self.tex))
        integration_time.config(width=15)
        integration_time.grid(row=3, column=0, padx=100, pady=20, ipadx= 20)




    def display_selected(self, choice, tex):
        tex.insert(tk.END, '{}\n'.format(self.variable.get()))
        tex.see(tk.END)

    def cbc(self, id, tex):
        return lambda : self.callback(id, tex)

    def callback(self, id, tex):
        s = '{}\n'.format(id)
        tex.insert(tk.END, s)
        tex.see(tk.END)


if __name__ == '__main__':
    log_lvl = logging.INFO
    fmt = '[%(levelname)s] %(asctime)s - %(message)s'
    logging.basicConfig(level=log_lvl, format=fmt)
    app = App()
    app.title('My Tkinter app')
    app.state('normal')
    app.mainloop()

