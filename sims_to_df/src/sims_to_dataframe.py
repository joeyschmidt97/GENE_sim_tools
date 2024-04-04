import os
import pandas as pd
import numpy as np
import math
from ast import literal_eval

from GENE_sim_tools.sims_to_df.src.utils.file_functions import string_to_list, switch_suffix_file
from GENE_sim_tools.sims_to_df.src.utils.find_buried_filetypes import find_buried_filetypes

from GENE_sim_tools.sims_to_df.src.dict_parameters_data import parameters_filepath_to_dict
from GENE_sim_tools.sims_to_df.src.dict_omega_data import omega_filepath_to_dict
from GENE_sim_tools.sims_to_df.src.dict_nrg_data import nrg_filepath_to_dict
from GENE_sim_tools.sims_to_df.src.dict_field_data import field_filepath_to_dict


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








def save_df_to_parquet(input_sim_df: pd.DataFrame, save_directory: str, filename: str = 'sim_df.parquet'):
    # Identify and drop columns that contain arrays or lists
    columns_to_drop = [col for col in input_sim_df.columns if any(isinstance(x, (list, np.ndarray)) for x in input_sim_df[col])]
    columns_to_drop.append('time')
    columns_to_drop.sort()

    # Print the columns that will be dropped
    print("Dropping columns containing arrays or lists:", columns_to_drop)

    # Drop the identified columns
    input_sim_df = input_sim_df.drop(columns=columns_to_drop)

    # Ensure the filename ends with .parquet
    if not filename.endswith('.parquet'):
        filename += '.parquet'
    
    save_filepath = os.path.join(save_directory, filename)
    input_sim_df.to_parquet(save_filepath)

    print(f"DataFrame saved to {save_filepath}")








def load_parquet_to_df(directory: str) -> pd.DataFrame:
    # Get all parquet files in the directory
    files = [f for f in os.listdir(directory) if f.endswith('.parquet')]
    
    if len(files) == 0:
        raise FileNotFoundError("No Parquet files found in the specified directory.")
    elif len(files) == 1:
        filepath = os.path.join(directory, files[0])
    else:
        print("Multiple Parquet files found:")
        for i, file in enumerate(files, start=1):
            print(f"{i}: {file}")
        
        file_index = int(input("Enter the number of the file you want to load: ")) - 1
        if file_index < 0 or file_index >= len(files):
            raise ValueError("Invalid file number selected.")
        
        filepath = os.path.join(directory, files[file_index])
    

    print(f"Loading {filepath}")

    # Load the DataFrame from the chosen Parquet file
    loaded_df = pd.read_parquet(filepath)

    sim_df = reload_field_data_to_df(loaded_df)

    return sim_df




def reload_field_data_to_df(input_sim_df):
    field_output_data = []
    
    sim_df = input_sim_df.copy()
    reloaded_field_col = set()

    for ind, row in sim_df.iterrows():
        if not pd.isna(row['gamma']):  # Correct way to check for NaN

            parameters_path = row['filepath']
            field_path = switch_suffix_file(parameters_path, 'field')
            field_dict = field_filepath_to_dict(field_path)

            field_output_data.append(field_dict)

            for key, val in field_dict.items():
                reloaded_field_col.add(key)
        else:
            field_output_data.append({})

    reloaded_field_col = list(reloaded_field_col)
    reloaded_field_col.sort()

    field_df = pd.DataFrame(field_output_data)
    merged_df = pd.concat([sim_df, field_df], axis=1)

    print(f'Reloaded dataframe with field columns: {reloaded_field_col}')

    return merged_df
    
