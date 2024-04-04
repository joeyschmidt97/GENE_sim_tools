import xarray as xr
import pandas as pd
import math


from GENE_sim_tools.sims_to_df.src.utils.file_functions import string_to_list, switch_suffix_file
from GENE_sim_tools.sims_to_df.src.utils.find_buried_filetypes import find_buried_filetypes

from GENE_sim_tools.sims_to_df.src.GENE_data_extraction.dict_parameters_data import parameters_filepath_to_dict
from GENE_sim_tools.sims_to_df.src.GENE_data_extraction.dict_omega_data import omega_filepath_to_dict
from GENE_sim_tools.sims_to_df.src.GENE_data_extraction.dict_nrg_data import nrg_filepath_to_dict
from GENE_sim_tools.sims_to_df.src.GENE_data_extraction.dict_field_data import field_filepath_to_dict






def filepath_to_sim_df(input_filepath:str):
    filepath_list = string_to_list(input_filepath)

    # Search for 'parameters' files up to a specified depth
    max_depth = 3
    parameter_filepath_list = find_buried_filetypes(filepath_list, 'parameters', max_depth)

    simulation_output_data = []
    parameters_data = []

    for parameters_path in parameter_filepath_list:
        parameters_dict = parameters_filepath_to_dict(parameters_path)
        parameters_data.append(parameters_dict)

        sim_output_dict = {}
        omega_path = switch_suffix_file(parameters_path, 'omega')
        omega_dict = omega_filepath_to_dict(omega_path)

        if not all(math.isnan(value) for value in omega_dict.values()):
            sim_output_dict.update(omega_dict)

            nrg_path = switch_suffix_file(parameters_path, 'nrg')
            nrg_dict = nrg_filepath_to_dict(nrg_path)
            sim_output_dict.update(nrg_dict)

            field_path = switch_suffix_file(parameters_path, 'field')
            field_dict = field_filepath_to_dict(field_path)
            sim_output_dict.update(field_dict)

        simulation_output_data.append(sim_output_dict)

    # Convert to DataFrame
    parameters_df = pd.DataFrame(parameters_data)
    simulations_df = pd.DataFrame(simulation_output_data)

    merged_df = pd.concat([parameters_df, simulations_df], axis=1)

    return merged_df




