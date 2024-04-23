
import numpy as np






import numpy as np
import pandas as pd

def flatten_sim_arrays(input_sim_df):
    sim_df = input_sim_df.copy()

    # # Function to flatten the array and generate a zgrid (example implementation)
    # def data_array_flattened(array):
    #     # Example of flattening an array and creating a zgrid
    #     flat_array = array.flatten()
    #     zgrid = np.arange(len(flat_array))  # Example zgrid
    #     return flat_array, zgrid

    # Loop through each column that needs to be flattened
    for column in ['field_phi', 'field_apar', 'field_bpar']:
        if column in sim_df.columns:
            flat_arrays = []
            zgrids = []
            for index, row in sim_df.iterrows():
                if isinstance(row[column], np.ndarray):
                    flat_array, zgrid = data_array_flattened(row, column)
                    flat_arrays.append(flat_array)
                    zgrids.append(zgrid)
                else:
                    flat_arrays.append(row[column])
                    zgrids.append(np.nan)  # or some default value for non-array rows

            sim_df[column] = flat_arrays
            sim_df['zgrid'] = zgrids  # Add a new column for zgrid

    return sim_df



# #------------------------------------------------------------------------------------------------
# # Functions to prepare complex numbers for plotting----------------------------------------------
# #------------------------------------------------------------------------------------------------

def data_array_flattened(sim_df, array_name, time_ind=0):

    data_array = np.array(sim_df[array_name][time_ind])
    nz = sim_df['nz0']
    nx = sim_df['nx0']

    dz = float(2.0)/float(nz)
    ntot = nz*nx
    zgrid = np.arange(ntot)/float(ntot-1)*(2*nx-dz)-nx


    flattened_array = np.zeros(nz*nx,dtype='complex128')
    half_nx_int = int(nx/2)

    for i in range(half_nx_int):

        lower_end = (i+half_nx_int)*nz
        upper_end = (i+half_nx_int+1)*nz
        
        flattened_array[lower_end:upper_end] = data_array[:,0,i]

        lower_end_neg = (half_nx_int-i-1)*nz
        upper_end_neg = (half_nx_int-i)*nz

        flattened_array[lower_end_neg:upper_end_neg] = data_array[:,0,-1-i]

    half_nz_int = int(nz/2)
    rescaled_flattened_array = flattened_array/data_array[half_nz_int,0,0]

    return rescaled_flattened_array, zgrid



def rescale_array(original_array, sim_df):

    array_rescaled = np.zeros(len(original_array),dtype='complex128')
    
    nx = sim_df['nx0'][0]
    half_nx_int = int(nx/2)
    nz = sim_df['nz0'][0]

    phase_fac = -np.e**(-2.0*np.pi*(0.0+1.0J)*sim_df['n0_global'][0]*sim_df['q0'][0])

    for i in range(half_nx_int):

        lower_end = (i+half_nx_int)*nz
        upper_end = (i+half_nx_int+1)*nz

        array_rescaled[lower_end:upper_end] = original_array[lower_end:upper_end]*phase_fac**i

        lower_end_neg = (half_nx_int-i-1)*nz
        upper_end_neg = (half_nx_int-i)*nz

        array_rescaled[lower_end_neg:upper_end_neg] = original_array[lower_end_neg:upper_end_neg]*phase_fac**(-(i+1))
    
    return array_rescaled





