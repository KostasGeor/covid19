import datetime

import pandas as pd
import preprocess_data as pre
# Import the libraries
import matplotlib.pyplot as plt
import seaborn as sns

OXFORD_PATH = 'data/OxCGRT_Download_latest_data.xlsx'
ECDC_PATH = 'data/ecdcdata.csv'
OXFORD_ECDC_PATH = 'data/oxford_ecdc.csv'

ACTION_COLUMNS = ['S1_School closing', 'S2_Workplace closing', 'S3_Cancel public events', 'S4_Close public transport',
                    'S5_Public information campaigns', 'S6_Restrictions on internal movement',
                    'S7_International travel controls', 'S8_Fiscal measures', 'S9_Monetary measures',
                    'S10_Emergency investment in health care', 'S11_Investment in Vaccines', 'StringencyIndex']

# Action columns including the IsGeneral columns per action
# ACTION_COLUMNS = ['S1_School closing', 'S1_IsGeneral', 'S2_Workplace closing', 'S2_IsGeneral',
# 'S3_Cancel public events', 'S3_IsGeneral', 'S4_Close public transport', 'S4_IsGeneral',
# 'S5_Public information campaigns', 'S5_IsGeneral', 'S6_Restrictions on internal movement', 'S6_IsGeneral',
# 'S7_International travel controls', 'S8_Fiscal measures', 'S9_Monetary measures',
# 'S10_Emergency investment in health care', 'S11_Investment in Vaccines', 'StringencyIndex']


def read_preprocess_data(merge=False):
    """
    Reads and pre-processes the raw data
    :param merge: Optional parameter to specify if pre-processing for merging between ECDC and Oxford data is required
    :return: Two dataframes, one for the Oxford dataset and one for the ECDC dataset
    """
    # Read CSVs
    oxford = pd.read_excel(OXFORD_PATH, converters={'Date': str})
    ecdc = pd.read_csv(ECDC_PATH)
    # Convert country codes to ISO2
    if 'countryterritoryCode' not in ecdc and merge:  # ECDC data old format
        iso3_country_codes = pre.covert_country_name_to_country_code(ecdc['Countries and territories'].tolist(),
                                                                     convert_to='ISO3')
        ecdc['countryterritoryCode'] = iso3_country_codes
    # Remove Notes columns and last column (\t)
    oxford = oxford[oxford.columns.drop(list(oxford.filter(regex='Notes')))]
    oxford = oxford.drop(labels='Unnamed: 34', axis=1)
    # Convert dates to appropriate format
    ecdc['Date'] = ecdc['DateRep'].str.replace('-', '')

    # Fill empty cells with previous value for confirmed deaths and cases (cumulative) or 0 for rest of the fields
    oxford = oxford.groupby('CountryName').ffill().fillna(0).reindex(oxford.columns, axis=1)
    return oxford, ecdc


# Currently not used
def merge_ecdc_oxford_data():
    """
    Merges Oxford and ECDC data into a common dataframe to enable analysis
    :return: A CSV file containing the merged dataframe
    """
    # todo Properly merge the two datasets or use Ilias' function
    oxford, ecdc = read_preprocess_data(merge=True)
    # Merge dataframes on ISO3 country code and date
    oxford_ecdc = oxford.merge(ecdc, how='left', left_on=['CountryCode', 'Date'],
                               right_on=['countryterritoryCode', 'Date'])
    # Fill empty cells with 0 for days without new cases reported by ECDC
    oxford_ecdc[['Cases', 'Deaths']] = oxford_ecdc[['Cases', 'Deaths']].fillna(0)
    # Write to file
    oxford_ecdc.to_csv(OXFORD_ECDC_PATH)
    print('Finished merging...')


def get_first_cases_deaths_per_country(oxford):
    """
    Gets the dates when each country had its FIRST COVID9 case and death
    :param oxford: The dataframe containing the Oxford dataset
    :return: A dataframe containing the date when each country (row) had its first case and death (columns)
    """
    print("Getting first cases per country...")
    first_cases_per_country = {}
    first_deaths_per_country = {}

    # Get unique countries
    all_countries = oxford['CountryName'].unique()
    # Get the first case and death per country
    for country in all_countries:  # For each country
        cases_deaths = oxford.loc[oxford['CountryName'] == country, ['ConfirmedCases', 'ConfirmedDeaths']]
        # Get the row index of first confirmed case and death
        first_case_death_indices = cases_deaths.ne(0).idxmax()
        # Get dates of first confirmed case and death
        first_case_death_date = oxford.loc[first_case_death_indices, 'Date']

        # If there are no confirmed cases, set first case dates to None
        if cases_deaths.loc[first_case_death_indices[0], 'ConfirmedCases'] == 0:
            first_cases_per_country.update({country: None})
        else:
            first_cases_per_country.update({country: first_case_death_date.iloc[0]})
        # If there are no confirmed deaths, set first death date to None
        if cases_deaths.loc[first_case_death_indices[1], 'ConfirmedDeaths'] == 0:
            first_deaths_per_country.update({country: None})
        else:
            first_deaths_per_country.update({country: first_case_death_date.iloc[1]})

    # Return a dataframe with the first case and death dates per country
    first_cases_per_country_df = \
        pd.DataFrame(first_cases_per_country.items(), columns=['CountryName', 'FirstCaseDate'])
    first_deaths_per_country_df = \
        pd.DataFrame(first_deaths_per_country.items(), columns=['CountryName', 'FirstDeathDate'])
    return first_cases_per_country_df.merge(first_deaths_per_country_df, on='CountryName').set_index('CountryName')


def get_first_actions_per_country(oxford, is_general=False):
    """
    Gets the dates when each country took its FIRST political action (one of 11 Oxford categories) against the virus
    :param is_general: True, if we need to consider measures taken only if they apply to the whole country.
    :param oxford: The dataframe containing the Oxford dataset
    :return: A dataframe containing the date when each country (row) took each type of action (column) for the first time
    """
    print("Getting first political response per country...")
    first_actions_per_country = {}

    # if is_general:  # remove rows that express non-general measures
    #     oxford = oxford[oxford.S1_IsGeneral != 0]
    #     oxford = oxford[oxford.S2_IsGeneral != 0]
    #     oxford = oxford[oxford.S3_IsGeneral != 0]
    #     oxford = oxford[oxford.S4_IsGeneral != 0]
    #     oxford = oxford[oxford.S5_IsGeneral != 0]
    #     oxford = oxford[oxford.S6_IsGeneral != 0]

    # Get unique countries
    all_countries = oxford['CountryName'].unique()
    # Get the first case and death per country
    for country in all_countries:  # For each country
        actions = oxford.loc[oxford['CountryName'] == country, ACTION_COLUMNS]
        # Get the row index of first confirmed case and death
        first_actions_indices = actions.ne(0).idxmax()
        # Get dates of first confirmed case and death
        first_actions_dates = oxford.loc[first_actions_indices, 'Date'].to_frame()
        first_actions_dates['Action'] = first_actions_indices.index
        first_actions_dates.set_index('Action', inplace=True)

        country_actions = {}
        # For each action check if there are or not measures taken
        for action in first_actions_indices.index:
            if actions.loc[first_actions_indices[action], action] == 0:  # If no action was taken
                country_actions.update({action: None})
            else:
                country_actions.update({action: first_actions_dates.loc[action, 'Date']})

        first_actions_per_country.update({country: country_actions})

    return pd.DataFrame(first_actions_per_country).transpose()


def get_political_response_speed(first_cases, first_actions):
    """
    Find the difference between first case/death and first action (per action type) per country
    :param first_cases: A dataframe containing the date when each country (row) had its first case and death (columns)
    :param first_actions: A dataframe containing the date when each country (row) took each type of action (column) for the first time
    :return: Per country response time (in day) since the first COVID19 case/death
    """
    print("Calculating Speed of Political Response...")
    # If a country has no reported cases, we remove it from the analysis
    first_cases = first_cases[first_cases['FirstCaseDate'].notna()]
    df = first_cases.merge(first_actions, how='left', right_index=True, left_index=True)

    # For countries that have taken 0 actions, replace None values with today
    # df.fillna(datetime.datetime.now().strftime('%Y%m%d'), inplace=True)
    # For countries that have taken 0 actions, replace None values with a custom date (a year from now)
    df.fillna('20210331', inplace=True)

    # df.apply(pd.to_datetime, format='%Y%m%d', errors='coerce')
    for col in df.columns:
        if col == 'CountryName':
            continue
        else:
            df[col] = pd.to_datetime(df[col], format='%Y%m%d')

    diff_case = pd.DataFrame()
    diff_death = pd.DataFrame()
    for col in ACTION_COLUMNS:
        diff_case.loc[:, col] = (df.loc[:, col] - df.loc[:, 'FirstCaseDate']).dt.days
        diff_death.loc[:, col] = (df.loc[:, col] - df.loc[:, 'FirstDeathDate']).dt.days

    # Ignore very large day differences (they represent countries that have taken 0 measures)
    diff_death.mask(diff_death > 300, inplace=True)
    diff_case.mask(diff_case > 300, inplace=True)

    # Plot results
    # density_plot(diff_case, diff_death)
    # individual_kde_hist_plots(diff_case, diff_death)
    # Plot nan values vs non-nans
    plot_percentage_per_action(diff_case, diff_death)
    # Plot sorted speed per country
    plot_sorted_speed_per_country(diff_case, diff_death)
    return diff_case, diff_death


# todo Find more appropriate distribution for each action type (if it exists)
def individual_kde_hist_plots(diff_case, diff_death):
    """
    Plots a density plot (assuming normal distribution) per action type along with a histogram
    :param diff_case: Per country difference between patient 0 and actions taken by the government
    :param diff_death: Per country difference between patient 0 and actions taken by the government
    :return: Visualizes the density plots and stores them as files
    """
    # Density Plot and Histogram of all arrival delays
    for col in diff_case.columns:
        sns.distplot(diff_case.loc[:, col], hist=True, kde=True,
                     color='darkblue',
                     hist_kws={'edgecolor': 'black'},
                     kde_kws={'linewidth': 4})

        # Plot formatting
        # plt.legend(prop={'size': 16}, title='Airline')
        plt.title('Density and Histogram Plot of Government Response to COVID19')
        plt.xlabel('Delay (days) of ' + col + ' since patient 0')
        plt.ylabel('Density')
        plt.savefig('img/' + col + '.png')
        plt.show()


# todo Find more appropriate distribution for each action type (if it exists)
def density_plot(diff_case, diff_death):
    """
    Plots a density plot per action type into a single graph
    :param diff_case: Per country difference between patient 0 and actions taken by the government
    :param diff_death: Per country difference between patient 0 and actions taken by the government
    :return: Visualizes the combined density plot and stores it as files
    """
    # Don't plot stringency index
    columns_to_include = diff_case[diff_case.columns.difference(['StringencyIndex'])].columns
    diff_case[columns_to_include].plot.kde(figsize=(25, 10)).legend(loc='upper left')
        #.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    plt.title('Density and Histogram Plot of Government Response to COVID19')
    plt.xlabel('Delay (days) of government action since patient 0')
    plt.ylabel('Density')
    plt.savefig('img/density_plot.png')
    plt.show()


def plot_percentage_per_action(diff_case, diff_death):
    """
    Basic plot of percentage of nulls per type of action
    :param diff_case: Per country difference between patient 0 and actions taken by the government
    :param diff_death: Per country difference between patient 0 and actions taken by the government
    :return: Plot figure and save to file
    """
    percentage_of_nulls = diff_case.isna().mean().round(4) * 100
    percentage_of_nulls.plot.bar()
    plt.ylim([0, 100])
    plt.savefig('img/percentage_nulls.png')
    plt.show()


def plot_sorted_speed_per_country(diff_case, diff_death, top=10):
    """
    Plot top/bottom x countries based on speed of taking action (per action type)
    :param top: The number of countries to plot
    :param diff_case: Per country difference between patient 0 and actions taken by the government
    :param diff_death: Per country difference between patient 0 and actions taken by the government
    :return: Plot figure and save to file
    """
    for col in diff_case.columns:
        sorted_col = diff_case.loc[:, col].sort_values().dropna()
        sorted_col.head(top).plot.bar(figsize=(20, 10))
        plt.xticks(rotation=45)
        plt.title('Countries with the fastest response in terms of ' + col)
        plt.ylabel('Days after patient 0')
        plt.savefig('img/sorted_head_' + col + '.png')
        plt.show()
        sorted_col.tail(top).plot.bar(figsize=(20, 10))
        plt.xticks(rotation=45)
        plt.title('Countries with the slowest response in terms of ' + col)
        plt.ylabel('Days after patient 0')
        plt.savefig('img/sorted_tail_' + col + '.png')
        plt.show()


if __name__ == '__main__':
    """
    Test main function
    """
    # 1. Read data (using only Oxford dataset for now)
    oxford, _ = read_preprocess_data()
    # 2. Find dates of first cases/deaths per country
    first_cases_deaths_per_country = get_first_cases_deaths_per_country(oxford)
    # 3. Find dates of first actions per country and per action type
    first_actions_per_country = get_first_actions_per_country(oxford, is_general=True)
    # 4. Calculate and plot the difference between patient_0/death_0 and first actions
    diff_case, diff_death = get_political_response_speed(first_cases_deaths_per_country, first_actions_per_country)
    print()