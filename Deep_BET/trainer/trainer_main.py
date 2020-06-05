#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May 24 06:08:37 2020

@author: siddhesh
"""


import os
import time
import sys
import torch
import pandas as pd
from pytorch_lightning import Trainer
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping
from pytorch_lightning.logging import TensorBoardLogger
from Deep_BET.utils.csv_creator_adv import generate_csv
from Deep_BET.trainer.lightning_networks import SkullStripper

def train_network(cfg, device, weights):
    """
    Receiving a configuration file and a device, the training is pushed through this file

    Parameters
    ----------
    cfg : TYPE
        DESCRIPTION.
    device : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    """
    training_start_time = time.asctime()
    startstamp = time.time()
    print("\nHostname   :" + str(os.getenv("HOSTNAME")))
    print("\nStart Time :" + str(training_start_time))
    print("\nStart Stamp:" + str(startstamp))
    sys.stdout.flush()
    print("Checking for this cfg file : ", cfg)
    # READING FROM A CFG FILE and check if file exists or not
    if os.path.isfile(cfg):
        params_df = pd.read_csv(cfg, sep=' = ', names=['param_name', 'param_value'],
                                comment='#', skip_blank_lines=True,
                                engine='python').fillna(' ')
    else:
        print('Missing train_params.cfg file?')
        sys.exit(0)

    # Reading in all the parameters
    params = {}
    for i in range(params_df.shape[0]):
        params[params_df.iloc[i, 0]] = params_df.iloc[i, 1]
    print(type(device), device)
    if type(device) != str:
        params['device'] = str(device)
    params['weights'] = weights
    # Although uneccessary, we still do this
    if not os.path.isdir(str(params['model_dir'])):
        os.mkdir(params['model_dir'])

    # PRINT PARSED ARGS
    print("\n\n")
    print("Training Folder Dir     :", params['train_dir'])
    print("Validation Dir          :", params['validation_dir'])
    print("Model Directory         :", params['model_dir'])
    print("Mode                    :", params['mode'])
    print("Number of modalities    :", params['num_modalities'])
    print("Modalities              :", params['modalities'])
    print("Number of classes       :", params['num_classes'])
    print("Max Number of epochs    :", params['max_epochs'])
    print("Batch size              :", params['batch_size'])
    print("Optimizer               :", params['optimizer'])
    print("Learning Rate           :", params['learning_rate'])
    print("Learning Rate Milestones:", params['lr_milestones'])
    print("Patience to decay       :", params['decay_milestones'])
    print("Early Stopping Patience :", params['early_stop_patience'])
    print("Depth Layers            :", params['layers'])
    print("Model used              :", params['model'])
    print("Weights used            :", params['weights'])
    sys.stdout.flush()
    print("Device Given :", device)
    sys.stdout.flush()
    # Although uneccessary, we still do this
    os.makedirs(params['model_dir'], exist_ok=True)
    print("Current Device : ", torch.cuda.current_device())
    print("Device Count on Machine : ", torch.cuda.device_count())
    print("Device Name : ", torch.cuda.get_device_name())
    print("Cuda Availibility : ", torch.cuda.is_available())
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Using device:', device)
    if device.type == 'cuda':
        print('Memory Usage:')
        print('Allocated:', round(torch.cuda.memory_allocated(0)/1024**3, 1),
              'GB')
        print('Cached: ', round(torch.cuda.memory_cached(0)/1024**3, 1), 'GB')
    sys.stdout.flush()

    # We generate CSV for training if not provided
    print("Generating CSV Files")
    # Generating training csv files
    if not params['csv_provided'] == 'True':
        print('Since CSV were not provided, we are gonna create for you')
        generate_csv(params['train_dir'],
                     to_save=params['model_dir'],
                     mode=params['mode'], ftype='train',
                     modalities=params['modalities'])
        generate_csv(params['validation_dir'],
                     to_save=params['model_dir'],
                     mode=params['mode'], ftype='validation',
                     modalities=params['modalities'])
        params['train_csv'] = os.path.join(params['model_dir'], 'train.csv')
        params['validation_csv'] = os.path.join(params['model_dir'], 'validation.csv')
    else:
        # Taken directly from params
        pass
    os.makedirs(params['model_dir'], exist_ok=True)
    try:
        log_dir = sorted(os.listdir(params['model_dir']))[-1]
    except IndexError:
        log_dir = os.path.join(params['model_dir'], 'version_0')
    checkpoint_callback = ModelCheckpoint(filepath=os.path.join(log_dir,
                                                                'checkpoints'),
                                          monitor='val_loss',
                                          verbose=True,
                                          save_top_k=3,
                                          mode='auto',
                                          save_weights_only=False,
                                          prefix=str('deep_resunet_'+
                                                     params['base_filters'])
                                          )
    stop_callback = EarlyStopping(monitor='val_loss', mode='auto',
                                  patience=int(params['early_stop_patience']),
                                  verbose=True)
    tensorboard_logger = TensorBoardLogger(params['model_dir'], name="my_model")
    model = SkullStripper(params)

    res_ckpt = weights
    trainer = Trainer(logger=tensorboard_logger,
                      checkpoint_callback=checkpoint_callback,
                      early_stop_callback=stop_callback,
                      default_save_path=params['model_dir'],
                      gpus=params['device'],
                      log_gpu_memory='min_max',
                      show_progress_bar=False,
                      check_val_every_n_epoch=1,
                      fast_dev_run=False,
                      max_epochs=int(params['max_epochs']),
                      min_epochs=int(params['min_epochs']),
                      train_percent_check=1.0,
                      val_percent_check=1.0,
                      val_check_interval=1.0,
                      log_save_interval=100,
                      row_log_interval=10,
                      distributed_backend=None,
                      use_amp=False,  # Do you need 16 bit?
                      weights_summary='full',
                      weights_save_path=params['model_dir'],
                      amp_level='O1',
                      num_sanity_val_steps=5,
                      resume_from_checkpoint=res_ckpt
                      )
    trainer.fit(model)