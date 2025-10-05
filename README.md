**aster_spot_blockpit.py**

Run script in MacOS Terminal

> python3 aster_spot_blockpit.py aster_copy_paste.txt aster_spot_blockpit.csv

copy paste trade history directly from aster website and dump in to aster_copy_paste.txt
make sure to use plaintext format in txt file 

Assumes that all fees are paid in USDT --> hardcoded

So if you are using aster to pay fees or are trading USDC, it needs to be adapted

Adds "Aster Spot" to comment section for each trade

Integration Name "Aster"


**lighter_funding_to_blockpit.py**

Run script in MacOS Terminal
  
  > python3 lighter_funding_to_blockpit.py lighter_funding_history.csv funding_for_blockpit.csv

converts the lighter funding history to "Derivative Profit" or "Derivative Loss" Type transactions
Processes each asset individually
Adds up 7 days of funding for each asset and uses the start date of each 7 day period for the blockpit transaction

Uses Integration Name "lighter.xyz"

!!Always processes the whole input file. So when repeating the process make sure that all fundings that have already been imported to blockpit are manually deleted from the input file!!


**lighter_trades_to_blockpit.py**

Run script in MacOS Terminal
  
  > python3 lighter_trades_to_blockpit.py lighter_trades_history.csv trades_for_blockpit.csv
 
Converts all trades to Blockpit format. Creates transactions of Type "Derivative Profit" or "Derivative Loss"

Uses Integration Name "lighter.xyz"

No additional Info added to comments. Improvement could be to add trade details as comment (Asset, long/short, price etc.)
