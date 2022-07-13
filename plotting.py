import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sys
import re
import os


def plot_selected():
    filenames = []
    if not os.path.exists('./selected_plots'):
        os.makedirs('./selected_plots')
    for file in os.listdir('./selected_plots'):
        if file.endswith('.csv'):
            filenames.append(file)
    for name in filenames:
        found = False
        with open('./selected_plots/'+name) as readfile:
            for cnt, line in enumerate(readfile):
                if "wavelength,intensity" in line:
                    row_num = cnt
                    found = True
        if not found:continue
        readfile.close
        df = pd.read_csv('./selected_plots/'+name, skiprows=row_num)
        plt.rc('xtick',labelsize=12)
        plt.rc('ytick',labelsize=12)
        plt.rc('axes', labelsize=12)
        plt.xlabel('Wavelength')
        plt.ylabel('Intensity')
        plt.ylim((0,60000))
        plt.plot(df['wavelength'], df['intensity'], label=name.rsplit('/', 1)[-1])
        plt.legend(loc='upper right')

    plt.show()

if __name__ == "__main__":
    plot_selected()