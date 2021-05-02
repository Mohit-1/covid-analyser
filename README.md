# covid-analyser

A script that fetches the COVID-19 data, and analyses it to generate metrics for each state and sorts them in a table.

#### Usage instructions:
virtualenv -p python3 venv

source venv/bin/activate

pip3 install -r requirements.txt

python3 covid_analysis.py (use the command line argument '--local' to use the local file for analysis, to avoid hitting the API)

#### Data source -
https://api.covid19india.org/data.json
