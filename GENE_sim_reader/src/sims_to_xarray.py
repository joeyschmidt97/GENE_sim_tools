import xarray as xr


from GENE_sim_tools.GENE_sim_reader.src.utils.file_functions import suffix_from_filename, string_to_list, switch_suffix_file
from GENE_sim_tools.GENE_sim_reader.src.utils.find_buried_filetypes import find_buried_filetypes

from GENE_sim_tools.GENE_sim_reader.src.dict_parameters_data import parameters_filepath_to_dict
from GENE_sim_tools.GENE_sim_reader.src.dict_omega_data import omega_filepath_to_dict
from GENE_sim_tools.GENE_sim_reader.src.dict_nrg_data import nrg_filepath_to_dict



def filepath_to_sim_xarray(input_filepath):

    filepath_list = string_to_list(input_filepath)

    # Search for 'parameters' files up to a specified depth
    max_depth = 3
    parameter_filepath_list = find_buried_filetypes(filepath_list, 'parameters', max_depth)


    simulations_xarray = []

    for parameters_path in parameter_filepath_list:
        parameters_dict = parameters_filepath_to_dict(parameters_path)

        omega_path = switch_suffix_file(parameters_path, 'omega')
        omega_dict = omega_filepath_to_dict(omega_path)

        nrg_path = switch_suffix_file(parameters_path, 'nrg')
        time_criteria = {'bounds': 'last'}
        nrg_dict = nrg_filepath_to_dict(nrg_path, time_criteria='time==last')


        

        sim_dict = parameters_dict.copy()  # Start with a copy of the first dictionary to avoid modifying it directly
        sim_dict.update(omega_dict)
        sim_dict.update(nrg_dict)

        simulations_xarray.append(sim_dict)
        

        # Each param_apth is converted to an ind xarray and appended to the overall xarray


    return simulations_xarray