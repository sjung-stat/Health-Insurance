# Your API keys
api_keys = ''  # Insert your API keys here


# Load necessary libraries
import requests
import sqlalchemy as sqla
from sqlalchemy import create_engine
import pandas as pd
import numpy as np
import seaborn as sns
import plotnine as p9
import matplotlib.pyplot as plt


# Convert JSON format into pandas dataframe
def df_converter(getrequest):
    return pd.DataFrame(getrequest.json()[1:], columns=getrequest.json()[0])


# Create engines for SQLite databases: [1] US data, [2] Georgia data (we will see that GA has the highest uninsured ratio)
healthinsurance_sqlite_db = 'healthinsurance.sqlite'
healthinsurance_conn = sqla.create_engine('sqlite:///' + healthinsurance_sqlite_db)
healthinsurance_ga_sqlite_db = 'healthinsurance.ga.sqlite'
healthinsurance_ga_conn = sqla.create_engine('sqlite:///' + healthinsurance_ga_sqlite_db)




# US data from 2010 to 2018 (state-wise)
years = 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018
state_years = pd.DataFrame()
for i in years:
    url = "https://api.census.gov/data/timeseries/healthins/sahie?get=SEXCAT,RACECAT,AGECAT,IPRCAT,NIC_PT,NUI_PT,NAME&for=state:*&time={0}&key={1}".format(i, api_keys)
    response = requests.request("GET", url)
    
    # Convert to pandas dataframe
    data = df_converter(response)
    
    # Change column names 
    data = data.rename(columns={'SEXCAT':'sex', 'RACECAT':'race', 'AGECAT':'age','IPRCAT':'income_poverty_ratio','NIC_PT':'number_insured','NUI_PT':'number_uninsured','NAME':'states','time':'year','state':'state_index'})
    
    # Convert to integer
    data["number_insured"] = data["number_insured"].astype(int)
    data["number_uninsured"] = data["number_uninsured"].astype(int)
    
    # Give actual levels in the categorical variables (e.g. in 'age', '0' indicates 'under 65 years')
    cleanup_nums = {"sex": {"0": "Both sexes", "1": "male only", "2": "female only"},
                    "race": {"0": "All Races", "1": "White alone, not Hispanic", "2": "Black alone, not Hispanic", "3": "Hispanic (any race)"},
                    "age": {"0": "under 65 years", "1": "18 to 64 years", "2": "40 to 64 years", "3": "50 to 64 years", "4": "under 19 years", "5": "21 to 64 years"},
                    "income_poverty_ratio": {"0": "All Incomes", "1": "<= 200% of Poverty", "2": "<= 250% of Poverty", "3": "<= 138% of Poverty", "4": "<= 400% of Poverty", "5": "138% to 400% of Poverty"}}
    data = data.replace(cleanup_nums)
    
    # Create ratios of insured / uninsured
    data["ratio_insured"] = data["number_insured"] / (data["number_insured"] + data["number_uninsured"])
    data["ratio_uninsured"] = 1 - data["ratio_insured"] 
    
    data.to_sql('healthinsurance', healthinsurance_conn, if_exists='append')
    




# Georgia data from 2010 to 2018 (county-wise)
years = 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018
state_years = pd.DataFrame()
for i in years:
    url_ga = "https://api.census.gov/data/timeseries/healthins/sahie?get=SEXCAT,RACECAT,AGECAT,IPRCAT,NIC_PT,NUI_PT,NAME&for=county:*&in=state:13&time={0}&key={1}".format(i, api_keys)
    response = requests.request("GET", url_ga)
    
    # Convert to pandas dataframe
    data = df_converter(response)
    
    # Change column names 
    data = data.rename(columns={'SEXCAT':'sex', 'RACECAT':'race', 'AGECAT':'age','IPRCAT':'income_poverty_ratio','NIC_PT':'number_insured','NUI_PT':'number_uninsured','time':'year','state':'state_index'})
    
    # Convert to integer
    data["number_insured"] = data["number_insured"].astype(int)
    data["number_uninsured"] = data["number_uninsured"].astype(int)
    
    # Give actual levels in the categorical variables (e.g. in 'age', '0' indicates 'under 65 years')
    cleanup_nums = {"sex": {"0": "Both sexes", "1": "male only", "2": "female only"},
                    "race": {"0": "All Races", "1": "White alone, not Hispanic", "2": "Black alone, not Hispanic", "3": "Hispanic (any race)"},
                    "age": {"0": "under 65 years", "1": "18 to 64 years", "2": "40 to 64 years", "3": "50 to 64 years", "4": "under 19 years", "5": "21 to 64 years"},
                    "income_poverty_ratio": {"0": "All Incomes", "1": "<= 200% of Poverty", "2": "<= 250% of Poverty", "3": "<= 138% of Poverty", "4": "<= 400% of Poverty", "5": "138% to 400% of Poverty"}}
    data = data.replace(cleanup_nums)

    # Create ratios of insured / uninsured
    data["ratio_insured"] = data["number_insured"] / (data["number_insured"] + data["number_uninsured"])
    data["ratio_uninsured"] = 1 - data["ratio_insured"] 
    
    data.to_sql('healthinsurance_ga', healthinsurance_ga_conn, if_exists='append')
    


# Check the data (All states)
pd.read_sql_query("select * from healthinsurance",healthinsurance_conn)


# Check the data (Georgia)
pd.read_sql_query("select * from healthinsurance_ga",healthinsurance_ga_conn)


# Average uninsured ratio in the U.S.
sql_query = """
select avg(ratio_insured), avg(ratio_uninsured)
from healthinsurance
"""
pd.read_sql_query(sql_query, healthinsurance_conn)



# Number of insured & uninsured by sex
sql_query_by_sex = """
select sex, number_insured, number_uninsured
from healthinsurance
where sex in ('female only', 'male only')
"""
by_sex = pd.read_sql_query(sql_query_by_sex, healthinsurance_conn)



# Number of insured & uninsured by race
sql_query_by_race = """
select race, number_insured, number_uninsured
from healthinsurance
where race in ('White alone, not Hispanic', 'Black alone, not Hispanic', 'Hispanic (any race)') 
"""
by_race = pd.read_sql_query(sql_query_by_race, healthinsurance_conn)


# Number of insured & uninsured by age
sql_query_by_age = """
select age, number_insured, number_uninsured
from healthinsurance
where age in ('under 19 years', '21 to 64 years')
"""
by_age = pd.read_sql_query(sql_query_by_age, healthinsurance_conn)


# Number of insured & uninsured by income poverty ratio
sql_query_by_ipr = """
select income_poverty_ratio, number_insured, number_uninsured
from healthinsurance
where income_poverty_ratio in ('138% to 400% of Poverty', '<= 138% of Poverty')  
"""
by_ipr = pd.read_sql_query(sql_query_by_ipr, healthinsurance_conn)


# Scatterplots of the above data
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, ncols=2, figsize=(15,12))
sns.scatterplot(data=by_sex, x="number_insured", y="number_uninsured", hue="sex", ax=ax1)
ax1.set_ylabel("Number uninsured")
ax1.set_xlabel("Number insured")
ax1.set_title("Sex",fontdict= {'fontsize': 15, 'fontweight':'bold'})
sns.scatterplot(data=by_race, x="number_insured", y="number_uninsured", hue="race", ax=ax2)
ax2.set_ylabel("Number uninsured")
ax2.set_xlabel("Number insured")
ax2.set_title("Race",fontdict= {'fontsize': 15, 'fontweight':'bold'})
sns.scatterplot(data=by_age, x="number_insured", y="number_uninsured", hue="age", ax=ax3)
ax3.set_ylabel("Number uninsured")
ax3.set_xlabel("Number insured")
ax3.set_title("Age",fontdict= {'fontsize': 15, 'fontweight':'bold'})
sns.scatterplot(data=by_ipr, x="number_insured", y="number_uninsured", hue="income_poverty_ratio", ax=ax4)
ax4.set_ylabel("Number uninsured")
ax4.set_xlabel("Number insured")
ax4.set_title("Income Poverty Ratio",fontdict= {'fontsize': 15, 'fontweight':'bold'})


# Uninsured ratio by Sex
sql_query_1 = """
select avg(ratio_insured) as 'Insured ratio', avg(ratio_uninsured) as 'Uninsured ratio'
from healthinsurance
where sex in ('male only', 'female only')
group by sex
"""
print(pd.read_sql_query(sql_query_1, healthinsurance_conn)) #0: female / 1: male


# Uninsured ratio by ethnicity
sql_query_2 = """
select avg(ratio_insured) as 'Insured ratio', avg(ratio_uninsured) as 'Uninsured ratio'
from healthinsurance
where race in ('White alone, not Hispanic', 'Black alone, not Hispanic', 'Hispanic (any race)')
group by race
"""
print(pd.read_sql_query(sql_query_2, healthinsurance_conn)) #0: Black alone, not Hispanic / 1: Hispanic (any race) / 2: White alone, not Hispanic


# Uninsured ratio by age group
sql_query_3 = """
select avg(ratio_insured) as 'Insured ratio', avg(ratio_uninsured) as 'Uninsured ratio'
from healthinsurance
where age in ('under 19 years', '21 to 64 years')
group by age
"""
print(pd.read_sql_query(sql_query_3, healthinsurance_conn)) #0: 21 to 64 years / 1: under 19 years


# Uninsured ratio by income poverty ratio
sql_query_4 = """
select avg(ratio_insured) as 'Insured ratio', avg(ratio_uninsured) as 'Uninsured ratio'
from healthinsurance
where income_poverty_ratio in ('<= 138% of Poverty', '138% to 400% of Poverty')
group by income_poverty_ratio
"""
print(pd.read_sql_query(sql_query_4, healthinsurance_conn)) #0: 138% to 400% of Poverty / 1: <= 138% of Poverty


# Uninsured ratio by income poverty ratio
sql_query_by_ipr = """
select income_poverty_ratio, ratio_uninsured
from healthinsurance
where income_poverty_ratio not in ('All Incomes', '138% to 400% of Poverty')
"""
by_ipr = pd.read_sql_query(sql_query_by_ipr, healthinsurance_conn)
fig, ax = plt.subplots(figsize=(30, 12))
ax = sns.violinplot(x= "income_poverty_ratio", y="ratio_uninsured", data=by_ipr, inner=None, color="0.4")
ax = sns.stripplot(x= "income_poverty_ratio", y="ratio_uninsured", data=by_ipr, order=["<= 138% of Poverty", "<= 200% of Poverty", "<= 250% of Poverty", "<= 400% of Poverty"])
ax.tick_params(labelsize=24)


# Plot the uninsured Ratio by state
sql_query_by_state = """
select states, ratio_uninsured
from healthinsurance
"""
by_state = pd.read_sql_query(sql_query_by_state, healthinsurance_conn)
sns.set_theme(style="whitegrid")
fig, axs = plt.subplots(ncols=1, figsize=(15,5))
bar_plot = sns.barplot(data=by_state, x="states", y="ratio_uninsured")
bar_plot.set(xlabel="State", ylabel = "Uninsured Ratio")
bar_plot.set_title('Uninsured Ratio by State',fontdict= {'fontsize': 20, 'fontweight':'bold'})
plt.xticks(rotation=90)
plt.show()


# 5 States with the highest and lowest uninsured ratios
state_uninsured_ratio = by_state.groupby("states").mean()
state_uninsured_ratio.sort_values(by=['ratio_uninsured'], inplace=True, ascending=False)
print(state_uninsured_ratio.head(5))    # 5 states with highest uninsured ratio
print(state_uninsured_ratio.tail(5))    # 5 states with lowest uninsured ratio


# Uninsured ratio by county in Georgia
sql_query_by_county_ga = """
select NAME, ratio_uninsured
from healthinsurance_ga
"""
by_county_ga = pd.read_sql_query(sql_query_by_county_ga, healthinsurance_ga_conn)


# Plot the uninsured ratio by county in Georgia
by_county_ga['county'] = by_county_ga['NAME'].str.split(',').str[0]
sns.set_theme(style="whitegrid")
fig, axs = plt.subplots(ncols=1, figsize=(23,5))
bar_plot = sns.barplot(data=by_county_ga, x="county", y="ratio_uninsured")
bar_plot.set(xlabel="County", ylabel = "Uninsured Ratio")
bar_plot.set_title('Uninsured Ratio by County in Georgia',fontdict= {'fontsize': 20, 'fontweight':'bold'})
plt.xticks(rotation=90)
plt.show()


# ratio of insured/uninsured by year in the US
sql_query_by_year = """
select income_poverty_ratio, year, ratio_uninsured
from healthinsurance
where (income_poverty_ratio = '138% to 400% of Poverty' or income_poverty_ratio = '<= 138% of Poverty') and year not in ('2010', '2011')

"""
by_year = pd.read_sql_query(sql_query_by_year, healthinsurance_conn)


# ratio of insured/uninsured by year in Georgia
sql_query_by_year_ga = """
select income_poverty_ratio, year, ratio_uninsured
from healthinsurance_ga
where (income_poverty_ratio = '138% to 400% of Poverty' or income_poverty_ratio = '<= 138% of Poverty') and year not in ('2010', '2011')
"""
by_year_ga = pd.read_sql_query(sql_query_by_year_ga, healthinsurance_ga_conn)


# Plot the above data
fig, ((ax1), (ax2)) = plt.subplots(2, ncols=1, figsize=(15,12))
sns.barplot(data=by_year, x="year", y="ratio_uninsured", hue="income_poverty_ratio", palette="Blues_d", ax=ax1)
ax1.set(xlabel="Year", ylabel = "Uninsured Ratio")
ax1.set_title('Uninsured Ratio Based on Year & Income Poverty Ratio in the US',fontdict= {'fontsize': 20, 'fontweight':'bold'})
sns.barplot(data=by_year_ga, x="year", y="ratio_uninsured", hue="income_poverty_ratio", palette="Blues_d", ax=ax2)
ax2.set(xlabel="Year", ylabel = "Uninsured Ratio")
ax2.set_title('Uninsured Ratio Based on Year & Income Poverty Ratio in Georgia',fontdict= {'fontsize': 20, 'fontweight':'bold'})


# Sex and state 
sql_query_by_sex_state = """
select race, ratio_uninsured, states, sex
from healthinsurance
where states in ('Georgia', 'Texas', 'Alaska', 'Massachusetts', 'District of Columbia', 'Hawaii') and sex in ('male only', 'female only')
"""
by_sex_state = pd.read_sql_query(sql_query_by_sex_state, healthinsurance_conn)


fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, ncols=3, figsize=(15,12))

# Georgia
sns.stripplot(x=by_sex_state[by_sex_state['states']=='Georgia']['sex'], y=by_sex_state[by_sex_state['states']=='Georgia']['ratio_uninsured'], ax=ax1)
ax1.set_ylabel("Uninsured Ratio")
ax1.set_xlabel("Sex")
ax1.set_title("Georgia (Highest uninsured ratio)",fontdict= {'fontsize': 10, 'fontweight':'bold'})

# Texas
sns.stripplot(x=by_sex_state[by_sex_state['states']=='Texas']['sex'], y=by_sex_state[by_sex_state['states']=='Texas']['ratio_uninsured'], ax=ax2)
ax2.set_ylabel("Uninsured Ratio")
ax2.set_xlabel("Sex")
ax2.set_title("Texas (2nd highest uninsured ratio)",fontdict= {'fontsize': 10, 'fontweight':'bold'})

# Alaska
sns.stripplot(x=by_sex_state[by_sex_state['states']=='Alaska']['sex'], y=by_sex_state[by_sex_state['states']=='Alaska']['ratio_uninsured'], ax=ax3)
ax3.set_ylabel("Uninsured Ratio")
ax3.set_xlabel("Sex")
ax3.set_title("Alaska (3rd highest uninsured ratio)",fontdict= {'fontsize': 10, 'fontweight':'bold'})

# Hawaii
sns.stripplot(x=by_sex_state[by_sex_state['states']=='Hawaii']['sex'], y=by_sex_state[by_sex_state['states']=='Hawaii']['ratio_uninsured'], ax=ax4)
ax4.set_ylabel("Uninsured Ratio")
ax4.set_xlabel("Sex")
ax4.set_title("Hawaii (3rd lowest uninsured ratio)",fontdict= {'fontsize': 10, 'fontweight':'bold'})

# District of Columbia
sns.stripplot(x=by_sex_state[by_sex_state['states']=='District of Columbia']['sex'], y=by_sex_state[by_sex_state['states']=='District of Columbia']['ratio_uninsured'], ax=ax5)
ax5.set_ylabel("Uninsured Ratio")
ax5.set_xlabel("Sex")
ax5.set_title("District of Columbia (2nd lowest uninsured ratio)",fontdict= {'fontsize': 10, 'fontweight':'bold'})

# Massachusetts
sns.stripplot(x=by_sex_state[by_sex_state['states']=='Massachusetts']['sex'], y=by_sex_state[by_sex_state['states']=='Massachusetts']['ratio_uninsured'], ax=ax6)
ax6.set_ylabel("Uninsured Ratio")
ax6.set_xlabel("Sex")
ax6.set_title("Massachusetts (Lowest uninsured ratio)",fontdict= {'fontsize': 10, 'fontweight':'bold'})



# Conditions that possibly generate highest uninsured ratio
sql_query_highest_GA = """
select avg(ratio_insured) as 'Insured ratio', avg(ratio_uninsured) as 'Uninsured ratio'
from healthinsurance
where income_poverty_ratio = '<= 138% of Poverty' and states = 'Georgia' and sex = 'male only' and race = 'Hispanic (any race)'
"""
print(pd.read_sql_query(sql_query_highest_GA, healthinsurance_conn))   # Georgia

# Same conditions as above but from MA (lowest uninsured ratio)
sql_query_highest_MA = """
select avg(ratio_insured) as 'Insured ratio', avg(ratio_uninsured) as 'Uninsured ratio'
from healthinsurance
where income_poverty_ratio = '<= 138% of Poverty' and states = 'Massachusetts' and sex = 'male only' and race = 'Hispanic (any race)'
"""
print(pd.read_sql_query(sql_query_highest_MA, healthinsurance_conn))   # Massachusetts 


# Conditions that possibly generate lowest uninsured ratio
sql_query_lowest = """
select avg(ratio_insured) as 'Insured ratio', avg(ratio_uninsured) as 'Uninsured ratio'
from healthinsurance
where income_poverty_ratio = '138% to 400% of Poverty' and states = 'Massachusetts' and sex = 'female only' and race = 'White alone, not Hispanic'
"""
print(pd.read_sql_query(sql_query_lowest, healthinsurance_conn))


# Plot the observations with the conditions that possibly give the highest uninsured ratio by year
sql_query_highest_GA_by_year = """
select age, year, ratio_uninsured
from healthinsurance
where income_poverty_ratio = '<= 138% of Poverty' and states = 'Georgia' and sex = 'male only' and race = 'Hispanic (any race)' and age not in ('under 65 years', '21 to 64 years')
"""
highest_GA_by_year = pd.read_sql_query(sql_query_highest_GA_by_year, healthinsurance_conn)
fig, ax1 = plt.subplots(1, ncols=1, figsize=(15,5))
sns.barplot(data=highest_GA_by_year, x="year", y="ratio_uninsured", hue="age", palette="Blues_d", ax=ax1)
ax1.set(xlabel="Year", ylabel = "Uninsured Ratio")
ax1.set_title('Uninsured Ratio of Hispanic males w/ low IPR in Georgia',fontdict= {'fontsize': 15, 'fontweight':'bold'})


