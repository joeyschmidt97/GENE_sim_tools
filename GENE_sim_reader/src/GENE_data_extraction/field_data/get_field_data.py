import numpy as np
from typing import Tuple, Dict




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







import numpy as np
from scipy.interpolate import interp1d

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

