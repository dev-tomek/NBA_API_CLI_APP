# NBA_API_CLI_APP
# Author: Tomasz Kuczyński
# script/CLI that processes data from external API about NBA related data

Script usage examples:
 - In the terminal window:
   - python script.py grouped-teams 
   - python script.py player-stats --name Kyle
      #--name (required)
   - python script.py teams-stats --season 2018 --output csv 
      #--season (required) --output (not required), default stdout
                          Possible outputs: csv, stdout, json
      
 Script flaws / areas for prospective improvement:
- Insufficient exception handling
- Lack of support for sqlite output
- async requests should be implemented in order to speed up the api calls
- conversion of the script so that it is in accordance with OOP paradigm
- spliting the functions into some smaller ones
- more precise docstrings
