import os
import re
import sys
import subprocess
import shutil

from GENE_sim_tools.sim_reader.src.dict_parameters_data import parameters_filepath_to_dict
from GENE_sim_tools.sim_writer.src.default_values import GENE_prob_source_dir, GENE_path





def run_GENE_parameters(param_batch_filepath:str):
    """ Run GENE simulations for each parameter folder in the parameter batch folder """
    
    param_batch_files = os.listdir(param_batch_filepath)
    param_batch_files.sort()

    batch_name = os.path.basename(param_batch_filepath).split('_parameter_batch')[0]

    for parameter_folder in param_batch_files:    
        folder_path = os.path.join(param_batch_filepath, parameter_folder)
        
        if os.path.isdir(folder_path):

            # Define the source and the new destination directory names
            # source_dir = '/global/homes/j/joeschm/tools/GENE_sim_tools/sim_writer/data/prob_template'
            destination_dir = os.path.join(GENE_path, batch_name + parameter_folder)
            
            
            # Copy file over and add contents
            cmd = f"rsync -avz {GENE_prob_source_dir}/ {destination_dir}/"
            # print(cmd)
            try:
                subprocess.run(cmd, check=True, shell=True)
                # print(f"Directory copied to {destination_dir}")
            except subprocess.CalledProcessError as e:
                print(f"An error occurred during rsync: {e}")
            

            param_file = folder_path + '/parameters'
            # Copy the parameters file to the destination directory
            try:
                shutil.copy(param_file, destination_dir)
                # print(f"Parameter file copied to {destination_dir}")
            except Exception as e:
                print(f"An error occurred while copying the parameter file: {e}")
                print(param_file, destination_dir)

            
            update_submit_file(destination_dir + '/parameters', os.path.basename(destination_dir))

            submit_job = input(f"Do you want to submit the job for {parameter_folder}? (y/n): ")
            if submit_job.lower() == 'y':
                # Submit the job
                os.chdir(destination_dir)
                cmd = f'sbatch submit_knl.cmd'
                try:
                    subprocess.run(cmd, check=True, shell=True)
                    print(f"Job submitted for {parameter_folder}")
                except subprocess.CalledProcessError as e:
                    print(f"An error occurred while submitting the job in {parameter_folder}: {e}")










########################################################################################
############################## Update submit file functions ############################
########################################################################################


def is_valid_time_format(time_str):
    """ Validate time format HH:MM:SS """
    if re.match(r'^\d{2}:\d{2}:\d{2}$', time_str):
        hours, minutes, seconds = map(int, time_str.split(':'))
        return 0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59
    return False


def get_time_input(update_file):
    """ Prompt user until a valid time is entered or they choose to exit """
    while True:
        time_input = input(f'Enter the time for the simulation {update_file} in the format HH:MM:SS or type "quit" to exit: ')
        if time_input.lower() == "quit":
            print("Exiting program.")
            sys.exit(0)  # Terminate the program
        elif is_valid_time_format(time_input):
            return time_input
        else:
            print("Invalid time format. Please enter a time in the format HH:MM:SS where HH is 00-23, MM is 00-59, and SS is 00-59.")



def update_submit_file(param_path, update_file):

    param_dict = parameters_filepath_to_dict(param_path)

    # print(param_dict['diagdir'])
    if not os.path.exists(param_dict['diagdir']):
        os.makedirs(param_dict['diagdir'])

    core_num = param_dict['n_procs_sim'] * param_dict['n_parallel_sims']
    node_num = core_num // 128
    time_input = get_time_input(update_file)



    submit_filepath = os.path.dirname(param_path) + '/submit_knl.cmd'

    with open(submit_filepath, 'r') as file:
        lines = file.readlines()
    
    # Update the necessary lines using regular expressions
    for i in range(len(lines)):
        if lines[i].startswith('#SBATCH --qos'):
            if time_input <= '00:30:00':
                debug_input = input('Time is less than 30 minutes. Do you want to use the debug queue? (y/n): ')
                if debug_input.lower() == 'y':
                    qos_mode = 'debug'
                else:
                    qos_mode = 'regular'
            else:
                qos_mode = 'regular'
            lines[i] = f'#SBATCH --qos {qos_mode}\n'

        if lines[i].startswith('#SBATCH -n'):
            lines[i] = re.sub(r'(?<=#SBATCH -n )\d+', str(core_num), lines[i])

        elif lines[i].startswith('#SBATCH --nodes'):
            lines[i] = re.sub(r'(?<=#SBATCH --nodes=)\d+', str(node_num), lines[i])

        elif lines[i].startswith('#SBATCH -t'):
            lines[i] = f'#SBATCH -t {time_input}\n'
            
        elif './scanscript' in lines[i]:
            lines[i] = re.sub(r'(?<=--np )\d+', str(core_num), lines[i])
            lines[i] = re.sub(r"(?<=srun -n )\d+", str(core_num), lines[i])
            lines[i] = re.sub(r"(?<=--syscall='srun -n )\d+", str(core_num), lines[i])
    
    # Write the updated contents back to the submit file
    with open(submit_filepath, 'w') as file:
        file.writelines(lines)
    