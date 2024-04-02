import xarray as xr
import pandas as pd
import math


from GENE_sim_tools.GENE_sim_reader.src.utils.file_functions import string_to_list, switch_suffix_file
from GENE_sim_tools.GENE_sim_reader.src.utils.find_buried_filetypes import find_buried_filetypes

from GENE_sim_tools.GENE_sim_reader.src.GENE_data_extraction.dict_parameters_data import parameters_filepath_to_dict, create_species_tuple
from GENE_sim_tools.GENE_sim_reader.src.GENE_data_extraction.dict_omega_data import omega_filepath_to_dict
from GENE_sim_tools.GENE_sim_reader.src.GENE_data_extraction.dict_nrg_data import nrg_filepath_to_dict
from GENE_sim_tools.GENE_sim_reader.src.GENE_data_extraction.dict_field_data import field_filepath_to_dict




def filepath_to_sim_xarray(input_filepath:str):
    filepath_list = string_to_list(input_filepath)

    # Search for 'parameters' files up to a specified depth
    max_depth = 3
    parameter_filepath_list = find_buried_filetypes(filepath_list, 'parameters', max_depth)

    simulation_output_data = []
    parameters_data = []

    for parameters_path in parameter_filepath_list:
        parameters_dict = parameters_filepath_to_dict(parameters_path)
        spec_tuple, _ = create_species_tuple(parameters_dict)
        parameters_dict = rename_num_quantity_to_spec_name(parameters_dict, spec_tuple)
        parameters_data.append(parameters_dict)

        sim_output_dict = {}

        omega_path = switch_suffix_file(parameters_path, 'omega')
        omega_dict = omega_filepath_to_dict(omega_path)

        if not all(math.isnan(value) for value in omega_dict.values()):
            sim_output_dict.update(omega_dict)

            nrg_path = switch_suffix_file(parameters_path, 'nrg')
            nrg_dict = nrg_filepath_to_dict(nrg_path)
            sim_output_dict.update(nrg_dict)


            sim_output_dict = rename_num_quantity_to_spec_name(sim_output_dict, spec_tuple)
    
        simulation_output_data.append(sim_output_dict)

    # Convert to DataFrame
    parameters_df = pd.DataFrame(parameters_data)
    simulations_df = pd.DataFrame(simulation_output_data)

    # Convert to xarray Dataset
    xr_ds = xr.Dataset.from_dataframe(simulations_df)
    for column in parameters_df.columns:
        xr_ds = xr_ds.assign_coords({column: ('index', parameters_df[column].values)})

    return xr_ds






def rename_num_quantity_to_spec_name(input_dict:dict, spec_tuple):

    # Generate a new list with updated keys
    renamed_dict = {}
    for key, value in input_dict.items():
        if key[-1].isdigit(): #note [1,2,3] generated from range(n_spec) where n_spec=3
            for spec_name, spec_num in spec_tuple:
                if int(key[-1]) == spec_num:
                    renamed_key = f"{key[:-1]}_{spec_name}"
                    renamed_dict[renamed_key] = value
        else:
            renamed_dict[key] = value

    return renamed_dict