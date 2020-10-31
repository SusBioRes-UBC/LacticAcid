#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 09:35:43 2019

This is a master script for running LCA and TEA for lactic acid production

Data version: "Brightway2_input_LA_ei35_cutoff_w_uncertainty_adjusted for GA.xlsx" @ Aug.11, 2020

@author: Qingshi
"""

"""
===============
Import packages
===============
"""
import numpy as np
import LA_LCA_module3
import LA_TEA_module3
import GSA_module
import scipy.stats as st
import brightway2 as bw

    

"""
===============
Run nominal LCA 
===============
"""

##create a LCA object: this will automatically load the brightway2 package and load the default db and lcia methods
##this may take a few minutes
lca_obj=LA_LCA_module3.LA_LCA('test_LCA_module')

##load other db
##this may take a few minutes
if not "ecoinvent 3.5 cutoff" in list(bw.databases):
    db_path_name_dict={"INPUT PATH OF ECOINVENT DATABASE HERE"} # {'db_name':'db_location'}
    lca_obj.import_db(db_path_name_dict)
else:
    print ("\n ==== db 'ecoinvent 3.5 cutoff' already imported! ==== \n")

##load foreground LCI
##this may take a few minutes
forground_db_name="LA_ei35_cutoff"
input_file_path="INPUT PATH OF BRIGHTWAY2 INPUT TEMPLATE HERE"
db_mapping_dict={"self":('name', 'unit', 'location','reference product'),
                 "ecoinvent 3.5 cutoff":('name', 'unit', 'location','reference product'),
                 "biosphere3":('name', 'unit', 'location')}
lca_obj.import_foreground(forground_db_name,input_file_path,db_mapping_dict)

##calculate LCA results
lcia_methods=[('ReCiPe Midpoint (H)', 'climate change', 'GWP100')] #,('ReCiPe Midpoint (H)', 'freshwater eutrophication', 'FEP')
lca_obj.calc_lca(lcia_methods,lca_obj.foreground_db) #default values for other args: FU_activity_code='ThisIsFU',amount_FU=1

#print out the LCA results
print (lca_obj.LCA_results_dict)


##analyze LCA results
##this may take a few minutes
impact_of_interest=(('ReCiPe Midpoint (H)', 'climate change', 'GWP100'))
lca_obj.analyze_lca(impact_of_interest) #default values for other args: n_top_items=5,analysis_done=False

#print out the LCA results grouped by the tag of interest
print (lca_obj.techno_impact_results_grouped)


"""
==============
Run GSA module
==============
"""

##create a GSA object
GSA_obj=GSA_module.Perform_GSA()

##generate samples
n_sample=1 #total_n_sample = n_sample∗(2*num_vars+2)
n_vars=3 #three variables: 1) GLY/kg LA, 2) electricity use/kg LA, 3) heating energy/kg LA 
        #cooling energy is strongly correlated with heating, so no separate entry of it. 
        #Use a linear factor (e.g.,19.66101695 MJ/heat divided by 12.88135593 MJ/cool, based on AspenPlus sim) 
        #to calculate the cooling energy demand accordingly
var_names_lst=['GLY_var','elect_var','heating_var']
val_bounds_lst=[
        [3.471186441*1.1, 3.471186441*1.3],
        [2.50107247*1.1, 2.50107247*1.3],
        [19.66101695*1.1, 19.66101695*1.3]
        ]#assume a + (10-30%) for each variable based on the baseline scenario

GSA_obj.GSA_run(n_sample,n_vars,var_names_lst,val_bounds_lst)
sample_to_eval_model=GSA_obj.param_values
GSA_problem=GSA_obj.problem #this is needed for GSA analysis later


"""
====================
- perform MC for LCA
====================
"""

##reformat the sample data for running MC for LCA module
#link random samples to the corresponding names of exchanges (hard-coding)
linked_rand_samples={}
linked_rand_samples['esterification of soybean oil']=sample_to_eval_model[:,0] #sample values for GLY
linked_rand_samples['market for electricity, medium voltage']=sample_to_eval_model[:,1] #sample values for electricity
linked_rand_samples['steam production, as energy carrier, in chemical industry']=sample_to_eval_model[:,2] #sample value for heating
linked_rand_samples['cooling water production_customized']=sample_to_eval_model[:,2]*float(12.88135593/19.66101695) #sample value for cooling, using the factor of "MJ heat/MJ cool" from baseline 


##perform MC for LCA module
#[caution] in order for the 'lca_obj.foreground_monte_carlo()' method to function properly,
#   you will need to run 'lca_obj.parse_uncertainty' first to generate 'self.act_uncertain'
lca_obj.parse_uncertainty(lca_obj.foreground_db,'Lactic acid production from electrocatalysis',sample_to_eval_model.shape[0])

lca_obj.foreground_monte_carlo(linked_rand_samples) #use externally generated 'linked_rand_samples' instead of the one generated by 'lca_obj.foreground_monte_carlo()'

#print (lca_obj.foreground_MC_LCA_results)
#print (lca_obj.foreground_MC_LCA_results[0])



"""
======================
- perform GSA analysis
======================
"""
## create a dict to store the reformatted results for visualization later
foreground_MC_LCA_results_reformat_dict={}

#reformat the model results before feeding into GSA analysis method
for method in lcia_methods:
    ##re-arrange the foreground_MC_LCA_results {iter1: [{lcia1:result,lcia2:result,...}], iter2:[{lcia1:result,lcia2:result,...}]...}
    #the reformated variable is a list of all n_iter elements, each representing the impact result of a particular method from a given iteration
    foreground_MC_LCA_results_reformat=[v[0][method] for v in lca_obj.foreground_MC_LCA_results.values()]
    foreground_MC_LCA_results_reformat_dict[method]=foreground_MC_LCA_results_reformat

    ## calculate 95% CI
    tmp_95_CI=st.norm.interval(0.95,loc=np.mean(foreground_MC_LCA_results_reformat,axis=0),
                                                scale=st.sem(foreground_MC_LCA_results_reformat,axis=0))
    print (f"95% CI of {method} results are: ", tmp_95_CI, "\n")

    #convert the list to array
    foreground_MC_LCA_results_reformat=np.asarray(foreground_MC_LCA_results_reformat)
    #print (foreground_MC_LCA_results_reformat.shape)

    ## calculate the sensitivity indices
    GSA_obj.GSA_analyze(GSA_problem,foreground_MC_LCA_results_reformat)
    print (f"For {method}, First-order indices: ", GSA_obj.first_order_indices)
    print (f"For {method}, Second-order indices: ", GSA_obj.second_order_indices)
    print (f"For {method}, Total-order indices: ", GSA_obj.total_order_indices,"\n")


## print out top n processes that contribute most to the impact of interest
print (lca_obj.top_processes)



"""
====================
- perform MC for TEA
====================
"""

##create a TEA object
TEA_obj=LA_TEA_module3.LA_TEA()

##import TEA template
TEA_template_path='INPUT PATH OF TEA TEMPLATE HERE'
TEA_obj.import_parse_template(TEA_template_path)

##perform intermediate calculations
TEA_obj.interm_calc()
print ("NPV: ", TEA_obj.NPV)
print ("CAPX: ",TEA_obj.total_CAPX)
print ("net income before tax: ",TEA_obj.net_income_bt)
print ("net cf: ",TEA_obj.net_cf_at)
print ("calculated IRR: ",TEA_obj.IRR)
print ("min sales price: ", TEA_obj.min_sale_pr)
print ("interest payment: ", TEA_obj.interest_expense)


##Monte Carlo
lookup_dict={'market for electricity, medium voltage':'B12','esterification of soybean oil':'B4', \
             'treatment of hazardous waste, hazardous waste incineration':'B18', \
             'steam production, as energy carrier, in chemical industry':'B11', \
             'lime production, milled, loose':'B5','methanol production':'B6', \
             'market for sodium hydroxide, without water, in 50% solution state':'B7', \
             'sulfuric acid production': 'B8', \
             'water production, completely softened, from decarbonised water, at user':'B9', \
             'oxidation of methanol':'B14','cooling water production_customized':'B10'}

TEA_obj.foreground_monte_carlo(linked_rand_samples,lookup_dict,'Electrocatalysis',sample_to_eval_model.shape[0])
#print (TEA_obj.foreground_MC_TEA_results)


"""
======================
- perform GSA analysis
======================
"""
## create a dict to store the reformatted results for visualization later
foreground_MC_TEA_results_reformat_dict={}

#reformat the model results before feeding into GSA analysis method
for metric in ['NPV']: #,'IRR'
    foreground_MC_TEA_results_reformat=[v[metric] for v in TEA_obj.foreground_MC_TEA_results.values()]
    #print (foreground_MC_TEA_results_reformat)
    foreground_MC_TEA_results_reformat_dict[metric]=foreground_MC_TEA_results_reformat
    
    ## calculate 95% CI
    tmp_95_CI=st.norm.interval(0.95,loc=np.mean(foreground_MC_TEA_results_reformat,axis=0),
                                                scale=st.sem(foreground_MC_TEA_results_reformat,axis=0)) #only valid for large sample size (e.g., >=1000)
    print (f"95% CI of {metric} results are: ", tmp_95_CI, "\n")
    
    #convert the list to array
    foreground_MC_TEA_results_reformat=np.asarray(foreground_MC_TEA_results_reformat)
    #print (foreground_MC_TEA_results_reformat.shape)

    #calculate the sensitivity indices
    GSA_obj.GSA_analyze(GSA_problem,foreground_MC_TEA_results_reformat)
    print (f"For {metric}, First-order indices: ", GSA_obj.first_order_indices)
    print (f"For {metric}, Second-order indices: ", GSA_obj.second_order_indices)
    print (f"For {metric}, Total-order indices: ", GSA_obj.total_order_indices,"\n")





