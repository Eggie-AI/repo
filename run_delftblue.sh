#!/bin/bash
#
#SBATCH --job-name="eggie-ai"
#SBATCH --account=research-eemcs-st
#SBATCH --partition=compute
#SBATCH --time=2:59:00
#SBATCH --ntasks=16
#SBATCH --cpus-per-task=2
#SBATCH --mem-per-cpu=12G
#SBATCH --output=/home/fnmvanderheijd/aidmp/run-instances-%j.log

module load 2022r2
module load gcc
module load cmake
module load python

srun ./run_instances.sh "$@"
