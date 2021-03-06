#!/bin/bash
#SBATCH -p gpu
#SBATCH -n 1
#SBATCH --gres=gpu:4
#SBATCH -N 1                    # Ensure that all cores are on one machine
#SBATCH -t 2-00:00              # Runtime in D-HH:MM
#SBATCH -p serial_requeue       # Partition to submit to
#SBATCH --mem=20000               # Memory pool for all cores (see also --mem-per-cpu)
#SBATCH --constraint=cuda-7.5
#SBATCH -o theano-sherlock-multi.out      # File to which STDOUT will be written
#SBATCH -e theano-sherlock-multi.err      # File to which STDERR will be written
#SBATCH --mail-type=END         # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=andrewzhou@college.harvard.edu # Email to which notifications will be sent
 
hostname
module load python
module load cuda/7.5-fasrc01
module load cudnn/7.0-fasrc01

source activate mypython
KERAS_BACKEND=theano THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32,lib.cnmem=1 python src/train.py