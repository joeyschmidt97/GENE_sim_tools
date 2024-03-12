This code is used to regroup simulation data from GENE gyrokinetic simulations and collect and rebundle simulations that have similar specified properties (such as the same resolution). This allows for effecient rebundling of simulation data for easy cross comparison (such as resolution checks against several different resolution bounds).


It functions by specifying a list of dataframes and/or paths (whihc are automatically converted to dfs), the desired quantities you want to bundle simulations by, and the quantities you want bundled. 

For example, if you want to compare growth rates for two different `nz0` values you would input the dfs/paths to the simulations with different nz0-values, group_by 'nz0', and bundle_outputs = ['gamma', 'omega']. This would yield a dataframe object with two rows distinguished by their nz0-value with bundled 'gamma' and 'omega' values.
