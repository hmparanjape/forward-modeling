import copy
import logging
import os
import sys
import time
import warnings

import yaml

from hexrd import config

from forward_modeling.fwd_modeling_from_micro import *
from forward_modeling.microstructure_generation import *

if __name__ == '__main__':
    # Read args
    if len(sys.argv) < 2:
        print 'USAGE: python synth_fwd_modeling_patterns.py config.yml'
        sys.exit(1)
    elif sys.argv[1] == '-h' or sys.argv[1] == '--help':
        print 'USAGE: python synth_fwd_modeling_patterns.py config.yml'
        sys.exit(1)
    else:
        cfg_file = sys.argv[1]

    # Setup logger
    log_level = logging.DEBUG
    logger = logging.getLogger('hexrd')
    logger.setLevel(log_level)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    cf = logging.Formatter('%(asctime)s - %(message)s', '%y-%m-%d %H:%M:%S')
    ch.setFormatter(cf)
    logger.addHandler(ch)
    # load the configuration settings
    cfgs = config.open(cfg_file)
    # cfg is a list. We will loop over each cfg set.

    for cfg in cfgs:
    	logger.info('=== begin forward-modeling ===')

        fwd_model_mode = cfg.get('forward_modeling')['modeling_mode'].strip()
	fwd_model_nipt = cfg.get('forward_modeling')['datagen']['number_of_points']
	fwd_model_op_file = cfg.get('forward_modeling')['datagen']['output_file_name'].strip()

        if fwd_model_mode == "datagen":
            logger.info('=== generating synthetic microstructural data ===')
	    logger.info('=== writing output to %s ===', fwd_model_op_file)

	    generate_cubic_grain_mosaicity(nipt=fwd_model_nipt, output_file=fwd_model_op_file)
            #generate_cubic_grain_ideal(nipt=fwd_model_nipt, output_file=fwd_model_op_file)
            #generate_cubic_grains_random_ideal(nipt=fwd_model_nipt, output_file=fwd_model_op_file)

        elif fwd_model_mode == "fwdmodel":
            try:
                fwd_model_ip_filename = \
                    cfg.get('forward_modeling')['input_file_name'].strip()
            except:
                fwd_model_ip_filename = 'ms-data-test.csv'

            fwd_model_op_filename = cfg.get('forward_modeling')['output_file_name'].strip()

            ms = Microstructure(cfg, logger, fwd_model_ip_filename)
            ms.read_csv()
            ms.get_diffraction_angles()
            ms.project_angs_to_detector(output_file=fwd_model_op_filename)

	    output_ge2 = cfg.get('forward_modeling')['output_ge_name']
	    omega_start = cfg.get('forward_modeling')['output_omega']['start']
            omega_step = cfg.get('forward_modeling')['output_omega']['step']
            omega_stop = cfg.get('forward_modeling')['output_omega']['stop']
	    ms.write_xyo_to_ge2(output_ge2=output_ge2, omega_start=omega_start, omega_step=omega_step, omega_stop=omega_stop)

        else:
            logger.error('Invalid forward modeling mode: %s. Choices are datagen and fwdmodel', fwd_model_mode)
