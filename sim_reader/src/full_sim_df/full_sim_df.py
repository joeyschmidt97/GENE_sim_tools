import os
import pandas as pd

from GENE_sim_tools.GENE_sim_reader.src.filetype_key_lists import omega_key_list, nrg_column_keys, field_column_keys
from GENE_sim_tools.GENE_sim_reader.src.dict_simulation_data import sim_filepath_to_df



def converged_last_time_sim_df(input_path):
    criteria = ['status==CONVERGED', 'time==last']
    criteria = criteria + omega_key_list + nrg_column_keys + field_column_keys
    
    criteria.remove('field_bpar')
    sim_df = sim_filepath_to_df(input_path, criteria)

    return sim_df



def sim_df_to_csv(input_path_df, save_path:str = None):

    if isinstance(input_path_df, str):
        save_path = input_path_df
        filename = 'converged_tlast_sims.csv'
        print(f'Saving simulation data to dataframe to path \n {save_path}')
        sim_df = converged_last_time_sim_df(input_path_df)
    elif isinstance(input_path_df, pd.DataFrame):
        sim_df = input_path_df
        if save_path is None:
            save_path = input('Please enter a save path for the dataframe')
        filename = 'MODDED_converged_tlast_sims.csv'
        print(f'Saving modified simulation data to dataframe to path \n {save_path}')
    else:
        raise ValueError('Make sure to use a df or filepath')

    filepath = os.path.join(save_path, filename)
    sim_df.to_csv(filepath, index=False)





import os
import pandas as pd

def load_csv_from_path(path):
    # Check if the path is a directory and list all CSV files
    if os.path.isdir(path):
        csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
        if len(csv_files) == 0:
            print("No CSV files found in the directory.")
            return None
        elif len(csv_files) == 1:
            file_path = os.path.join(path, csv_files[0])
        else:
            # Construct the prompt with file options
            prompt = "Multiple CSV files found. Please choose one to load:\n"
            prompt += "\n".join(f"{idx + 1}: {file}" for idx, file in enumerate(csv_files))
            prompt += "\nEnter the number of the file to load: "
            file_index = int(input(prompt)) - 1
            file_path = os.path.join(path, csv_files[file_index])
    elif os.path.isfile(path) and path.endswith('.csv'):
        file_path = path
    else:
        print("The path is not a CSV file or a directory containing CSV files.")
        return None

    # Load the selected CSV file into a DataFrame
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        print(f"An error occurred while loading the file: {e}")
        return None
