import os

import pandas as pd
import numpy as np

from GENE_sim_tools.GENE_sim_reader.src.utils.file_functions import string_to_list


def simulation_df_bundler(input_sim_df_list:list, input_group_by:list, input_bundle_outputs:list=['kymin', 'gamma', 'omega']):

    # Convert stringss to list if necessary
    group_by = string_to_list(input_group_by)    
    bundle_outputs = string_to_list(input_bundle_outputs)

    # Check if the input not a list and convert it to one if needed
    if not isinstance(input_sim_df_list, list):
        input_sim_df_list = [input_sim_df_list]

    # Check that all objects into simulation list are dataframe objects
    for ind, sim_df in enumerate(input_sim_df_list):
        if not isinstance(sim_df, pd.DataFrame):
            raise ValueError(f'Please ensure the object in the {ind} place of the input_sim_list is a pandas Dataframe.')

    # Combine all dataframes
    combined_df = pd.concat(input_sim_df_list, ignore_index=True)

    # Initialize an empty DataFrame to store results
    bundled_df = pd.DataFrame(columns=group_by + bundle_outputs)

    # Iterate over unique groups and bundle outputs
    for name, group in combined_df.groupby(group_by):
        # For simplicity, name will be a tuple if group_by has more than one column
        row = list(name) if isinstance(name, tuple) else [name]
        for col in bundle_outputs:
            # Collect unique values in this column into a list
            bundled_list = list(group[col])
            # Convert the list to a numpy array
            bundled_array = np.array(bundled_list)
            row.append(bundled_array)
        bundled_df.loc[len(bundled_df)] = row

    return bundled_df, group_by, bundle_outputs





def sort_by_column_name(input_df, column_name:str='kymin'):
    rearranged_df = input_df.copy()

    # Ensure the specified column exists
    if column_name not in rearranged_df.columns:
        raise ValueError(f"DataFrame must contain '{column_name}' column")
    
    columns_to_rearrange = set()  # Use a set for dynamic additions
    for _, row in rearranged_df.iterrows():
        for col in rearranged_df.columns:
            if col != column_name and isinstance(row[col], (list, np.ndarray)):
                columns_to_rearrange.add(col)

    # Iterate over rows in DataFrame
    for index, row in rearranged_df.iterrows():
        # Get the sorting order from the specified column
        sort_order = np.argsort(row[column_name])
        # Rearrange the specified column and other identified columns by the sort order
        rearranged_df.at[index, column_name] = np.array(row[column_name])[sort_order].tolist()
        for col in columns_to_rearrange:
            rearranged_df.at[index, col] = np.array(row[col])[sort_order].tolist()

    return rearranged_df

