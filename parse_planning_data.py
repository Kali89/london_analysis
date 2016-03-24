import pandas as pd
import datetime

planning = pd.read_csv('new_planning_data.csv')
planning['Date'] = planning.Date.apply(lambda x: None if x == '--' else x)
no_null_planning = planning[pd.isnull(planning).any(axis=1) == False]
no_null_planning['Date'] = pd.to_datetime(no_null_planning.Date)
no_null_planning.sort('Date', inplace=True)
no_null_planning['Postcode'] = no_null_planning.Address.apply(lambda x: ' '.join(x.strip().replace('\n', ',').split(',')[-1].split()[-2:]))

interesting_decisions = no_null_planning[(no_null_planning.Status == 'FINAL DECISION') & (no_null_planning.Outcome.isin(['Refusal of permission', 'Refuse permission and take enforcement']))]

last_years_decisions = interesting_decisions[interesting_decisions.Date > datetime.datetime.now() - datetime.timedelta(days=365)]

refused_change_of_use = last_years_decisions[last_years_decisions.Description.apply(lambda x: 'Change of use' in x) == True]

print(refused_change_of_use)
