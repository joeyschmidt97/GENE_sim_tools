import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from GENE_sim_tools.sims_to_df.src.dict_field_data import field_filepath_to_dict
from GENE_sim_tools.sims_to_df.src.utils.file_functions import switch_suffix_file



def complex_array_resolution_analysis(input_sim_df, field_name='field_phi'):
    sim_df = input_sim_df.copy()


    sim_df['diff_abs'] = None
    sim_df['corr_len'] = None

    # Prepare columns for storing FFT and angle info
    sim_df[f'{field_name}_fft_freq'] = None
    sim_df[f'{field_name}_rel_mag'] = None
    sim_df[f'{field_name}_ave_freq'] = None
    sim_df[f'{field_name}_lower_95_freq'] = None
    sim_df[f'{field_name}_upper_95_freq'] = None

    sim_df[f'{field_name}_angles'] = None
    sim_df[f'{field_name}_rel_freq'] = None
    sim_df[f'{field_name}_ave_angle'] = None
    sim_df[f'{field_name}_lower_95_angle'] = None
    sim_df[f'{field_name}_upper_95_angle'] = None



    for index, row in sim_df.iterrows():  

        gamma = row['gamma']
        if pd.notna(gamma): 
        
            if (gamma > 0):
                diff_abs_value, corr_len_value =  get_row_field_quantities(row)
                sim_df.at[index, 'diff_abs'] = diff_abs_value
                sim_df.at[index, 'corr_len'] = corr_len_value

            
            if field_name not in sim_df.columns:
                field_path = switch_suffix_file(row['filepath'], 'field')
                field_dict = field_filepath_to_dict(field_path)
                complex_array = field_dict[field_name]
            else:
                complex_array = row[field_name]        
            
            # Calculate FFT and angle information
            freq_bins, relative_mag_counts = get_fft_mag_counts(complex_array)
            mean_freq, freq_lower_95, freq_upper_95 = histogram_stats(freq_bins, relative_mag_counts)

            angle_bins, relative_frequency = get_delta_angle_counts(complex_array)
            mean_angle, angle_lower_95, angle_upper_95 = histogram_stats(angle_bins, relative_frequency)

            # Assign the calculated data to individual columns in the DataFrame
            sim_df.at[index, f'{field_name}_fft_freq'] = freq_bins
            sim_df.at[index, f'{field_name}_rel_mag'] = relative_mag_counts
            sim_df.at[index, f'{field_name}_ave_freq'] = mean_freq
            sim_df.at[index, f'{field_name}_lower_95_freq'] = freq_lower_95
            sim_df.at[index, f'{field_name}_upper_95_freq'] = freq_upper_95

            sim_df.at[index, f'{field_name}_angles'] = angle_bins
            sim_df.at[index, f'{field_name}_rel_freq'] = relative_frequency
            sim_df.at[index, f'{field_name}_ave_angle'] = mean_angle
            sim_df.at[index, f'{field_name}_lower_95_angle'] = angle_lower_95
            sim_df.at[index, f'{field_name}_upper_95_angle'] = angle_upper_95

    return sim_df




def histogram_stats(x_bins, y_rel_freq):

    # Weighted average (mean angle)
    mean_x = np.average(x_bins, weights=y_rel_freq)

    # Bootstrapping to estimate 95% confidence interval
    bootstrap_means = []
    for _ in range(1000):  # number of bootstrap samples
        sample_indices = np.random.choice(np.arange(len(x_bins)), size=len(x_bins), replace=True, p=y_rel_freq)
        sample = x_bins[sample_indices]
        bootstrap_means.append(np.mean(sample))

    x_lower_95 = np.percentile(bootstrap_means, 2.5)
    x_upper_95 = np.percentile(bootstrap_means, 97.5)

    return mean_x, x_lower_95, x_upper_95





def get_delta_angle_counts(complex_num_array: np.ndarray, output_length: int = 100):
    # Compute the vector differences between consecutive complex numbers to get direction vectors
    vectors = np.diff(complex_num_array)

    angles = []
    for v1, v2 in zip(vectors[:-1], vectors[1:]):
        if np.isclose(np.abs(v1), 0) or np.isclose(np.abs(v2), 0):
            angles.append(0)
        else:
            angle = np.angle(v1/v2)
            angles.append(angle)


    angles = np.array(angles)
    angles = np.abs(angles)

    # Compute histogram of angles with the specified number of bins
    counts, bin_edges = np.histogram(angles, bins=output_length)

    # Calculate the relative frequency of each bin
    relative_angle_counts = counts / counts.sum()

    # Use the bin centers as the representative angle for each bin
    angle_bins = (bin_edges[:-1] + bin_edges[1:]) / 2

    return angle_bins, relative_angle_counts








def get_fft_mag_counts(complex_num_array: np.ndarray, output_length: int = 100):
    # Compute the Fourier transform
    fft_result = np.fft.fft(complex_num_array)

    # Get frequencies and magnitudes
    freq = np.fft.fftfreq(len(complex_num_array))
    magnitude = np.abs(fft_result)

    # Use only the positive part of the frequency spectrum for interpolation
    positive_freq_indices = np.where(freq >= 0)
    positive_freqs = freq[positive_freq_indices]
    positive_magnitudes = magnitude[positive_freq_indices]

    # Interpolate to get a uniform distribution of 100 points
    interp_func = interp1d(positive_freqs, positive_magnitudes, kind='linear')
    freq_bins = np.linspace(positive_freqs[0], positive_freqs[-1], output_length)
    interpolated_magnitudes = interp_func(freq_bins)

    # Normalize the magnitudes to get relative counts
    total_magnitude = np.sum(interpolated_magnitudes)
    if total_magnitude > 0:
        relative_mag_counts = interpolated_magnitudes / total_magnitude
    else:
        relative_mag_counts = np.zeros_like(interpolated_magnitudes)

    return freq_bins, relative_mag_counts





import os
import subprocess

def get_row_field_quantities(sim_df_row):

    param_filepath = sim_df_row['filepath']
    dir_filepath = os.path.dirname(param_filepath)
    suffix = sim_df_row['suffix']

    os.chdir(dir_filepath)

    # Get the full path to the script
    script_path = os.path.abspath('/global/homes/j/joeschm/tools/IFS_scripts/plot_mode_structures.py')
    result = subprocess.run(['python3', script_path, suffix, '-e', '-b'], stdout=subprocess.PIPE)  # Run the script with the specified arguments

    # Get the stdout as a string
    output = result.stdout.decode('utf-8')

    # Find the line that contains the "diff/abs" value
    diff_abs_line = [line for line in output.split('\n') if 'diff/abs' in line][0]
    diff_abs_value = float(diff_abs_line.split()[-1])   # Extract the numerical value from the line
    
    # Find the line that contains the "corr_len" value
    corr_len_line = [line for line in output.split('\n') if 'correlation length (for phi):' in line][0]
    corr_len_value = float(corr_len_line.split()[-1])   # Extract the numerical value from the line

    return diff_abs_value, corr_len_value
