import xarray as xr
import numpy as np
import pandas as pd

from GENE_sim_tools.GENE_sim_reader.src.utils.file_functions import suffix_from_filename, string_to_list, switch_suffix_file
from GENE_sim_tools.GENE_sim_reader.src.utils.find_buried_filetypes import find_buried_filetypes

from GENE_sim_tools.GENE_sim_reader.src.dict_parameters_data import parameters_filepath_to_dict
from GENE_sim_tools.GENE_sim_reader.src.dict_omega_data import omega_filepath_to_dict
from GENE_sim_tools.GENE_sim_reader.src.dict_nrg_data import nrg_filepath_to_dict
from GENE_sim_tools.GENE_sim_reader.src.dict_field_data import field_filepath_to_dict



def filepath_to_sim_xarray(input_filepath):

    filepath_list = string_to_list(input_filepath)

    # Search for 'parameters' files up to a specified depth
    max_depth = 3
    parameter_filepath_list = find_buried_filetypes(filepath_list, 'parameters', max_depth)

    simulations_data = []

    for parameters_path in parameter_filepath_list:
        parameters_dict = parameters_filepath_to_dict(parameters_path)

        omega_path = switch_suffix_file(parameters_path, 'omega')
        omega_dict = omega_filepath_to_dict(omega_path)

        nrg_path = switch_suffix_file(parameters_path, 'nrg')
        nrg_dict = nrg_filepath_to_dict(nrg_path)

        field_path = switch_suffix_file(parameters_path, 'field')
        field_dict = field_filepath_to_dict(field_path)


        sim_dict = parameters_dict.copy()  # Start with a copy of the first dictionary to avoid modifying it directly
        sim_dict.update(omega_dict)
        sim_dict.update(nrg_dict)
        sim_dict.update(field_dict)

        flattened_sim_dict = {
            key: value[0] if (isinstance(value, list) or isinstance(value, np.ndarray)) and len(value) == 1 else value
            for key, value in sim_dict.items()
        }


        simulations_data.append(flattened_sim_dict)
        

    sim_df = pd.DataFrame(simulations_data)

    return sim_df