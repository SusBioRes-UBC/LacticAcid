#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 14 01:50:07 2019

This module calculates the environmental impacts of lactic acid production via electrocatalysis

@author: Qingshi
"""


"""
===============
import packages
===============
"""
from brightway2 import*
from bw2analyzer import ContributionAnalysis
import stats_arrays
#from bw2analyzer import traverse_tagged_databases
#from bw2analyzer.tagged import recurse_tagged_database
import collections
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.offline import plot


class LA_LCA:
    
    def __init__ (self,project_name):
        
        """
        ==========================
        create a brightway2 project
        ==========================
        """
        self.project_name=project_name
        projects.set_current(self.project_name)
        #print (projects.current)
        
        ##set up default dataset (biosphere3) and LCIA methods for current project
        bw2setup()
        

    def import_db (self,db_path_name_dict):
        
        """
        ==============================
        import database(s) of interest
        ==============================
        """
        self.db_path_name_dict=db_path_name_dict
        
        for key, val in self.db_path_name_dict.items():
            self.db_location=val
            self.db_name=key
        
            import_obj=SingleOutputEcospold2Importer(
                self.db_location,
                self.db_name)
            import_obj.apply_strategies()
            import_obj.statistics()
            
            ##write database
            import_obj.write_database()
        

    def import_foreground (self,forground_db_name,input_file_path,db_mapping_dict):
        
        """
        =========================================
        import foreground data of the LCA project
        =========================================
        """
        ##prepare foreground db
        self.forground_db_name=forground_db_name #this must be identical to the "Database" name in the input spreadsheet 
        self.input_file_path=input_file_path
        self.db_mapping_dict=db_mapping_dict #{db_name:('field_1','field_2',...)}
        
        self.import_foreground_obj=ExcelImporter(self.input_file_path)
        self.import_foreground_obj.apply_strategies()
        for db_name,fields_to_map in self.db_mapping_dict.items():
            if db_name=='self':
                self.import_foreground_obj.match_database(fields=fields_to_map) #link within the foreground processes
            else:
                self.import_foreground_obj.match_database(db_name,fields=fields_to_map) #mapping to processes in other db
        self.import_foreground_obj.statistics()
        #import_LA_foreground.write_excel(only_unlinked=True)
        
        self.import_foreground_obj.write_database()
        self.foreground_db=Database(forground_db_name)
        
        
    def calc_lca (self,lcia_methods,db,FU_activity_code='ThisIsFU',amount_FU=1,calc_done=False):

        """
        =====================
        calculate LCA results
        =====================
        """
        self.FU_activity_code=FU_activity_code
        self.FU_activity=[act for act in db if act['code']==self.FU_activity_code][0]
        self.amount_FU=amount_FU
        self.lcia_methods=lcia_methods #a list of LCIA methods of interest: [(method1),(method2)...]
        self.calc_done=calc_done #label to indicate if lca calucation has ever been performed
       
        ##create dict to store: (1) LCA results, (2) top processes (including backgr db)
        self.LCA_results_dict={}
        self.top_processes_dict={}
        
        ##create a ContributionAnalysis object
        self.contribut_anal_obj=ContributionAnalysis()

        for method in self.lcia_methods:
            self.lca=LCA({self.FU_activity:self.amount_FU},
                method)
            self.lca.lci()
            self.lca.lcia()
            self.LCA_results_dict[method]=self.lca.score
            self.top_processes_dict[method]=self.contribut_anal_obj.annotated_top_processes(self.lca) #'.annotated_top_processes' returns a list of tuples: (lca score, supply, activity).
            
        ##update the label to True
        self.calc_done=True

    def analyze_lca (self,impact_of_interest,n_top_items=5,analysis_done=False):
        
        """
        ===================
        Analyze LCA results
            outputs for a given impact cateogry: 
                (1) top technosphere processes from all db (including backgr db)
                (2) "group_tag" results for foreground db
        ===================
        """
        self.impact_of_interest=impact_of_interest
        self.n_top_items=n_top_items #number of top items (e.g., top processes) of interest
        assert self.impact_of_interest in self.LCA_results_dict.keys(), "This method is not in your LCIA method list!"
        self.analysis_done=analysis_done
        ##create a dict to store impact results by 'group_tag' (technoshpere exchanges only)
        self.techno_impact_results_grouped=collections.defaultdict(list)

        while not self.analysis_done: #if analysis has not been done yet
            ##find top technosphere processes (including background db)
            self.top_processes={self.impact_of_interest : self.top_processes_dict[self.impact_of_interest][:self.n_top_items+1]}

            ##group the results by tag
            for exc in self.FU_activity.technosphere():
                self.lca2=LCA({exc.input : exc['amount']},
                               self.impact_of_interest)
                self.lca2.lci()
                self.lca2.lcia()
                self.techno_impact_results_grouped[exc['group_tag']].append(self.lca2.score)
            
            self.techno_impact_results_grouped={key : sum(val) for key, val in self.techno_impact_results_grouped.items()}
            
            ##finally, update the label to True
            self.analysis_done=True
     
    def gen_fig (self,data_to_plot_dict,plot_type,x_label,y_label):
        
        """
        ================
        Generate figures
        ================
        """
        assert self.analysis_done==True,"please run the 'analyze_lca' method first!"        
        
        self.data_to_plot_dict=data_to_plot_dict #input data must be in the dict form
        self.df_for_plot=pd.DataFrame.from_dict([self.data_to_plot_dict]) #convert to a pandas dataframe for plotting
        
        if plot_type=='bar plot':
            ##bar chart for top processes (x-axis=impact results, y-axis=process names)
            ax=self.df_for_plot.plot(kind='barh')
            ax.set_xlabel(x_label, labelpad=20, weight='bold', size=12)
            ax.set_ylabel(y_label, labelpad=20, weight='bold', size=12)
        elif plot_type=='waterfall chart':
            ##waterfall chart for "group_tag" results (x-axis=group names, y-axis=impact results)
            #prepare param for Plotly
            measure_type=['relative']*len(self.df_for_plot.columns) #first n columns of the waterfall chart 
                #should represent relative changes from each column (e.g., waste treatment) of the dataframe
            measure_type.append('total') #add a represenation of net impact which is the total (sum) of individial changes
            self.df_for_plot['net']=self.df_for_plot.values.sum()#add a column corresponding to net impact
            values_to_plot=[val for lst in self.df_for_plot.values.tolist() for val in lst] #flatten the nested list of df.values
            values_as_text=[str(round(val,1)) for val in values_to_plot]
            waterfall_x_label=list(self.df_for_plot.columns)
        
            
            #create the plot object
            fig = go.Figure(go.Waterfall(
                    name = '-'.join(self.impact_of_interest), orientation = "v",
                    measure = measure_type,
                    x = waterfall_x_label,
                    textposition = "outside",
                    text = values_as_text,
                    y = values_to_plot,
                    connector = {"line":{"color":"rgb(63, 63, 63)"}},
                    ))

            fig.update_layout(
                    showlegend = True)

            #fig.show() #only works if you are using Jupyter Notebook
            plot(fig) #works for spyder, will create a temp html file to host the fig
            
        else:
            print ("Please choose 'bar plot' or 'waterfall chart' ")


        
        
    def gen_report (self):
        """
        =================================
        Generate a report for LCA results
        =================================
        """
        assert self.analysis_done==True,"please run the 'analyze_lca' method first!"
        pass
    
    
    def parse_uncertainty (self,db,act_name,n_iter):
        """
        ==============================================
        Parse the uncertainty data of a given activity
        ==============================================
        """
        #initiate the check
        self.no_uncertainty_dist=False
        
        self.n_iter=n_iter #save number of iterations for Monte Carlo simulation
        
        #identify the actitvity of interest
        self.act_uncertain=[act for act in db if act['name']==act_name][0]
        
        #parse uncertainty data into a list of dicts
        self.uncertain_list=[{'loc':exc['loc'],'scale':exc['scale'],'uncertainty type':exc['uncertainty type']} for exc in self.act_uncertain.technosphere() if exc['uncertainty type']!=0]
        
        """ check if uncertainty type is specified """
        if len(self.uncertain_list)==0:
            print ("\n no uncertainty distribution is specified! \n")
            self.no_uncertainty_dist=True
        else:            
            #get the corresponding name of the exchanges
            self.uncertain_names=[exc['name'] for exc in self.act_uncertain.technosphere() if exc['uncertainty type']!=0]    
                
            #create uncertainty variables
            self.uncertain_var=stats_arrays.UncertaintyBase.from_dicts(*self.uncertain_list)
            
            #generate random samples
            self.rand_sample_gen=stats_arrays.MCRandomNumberGenerator(self.uncertain_var)
            self.rand_samples=np.array([self.rand_sample_gen.next() for _ in range(self.n_iter)])
            
            #link random samples to the corresponding names of exchanges
            """Caution: self.uncertain_names[col_i] could have the same name as self.uncertain_names[col_j], 
                    if there exist more than one of the same exchange
            """
            self.linked_rand_samples={}
            for col in range(self.rand_samples.shape[1]):
                self.linked_rand_samples[self.uncertain_names[col]]=self.rand_samples[:,col]
        
            
        
    def foreground_monte_carlo (self,linked_rand_samples):
        """
        =====================================================================================
        Perform Monte Carlo simulation for foreground activities only
            Key assumptions:
                -same db as what's used in '.parse_uncertainty'
                -same activity of interest as what's used in '.parse_uncertainty'
                -number of iterations must be the same as that's used in '.parse_uncertainty'
                -deterministic LCA must be done before doing MC (so that lcia methods are
                imported already)
        =====================================================================================
        """
        ##check if a dterministric LCA has been performed
        assert self.calc_done==True,"Please perform a deterministic LCA using '.calc_lca' method first!"
        
        ##initiate results dict: {iter1: [{lcia1:result,lcia2:result,...}], iter2:[{lcia1:result,lcia2:result,...}]...}
        self.foreground_MC_LCA_results=collections.defaultdict(list)
        
        ##perform MC
        for iter_ in range(self.n_iter):
            #update the exchanges of the activity of interest
            for k,v in linked_rand_samples.items():
                for exc in self.act_uncertain.technosphere(): #self.act_uncertain from '.parse_uncertainty'
                    if exc['name']==k:
                        exc['amount']=v[iter_]
                        exc.save()
            #do LCA
            self.calc_lca(self.lcia_methods,self.foreground_db)
            self.foreground_MC_LCA_results[iter_].append(self.LCA_results_dict)
        
        #print ("\n, check out the raw MC results: ", self.foreground_MC_LCA_results, "\n")
        
        