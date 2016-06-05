# Core libraries
import copy
import logging
import os
import sys
import time
import warnings
# YAML config processing
import yaml
# Math/array magic
import numpy as np
# Parallelization for speed
from joblib import Parallel, delayed
import multiprocessing
# heXRD libraries for diffraction functions
from hexrd.xrd import experiment as expt
from hexrd.coreutil import initialize_experiment
from hexrd import matrixutil as mutil
from hexrd.xrd import rotations as rot
from hexrd.xrd import transforms_CAPI as xfcapi
#--

def get_diffraction_angles_MP(fwd_model_input_i):
    '''
    Parallel processing worker for eta, two-th, omega calculation
    '''

    hkls = fwd_model_input_i['hkls']
    chi = fwd_model_input_i['chi']
    rmat_c = fwd_model_input_i['rmat_c']
    bmat = fwd_model_input_i['bmat']
    wavelength = fwd_model_input_i['wavelength']
    defgrad_i = fwd_model_input_i['defgrad_i']

    omega0, omega1 = xfcapi.oscillAnglesOfHKLs(hkls, 
                                               chi, 
                                               rmat_c, 
                                               bmat, 
                                               wavelength,
                                               vInv=defgrad_i)
#    print hkls
#    print omega0
#    print omega1
    return np.concatenate((omega0, omega1), axis=0)

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
        self.synth_angles = []         # Two-theta, eta, omega from virtual diffraction
        self.calc_xyo = []             # X, Y, projected on the detector and omega

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
        self.ms_lat_defgrads = ms_data[:, range(7, 13)]

    def get_diffraction_angles(self):
        cfg = self.cfg
        logger = self.logger

        # Number of cores for multiprocessing
        num_cores = cfg.multiprocessing

        # Initialize a new heXRD experiment
        ws = expt.Experiment()

        cwd = cfg.working_dir

        materials_fname = cfg.material.definitions
        material_name = cfg.material.active
        detector_fname = cfg.instrument.detector.parameters_old

        # load materials
        ws.loadMaterialList(os.path.join(cwd, materials_fname))
        mat_name_list = ws.matNames

        # Create an array of all the essential parameters to be
        # sent to parallel diffraction angle calculation routine
        fwd_model_input = []

        for xyz_i, mat_name_i, quat_i, defgrad_i in zip(self.ms_grid,
                                                       self.ms_material_ids,
                                                       self.ms_quaternions,
                                                       self.ms_lat_defgrads):

            # Need t oread chi tilt from somewhere 
            # (old detector or start using YAML detector config?)
            chi = 0.0
            ws.activeMaterial = mat_name_i.strip() #material_name

            hkls = ws.activeMaterial.planeData.hkls.T
            rmat_c = rot.rotMatOfQuat(quat_i)
            bmat = ws.activeMaterial.planeData.latVecOps['B']
            wavelength = ws.activeMaterial.planeData.wavelength

            fwd_model_input.append(
                {
                    'chi': chi,
                    'hkls': hkls,
                    'rmat_c': rmat_c,
                    'bmat': bmat,
                    'wavelength': wavelength,
                    'defgrad_i': defgrad_i
                    }
                )

        # Now we have the data, run eta, twoth, omega calculations in parallel
        logger.info("Starting virtual diffraction calculations using %i processors", num_cores)
        synth_angles_MP_output = Parallel(n_jobs=num_cores, verbose=5)(delayed(get_diffraction_angles_MP)(fwd_model_input_i) for fwd_model_input_i in fwd_model_input)

        synth_angles = np.vstack(synth_angles_MP_output)

        self.synth_angles = synth_angles
        return synth_angles

    def project_angs_to_detector(self):
        '''
        Project two-theta, eta, omega angle to detector X, Y, omega
        '''
        cfg = self.cfg
        angs = self.synth_angles

        pd, reader, detector = initialize_experiment(cfg)

        calc_xyo = detector.angToXYO(angs[:, 0], angs[:, 1], angs[:, 2])
        calc_xyo = np.transpose(calc_xyo)
        
        template = "{0:12.2f}{1:12.2f}{2:12.2f}"
        for x, y, o in calc_xyo:
            print template.format(x, y, o)

        self.calc_xyo = calc_xyo
        return calc_xyo
#--
