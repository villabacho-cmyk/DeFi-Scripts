**Lighter funding to Blockpit**

Run script in MacOS Terminal
  
  > python3 lighter_funding_to_blockpit.py lighter_funding_history.csv funding_for_blockpit.csv

converts the lighter funding history to "Derivative Profit" or "Derivative Loss" Type transactions
Processes each asset individually
Adds up 7 days of funding for each asset and uses the start date of each 7 day period for the blockpit transaction

!!Always processes the whole input file. So when repeating the process make sure that all fundings that have already been imported to blockpit are manually deleted from the input file!!


