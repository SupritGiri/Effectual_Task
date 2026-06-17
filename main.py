# Importing the libraries

import tomllib
import requests
import numpy as np
import pandas as pd


# Creating a function to load the configuration file

def load_config(file_path):
    """Load and parse a TOML configuration file from the given file path and 
    return the resulting configuration as a dictionary."""
    
    with open("config.toml", "rb") as config_file:
        return tomllib.load(config_file)

configs = load_config("config.toml")


# Loading country codes for iterating through the URL

url = "https://api.worldbank.org/V2/country?format=json"

def get_country_codes(base_url):
    """Retrieves all countries from the World Bank API and 
    returns a dictionary mapping country names to their IDs.
    The API is paginated, so the function first fetches the total number of countries and 
    then requests all entries in a single call using `per_page`. 
    The response is parsed to extract each country's name and ID, 
    which are required for country-specific API queries.
    The input is a base URL for the World Bank country API, and 
    the function returns a dictionary where each key is a country name and 
    each value is its ID."""

    # Checking the number of unique countries
    response = requests.get(base_url)
    num_countries = response.json()[0]["total"]

    # Format URL to fetch num_countries, unique countries, in a single page
    modified_url = f"{base_url}&per_page={num_countries}"

    # Fetching the country codes from the modified URL
    response = requests.get(modified_url)
    data = response.json()

    # Creating a lookup dictionary to store country names and their corresponding codes
    country_codes = {}

    # Iterating over all countries to fetch their corresponding id, which will later be used in the URL to retrieve the data
    for country in data[1]:
        country_codes[country["name"]] = country["id"]

    return country_codes

country_codes = get_country_codes(url)


# Creating a function to formal URLs based on the configurations

def format_url(base_url, country_codes, configs):

    # Retrieving country codes from the lookup dictionary for the countries specified in the config file
    selected_codes = []
    missing_codes = []

    for country in configs["countries"]["list"]:
        try:
            selected_codes.append(country_codes[country])
        except KeyError:
            missing_codes.append(country)

    # Checking if information for any requested country is unavailable from the API
    if missing_codes:
        print(f"Warning: the '{', '.join(missing_codes)}' was not found in the list of {len(country_codes)} \
countries in the database while extracting data from the API.")
        
    # Retrieving the timeframe for which we want to retrieve the data and formatting it in the URL
    timeframe = f"{configs['time']['start_year']}:{configs['time']['end_year']}"
    
    # Retrieving the indicators from the configuration file and formatting them in the format expected by the URL
    indicators = [indicator for indicator in configs["series"].values()]

    # Creating an empty list to which all the URLs will be appended
    urls = []

    # Iterating over each country and indicators individually because too many semicolons are preventing the data from being fetched correctly
    for code in selected_codes:
        for indicator in indicators:
            url = f"https://api.worldbank.org/v2/country/{code}/indicator/{indicator}?date={timeframe}&format=json"
            urls.append(url)

    return urls

extracted_urls = format_url(url, country_codes, configs)


# Creating a function to fetch data from the URLs and store it in a DataFrame

def extract_data(urls):

    # Creating a lookup dictionary for indicators
    indicators_dict = {
        'NV.IND.TOTL.KD' : "Industry",
        'NV.IND.MANF.KD' : "Manufacturing",
        'NY.GDP.MKTP.KD' : "GDP" 
    }

    # Creating an empty DataFrame to which the fetched data will be appended
    df = pd.DataFrame({})

    # Creating a counter for indexing
    count = 0
    
    # Iterating over each URL to retrieve the relevant data

    for url in urls:
        response = requests.get(url)
        data = response.json()

        # Extracting the total number of entries and including it in the URL to retrieve all the data frpm a single page
        total_entries = data[0]["total"]
        modified_url = f"{url}&per_page={total_entries}"
        
        # Extracting all the data from the updated URL
        response = requests.get(modified_url)
        data = response.json()

        # Iterating over each entry retrieved from each URL
        for i in range(len(data[1])):
            df.loc[count, "country"] = data[1][i]["countryiso3code"]
            df.loc[count, "indicator"] = indicators_dict[data[1][i].get("indicator")["id"]]
            value = data[1][i]["value"]
            df.loc[count, f"year_{data[1][i]['date']}"] = int(value) if value != None else np.nan
                 
        count += 1
    
    return df

data_df = extract_data(extracted_urls)

# Reshaping the columns in the expected format

csv_df = data_df[list(data_df.columns[:2]) + list(data_df.columns[2:][::-1])]

# Exporting the dataset

csv_df.to_csv("main_dataset.csv", index = False)

# Creating a function to compute structural changes and store the results in a summary table

def compute_structural_changes(data):

    # Creating an empty dataframe to include the summary
    df = pd.DataFrame({})

    # Creating a counter for indexing
    count = 0

    # Iterating over each country and computing changes across indicators
    for country in data["country"].unique():
        
        # Extracting values for the year 2000
        industry_2000 = data.groupby("country").get_group(country).set_index("indicator")["year_2000"].Industry
        manufacturing_2000 = data.groupby("country").get_group(country).set_index("indicator")["year_2000"].Manufacturing
        gdp_2000 = data.groupby("country").get_group(country).set_index("indicator")["year_2000"].GDP

        # Extracting values for the year 2024, since most values for 2025 are NaN
        industry_2024 = data.groupby("country").get_group(country).set_index("indicator")["year_2024"].Industry
        manufacturing_2024 = data.groupby("country").get_group(country).set_index("indicator")["year_2024"].Manufacturing
        gdp_2024 = data.groupby("country").get_group(country).set_index("indicator")["year_2024"].GDP

        # Calculating each country’s industry and manufacuring share of GDP
        df.loc[count, "Country"] = country
        df.loc[count, "industry_share_2000"] = industry_2000 / gdp_2000
        df.loc[count, "industry_share_2024"] = industry_2024 / gdp_2024
        df.loc[count, "manufacturing_share_2000"] = manufacturing_2000 / gdp_2000
        df.loc[count, "manufacturing_share_2024"] = manufacturing_2024 / gdp_2024

        # Computing the compound annual growth rate for each country
        num_years = 24
        industry_cagr = (industry_2024 / industry_2000) ** (1 / num_years) - 1
        manufacturing_cagr = (manufacturing_2024 / manufacturing_2000) ** (1 / num_years) - 1
        gdp_cagr = (gdp_2024 / gdp_2000) ** (1 / num_years) - 1

        # Appending the CAGR data to the DataFrame
        df.loc[count, "industry_cagr"] = industry_cagr
        df.loc[count, "manufacturing_cagr"] = manufacturing_cagr
        df.loc[count, "gdp_cagr"] = gdp_cagr
        count += 1
        
    return df

summary_df = compute_structural_changes(csv_df)

summary_df.to_csv("summary_table.csv", index = False)

