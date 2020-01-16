#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 15 09:35:43 2019

This is a master script for testing different modules

@author: Qingshi
"""

"""
===============
Import packages
===============
"""
import LA_LCA_module3
import LA_TEA_module3


"""
===============
Test LCA module
===============
"""

##create a LCA object: this will automatically load the brightway2 package and load the default db and lcia methods
##this may take a few minutes
lca_obj=LA_LCA_module3.LA_LCA('test_LCA_module')

##load other db
##this may take a few minutes
db_path_name_dict={"ecoinvent 3.5 cutoff": "/Users/Qingshi/Downloads/ecoinvent 3.5_cutoff_ecoSpold02/datasets"} # {'db_name':'db_location'}
lca_obj.import_db(db_path_name_dict)

##load foreground LCI
##this may take a few minutes
forground_db_name="LA_ei35_cutoff"
input_file_path="/Users/Qingshi/Desktop/[Brightway2] study/LA project/Brightway2_input_LA_ei35_cutoff_w_uncertainty.xlsx"
db_mapping_dict={"self":('name', 'unit', 'location','reference product'),
                 "ecoinvent 3.5 cutoff":('name', 'unit', 'location','reference product'),
                 "biosphere3":('name', 'unit', 'location')}
lca_obj.import_foreground(forground_db_name,input_file_path,db_mapping_dict)

##calculate LCA results
lcia_methods=[('ReCiPe Midpoint (H)', 'climate change', 'GWP100'),('ReCiPe Midpoint (H)', 'freshwater eutrophication', 'FEP')]
lca_obj.calc_lca(lcia_methods,lca_obj.foreground_db) #default values for other args: FU_activity_code='ThisIsFU',amount_FU=1

#print out the LCA results
print (lca_obj.LCA_results_dict)


##analyze LCA results
##this may take a few minutes
impact_of_interest=(('ReCiPe Midpoint (H)', 'climate change', 'GWP100'))
lca_obj.analyze_lca(impact_of_interest) #default values for other args: n_top_items=5,analysis_done=False

#print out the LCA results grouped by the tag of interest
print (lca_obj.techno_impact_results_grouped)


##generate plots
plot_type='waterfall chart'
x_label='Impact results'
y_label='Group tags'

lca_obj.gen_fig(lca_obj.techno_impact_results_grouped,plot_type,x_label,y_label)

#print out top n processes that contribute most to the impact of interest
print (lca_obj.top_processes)


##generate random samples
lca_obj.parse_uncertainty(lca_obj.foreground_db,'Lactic acid production from electrocatalysis',15)
print (lca_obj.linked_rand_samples)
#save these random samples for use in Monte Carlo
linked_rand_samples=lca_obj.linked_rand_samples
n_iter=lca_obj.n_iter

##perform MC
lca_obj.foreground_monte_carlo(linked_rand_samples)
print (lca_obj.foreground_MC_LCA_results)
print (lca_obj.foreground_MC_LCA_results[0])



"""
===============
Test TEA module
===============
"""

##create a TEA object
TEA_obj=LA_TEA_module3.LA_TEA()

##import TEA template
TEA_template_path='/Users/Qingshi/Desktop/for TEA module_local copy/TEA_user_input_Dec.19 sim results_template update_Jan 07_qt_test.xlsx'
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


##update process inventory for electrocatalysis step
#sht_cel_new_val_dict={'Electrocatalysis':[{'B4':1500000},{'B6':-1200000}]} #B4 is the cell for 'glycerine', 'B6 is for 'methanol'
#TEA_obj.update_cells(sht_cel_new_val_dict)
##run intermediate calculation again
#TEA_obj.interm_calc()
#print ("NPV: ", TEA_obj.NPV)

##Monte Carlo
lookup_dict={'market for electricity, medium voltage':'B12','esterification of soybean oil':'B4', \
             'treatment of hazardous waste, hazardous waste incineration':'B18', \
             'steam production, as energy carrier, in chemical industry':'B11', \
             'lime production, milled, loose':'B5','methanol production':'B6', \
             'market for sodium hydroxide, without water, in 50% solution state':'B7', \
             'sulfuric acid production': 'B8', \
             'water production, completely softened, from decarbonised water, at user':'B9', \
             'oxidation of methanol':'B14','cooling water production_customized':'B10'}

TEA_obj.foreground_monte_carlo(linked_rand_samples,lookup_dict,'Electrocatalysis',n_iter)
print (TEA_obj.foreground_MC_TEA_results)

