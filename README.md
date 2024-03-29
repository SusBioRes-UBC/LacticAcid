## Code repo for the publication: 
Tu, Qingshi, Abhijeet Parvatker, Mahlet Garedew, Cole Harris, Matthew Eckelman, Julie B. Zimmerman, Paul T. Anastas, and Chun Ho Lam. "Electrocatalysis for Chemical and Fuel Production: Investigating Climate Change Mitigation Potential and Economic Feasibility." Environmental Science & Technology 55, no. 5 (2021): 3240-3249.
=======

### Last update:
10/30/2020
<br/>
<br/>

=======
### LA_LCA_module3.py: 
class 'LA_LCA' that contains methods for performing a LCA and results analysis
<br/>
<br/>
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
  #### .parse_uncertainty
  parse the uncertainty information of a given activity
  #### .foreground_monte_carlo
  perform Monte Carlo simulation for foreground dataset only
<br/>
<br/> 
### Methods to be developed for class 'LA_LCA':
  #### .gen_report: 
  export a customized LCA report

=======
### LA_TEA_module3.py:
class 'LA_TEA' that contains methods for performing a TEA
<br/>
<br/>
### Available methods in class 'LA_TEA':
#### .import_parse_template
import TEA data input template

#### .interm_calc
perform the intermediate calculations to derive values for key variables, such as NPV

#### .update_cells
update the cells of interest in a given sheet with new values

#### .foreground_monte_carlos
perform Monte Carlo simulation for foreground dataset only

