import struct
import numpy as np
from os.path import getsize

from GENE_sim_tools.sims_to_df.src.utils.file_functions import switch_suffix_file, file_checks, FileError
from GENE_sim_tools.sims_to_df.src.GENE_data_extraction.dict_parameters_data import parameters_filepath_to_dict



def field_filepath_to_dict(field_filepath:str, field_quantities:list=None, time_criteria='last'):

    try:
        file_checks(field_filepath, filetype='field')

        field_dict = create_field_dict(field_filepath, field_quantities, time_criteria)
        flattened_field_dict = {key: value[0] for key, value in field_dict.items()}

        return flattened_field_dict

    except FileError as e:
        print(e)



    return 







def create_field_dict(field_filepath:str, field_quantities:list=None, time_criteria='last'):
    """
    Reads field data from a binary file and returns a dictionary containing relevant information.

    Args:
    - field_filepath (str): The path to the field binary file.
    - choose_time (str, float, int, list): Specifies the time instance(s) to extract. Options:
        - 'last': Extracts data at the last available time.
        - 'first': Extracts data at the first available time.
        - float, int: Extracts data at the specified time value.
        - list: Extracts data for the specified time range [start_time, end_time].
    - named_field_col (str, list): Specifies the field column(s) to extract. Options:
        - 'all': Extracts all fields.
        - str: Extracts the specified field column (phi OR apar OR bpar).
        - list: Extracts multiple specified field columns (i.e. ['phi', 'bpar']).
    - time_option (str): toggles time between 'ABS' (absolute) or 'REL' (relative) time - doesn't affect output time added to nrg_dict
        - 'ABS': absolute time given by simulation 
        - 'REL': relative time scaled between [0,1]... useful to compare many simulations with different simulation times
    Returns:
    - dict: A dictionary containing field data and relevant information.
    """

    # Initializing the field dictionary with default values
    field_dict = {}

    if time_criteria=='all':
        time_criteria = {'bounds': [float('-inf'), float('inf')], 'logic_op_list': ['>', '<']}
    elif time_criteria=='last':
        time_criteria = {'bounds': 'last', 'logic_op_list': ['>', '<']}


    parameter_filepath = switch_suffix_file(field_filepath, 'parameters')
    param_dict = parameters_filepath_to_dict(parameter_filepath)
    if field_quantities is None:
        beta = param_dict['beta']
        bpar = param_dict.get('bpar', False)

        field_quantities = ['phi']
        if beta > 0:
            field_quantities.append('apar')
            if bpar:
                field_quantities.append('bpar')

    # Reading binary field data
    with open(field_filepath, 'rb') as file:
        # Extracting parameters from the parameter dictionary
        nx, ny, nz, n_fields, precision, endianness = (
            param_dict['nx0'],
            param_dict['nky0'],
            param_dict['nz0'],
            param_dict['n_fields'],
            param_dict['PRECISION'],
            param_dict['ENDIANNESS']
        )

        # Setting sizes based on precision
        intsize = 4
        realsize = 8 if precision == 'DOUBLE' else 4
        complexsize = 2 * realsize
        entrysize = nx * ny * nz * complexsize
        leapfld = n_fields * (entrysize + 2 * intsize)

        # Creating NumPy dtype for complex numbers based on precision
        complex_dtype = np.dtype(np.complex64) if precision == 'SINGLE' else np.dtype(np.complex128)

        # Setting the format string based on endianness and precision
        format_string = '>' if endianness == 'BIG' else '='
        format_string += 'ifi' if precision == 'SINGLE' else 'idi'
        timeentry = struct.Struct(format_string)
        timeentry_size = timeentry.size


        # Extracting time values from field file
        all_time_values = []
        for _ in range(int(getsize(field_filepath) / (leapfld + timeentry_size))):
            time = float(timeentry.unpack(file.read(timeentry_size))[1])
            file.seek(leapfld, 1)
            all_time_values.append(time)


        # Handling different time extraction options
        if time_criteria['bounds'] == 'last':
            time_index_list = [all_time_values.index(max(all_time_values))]
        elif time_criteria['bounds'] == 'first':
            time_index_list = [all_time_values.index(min(all_time_values))]
        elif isinstance(time_criteria['bounds'], list) and len(time_criteria['bounds']) == 2:
            start_time, end_time = time_criteria['bounds']
            
            time_index_list = [time_ind for time_ind, time in enumerate(all_time_values) if start_time <= time <= end_time]
        else:
            raise ValueError(f'Ensure choose time is given as "last", "first", a float, or a range "1 < time < 2"')


        # Add time values given choose_time value(s)
        field_dict['time'] = [all_time_values[time_ind] for time_ind in time_index_list]
        if field_dict['time'] == []:
            return {}
        

        # cycle through time values
        for time_index in time_index_list:

            # cycle through field names from named_field_col above
            for field_name in field_quantities:
                ind = field_quantities.index(field_name) # get index of field name (phi -> 0, apar -> 1, bpar -> 2)
                # calculate offset in field file to retrieve said data
                offset = timeentry_size + time_index * (timeentry_size + leapfld) + ind * (
                            entrysize + 2 * intsize) + intsize

                file.seek(offset)

                data_array = np.fromfile(file, count=nx * ny * nz, dtype=complex_dtype).reshape(nz, ny, nx)
                flat_data_array, zgrid = data_array_flattened(data_array, nz, nx)
                rescaled_array = rescale_array(flat_data_array, param_dict=param_dict)

                # Appending field data into field dict
                field_dict.setdefault(field_name, []).append(rescaled_array)
                field_dict.setdefault('zgrid', []).append(zgrid)

    return field_dict







def data_array_flattened(data_array, nz, nx):

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






def rescale_array(original_array, param_dict:dict):

    array_rescaled = np.zeros(len(original_array),dtype='complex128')
    
    nx = param_dict['nx0']
    half_nx_int = int(nx/2)
    nz = param_dict['nz0']

    phase_fac = -np.e**(-2.0*np.pi*(0.0+1.0J)*param_dict['n0_global']*param_dict['q0'])

    for i in range(half_nx_int):

        lower_end = (i+half_nx_int)*nz
        upper_end = (i+half_nx_int+1)*nz

        array_rescaled[lower_end:upper_end] = original_array[lower_end:upper_end]*phase_fac**i

        lower_end_neg = (half_nx_int-i-1)*nz
        upper_end_neg = (half_nx_int-i)*nz

        array_rescaled[lower_end_neg:upper_end_neg] = original_array[lower_end_neg:upper_end_neg]*phase_fac**(-(i+1))
    
    return array_rescaled



