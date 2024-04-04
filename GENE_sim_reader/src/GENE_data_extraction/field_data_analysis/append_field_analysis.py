import numpy as np
from scipy.interpolate import interp1d



def complex_array_data_analysis(input_sim_df, field_name='phi'):
    # Copy the DataFrame to avoid modifying the original data
    sim_df = input_sim_df.copy()

    # Initialize columns for FFT and angle info
    sim_df[f'{field_name}_fft_info'] = None
    sim_df[f'{field_name}_angle_info'] = None

    # Iterate over rows using iterrows()
    for index, row in sim_df.iterrows():
        # Get the complex array data
        complex_array = row[field_name]

        if isinstance(complex_array, (list, np.ndarray)):
            # Calculate FFT and angle information
            freq_bins, relative_mag_counts = get_fft_mag_counts(complex_array)
            mean_freq, freq_lower_95, freq_upper_95 = histogram_stats(freq_bins, relative_mag_counts)

            angle_bins, relative_frequency = get_delta_angle_counts(complex_array)
            mean_angle, angle_lower_95, angle_upper_95 = histogram_stats(angle_bins, relative_frequency)



            # Assign the calculated data to the DataFrame
            sim_df.at[index, f'{field_name}_fft_info'] = {'fft_freq': freq_bins, 
                                                          'rel_mag': relative_mag_counts,
                                                          'ave_freq': mean_freq,
                                                          'lower_95_freq': freq_lower_95,
                                                          'upper_95_freq': freq_upper_95}
            
            sim_df.at[index, f'{field_name}_angle_info'] = {'angles': angle_bins, 
                                                            'rel_freq': relative_frequency,
                                                            'ave_angle': mean_angle,
                                                            'lower_95_angle': angle_lower_95,
                                                            'upper_95_angle': angle_upper_95}

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

