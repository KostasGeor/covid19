#!/usr/bin/env python

import urllib.request
from datetime import datetime, timedelta, time
import datetime as dt
import pandas as pd
import pickle
import sys


def get_ecdc_data(filename='static/data/ecdcdata'):
    datetimeToday = datetime.today()
    date = datetimeToday.date()  # date now
    time = datetimeToday.time()  # time now
    yesterday = str(date - timedelta(1))  # yesterday
    try:
        url = 'https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-' + str(
            date) + '.xlsx'
        urllib.request.urlretrieve(url, filename)
    except:
        try:
            url = 'https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-' + str(
                date) + '.xls'
            urllib.request.urlretrieve(url, filename)
        except:
            try:
                url = 'https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-' + yesterday + '.xlsx'
                urllib.request.urlretrieve(url, filename)
            except:
                try:
                    url = 'https://www.ecdc.europa.eu/sites/default/files/documents/COVID-19-geographic-disbtribution-worldwide-' + yesterday + '.xls'
                    urllib.request.urlretrieve(url, filename)
                except:
                    print('no data to download! ???')
                    sys.exit(1)
    print('received data from ', url)


def get_oxford_government_action_data(filename = 'data/oxford_data.xlsx'):
    """
    Retrieves an .xlsx file from Oxford University regarding governmental response to COVID19
    :return: Saves oxford_data.xlsx file to data folder
    """
    print('...getting latest Oxford data...')
    try:
        url = 'https://www.bsg.ox.ac.uk/sites/default/files/OxCGRT_Download_latest_data.xlsx'
        urllib.request.urlretrieve(url, filename=filename)
    except Exception as e:
        print('Problem retrieving data from Oxford University: ' + str(e))

def get_new_format():
    ecdc = pd.read_excel('static/data/ecdcdata')
    ecdc = ecdc.rename(columns={'dateRep':'DateRep','day':'Day', 'month':'Month', 'year':'Year', 'cases':'Cases', 'deaths':'Deaths',
       'countriesAndTerritories':'Countries and territories', 'geoId':'GeoId','popData2018':'Pop_Data.2018'})
    ecdc.to_csv('static/data/ecdcdata.csv',index=False)

def merge_data():
    get_new_format()
    ecdc = pd.read_csv('static/data/ecdcdata.csv')
    ecdc=ecdc.drop(['Day','Month','Year'],axis=1)
    whr = pd.read_csv('data/whr2019.csv')
    hfr = pd.read_csv('data/human_freedom.csv')
    bank = pd.read_csv('data/world_bank_data.csv')
    oecd = pd.read_csv('data/oecd_data.csv')
    codes = pd.read_csv('data/newcodes.csv')
    whr = whr.rename(columns={"Log of GDP\r\nper capita":"logCapita","Healthy life\r\nexpectancy":"Healthy life expectancy",'country':'Countries and territories'})
    codes = codes.rename(columns={'Country':'Countries and territories'})
    ecdc_loc = pd.merge(ecdc,codes,on='Countries and territories',how='left')
    ecdc_loc_whr = pd.merge(ecdc_loc,whr,on='Countries and territories',how='left')
    hfr = hfr[['Countries and territories','hf_score','region']]
    final = pd.merge(ecdc_loc_whr,hfr,on='Countries and territories',how='left')
    final = final.rename(columns={'Cases':'NewConfCases','Countries and territories':'CountryExp','Deaths':'NewDeaths','Latitude (average)':'lat','Longitude (average)':'lon'})
    final = final.drop(['Unnamed: 0','Unnamed: 0.1'],axis=1)
    pickle.dump(final, open('static/data/df.pickle', 'wb'))

    df1 = final.groupby('CountryExp')['NewConfCases'].sum().reset_index()
    df2 = final.groupby('CountryExp')['NewDeaths'].sum().reset_index()
    final_df = pd.merge(df1, df2, on='CountryExp')
    final_df.to_csv('static/data/table-data.csv', index=False)
    return final

# def map_countries():
#     mapping = pickle.load(open('static/data/mapping', 'rb'))
#     countries = []
#     lats = []
#     lons = []
#     for k, v in mapping.items():
#         countries.append(k)
#         lats.append(v[0])
#         lons.append(v[1])
#     df = pd.DataFrame()
#     df['CountryExp'] = countries
#     df['lat'] = lats
#     df['lon'] = lons
#     return (df)


# def merge_data():
#     iso = pd.read_csv('static/data/iso.csv', names=['Country', 'iso2', 'iso3'])
#     iso2dict = dict(zip(iso.iso2, iso.Country))
#     iso3dict = dict(zip(iso.iso3, iso.Country))
#     locs = map_countries()
#     oldData = pd.read_excel('static/data/oldData.xls')
#     eudict = dict(zip(oldData.GeoId, oldData.EU))
#     get_ecdc_data()
#     covid = pd.read_excel('static/data/ecdcdata', converters={'geoId': str})
#     covid = covid.rename(columns={'dateRep':'DateRep','day':'Day', 'month':'Month', 'year':'Year', 'cases':'NewConfCases', 'deaths':'NewDeaths',
#        'countriesAndTerritories':'CountryExp', 'geoId':'GeoId','popData2018':'Pop_Data.2018'})
#     countryExp = list()
#     for i, r in covid.iterrows():
#         try:
#             if len(r['GeoId']) > 2:
#                 try:
#                     countryExp.append(iso3dict[r['GeoId']])
#                 except KeyError:
#                     countryExp.append('Other')
#             else:
#                 try:
#                     countryExp.append(iso2dict[r['GeoId']])
#                 except KeyError:
#                     countryExp.append('Other')
#         except TypeError:
#             countryExp.append('Namibia')
#     covid['CountryExp'] = countryExp
#     covid['EU'] = covid['GeoId'].map(eudict)

#     whr2019 = pd.read_csv('static/data/world-happiness-report-2019.csv')
#     whr2019['CountryExp'] = whr2019['iso2'].map(iso2dict)
#     whr2019 = whr2019.rename(columns={"Log of GDP\nper capita": "Log of GDP per capita",
#                                       "Healthy life\nexpectancy": "Healthy life expectancy"})

#     df1 = pd.merge(covid, whr2019, on="CountryExp", how='left')
#     df = pd.merge(df1, locs, on="CountryExp", how='left')

#     human_freedom = pd.read_csv('static/data/human_freedom.csv')
#     human_freedom['CountryExp'] = human_freedom['ISO_code'].map(iso3dict)
#     human_freedom = human_freedom.filter(['CountryExp', 'hf_score', 'ISO_code'])
#     df_final = pd.merge(df, human_freedom, on="CountryExp", how='left')
#     pickle.dump(df_final, open('static/data/df.pickle', 'wb'))
#     df1 = df.groupby('CountryExp')['NewConfCases'].sum().reset_index()
#     df2 = df.groupby('CountryExp')['NewDeaths'].sum().reset_index()
#     final_df = pd.merge(df1, df2, on='CountryExp')
#     final_df.to_csv('static/data/table-data.csv', index=False)


if __name__ == "__main__":
    # get_oxford_government_action_data()
    get_ecdc_data()
    merge_data()
    # print (df['Unnamed: 0'])
