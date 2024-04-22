import os
import itertools



######################################################################
######################### Parameter file IO ##########################
######################################################################

def read_clean_file(param_filepath):
    
    with open(param_filepath, 'r') as file:
        file_content = file.read()
    
    processed_lines = []

    lines = file_content.split('\n')
    for line in lines:
        if line.startswith('!'):
            continue

        elif '!' in line:
            index = line.index('!')
            processed_line = line[:index]
            processed_lines.append(processed_line.rstrip())
        else:
            processed_lines.append(line.rstrip())
    return '\n'.join(processed_lines)





def write_file(file_content, i:int=0):
    dir_name = f"param_batch/parameter_{i}"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    file_path = os.path.join(dir_name, 'parameters')
    with open(file_path, 'w') as file:
        file.write(file_content)




######################################################################
######################### Modify param files #########################
######################################################################



# Modify param values functions
def convert_type(var_value):
    try:
        return int(var_value)
    except ValueError:
        try:
            return float(var_value)
        except ValueError:
            return var_value




def change_var_value(file_content, input_string, value):
    lines = file_content.split('\n')
    
    
    if isinstance(value, str):
        value = f"'{value}'"

    for i, line in enumerate(lines):
        if ('=' in line) and (not line.strip().startswith('!')):
            line_parts = line.split('!')
            var_name_line = line_parts[0]

            var_name, var_value = var_name_line.split('=')
            var_value = convert_type(var_value.strip())
            
            # print(var_value, type(var_value))
            if (var_name.strip() == input_string.strip()):
                if (type(value) == type(var_value)):
                    lines[i] = var_name + ' = ' + str(value)
                else:
                    override_input = input(f"Value {value} is not of the same type as the original variable {var_name}. Would you like to override the type check? (y/n): ")
                    if override_input.lower() == 'y':
                        lines[i] = var_name + ' = ' + str(value)
                    else:
                        raise ValueError("Type mismatch. Exiting program.")

    return '\n'.join(lines)





# Scan line modification functions


def append_scan_line(file_content, input_string, values, scan_type='scanlist'):
    scan_added = False
    processed_lines = []

    if scan_type not in ['!scanlist', '!scan']:
        raise ValueError("Invalid scan type. Choose either !scanlist or !scan")


    if not scan_type.startswith('!'):
        scan_type = '!' + scan_type


    lines = file_content.split('\n')
    for line in lines:
        if '=' in line and line.split('=')[0].strip() == input_string:
            line_parts = line.split('!')
            if len(line_parts) > 1:
                # If there's a comment, insert the scan before it
                processed_line = line_parts[0].rstrip() + ' ' + scan_type + ': ' + ', '.join(map(str, values)) + ' !' + '!'.join(line_parts[1:])
            else:
                # If there's no comment, just append the scan at the end
                processed_line = line.rstrip() + ' ' + scan_type + ': ' + ', '.join(map(str, values))
            processed_lines.append(processed_line)
            scan_added = True
        else:
            processed_lines.append(line.rstrip())
    return '\n'.join(processed_lines), scan_added





def create_new_scan_line(file_content, input_string, values, scan_type='!scanlist', section_ind_dict=None):
    file_lines = []
    sections = []
    current_section = None

    if scan_type not in ['!scanlist', '!scan']:
        raise ValueError("Invalid scan type. Choose either !scanlist or !scan")


    lines = file_content.split('\n')
    for line in lines:
        file_lines.append(line)
        if line.strip().startswith('&'):
            current_section = line.strip()
            sections.append(current_section)
            
    
    if section_ind_dict is None:
        section_indices = [f"{index}: {section}" for index, section in enumerate(sections)]
        print("Sections:")
        print("\n".join(section_indices))
        
        section = input(f'Enter the index of the section where you want to add the {input_string} scan: ')
        section_ind_dict = {input_string: section}
    else:
        section = section_ind_dict.get(input_string)
        if section is None:
            section_indices = [f"{index}: {section}" for index, section in enumerate(sections)]
            print("Sections:")
            print("\n".join(section_indices))
            
            section = input(f'Enter the index of the section where you want to add the {input_string} scan: ')
            section_ind_dict[input_string] = section
        


    try:
        section_index = int(section)
        if section_index < 0 or section_index >= len(sections):
            raise ValueError("Invalid section index")
        else:
            # Find the index of the section in the processed_lines list
            section_line_index = file_lines.index(sections[section_index])
            # Insert the key with a default value of 0 right after the section divider
            processed_line = f'{input_string} = 0' + ' ' + scan_type + ': ' + ', '.join(map(str, values))
            file_lines.insert(section_line_index + 1, processed_line)
    except ValueError:
        raise ValueError("Invalid section index")

    return '\n'.join(file_lines), section_ind_dict



######################################################################
################## Break apart parallel simulation ###################
######################################################################


def get_parallel_sim(parallel_sim, scan_type, key, value):
    if scan_type == 'scanlist':
        parallel_sim *= len(value['values'])
    elif scan_type == 'scan':

        if parallel_sim == 1:                
            parallel_sim = len(value['values'])
        elif parallel_sim != len(value['values']):
            raise ValueError(f"Check '{key}' and ensure all scan values have the same length for 'scan'.")
        else:
            parallel_sim = len(value['values'])

    return parallel_sim




def create_param_scan_matrix(scan_dict, scan_type, auto_name_diagdir_path=None, debug:bool=False):
    ind_param_names = []
    ind_param_values = []

    param_scan_dict = {}
    parallel_sim = 1

    for key, value in scan_dict.items():
        split_param_bool = value.get('split_param', False)

        if split_param_bool:
            ind_param_names.append(key)
            ind_param_values.append(value['values'])
        else:
            param_scan_dict[key] = value['values']
            parallel_sim = get_parallel_sim(parallel_sim, scan_type, key, value)
            


    
    # Create a list of dictionaries, where each dictionary represents a point in the matrix
    # The keys of the dictionary are the variable names, and the values are the coordinates
    product = list(itertools.product(*ind_param_values))
    param_file_values_list = [dict(zip(ind_param_names, coordinates)) for coordinates in product]


    # Add additional parameters to files for running
    for param_file_values in param_file_values_list:
        param_file_values['n_parallel_sims'] = parallel_sim

        ignore_names = ['n_parallel_sims', 'geomfile']
        if auto_name_diagdir_path:
            auto_name_dir = '_'.join([f"{key}-{value}" for key, value in param_file_values.items() if key not in ignore_names])
            diagdir_path = os.path.join(auto_name_diagdir_path, auto_name_dir)
            param_file_values['diagdir'] = diagdir_path



    if param_file_values_list[0] == {}:
        param_file_values_list = []

    if debug:
        print(len(param_file_values_list))
        print("Adding scan parameters for:", '\n',  param_scan_dict, '\n')

        for dict_param in param_file_values_list:
            print("Changing param values:", dict_param)
            


    return param_file_values_list, param_scan_dict



######################################################################
################## Create unique parameter files #####################
######################################################################




def create_unique_param_file(param_file_contents, param_file_dict, param_scan_dict, scan_type, section_ind_dict=None):

    # Add scan values to param file first
    for key, values in param_scan_dict.items():
        param_file_contents, scan_added = append_scan_line(param_file_contents, key, values, scan_type=scan_type)

        if not scan_added:
            param_file_contents, section_ind_dict = create_new_scan_line(param_file_contents, key, values, scan_type=scan_type, section_ind_dict=section_ind_dict)
            print(section_ind_dict)  # Debugging output

    # Modify the parameter values individually
    for key, value in param_file_dict.items():
        param_file_contents = change_var_value(param_file_contents, key, value)
    
    return param_file_contents, section_ind_dict

    



def create_batch_param_files(param_path, scan_dict, scan_type, auto_name_diagdir_path=None, debug:bool=False):
    original_param_file = read_clean_file(param_path)
    param_file_values_list, param_scan_dict = create_param_scan_matrix(scan_dict, scan_type, auto_name_diagdir_path, debug)

    section_ind_dict = None  # Initialize if not provided

    for ind, param_file_dict in enumerate(param_file_values_list):
        mod_param_file, section_ind_dict = create_unique_param_file(original_param_file, param_file_dict, param_scan_dict, scan_type, section_ind_dict=section_ind_dict)

        write_file(mod_param_file, i=ind)






