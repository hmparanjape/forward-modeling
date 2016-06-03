import copy
import logging
import os
import sys
import time
import warnings

import yaml

from hexrd import config

from forward_modeling.microstructure_reader import *

#from ge_processor.ge_pre_processor import *

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
    	# Initialize the GE pre-processor
    	# gepp = GEPreProcessor(cfg=cfg, logger=logger)
    	# Start analysis
    	logger.info('=== begin forward-modeling ===')
    	# Load the GE2 data
    	# gepp.load_data()
    	# ID blobs and the local maxima
    	# gepp.find_blobs()

        ms = Microstructure(cfg, logger, 'ms-data-test.csv')
        ms.read_csv()
        ms.get_diffraction_angles()

