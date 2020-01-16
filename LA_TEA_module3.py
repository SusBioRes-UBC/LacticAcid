#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec 21 02:34:14 2019

This module calculates the economic performance of lactic acid production via electrocatalysis


@author: Qingshi
"""

"""
===============
import packages
===============
"""
import xlwings as xw
import collections


class LA_TEA():
    """
    ===========================================================================
    [Caution] create a new object for each iteration during stochastic modeling 
    ===========================================================================
    """
    
    def __init__(self):

        print ("[Caution] xlwings will open the input file and make changes directly there. So MAKE A COPY of the original input file before proceeding any further!")
        ##initialize inventory calculation label
                                
        
    def import_parse_template(self,TEA_template_path):
        
        """
        ============================
        Import the TEA data template
        ============================
        """      
        self.TEA_input_wb=xw.Book(TEA_template_path)
        
        
        """
        ===========================
        Parse the imported TEA data
        ===========================
        """
        ##create a dict of defined names (i.e., named ranges) and their correponding cell ranges
        self.parsed_dn={name.name : name.refers_to[1:] for name in self.TEA_input_wb.names}
        
    
    def interm_calc(self):
        
        """
        ============================================
        Perform intermediate calculation of interest
            [Caution] this method is hard-coded
        ============================================
        """
        ##intermediate calculation happens in the 'Intermediate' sheet
        self.interm_sht=self.TEA_input_wb.sheets['Intermediate']
        
        ##CAPX
        #total equipment cost
        self.interm_sht['B3'].value=f"=SUM({self.parsed_dn['Equipment_cost_col']})"
        self.total_equip_cost=self.interm_sht['B3'].value
        #total installation cost
        self.interm_sht['B4'].value=f"=SUM({self.parsed_dn['Installation_costs_col']})"
        self.total_install_cost=self.interm_sht['B4'].value
        #total CAPX
        self.interm_sht['B5'].value=self.total_equip_cost+self.total_install_cost
        self.total_CAPX=self.interm_sht['B5'].value
        
        ##Operation: these values do NOT change during model running
        self.prod_hr=self.interm_sht['B9'].value
        self.labor_hr=self.interm_sht['B10'].value
        self.total_prod_output=self.interm_sht['B11'].value
        
        ##Inventory
        #create inventory amount and cost dicts
        self.invent_amt_dict={}
        self.invent_cost_dict={}
        self.invent_rev_dict={}
        #make a new dict of parsed dn {sht_name:dn_name}
        new_dict={v.split('!')[0]:k for k,v in self.parsed_dn.items() if v.split('!')[0]=='Electrocatalysis' or 
         v.split('!')[0]=='Purification'}
        #update the inventory amount
        for row_num,cell in enumerate(self.interm_sht.range('inventory_amt_col')):
            cell.value=0.0
            for sht_name,dn_name in new_dict.items():
                cell.value+=self.TEA_input_wb.sheets[sht_name].range(dn_name)[row_num].value
            cell.value*=self.total_prod_output
            self.invent_amt_dict[self.interm_sht.range('inventory_name_col')[row_num].value]=cell.value
        #update the inventory cost
        for row_num,cell in enumerate(self.interm_sht.range('inventory_cost_col')):
            cell.value=0.0
            temp_cost_factor=self.TEA_input_wb.sheets['Factors'].range('cost_rev_factor_col')[row_num].get_address(False,False,True)
            temp_amt_inventory=self.interm_sht.range('inventory_amt_col')[row_num].get_address()
            cell.value=f"=IF({temp_amt_inventory}*{temp_cost_factor}>=0,0,{temp_amt_inventory}*{temp_cost_factor})"
            self.invent_cost_dict[self.interm_sht.range('inventory_name_col')[row_num].value]=cell.value            
        #update the inventory revenue
        for row_num,cell in enumerate(self.interm_sht.range('inventory_rev_col')):
            cell.value=0.0
            temp_cost_factor=self.TEA_input_wb.sheets['Factors'].range('cost_rev_factor_col')[row_num].get_address(False,False,True)
            temp_amt_inventory=self.interm_sht.range('inventory_amt_col')[row_num].get_address()
            cell.value=f"=IF({temp_amt_inventory}*{temp_cost_factor}>=0,{temp_amt_inventory}*{temp_cost_factor},0)"
            self.invent_rev_dict[self.interm_sht.range('inventory_name_col')[row_num].value]=cell.value 
        
        ##Total cost and revenue
        self.total_op_cost=sum(self.invent_cost_dict.values())
        self.total_pay_cost=self.TEA_input_wb.sheets['Operation param'].range('C6').value \
        *self.TEA_input_wb.sheets['Operation param'].range('C4').value*self.TEA_input_wb.sheets['Factors'].range('F3').value \
        *(1+self.TEA_input_wb.sheets['Factors'].range('F4').value/100)
        self.total_other_cost=self.TEA_input_wb.sheets['Factors'].range('J3').value+self.TEA_input_wb.sheets['Factors'].range('J4').value  
        self.total_cost=self.total_op_cost+self.total_pay_cost+self.total_other_cost
        self.total_rev=sum(self.invent_rev_dict.values())
        self.project_LT=int(self.TEA_input_wb.sheets['Financial param'].range('I11').value)
       
        ##EBITDA
        self.EBITDA=self.total_cost+self.total_rev
        
        ##Interest, deprecation and amortisation for FIRST year
        self.annual_depreciation=self.total_equip_cost/self.TEA_input_wb.sheets['Financial param'].range('I7').value
        self.amortized_setup_cost=self.total_install_cost/self.TEA_input_wb.sheets['Financial param'].range('I9').value
        self.interest_1st_yr=self.total_CAPX*self.TEA_input_wb.sheets['Financial param'].range('I6').value/100 \
        *self.TEA_input_wb.sheets['Financial param'].range('I5').value/100
        self.total_IDA_1st_yr=self.interest_1st_yr+self.annual_depreciation+self.amortized_setup_cost
        #Create a list of interest expense throughout the project life time
        self.interest_expense=[self.interest_1st_yr] #starts at yr 1
        for yr in range (1,self.project_LT): #the interest of yr2 depends on the remaining debt after yr1
            self.interest_expense.append(self.TEA_input_wb.sheets['Financial param'].range('I5').value/100 \
            *(self.total_CAPX-(self.annual_depreciation+self.amortized_setup_cost)*yr))
        
        ##income and cash flow
        #net income before and after tax
        self.net_income_bt=[] #starts at yr 1
        self.net_income_at=[] #starts at yr 1
        self.net_income_bt.append(self.EBITDA-self.total_IDA_1st_yr)
        for yr in range(1,self.project_LT):
            temp_income=self.EBITDA-self.TEA_input_wb.sheets['Financial param'].range('I5').value/100 \
            *(self.total_CAPX-(self.annual_depreciation+self.amortized_setup_cost)*yr)-(self.annual_depreciation+self.amortized_setup_cost)
            self.net_income_bt.append(temp_income)
        for income in self.net_income_bt:
            self.net_income_at.append(income*(1-self.TEA_input_wb.sheets['Financial param'].range('I10').value/100))        
        #net cash flow after tax
        self.net_cf_at=[-self.total_CAPX] #starts at yr 0
        for income in self.net_income_at:
            self.net_cf_at.append(income+self.annual_depreciation+self.amortized_setup_cost)
        
        ##NPV
        #self.NPV=np.npv(self.TEA_input_wb.sheets['Financial param'].range('I4').value/100,self.net_cf_at[1:])-self.total_CAPX
        self.interm_sht['B55'].value=f"=NPV({self.TEA_input_wb.sheets['Financial param'].range('I4').value/100},{self.net_cf_at[1:]})-{self.total_CAPX}"
        self.NPV=self.interm_sht['B55'].value
        
        ##IRR
        self.interm_sht['B56'].value=f"=IRR({self.net_cf_at})"        
        self.IRR=self.interm_sht['B56'].value
        
        ##Min sales price
        self.total_fixed_cost=[self.total_pay_cost+self.total_other_cost-(self.annual_depreciation \
                               +self.amortized_setup_cost+interest) for interest in self.interest_expense] #starts at yr1     
        self.min_sale_pr=[-fixed_cost/self.total_prod_output+(-self.total_op_cost/self.total_prod_output) for fixed_cost in self.total_fixed_cost] #starts at yr 1

    
    def update_cells (self,sht_cel_new_val_dict):
        
        """
        ============================================
        Update the cells of interest with new values
        ============================================
        """
        ##a nested dict of {sht_name: [{cel_range_1:new_vals_1},{cel_range_2:new_vals_2}..]}
        self.sht_cel_new_val_dict=sht_cel_new_val_dict 
        
        for sht_name, cel_new_val_lst in self.sht_cel_new_val_dict.items():
            temp_sht=self.TEA_input_wb.sheets[sht_name]
            for cel_new_val_dict in cel_new_val_lst:
                temp_sht.range([*cel_new_val_dict][0]).value=[*cel_new_val_dict.values()]

      
    def foreground_monte_carlo (self,linked_rand_samples,lookup_dict,sht_name,n_iter):
        
        """
        =======================================================
        Reformat the random samples into 'sht_cel_new_val_dict'
        =======================================================
        """
        ##initiate results dict: {iter1: TEA_result, iter2: TEA_result,...}
        self.foreground_MC_TEA_results={}
        
        ##perform MC
        for iter in range(n_iter):
            #initiate the 'sht_cel_new_val_dict'
            self.temp_sht_cel_new_val_dict=collections.defaultdict(list)
            #update the exchanges of the activity of interest
            for k,v in linked_rand_samples.items():
                #reformat the random samples into '{sht_name: [{cel_range_1:new_vals_1},{cel_range_2:new_vals_2}..]}'
                #[caution] need to pay attention to the pos/neg sign of each cell
                temp_sht=self.TEA_input_wb.sheets[sht_name]
                sign=-1 if temp_sht.range(lookup_dict[k]).value<0 else 1 #-1 for inputs, 1 for outputs
                self.temp_sht_cel_new_val_dict[sht_name].append({lookup_dict[k]:abs(v[iter])*sign})
            #update cell values
            self.update_cells(self.temp_sht_cel_new_val_dict)
            #re-do the intermediate calc
            self.interm_calc()
            #store results of interest
            self.foreground_MC_TEA_results[iter]={'NPV':self.NPV,'IRR':self.IRR,'min sale price':self.min_sale_pr}
        
        
        
        
        
        
        
        