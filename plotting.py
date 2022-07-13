from cProfile import label
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys
import re

def plot_selected():
    paths = input("Drop the files you want to plot and press enter\n")
    paths = paths.replace(" ", "")
    paths = re.findall(r"'(.*?)'", paths, re.DOTALL)
    for path in paths:
        found = False
        with open(path) as readfile:
            for cnt, line in enumerate(readfile):
                if "wavelength,intensity" in line:
                    row_num = cnt
                    found = True
        if not found:continue
        readfile.close
        df = pd.read_csv(path, skiprows=row_num)
        plt.rc('xtick',labelsize=12)
        plt.rc('ytick',labelsize=12)
        plt.rc('axes', labelsize=12)
        plt.xlabel('Wavelength')
        plt.ylabel('Intensity')
        plt.ylim((0,60000))
        plt.plot(df['wavelength'], df['intensity'], label=path.rsplit('/', 1)[-1])
        plt.legend(loc='upper right')

    plt.show()

