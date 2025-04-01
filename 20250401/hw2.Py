import requests
import html
import pandas as pd
from bs4 import BeautifulSoup

def get_stop_info(stop_link:str) -> dict:

    url = f'https://pda5284.gov.taipei/MQS/{stop_link}'
    # get url and save to html file 
    # the html file is saved files as bus_{stop_link}.html
    response = requests.get(url)
    if response.status_code == 200:

        # read id from url
        stop_id = stop_link.split("=")[1]

        with open(f"bus_stop_{stop_id}.html", "w", encoding="utf-8") as file:
            file.write(response.text)

        print(f"網頁已成功下載並儲存為 bus_{stop_link}.html")
    else:
        print(f"無法下載網頁，HTTP 狀態碼: {response.status_code}") 


def get_bus_route(rid):
    """
    Retrieve two DataFrames containing bus stop names and their corresponding URLs based on the route ID (rid).

    Args:
        rid (str): Bus route ID.

    Returns:
        tuple: Two Pandas DataFrames, each corresponding to one direction of the bus route.

    Raises:
        ValueError: If the webpage cannot be downloaded or if insufficient table data is found.
    """
    url = f'https://pda5284.gov.taipei/MQS/route.jsp?rid={rid}'

    # Send GET request
    response = requests.get(url)

    # Ensure the request is successful
    if response.status_code == 200:
        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all tables
        tables = soup.find_all("table")

        # Initialize DataFrame list
        dataframes = []

        # Iterate through tables
        for table in tables:
            rows = []
            # Find all tr tags with the specified classes
            for tr in table.find_all("tr", class_=["ttego1", "ttego2"]):
                # Extract stop name and link
                td = tr.find("td")
                if td:
                    stop_name = html.unescape(td.text.strip())  # Decode stop name
                    stop_link = td.find("a")["href"] if td.find("a") else None

                    if stop_link:
                        # Call get_stop_info function to get stop information
                        get_stop_info(stop_link)
                    # Append to rows

                    rows.append({"stop_name": stop_name, "stop_link": stop_link})
            # If data exists, convert to DataFrame
            if rows:
                df = pd.DataFrame(rows)
                dataframes.append(df)

        # Return two DataFrames
        if len(dataframes) >= 2:
            return dataframes[0], dataframes[1]
        else:
            raise ValueError("Insufficient table data found.")
    else:
        raise ValueError(f"Failed to download webpage. HTTP status code: {response.status_code}")

# Test function
if __name__ == "__main__":
    rid = "10417"  # Test route ID
    try:
        df1, df2 = get_bus_route(rid)
        print("去程")
        print(df1)
        print("\n回程")
        print(df2)
    except ValueError as e:
        print(f"Error: {e}")