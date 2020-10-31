#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 15:08:16 2020

This module performs global sensitivity analysis for models of interest

[Reference]
    https://salib.readthedocs.io/en/latest/basics.html#an-example

@author: Qingshi
"""

"""
===============
import packages
===============
"""
from SALib.sample import saltelli
from SALib.analyze import sobol


class Perform_GSA:
    
    def GSA_run(self,n_sample,n_vars,var_names_lst,val_bounds_lst):
        """
        =====================================================================
        this method will:
            - run the sampling procedure
            * the samples will be used by an exteranl model (e.g., LCA model)
                to generate evaluation results
        =====================================================================
        """
        
        ##define model inputs
        self.problem = {
                'num_vars': n_vars,
                'names': var_names_lst,
                'bounds': val_bounds_lst
                }
        
        ##generate samples
        #[caution] the Saltelli sampler generates: total_n_sample = n_sample∗(2*num_vars+2)
        #the samples will be used by an exteranl model (e.g., LCA model) to generate evaluation results
        self.param_values = saltelli.sample(self.problem, n_sample) #dim = (total_n_sample,num_vars)
                    

    def GSA_analyze(self,problem,eval_outcome):
        """
        =============================================================
        this method will generate the sensitivity indices of interest
        =============================================================
        """
        
        ##generate the sensitivity indices
        #Si is a Python dict with the keys "S1", "S2", "ST", "S1_conf", "S2_conf", and "ST_conf"
        #The _conf keys store the corresponding confidence intervals, typically with a confidence level of 95%
        #[caution] dim of eval_outcome has to be (total_n_sample,)
        self.Si = sobol.analyze(problem,eval_outcome)
        
        ##prepare output of sensitivity indices
        #first-order sensitivities
        self.first_order_indices = self.Si['S1']
        #second-order senitivities
        self.second_order_indices = self.Si['S2']
        #total-order sensitivities
        self.total_order_indices = self.Si['ST']
        
            
        