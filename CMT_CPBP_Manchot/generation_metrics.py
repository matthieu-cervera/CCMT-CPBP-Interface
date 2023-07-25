from collections import Counter
from msilib.schema import Error
from mgeval import core, utils
from music21 import *
from pprint import pprint
from scipy.spatial import distance
from sklearn.model_selection import LeaveOneOut

import copy
import numpy as np
import os
import pickle
import pretty_midi as pm
import time
import torch

FRAME_PER_BAR = 16
NUM_BAR = 8
NUM_TIME_STEP = FRAME_PER_BAR * NUM_BAR

ONSET_TOKEN = 2
HOLD_PITCH_TOKEN = 48
REST_PITCH_TOKEN = 49

NB_PITCH_CLASS = 12

C_MAJOR = [0, 2, 4, 5, 7, 9, 11]
C_NOTE = 0
A_NOTE = 9

################################################### RHYTHM METRICS ###################################################

def get_metrics_rhythm_NDBR_RPD(sampling_results_path):
    """
    Calculates the NDBR for the test and generated samples.
    Calculates the RPD.
    Calculates Top 10 bar rhythm patterns in test dataset with number of occurrences in test and generated samples respectively (e.g., 2262 | 2143)

    :sampling_results_path: folder path where all the .pkl files are for test and generated samples

    return                  prints the metrics
    """
    rhythm_distribution_test = {}
    rhythm_distribution_sample = {}

    for root, _ , files in os.walk(sampling_results_path, topdown=True):
        for file in files:
            if not file.endswith('.pkl'):
                continue
            if 'groundtruth' in file:
                _rhythm_patterns(os.path.join(root, file), rhythm_distribution_test)
            else:
                _rhythm_patterns(os.path.join(root, file), rhythm_distribution_sample)

    print('RHYTHM DISTRIBUTION')
    print(f'{len(rhythm_distribution_test.keys())} different bar rhythms in the test dataset')
    print(f'{len(rhythm_distribution_sample.keys())} different bar rhythms in the generated samples')
    print(f'{_jensen_shannon_divergence(rhythm_distribution_test, rhythm_distribution_sample):.5f} Jensen-Shannon divergence')
    print('\nTop 10 bar rhythm patterns in test dataset')
    c_test = Counter(rhythm_distribution_test)
    for k, v in c_test.most_common(10):
        print(f'{k} : {v} | {rhythm_distribution_sample.get(k, 0)}')
    print('')

def _rhythm_patterns(pkl_file, rhythm_distribution):
    with open(pkl_file, 'rb') as f:
        data = pickle.load(f)
        rhythm_data = data['rhythm']
        for i in range(0, len(rhythm_data) - (len(rhythm_data) % FRAME_PER_BAR), FRAME_PER_BAR):
            rhythm_key = tuple(rhythm_data[i:i+FRAME_PER_BAR])
            rhythm_distribution[rhythm_key] = rhythm_distribution.get(rhythm_key, 0) + 1

def _jensen_shannon_divergence(rhythm_distribution_test, rhythm_distribution_sample):
    all_rhythm_keys = set(list(rhythm_distribution_test.keys()) + list(rhythm_distribution_sample.keys()))
    rdt = []
    rds = []
    for rhythm_key in all_rhythm_keys:
        rdt.append(rhythm_distribution_test.get(rhythm_key, 0))
        rds.append(rhythm_distribution_sample.get(rhythm_key, 0))
    
    return distance.jensenshannon(rdt, rds, 2.0) ** 2

def get_metrics_rhythm_OTPD(sampling_results_path):
    """
    Calculates the OTPD.

    :sampling_results_path: folder path where all the .pkl files are for test and generated samples

    return                  prints results (mean and std) 
    """
    heatmaps_test = np.zeros(((FRAME_PER_BAR - 1), FRAME_PER_BAR))
    heatmaps_sample = np.zeros(((FRAME_PER_BAR - 1), FRAME_PER_BAR))
    total_test = [0] * (FRAME_PER_BAR - 1)
    total_sample = [0] * (FRAME_PER_BAR - 1)
    for root, _ , files in os.walk(sampling_results_path, topdown=True):
        for file in files:
            if not file.endswith('.pkl'):
                continue
    
            with open(os.path.join(root, file), 'rb') as f: 
                data = pickle.load(f)
                rhythm_data = data['rhythm']
                for i in range(0, len(rhythm_data) - (len(rhythm_data) % FRAME_PER_BAR), FRAME_PER_BAR):
                    rhythm_bar = rhythm_data[i:i+FRAME_PER_BAR]
                    rhythm_onset = rhythm_bar == ONSET_TOKEN
                    nb_onsets = rhythm_onset.sum()
                    if nb_onsets == 0 or nb_onsets == FRAME_PER_BAR:
                        continue
                    if 'groundtruth' in file:
                        heatmaps_test[nb_onsets - 1] = np.add(heatmaps_test[nb_onsets - 1], rhythm_onset)
                        total_test[nb_onsets - 1] += 1
                    else:
                        heatmaps_sample[nb_onsets - 1] = np.add(heatmaps_sample[nb_onsets - 1], rhythm_onset)
                        total_sample[nb_onsets - 1] += 1

    jsd_per_nb_notes = [0] * (FRAME_PER_BAR - 1)
    for i in range(FRAME_PER_BAR - 1):
        heatmaps_test[i] = heatmaps_test[i] / total_test[i]
        heatmaps_sample[i] = heatmaps_sample[i] / total_sample[i]
        jsd = distance.jensenshannon(heatmaps_test[i], heatmaps_sample[i], 2.0) ** 2
        jsd_per_nb_notes[i] = jsd
    
    
    for i in range(FRAME_PER_BAR - 1):
        print(f'{jsd_per_nb_notes[i]:.3f} ', end='')
    print('')
    print(f'JSD mean: {np.mean(jsd_per_nb_notes):.3f}')
    print(f'JSD std: {np.std(jsd_per_nb_notes):.3f}')
    print('')

def count_last_token_onset(sampling_results_path, nb_bars_group, on_test_dataset=False):
    """
    Calculates the ratio of bars where they last token is an onset token.

    :sampling_results_path: folder path where all the .pkl files are for test and generated samples
    :nb_bars_group:         number of bars that are constrained
    :on_test_dataset:       set to True to calculate the ratio of bars on the test samples

    return                  prints the results
    """
    total = 0
    total_bars = 0
    for root, _ , files in os.walk(sampling_results_path, topdown=True):
        for file in files:
            if not file.endswith('.pkl') or ('sample' if on_test_dataset else 'groundtruth') in file:
                continue
            with open(os.path.join(root, file), 'rb') as f:
                data = pickle.load(f)
                rhythm_data = data['rhythm']
                rhythm_data = rhythm_data[0:nb_bars_group*FRAME_PER_BAR]
                for i in range(0, len(rhythm_data) - (len(rhythm_data) % FRAME_PER_BAR), FRAME_PER_BAR):
                    total_bars += 1
                    rhythm_bar = rhythm_data[i:i+FRAME_PER_BAR]
                    if rhythm_bar[-1] == ONSET_TOKEN:
                        total += 1
    
    print(f'Total: {total / total_bars:.3f}')
    print('')

def get_metric_rhythm_patterns_top_k(sampling_results_path, topk, nb_bar_group):
    """
    Calculates Top k bar rhythm patterns being the i_th bar (used to generate the rhythm heatmaps).
    The frequency of each pattern is also shown next to its corresponding pattern.

    :sampling_results_path: folder path where all the .pkl files generated samples
    :topk:                  top k patterns to show
    :nb_bars_group:         number of bars that are constrained

    return                  prints the results
    """
    rhythm_distributions = []
    for i in range(nb_bar_group):
        rhythm_distributions.append({})

    for root, _ , files in os.walk(sampling_results_path, topdown=True):
            for file in files:
                if not file.endswith('.pkl') or not 'sample' in file:
                    continue
                with open(os.path.join(root, file), 'rb') as f:
                    data = pickle.load(f)
                    rhythm_data = data['rhythm']
                    for i in range(nb_bar_group):
                        rhythm_key = tuple(rhythm_data[i * FRAME_PER_BAR:(i + 1) * FRAME_PER_BAR])
                        rhythm_distributions[i][rhythm_key] = rhythm_distributions[i].get(rhythm_key, 0) + 1

    for i in range(nb_bar_group):
        print(f'Top {topk} Bar {i + 1}')
        counter = Counter(rhythm_distributions[i])
        for k, v in counter.most_common(topk):
            print(f'{k} : {v}')
    print('')

def get_metric_distribution_number_notes_per_bar(sampling_results_path):
    """
    Calculates the distribution of the number of notes per bar in the test and generated samples.

    :sampling_results_path: folder path where all the .pkl files are for test and generated samples

    return                  prints the metric
    """
    rhythm_distribution_test = {}
    rhythm_distribution_sample = {}

    for root, _ , files in os.walk(sampling_results_path, topdown=True):
        for file in files:
            if not file.endswith('.pkl'):
                continue
            if 'groundtruth' in file:
                _rhythm_patterns_by_onset_note(os.path.join(root, file), rhythm_distribution_test)
            else:
                _rhythm_patterns_by_onset_note(os.path.join(root, file), rhythm_distribution_sample)

    total_test = 0
    total_sample = 0
    print('    TEST   SAMPLE')
    for i in range(FRAME_PER_BAR + 1):
        count_test = rhythm_distribution_test.get(i, 0)
        count_sample = rhythm_distribution_sample.get(i, 0)
        print(f'{i:<2}: {count_test:<6} {count_sample:<6}')
        total_test += count_test
        total_sample += count_sample
    
    print(f'T : {total_test:<6} {total_sample:<6}\n')

def _rhythm_patterns_by_onset_note(pkl_file, rhythm_distribution):
    with open(pkl_file, 'rb') as f:
        data = pickle.load(f)
        rhythm_data = data['rhythm']
        for i in range(0, len(rhythm_data) - (len(rhythm_data) % FRAME_PER_BAR), FRAME_PER_BAR):
            bar = rhythm_data[i:i+FRAME_PER_BAR]
            onset_count = (bar == ONSET_TOKEN).sum()
            rhythm_distribution[onset_count] = rhythm_distribution.get(onset_count, 0) + 1

################################################### PITCH METRICS ###################################################

def get_metric_chord_tone_ratio(sampling_results_path, ctr_type, nb_bars_group):
    """
    Calculates the chord tone ratio for the test and generated samples.

    :sampling_results_path: folder path where all the .pkl files are for test and generated samples
    :ctr_type:              type of the chord tone ratio to calculate:
                            - 'ctr' is the general ctr calculated on all the melody notes
                            - 'ctr_1' is only calculated on notes on the first beat of a mesure
                            - 'ctr_last' is only calculated on notes from the last chord that is part of the constrained tokens
    :nb_bars_group:         number of bars that are constrained

    return                  prints the results for the test and generated samples
    """
    if not os.path.isdir(sampling_results_path):
        raise NotADirectoryError('Not a directory')

    metric_test = 0
    metric_sample = 0
    num_test = 0
    num_sample = 0
    for root, _ , files in os.walk(sampling_results_path):
        for file in files:
            if not file.endswith('.pkl'):
                continue
            
            try:
                if ctr_type.lower() == 'ctr':
                    metric = _chord_tone_ratio(os.path.join(root, file), False)
                elif ctr_type.lower() == 'ctr_1':
                    metric = _chord_tone_ratio(os.path.join(root, file), True)
                elif ctr_type.lower() == 'ctr_last':
                    metric = _chord_tone_ratio_last_chord(os.path.join(root, file), nb_bars_group)
                else:
                    raise Exception('not a valid chord tone ratio type')

                if 'groundtruth' in file:
                    metric_test += metric
                    num_test += 1
                else:
                    metric_sample += metric
                    num_sample += 1
            except ZeroDivisionError:
                pass
            except Exception as e:
                print(f'Error: {e}, {os.path.join(root, file)}')
    
    metric_test /= num_test * 100
    metric_sample /= num_sample * 100


    # print results
    if ctr_type.lower() == 'ctr':
        print('CHORD TONE RATIO')
    elif ctr_type.lower() == 'ctr_1':
        print('CHORD TONE RATIO 1ST BEAT')
    elif ctr_type.lower() == 'ctr_last':
        print('CHORD TONE RATIO LAST CHORD')
    else:
        raise Exception('Not a valid chord tone ratio type.')
    print('     test   sample')
    print(f'    ({metric_test:.3f}, {metric_sample:.3f})\n')

def _chord_tone_ratio(pkl_file, on_1st_beat=False):
    with open(pkl_file, 'rb') as f:
        data = pickle.load(f)
        pitch_data = data['pitch']
        chord_data = data['chord']

        ctr = 0
        num_notes = 0
        step = FRAME_PER_BAR if on_1st_beat else 1
        for i in range(0, NUM_TIME_STEP, step):
            # if hold or rest or no chord
            if pitch_data[i] == 48 or pitch_data[i] == 49 or len(chord_data[i].nonzero()[1]) == 0:
                continue
            num_notes += 1
            if (pitch_data[i] % 12) in chord_data[i].nonzero()[1]:
                ctr += 1
        
        return ctr / num_notes * 100

def _chord_tone_ratio_last_chord(pkl_file, nb_bars_group):
    with open(pkl_file, 'rb') as f:
        data = pickle.load(f)
        pitch_data = data['pitch']
        chord_data = data['chord']

        # find last chord
        last_chord_idx = -1
        last_chord = None
        for i in range((nb_bars_group * FRAME_PER_BAR) - 1, -1, -1):
            chord = list(chord_data[i].nonzero()[1])

            if not chord and last_chord is None:
                # The file is ignored in the chord tone ratio calculation.
                # This exception will be catched and ignored.
                raise ZeroDivisionError('Empty chord')

            if last_chord is None:
                last_chord = chord
            
            if last_chord != chord:
                break
            
            last_chord_idx = i

        if last_chord_idx == -1:
            raise Exception('Could not find last chord index')
        
        # calculate ctr on last chord only
        ctr = 0
        num_notes = 0
        for i in range(last_chord_idx, nb_bars_group * FRAME_PER_BAR):
            # if hold or rest or no chord
            if pitch_data[i] == 48 or pitch_data[i] == 49:
                continue
            num_notes += 1
            if (pitch_data[i] % 12) in chord_data[i].nonzero()[1]:
                ctr += 1
        
        return ctr / num_notes * 100

def heatmap_first_time_c_major_data(sampling_results_path, nb_bars_group, on_test_dataset=False):
    """
    Calculates the first occurrence of the notes of the C major scale within the span of constrained bars
    (used to generate the pitch heatmaps)

    :sampling_results_path: folder path where all the .pkl files are for test and generated samples
    :nb_bars_group:         number of bars that are constrained
    :on_test_dataset:       set to True to calculate the heatmap data on the test samples

    return                  prints the results
    """
    occ_c_major_samples = []
    for root, _ , files in os.walk(sampling_results_path, topdown=True):
        for file in files:
            if not file.endswith('.pkl') or ('sample' if on_test_dataset else 'groundtruth') in file:
                continue
            with open(os.path.join(root, file), 'rb') as f: 
                data = pickle.load(f)
                rhythm_data = data['rhythm']
                pitch_data = data['pitch']
                
                nb_tokens = nb_bars_group * FRAME_PER_BAR
                bar = rhythm_data[0:nb_tokens]
                onset_count = (bar == ONSET_TOKEN).sum()
                if onset_count < 2:
                    continue

                onset_idx_seen_count = 0
                occ_first_time = []
                for i in range(nb_tokens):
                    if pitch_data[i] == HOLD_PITCH_TOKEN or pitch_data[i] == REST_PITCH_TOKEN:
                        continue
                    pitch_class = pitch_data[i] % 12
                    if pitch_class not in occ_first_time:
                        if pitch_class in C_MAJOR:
                            prob = pow((1 - (1 / NB_PITCH_CLASS)), onset_idx_seen_count)
                            occ_c_major_samples.append((onset_idx_seen_count / (onset_count - 1), prob))
                        occ_first_time.append(pitch_class)

                    onset_idx_seen_count += 1

    occ_c_major_samples = sorted(occ_c_major_samples, key=lambda x: x[0])

    heatmap_data = [0] * 10
    bin_lowers = [0.0000, 0.1000, 0.2000, 0.3000, 0.4000, 0.5000, 0.6000, 0.7000, 0.8000, 0.9000]
    bin_uppers = [0.1000, 0.2000, 0.3000, 0.4000, 0.5000, 0.6000, 0.7000, 0.8000, 0.9000, 1.0001]
    heatmap_idx = 0
    for placement in occ_c_major_samples:
        while True:
            if bin_lowers[heatmap_idx] <= placement[0] and placement[0] < bin_uppers[heatmap_idx]:
                break
            heatmap_idx += 1
        heatmap_data[heatmap_idx] += 1 / placement[1]
    

    heatmap_data = list(map(int, heatmap_data))

    dataset = 'test' if on_test_dataset else 'sample'
    print(f'{dataset} pitch first occ heatmap: {nb_bars_group}')
    print(heatmap_data)
    print('')

################################################### MGEVAL METRICS ###################################################

def get_mgeval_metrics(sampling_results_path, output_path, num_samples, max_samples=3150):
    """
    Calculates the MGEval framework's absolute measures and inter-set metrics
    ***The metrics is calculated using MIDI (.mid) files***

    :sampling_results_path: folder path where all the .mid files are for test and generated samples
    :output_path:           output path where the file containing the results will be created
    :num_samples:           number of samples to use in each of the dataset
    :max_samples:           upper index limit (excluded) of the samples that can be chosen in the num_samples samples

    return                  creates a file containing the results
    """
    SEED = 42
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    np.random.seed(SEED)

    if os.path.exists(output_path):
        raise OSError(f'Error: {output_path} already exist')

    start_total = time.time()

    sub_sample = np.random.choice(max_samples, num_samples, replace=False)

    set1 = []
    set2 = []
    for root, _ , files in os.walk(sampling_results_path, topdown=True):
        for file in files:
            if not file.endswith('.mid'):
                continue
            if 'sample' in file:
                if int(file.split('sample')[1][:-4]) in sub_sample:
                    set1.append(os.path.join(root, file))
            elif int(file.split('groundtruth')[1][:-4]) in sub_sample:
                set2.append(os.path.join(root, file))

    if not any(set1) or not any(set2):
        print("Error: set empty")
        exit()

    num_samples = min(len(set2), len(set1))
    print(f'num_samples: {num_samples}')

    # Initialize Evaluation Set
    evalset = {
        'total_used_pitch': np.zeros((num_samples, 1)),
        'bar_used_pitch': np.zeros((num_samples, NUM_BAR, 1)),
        'pitch_range': np.zeros((num_samples, 1)),
        'avg_pitch_shift': np.zeros((num_samples, 1)),
        'total_pitch_class_histogram': np.zeros((num_samples, 12)),
        'bar_pitch_class_histogram': np.zeros((num_samples, NUM_BAR, 12)),
        'pitch_class_transition_matrix': np.zeros((num_samples, 12, 12)),

        'total_used_note': np.zeros((num_samples, 1)),
        'bar_used_note': np.zeros((num_samples, NUM_BAR, 1)),
        'avg_IOI': np.zeros((num_samples, 1)),
        'note_length_hist': np.zeros((num_samples, 12)),
        'note_length_transition_matrix': np.zeros((num_samples, 12, 12))
            }
    metrics_list = list(evalset.keys())
    key_abbreviated = {
            'total_used_pitch': 'PC',
            'pitch_range': 'PR',
            'avg_pitch_shift': 'PI',
            'avg_IOI': 'IOI',
            'total_used_note': 'NC',
            'bar_used_pitch': 'PC/bar',
            'bar_used_note': 'NC/bar',
            'total_pitch_class_histogram': 'PCH',
            'bar_pitch_class_histogram': 'PCH/bar',
            'note_length_hist': 'NLH',
            'pitch_class_transition_matrix': 'PCTM',
            'note_length_transition_matrix': 'NLTM' 
            }
    absolute_metrics = ['PC', 'NC', 'PR', 'PI', 'IOI']

    bar_metrics = [ 'bar_used_pitch', 'bar_used_note', 'bar_pitch_class_histogram' ]

    single_arg_metrics = (
        [ 'total_used_pitch'
        , 'avg_IOI'
        , 'total_pitch_class_histogram'
        , 'pitch_range'
        ])

    set1_eval = copy.deepcopy(evalset)
    set2_eval = copy.deepcopy(evalset)

    sets = [(set1, set1_eval), (set2, set2_eval)]

    print('Calculating Features')
    start_time = time.time()

    # Extract Features
    for _set, _set_eval in sets:
        for i in range(0, num_samples):
            feature = core.extract_feature(_set[i])
            for metric in metrics_list:
                evaluator = getattr(core.metrics(), metric)
                if metric in single_arg_metrics:
                    tmp = evaluator(feature)
                elif metric in bar_metrics:
                    if metric == 'bar_pitch_class_histogram':
                        tmp = evaluator(feature, 0, NUM_BAR)
                    else:
                        tmp = evaluator(feature, 1, NUM_BAR)
                else:
                    tmp = evaluator(feature, 1)
                _set_eval[metric][i] = tmp
    
    print(f'{int(time.time() - start_time)}s')
    print('Calculating Intra-set Metrics')
    start_time = time.time()

    # Intra-set distances
    loo = LeaveOneOut()
    loo.get_n_splits(np.arange(num_samples))
    set1_intra = np.zeros((num_samples, len(metrics_list), num_samples - 1))
    set2_intra = np.zeros((num_samples, len(metrics_list), num_samples - 1))

    for i, metric in enumerate(metrics_list):
        for train_index, test_index in loo.split(np.arange(num_samples)):
            set1_intra[test_index[0]][i] = utils.c_dist(
                set1_eval[metrics_list[i]][test_index], set1_eval[metrics_list[i]][train_index])
            set2_intra[test_index[0]][i] = utils.c_dist(
                set2_eval[metrics_list[i]][test_index], set2_eval[metrics_list[i]][train_index])

    print(f'{int(time.time() - start_time)}s')
    print('Calculating Inter-set Metrics')
    start_time = time.time()

    # Inter-set distances
    loo = LeaveOneOut()
    loo.get_n_splits(np.arange(num_samples))
    sets_inter = np.zeros((num_samples, len(metrics_list), num_samples))

    for i, metric in enumerate(metrics_list):
        for train_index, test_index in loo.split(np.arange(num_samples)):
            sets_inter[test_index[0]][i] = utils.c_dist(set1_eval[metric][test_index], set2_eval[metric])

    plot_set1_intra = np.transpose(
        set1_intra, (1, 0, 2)).reshape(len(metrics_list), -1)
    plot_set2_intra = np.transpose(
        set2_intra, (1, 0, 2)).reshape(len(metrics_list), -1)
    plot_sets_inter = np.transpose(
        sets_inter, (1, 0, 2)).reshape(len(metrics_list), -1)

    print(f'{int(time.time() - start_time)}s')

    print('Calculating Metrics')
    start_time = time.time()

    output_file = open(output_path, 'w')
    output_file.write('			 Test dataset			     CMTCP dataset\n')
    output_file.write('		  Absolute measure	  Absolute measure     Inter-set\n')
    output_file.write('			Mean     STD	  	Mean     STD	  KLD      OA\n')

    for i, metric in enumerate(metrics_list):
        # absolute measurement
        mean_set1 = np.mean(set1_eval[metric], axis=0)
        std_set1 = np.std(set1_eval[metric], axis=0)
        mean_set2 = np.mean(set2_eval[metric], axis=0)
        std_set2 = np.std(set2_eval[metric], axis=0)
        
        # inter-set distances
        kl2 = utils.kl_dist(plot_set2_intra[i], plot_sets_inter[i]) # (test, test), (CMT, test)
        ol2 = utils.overlap_area(plot_set2_intra[i], plot_sets_inter[i])

        # write in file
        output_file.write(f'{key_abbreviated[metric]:<12}')

        output_file.write(f'{mean_set2.item():<9.3f}' if key_abbreviated[metric] in absolute_metrics else '----     ')
        output_file.write(f'{std_set2.item():<11.3f}' if key_abbreviated[metric] in absolute_metrics else '----       ')

        output_file.write(f'{mean_set1.item():<9.3f}' if key_abbreviated[metric] in absolute_metrics else '----     ')
        output_file.write(f'{std_set1.item():<9.3f}' if key_abbreviated[metric] in absolute_metrics else '----     ')

        output_file.write(f'{kl2.item():<9.3f}')
        output_file.write(f'{ol2:<9.3f}')

        output_file.write('\n')

    output_file.close()
    
    print(f'{int(time.time() - start_time)}s')
    print(f'Total time: {int(time.time() - start_total)}s')

sample_path = r'path\path\path\generated_folder_files'
mgeval_output = r'output\path\path\mgeval'
nb_bars_constrained = 8
# get_metrics_rhythm_NDBR_RPD(sample_path)
# get_metrics_rhythm_OTPD(sample_path)
# count_last_token_onset(sample_path, nb_bars_constrained, False)
# count_last_token_onset(sample_path, nb_bars_constrained, True)
# get_metric_rhythm_patterns_top_k(sample_path, 10, nb_bars_constrained)
# get_metric_distribution_number_notes_per_bar(sample_path)
# get_mgeval_metrics(sample_path, mgeval_output, 500)

# get_metric_chord_tone_ratio(sample_path, 'ctr', nb_bars_constrained)
# get_metric_chord_tone_ratio(sample_path, 'ctr_1', nb_bars_constrained)
# get_metric_chord_tone_ratio(sample_path, 'ctr_last', nb_bars_constrained)
# heatmap_first_time_c_major_data(sample_path, nb_bars_constrained, False)
# heatmap_first_time_c_major_data(sample_path, nb_bars_constrained, True)