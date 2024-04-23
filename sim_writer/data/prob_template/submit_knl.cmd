#!/bin/bash -l
#SBATCH --qos regular
#SBATCH -C cpu
#SBATCH -n 4608
#SBATCH --nodes=36
#SBATCH --ntasks-per-node=128
#SBATCH -t 01:30:00
#SBATCH -J GENE
#SBATCH -o ./%x.%j.out
#SBATCH -e ./%x.%j.err
##uncomment for particular account usage
#SBATCH -A m2116

if [ "$PE_ENV" == "CRAY" ]; then
  export FILENV=my_filenenv
  assign -U on g:sf
fi

## set openmp threads
export OMP_NUM_THREADS=1

#do not use file locking for hdf5
export HDF5_USE_FILE_LOCKING=FALSE


# run GENE
# srun -n 1536 ./gene_perlmutter

# run scanscript
./scanscript --np 4608 --ppn 128 --mps 128 --syscall='srun -n 4608 ./gene_perlmutter'
