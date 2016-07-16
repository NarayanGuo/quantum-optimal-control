import tensorflow as tf
import numpy as np
import scipy.linalg as la
from core.TensorflowState import TensorflowState
from system.SystemParametersGeneral import SystemParametersGeneral
from math_functions.c_to_r_mat import CtoRMat
from runtime_functions.ConvergenceGeneral import ConvergenceGeneral
from runtime_functions.run_session import run_session
from math_functions.Get_state_index import Get_State_index


import random as rd
import time
from IPython import display


def Grape(H0,Hops,Hnames,U,U0,total_time,steps,states_concerned_list,convergence, reg_coeffs = None,multi_mode = None, maxA = None ,use_gpu= True, draw= None, forbidden = None, initial_guess = None, evolve = False, evolve_error = False,show_plots = True, H_time_scales = None, Unitary_error=1e-4, method = 'Adam',state_transfer = False, switch = True,no_scaling = False):
    
    
    if reg_coeffs == None:
        if evolve:
            reg_coeffs = {'alpha' : 0, 'z':0, 'dwdt':0,'d2wdt2':0, 'inter':0}
        else:
            reg_coeffs = {'alpha' : 0.01, 'z':0.01, 'dwdt':0.001,'d2wdt2':0.001*0.0001, 'inter':100}
            #reg_coeffs = {'alpha' : 0, 'z':0, 'dwdt':0.000001,'d2wdt2':0.000001, 'inter':0}
        # alpha: to make it close to a Gaussian envelope
        # z: to limit DC offset of z pulses 
        # dwdt: to limit pulse first derivative
        # d2wdt2: to limit second derivatives
        # inter: to penalize forbidden states
        #reg_coeffs = {'alpha' : 0, 'z':0, 'dwdt':0,'d2wdt2':0, 'inter':0}
        
    if maxA == None:
        if initial_guess == None:
            maxAmp = 4*np.ones(len(Hops))
        else:
            maxAmp = 1.5*np.max(np.abs(initial_guess))*np.ones(len(Hops))
    else:
        maxAmp = maxA
    
            
    
    
    
    class SystemParameters(SystemParametersGeneral): #build pyhton system parameters
        
        def __init__(self):
            SystemParametersGeneral.__init__(self,H0,Hops,Hnames,U,U0,total_time,steps,forbidden,states_concerned_list,multi_mode,maxAmp, draw,initial_guess, evolve, evolve_error, show_plots, H_time_scales,Unitary_error,state_transfer,no_scaling )
        
    sys_para = SystemParameters()
    if use_gpu:
        dev = '/gpu:0'
    else:
        dev = '/cpu:0'
            
    with tf.device(dev):
        tfs = TensorflowState(sys_para,use_gpu) # create tensorflow graph
        graph = tfs.build_graph()
    
    class Convergence(ConvergenceGeneral):
        def __init__(self):
        # paramters
            self.sys_para = sys_para
            self.Modulation = self.sys_para.Modulation
            self.Interpolation = self.sys_para.Interpolation
            
            

            if 'rate' in convergence:
                self.rate = convergence['rate']
            else:
                self.rate = 0.01
            
            if 'update_step' in convergence:
                self.update_step = convergence['update_step']
            else:
                self.update_step = 100
                
            if 'conv_target' in convergence:
                self.conv_target = convergence['conv_target']
            else:
                self.conv_target = 1e-8
                
            if 'max_iterations' in convergence:
                self.max_iterations = convergence['max_iterations']
            else:
                self.max_iterations = 5000    
            
            if 'learning_rate_decay' in convergence:
                self.learning_rate_decay = convergence['learning_rate_decay']
            else:
                self.learning_rate_decay = 5000
            
            if 'min_grad' in convergence:
                self.min_grad = convergence['min_grad']
            else:
                self.min_grad = 1e-25 
            


            
            self.reg_alpha_coeff = reg_coeffs['alpha']

            self.z_reg_alpha_coeff = reg_coeffs['z']

            self.dwdt_reg_alpha_coeff = reg_coeffs['dwdt']
            self.d2wdt2_reg_alpha_coeff = reg_coeffs['d2wdt2']

            self.inter_reg_alpha_coeff = reg_coeffs['inter']
            

            self.reset_convergence()  
    conv = Convergence()
    
    try:
        SS = run_session(tfs,graph,conv,sys_para,method,switch = switch, show_plots = sys_para.show_plots)
        return SS.uks,SS.Uf
    except KeyboardInterrupt:
        display.clear_output()
    
    
   
