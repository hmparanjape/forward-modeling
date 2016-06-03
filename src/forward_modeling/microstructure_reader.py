import copy
import logging
import os
import sys
import time
import warnings

import yaml

import numpy as np

from hexrd.xrd import experiment as expt
from hexrd import matrixutil as mutil
from hexrd.xrd import rotations as rot
from hexrd.xrd import transforms_CAPI as xfcapi

class Microstructure:
    '''
    Microstructural information for forward modeling. This object holds
    spatial information for material/phase, crystal orientation, lattice strain
    and material properties and detector parameters for the virtual experiment.
    '''
    def __init__(self, config, logger, datafile):
        self.cfg = config              # heXRD config object
        self.logger = logger           # logger
        self.ms_datafile = datafile    # microstructural data file
        self.ms_grid = []              # (N, 3) array of X, Y, Z positions in microns
        self.ms_material_ids = []      # (N) Array of material present at X, Y, Z
        self.ms_quaternions = []       # (N, 4) Orientation at X, Y, Z in quaternions
        self.ms_lat_strains = []       # (N, 6) Lattice strain a X, Y, Z

    def read_csv(self):
        ''' 
        Load microstructural data from a csv file. Required columns are
        Position_X, position_Y, position_Z, material_name, 
        orientation_quat_1, orientation_quat_2, orientation_quat_3, orientation_quat_4,
        strain_11, strain_22, strain_33, 
        strain_12, strain_23, strain_31, 
        '''

        filename = self.ms_datafile
        logger = self.logger

        try:
            ms_data = np.loadtxt(filename, dtype=None, comments='#', delimiter=',',
                              usecols=(0,1,2,4,5,6,7,8,9,10,11,12,13),
                                 ndmin=2)
            ms_mat_data = np.loadtxt(filename, dtype='str', comments='#', delimiter=',',
                                  usecols=(3,), ndmin=2)

            ms_data = np.array(ms_data)
            ms_mat_data = np.array(ms_mat_data)
        except:
            logger.error('Could not read microstructural data from %s', filename)
            ms_data = None
            ms_material_data = None

        self.ms_grid = ms_data[:, range(0, 3)]
        self.ms_material_ids = ms_mat_data[:, 0]
        self.ms_quaternions = ms_data[:, range(3, 7)]
        self.ms_lat_strains = ms_data[:, range(7, 13)]

    def get_diffraction_angles(self):
        cfg = self.cfg
        logger = self.logger

        # Initialize a new heXRD experiment
        ws = expt.Experiment()

        cwd = cfg.working_dir

        materials_fname = cfg.material.definitions
        material_name = cfg.material.active
        detector_fname = cfg.instrument.detector.parameters_old

        # load materials
        ws.loadMaterialList(os.path.join(cwd, materials_fname))
        mat_name_list = ws.matNames

        for xyz_i, mat_name_i, quat_i, strain_i in zip(self.ms_grid,
                                                       self.ms_material_ids,
                                                       self.ms_quaternions,
                                                       self.ms_lat_strains):

            # Need t oread chi tilt from somewhere 
            # (old detector or start using YAML detector config?)
            chi = 0.0

            ws.activeMaterial = mat_name_i.strip() #material_name
            logger.info("setting active material to '%s'", mat_name_i)
            hkls = ws.activeMaterial.planeData.hkls.T

            rmat_c = rot.rotMatOfQuat(quat_i)

            bmat = ws.activeMaterial.planeData.latVecOps['B']

            wavelength = ws.activeMaterial.planeData.wavelength

            omega0, omega1 = xfcapi.oscillAnglesOfHKLs(hkls, 
                                                       chi, 
                                                       rmat_c, 
                                                       bmat, 
                                                       wavelength,
                                                       vInv=strain_i)
            print hkls
            print omega0
            print omega1

