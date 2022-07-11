import pandas as pd
import numpy as np
import itertools
from statistics import mean
from sklearn.cluster import KMeans, k_means
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', 500)

def highLow_intensity(current_intensities):
        highest_intensity = [0,current_intensities[0]]
        lowest_high_intensity = [0,current_intensities[0]]

        for index,dataframe in enumerate(current_intensities):
            if int(dataframe.max()) >= int(highest_intensity[1].max()):
                highest_intensity = [index,dataframe]
            if int(dataframe.max()) <= int(lowest_high_intensity[1].max()):
                lowest_high_intensity = [index,dataframe]
        
        return highest_intensity, lowest_high_intensity

def abs_from_mean(current_intensities, all_intensities=None):
    if all_intensities == None:
        shot_mean = pd.concat(current_intensities,axis=1).T.mean(0)
    else:
        shot_mean = pd.concat(all_intensities,axis=1).T.mean(0)

    distances_list = []
    for x in current_intensities:
        dist_from_mean = shot_mean.subtract(x).abs().mean()
        distances_list.append(dist_from_mean)
    return distances_list

def grouper(n,iterable):
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it,n))
        if not chunk:
            return
        yield chunk

from scipy.signal import argrelextrema

def peak_finder2(spectra):
    spectra = spectra.copy()
    df = pd.DataFrame(data=spectra.T)
    df2 = df['intensity']
    ilocs_max = argrelextrema(df.values, np.greater_equal, order=5)[0]
    ilocs_min = argrelextrema(df.values, np.less_equal, order=5)[0]
    #print(ilocs_max)
    minmaxsorted = np.sort(np.concatenate((ilocs_max, ilocs_min)))
    selected_peaks = []
    l = len(minmaxsorted)
    for index, obj in enumerate(minmaxsorted):
        if (index > 0) and (index < l-1):
            previous = df2[minmaxsorted[index-1]]
            current = df2[minmaxsorted[index]]
            next_ = df2[minmaxsorted[index+1]]
            ero = 300
            if (current > (previous+ero)) and (current > (next_+ero)):
                selected_peaks.append(minmaxsorted[index]) 
    
    mask = np.ones(len(spectra), bool)
    mask[selected_peaks] = 0
    spectra[mask] = 0
    return spectra

def single_group(current_intensities, shots):
    shot_idx = 0
    shot_groups = 0
    df = pd.DataFrame()
    grouped_shots = grouper(shots,current_intensities)
    for x in grouped_shots:
        shot_groups += 1
    highest_intensity , lowest_high_intensity = highLow_intensity(current_intensities)
    avg_std = pd.concat(current_intensities,axis=1).T.std(0).sum()/4094
    abs_dist = abs_from_mean(current_intensities)
    data = pd.concat(current_intensities,axis=1).T
    max_channel = data.idxmax(1)
    #print('---',len(current_intensities))
    kmeans = KMeans(n_clusters=shots).fit(current_intensities)

    for shot in current_intensities:
        peaks = peak_finder2(shot)

        df2 = pd.DataFrame({'shot_nr': [shot_idx+1],
                            'shot_group': [((len(current_intensities)+(shot_idx))//((len(current_intensities)//shot_groups))-shot_groups+1) if shot_groups > 1 else 1],
                            'highest_shot_nr': [highest_intensity[0]+1],
                            'highest_intensity': [shot.max()],
                            'highest_channel': [max_channel[shot_idx]],
                            'avg_std': [round(avg_std,2)],
                            'abs_dist_from_avg': [round(abs_dist[shot_idx],2)],
                            'recognized_peaks': [peaks[(peaks > 0)].count()],
                            'kmeans_group': [kmeans.labels_[shot_idx]],
                            })
        df = pd.concat([df,df2], ignore_index=True, axis=0)
        shot_idx += 1
    print(df)


def group_shots(current_intensities, shots):
    shot_idx = 0
    df = pd.DataFrame()
    grouped_shots = grouper(shots,current_intensities)
    for shot_group in grouped_shots:
        highest_intensity , lowest_high_intensity = highLow_intensity(shot_group)
        avg_std = pd.concat(shot_group,axis=1).T.std(0).sum()/4094
        abs_dist_all = abs_from_mean(shot_group, current_intensities)
        abs_dist_grp = abs_from_mean(shot_group)

        df2 = pd.DataFrame({'shot_group': [shot_idx+1],
                            'highest_shot_nr_in_grp': [highest_intensity[0]+1],
                            'highest_intensity': [highest_intensity[1].max()],
                            'lowest_high_shot_nr': [lowest_high_intensity[0]+1],
                            'lowest_high_intensity': [lowest_high_intensity[1].max()],
                            'avg_std': [round(avg_std,2)],
                            'grp_avg_abs_dist_from_all': [round(mean(abs_dist_all),2)],
                            'avg_abs_dist_from_grp': [round(mean(abs_dist_grp),2)],
                            })
        df = pd.concat([df,df2], ignore_index=True, axis=0)
        shot_idx += 1
    print(df)
    single_group(current_intensities,shots)