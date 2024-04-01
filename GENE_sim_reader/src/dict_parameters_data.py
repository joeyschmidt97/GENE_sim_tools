#!/usr/bin/env python3
import os
import copy

from GENE_sim_tools.GENE_sim_reader.src.utils.ParIO import Parameters
from GENE_sim_tools.GENE_sim_reader.src.utils.file_functions import file_checks, FileError, string_to_list, suffix_from_filename

#------------------------------------------------------------------------------------------------
# BASE FUNCTION TO CONVERT PARAMETER TO DICT-----------------------------------------------------
#------------------------------------------------------------------------------------------------

def parameters_filepath_to_dict(parameters_filepath:str, debug:bool = False):
    """
    Converts a 'parameters' file at a given filepath to a parameter dictionary.
    Returns the parameter dictionary.
    """

    try:
        file_checks(parameters_filepath, filetype='parameters')
        parameters_dict = create_parameters_dict(parameters_filepath)

        return parameters_dict
    except FileError as e:
        print(e)



def create_parameters_dict(parameters_filepath:str):

    # Create a parameter dictionary using the Parameters class
    par = Parameters()
    par.Read_Pars(parameters_filepath)  # Read the parameter file
    parameter_dict = par.pardict 

    # Add the filename, filepath, and suffix to the parameter dictionary
    parameter_dict['filepath'] = parameters_filepath
    parameter_dict['suffix'] = suffix_from_filename(os.path.basename(parameters_filepath))
    parameter_dict = rename_species_quantities(parameter_dict)

    for key, value in parameter_dict.items():
        if isinstance(value, str):
            strip_value = value.strip("'")
            strip_value = strip_value.strip('"')
            parameter_dict[key] = strip_value
        
    return parameter_dict


#------------------------------------------------------------------------------------------------
# -----------------------------------------------------
#------------------------------------------------------------------------------------------------




def rename_species_quantities(input_parameters_dict:dict):

    # Extract name mappings and filter out keys ending with digits 1 to 3
    name_mapping = {key[-1]: value for key, value in input_parameters_dict.items() if key.startswith('name') and key[-1].isdigit()}

    # Function to check if the key ends with a digit that we have a name for
    def should_rename(key):
        if not key.startswith('name'):
            return key[-1] in name_mapping and key[-1].isdigit()

    # Generate a new list with updated keys
    updated_data = []
    for key, value in input_parameters_dict.items():
        if should_rename(key):
            species = name_mapping[key[-1]].strip("'")
            new_key = f"{key[:-1]}_{species}"
            updated_data.append((new_key, value))
        else:
            updated_data.append((key, value))

    # Convert the list of tuples into a dictionary
    parameters_dict = dict(updated_data)

    return parameters_dict










def create_species_tuple(parameters_filepath: str, input_spec_list:list='all'):

    input_spec_list = string_to_list(input_spec_list) # 'i', ['i', 'c'], 'all'

    param_dict = parameters_filepath_to_dict(parameters_filepath)
    n_spec = param_dict['n_spec']

    all_species_tuple = ()
    for spec_num in range(1, n_spec + 1):
        spec_name = param_dict['name' + str(spec_num)].strip("'")
        all_species_tuple += ((spec_name, spec_num),)

    if input_spec_list==['all']:
        return all_species_tuple, n_spec


    output_spec_tuple = ()
    for input_spec_name in input_spec_list:

        input_spec_found = False
        for spec in all_species_tuple:
            if input_spec_name in spec:
                output_spec_tuple += (spec,)
                input_spec_found = True

        if not input_spec_found:
            printout_spec_list = [spec_name for spec_name, _ in all_species_tuple]
            raise ValueError(f'Species "{input_spec_name}" is not a valid species. Please choose from: {printout_spec_list}')


    return output_spec_tuple, n_spec


#------------------------------------------------------------------------------------------------
# -----------------------------------------------------
#------------------------------------------------------------------------------------------------


if __name__=="__main__":
    filepath = os.getcwd()
