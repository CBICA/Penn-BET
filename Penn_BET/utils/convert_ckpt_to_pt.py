#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat May 30 07:55:22 2020

@author: siddhesh
"""

import os
from argparse import ArgumentParser
import torch

if __name__ == '__main__':

    parser = ArgumentParser(description='Convert the .ckpt files to .pt files')
    parser.add_argument('-i', '--input', dest='input',
                        help='Input .ckpt file generated by lightning', required=True)
    parser.add_argument('-o', '--output', dest='output',
                        help='Output .pt file to be generated, must be with extension of .pt',
                        required=True)
    args = parser.parse_args()

    ckpt_file = os.path.abspath(args.input)
    pt_file = os.path.abspath(args.output)

    print("Attempting to load file : ", ckpt_file)
    weight_load = torch.load(ckpt_file)
    print("Load Successful! Converting file.")
    new_state_dict = {}
    for key in weight_load['state_dict'].keys():
        new_key = key[6:]
        new_state_dict[new_key] = weight_load['state_dict'][key]
    model_state_dict = {'model_state_dict' : new_state_dict}
    print("Conversion successful!")
    torch.save(model_state_dict, pt_file)
    print("File saved successfully at :", pt_file)
