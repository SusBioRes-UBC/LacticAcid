The LCA module provides a quantitative estimation of the environmental impacts of lactic acid production from electrocatalysis

### Last update: 
12/18/2019

### Files:
#### LA_LCA_module2.py: 
class 'LA_LCA' that contains methods for performing a LCA and results analysis
#### test_field_for_modules.py: 
a script where different methods of the class 'LA_LCA' are tested

### Available methods in class 'LA_LCA':
  #### __init__(self,project_name): 
  set up the LCA project
  #### .import_db: 
  import database(s) of interest
  #### .import_foreground: 
  import foreground inventory data from input template (e.g., 'Brightway2_input_LA_ei35_cutoff.xlsx')
  #### .calc_lca: 
  calculate the LCA results with respect to impact analysis method(s) of interest
  #### .analyze_lca: 
  ananlyze the LCA results (e.g., identify top n processes that contribute most to the impacts; groupping results by tag of interest)
  #### .gen_fig: 
  generate a (horizontal) bar plot or a waterfall chart for the LCA results
  
### Methods to be developed for class 'LA_LCA':
  #### .gen_report: 
  export a customized LCA report
  #### .monte_carlo: 
  performs Monte Carlo simulations
