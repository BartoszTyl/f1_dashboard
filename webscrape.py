import requests
import pandas as pd
from bs4 import BeautifulSoup
import regex as re

def get_f1_drivers() -> pd.DataFrame:
    url = "https://en.wikipedia.org/wiki/List_of_Formula_One_drivers"
    
    # Fetch the webpage content
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to fetch data. HTTP Status code: {response.status_code}")
        return pd.DataFrame()  # Return an empty DataFrame in case of failure
    
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find all tables with the class 'wikitable'
    tables = soup.find_all('table', {'class': 'wikitable'})

    # Select the second table (index 1)
    table = tables[1]

    # Extract headers (table column names)
    headers = [header.text.strip() for header in table.find_all('th')]

    # Extract data rows
    rows = []
    for row in table.find_all('tr')[1:]:  # Skip the header row
        cols = row.find_all('td')
        if len(cols) > 0:
            data = [col.text.strip() for col in cols]
            if len(data) < len(headers):
                data.extend([None] * (len(headers) - len(data)))
            elif len(data) > len(headers):
                data = data[:len(headers)]
            rows.append(data)

    # Create the DataFrame
    df_wiki_drivers = pd.DataFrame(rows, columns=headers)

    # Remove duplicate columns if any
    df_wiki_drivers = df_wiki_drivers.loc[:, ~df_wiki_drivers.columns.duplicated()]
    # if "Points[a]" in df_wiki_drivers.columns:
    df_wiki_drivers = df_wiki_drivers.drop(columns=["Points[a]"])
    df_wiki_drivers["Drivers' Championships"] = df_wiki_drivers["Drivers' Championships"].apply(
    lambda x: re.search(r'\d', x).group() if isinstance(x, str) and re.search(r'\d', x) else None
    )

    df_wiki_drivers["Race entries"] = df_wiki_drivers["Race entries"].str.replace(r'\D', '', regex=True)
    df_wiki_drivers["Race starts"] = df_wiki_drivers["Race starts"].str.replace(r'\D', '', regex=True)
    df_wiki_drivers["Race wins"] = df_wiki_drivers["Race wins"].str.replace(r'\D', '', regex=True)
    df_wiki_drivers["Podiums"] = df_wiki_drivers["Podiums"].str.replace(r'\D', '', regex=True)
    df_wiki_drivers["Fastest laps"] = df_wiki_drivers["Fastest laps"].str.replace(r'\D', '', regex=True)

    df_wiki_drivers["Driver name"] = df_wiki_drivers["Driver name"].str.rstrip("^~*")
    df_wiki_drivers = df_wiki_drivers.astype({
        "Race entries":int,
        "Race starts":int,
        "Pole positions":int,
        "Race wins":int,
        "Podiums":int,
        "Fastest laps":int
    })

    return df_wiki_drivers


if __name__ == "__main__":
    # Example usage
    df = get_f1_drivers()
    print(df.dtypes)  # Display the first few rows