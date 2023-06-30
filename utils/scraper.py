from scrapingbee import ScrapingBeeClient
from playwright.sync_api import sync_playwright
from datetime import datetime
from bs4 import BeautifulSoup
from collections import defaultdict
from dotenv import load_dotenv
import pandas as pd
import requests
import os

# Get the username and password from environment variables
load_dotenv()
username = os.getenv("STEAM_USERNAME")
password = os.getenv("STEAM_PASSWORD")
sessionid = os.getenv("STEAM_LOGIN_SECURE")
api_key = os.getenv("API_KEY")


# Login to Steam - To get the cookies - To-Do
def login(page):
    # Navigate to the login page
    page.goto("https://store.steampowered.com/login")

    # Fill the username and password fields
    page.fill("#input_username", username)
    page.fill("#input_password", password)

    # Click the login button
    page.click("#login_btn_signin > button")

    # Wait for navigation to complete
    page.wait_for_navigation()


def get_item_links(client):
    # Send a GET request to the ScrapingBee API
    response = client.get("https://steamcommunity.com/market/", params={"render_js": "true"})

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML from the response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get all item elements
        item_elements = soup.select('.market_listing_row_link')

        # Extract item links
        item_links = [item['href'] for item in item_elements]
        return item_links
    else:
        print(f"Failed to fetch page: {response.text[:100]}")  # Only print the first 100 characters

        return []




def get_item_id(link):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Define a list to store the item nameid and appid
        item_nameid = [None]
        appid = [None]

        # Define a callback function for the route
        def handle_route(route, request):
            # Check if the request URL matches the expected pattern
            if 'itemordershistogram' in request.url:
                # Extract the item nameid from the URL
                item_nameid[0] = request.url.split('item_nameid=')[1].split('&')[0]
                
            # Continue the request
            route.continue_()

        # Start network interception
        page.route('**', handle_route)

        # Navigate to the item page
        page.goto(link)

        if '/listings/' in link:
            appid[0] = link.split('/listings/')[1].split('/')[0]
        else:
            print(f"Failed to find '/listings/' in {link}")
            print(appid[0])

        # Stop network interception
        page.unroute('**')

        browser.close()
    print(f"Item nameid: {item_nameid[0]}, appid: {appid[0]}")
    return item_nameid[0], appid[0]



def get_histogram_data(item_nameid, headers):
    
    # Define the histogram link
    histogram_link = f"https://steamcommunity.com/market/itemordershistogram?country=US&language=english&currency=1&item_nameid={item_nameid}&two_factor=0"
    print(f'histogram link: {histogram_link}, {item_nameid}')
    # Send a GET request to the histogram route with the headers
    response = requests.get(histogram_link, headers=headers)

    if response.status_code == 200:
        # Parse the JSON response
        histogram_data = response.json()

        return histogram_data
    else:
        print(f"Failed to get histogram data for item with nameid {item_nameid}")
        return None


def process_histogram(histogram_data):
    # Extract data
    buy_order_graph = histogram_data['buy_order_graph']
    sell_order_graph = histogram_data['sell_order_graph']
    processed_data = {
        "Buy Order Graph": buy_order_graph,
        "Sell Order Graph": sell_order_graph,
    }
    
    return processed_data

    

def get_item_details(client, link, headers):
    # Send a GET request to the ScrapingBee API
    response = client.get(link, params={"render_js": "true"})

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML from the response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the item details from the HTML
        name = soup.select_one('.market_listing_item_name').text
        game = soup.select_one('.market_listing_game_name').text
        item_type_element = soup.select_one('#largeiteminfo_item_type').text

        # Get all elements with the class 'market_commodity_orders_header_promote'
        elements = soup.select('.market_commodity_orders_header_promote')

        # Extract the data from the elements
        items_for_sale = elements[0].text if len(elements) > 0 else None
        sell_price = elements[1].text if len(elements) > 1 else None
        buy_requests = elements[2].text if len(elements) > 2 else None
        buy_price = elements[3].text if len(elements) > 3 else None

        print(f"Name: {name}, Game: {game}, Item Type: {item_type_element}, Items for Sale: {items_for_sale}, Sell Price: {sell_price}, Buy Requests: {buy_requests}, Buy Price: {buy_price}")
        return name, game, item_type_element, items_for_sale, sell_price, buy_requests, buy_price
    else:
        print(f"Failed to fetch page: {response.text}")
        return None, None, None, None, None, None, None

def get_priceoverview_data(name,appid, headers):
    # Navigate to the priceoverview route
    name_encoded = name.replace(' ', '%20').replace('&', '%26')
    priceoverview_link = f"https://steamcommunity.com/market/priceoverview/?appid={appid}&currency=1&market_hash_name={name_encoded}"
    # Send a GET request to the priceoverview route
    response = requests.get(priceoverview_link)

    if response.status_code == 200:
        # Parse the JSON response
        priceoverview_data = response.json()
        
        # Extract and print the data
        lowest_price = priceoverview_data['lowest_price']
        volume = priceoverview_data['volume']
        median_price = priceoverview_data['median_price']
        print(f"Lowest Price: {lowest_price}, Volume: {volume}, Median Price: {median_price}")
        return lowest_price, volume, median_price
    else:
        print(f"Failed to get priceoverview data for {name}")
        return None, None, None


def get_pricehistory_data(name, headers, appid):
    name_encoded = name.replace(' ', '%20').replace('&', '%26')
    print(name_encoded)
    print(appid)
    pricehistory_link = f"https://steamcommunity.com/market/pricehistory/?appid={appid}&market_hash_name={name_encoded}"
    
    # Print the pricehistory_link for debugging
    print('This is pricehistory_link:', pricehistory_link)

    # Send a GET request to the pricehistory route with the headers
    response = requests.get(pricehistory_link, headers=headers)

    if response.status_code == 200:
        # Parse the JSON response
        pricehistory_data = response.json()
        print('This is pricehistory_data:', pricehistory_data['prices'])
        return pricehistory_data['prices']
    else:
        print(f"Failed to get pricehistory data for {name}")
        return None


def process_pricehistory_data(pricehistory_data, last_date=None):
    if not pricehistory_data:
        return {}
    # Create a dictionary to store the daily data
    daily_data = defaultdict(list)
    print(f'last_date: {last_date}', )
    print(f'pricehistory_data: {pricehistory_data}', )
    # Iterate over the prices data
    for price_data in pricehistory_data:
        # Extract the date, price, and volume
        date_string = price_data[0]
        date_string = date_string.rsplit(" ", 1)[0]  # Remove the timezone offset
        date = datetime.strptime(date_string, '%b %d %Y %H:')


        # Convert the date string to a datetime object
        if last_date is not None and date <= last_date:
            continue
        price = float(price_data[1])
        volume = int(price_data[2])

        # Add the price and volume to the daily data
        daily_data[date.strftime('%b %d %Y %H:')].append((price, volume))

    # Now, daily_data is a dictionary where each key is a date and the value is a list of (price, volume) tuples for that date

    # Get the last 5 days
    last_15_days = list(daily_data.keys())
    # Prepare a dictionary to store the processed data
    processed_data = {}

    # Iterate over the last 5 days
    for day in last_15_days:
        # Get the data for this day
        day_data = daily_data[day]

        # Calculate the average price and total volume for this day
        avg_price = sum(price for price, volume in day_data) / len(day_data)
        total_volume = sum(volume for price, volume in day_data)

        # Store the data in the processed_data dictionary
        processed_data[day] = {
            "Average Price": avg_price,
            "Total Volume": total_volume
        }
    print(f'processed_data: {processed_data}')
    return processed_data


def process_item_links(client, link, sessionid):
    print(f"Processing link: {link}")
    item_nameid, appid = get_item_id(link)
    
    headers = {
        'Cookie': f'steamLoginSecure={sessionid}'
    }

    # Send a GET request to the ScrapingBee API
    response = client.get(link, params={"render_js": "true"}, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML from the response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get item details
        name, game, item_type_element, items_for_sale, sell_price, buy_requests, buy_price = get_item_details(client, link, headers)

        # Get priceoverview data
        lowest_price, volume, median_price = get_priceoverview_data(name, appid, headers)

    # Get pricehistory data
    pricehistory_data = get_pricehistory_data(name, headers, appid)

    if pricehistory_data:
        # Load existing data
        try:
            existing_daily_df = pd.read_csv('daily.csv')
            last_date = pd.to_datetime(existing_daily_df[existing_daily_df['Name'] == name]['Date']).max()
        except (FileNotFoundError, pd.errors.EmptyDataError):
            last_date = None

        # Process pricehistory data
        daily_data = process_pricehistory_data(pricehistory_data, last_date)

    # Get histogram data
    histogram_data = get_histogram_data(item_nameid, headers)

    if histogram_data:
        # Load existing data
        try:
            existing_processed_df = pd.read_csv('processed.csv')
            if 'Date' in existing_processed_df.columns:
                last_date = pd.to_datetime(existing_processed_df[existing_processed_df['Name'] == name]['Date']).max()
            else:
                last_date = None
        except (FileNotFoundError, pd.errors.EmptyDataError):
            last_date = None


        # Process histogram data
        processed_data = process_histogram(histogram_data)

        
        data = {
            'Name': [name],
            'Game': [game],
            'Item Type': [item_type_element],
            'Items for Sale': [items_for_sale],
            'Sell Price': [sell_price],
            'Buy Requests': [buy_requests],
            'Buy Price': [buy_price],
            'Lowest Price': [lowest_price],
            'Volume': [volume],
            'Median Price': [median_price],
            'Daily Data': [daily_data],
            'Histogram Data': [processed_data]
        }

        item_df, daily_df, processed_df = create_dataframes(name, data, daily_data, processed_data)

        return item_df, daily_df, processed_df
    else:
        print(f"Failed to fetch page: {response.text}")
        return None, None, None
    
def create_dataframes(name, data, daily_data, processed_data):
    item_df = pd.DataFrame(data)

    # Create a DataFrame to store the daily data
    daily_df = pd.DataFrame(daily_data).T
    daily_df.index.name = 'Date'
    daily_df.reset_index(inplace=True)
    daily_df['Name'] = name  # Add a column to link the data to the item

    # Create a DataFrame to store the processed data
    processed_df = pd.DataFrame(processed_data)
    processed_df['Name'] = name  # Add a column to link the data to the item

    return item_df, daily_df, processed_df

    
def clean_data(item_df, daily_df, processed_df):
    # Remove commas and convert to int
    item_df['Items for Sale'] = item_df['Items for Sale'].str.replace(',', '').astype(int)
    item_df['Volume'] = item_df['Volume'].str.replace(',', '').astype(int)

    # Remove dollar signs and convert to float
    item_df['Sell Price'] = item_df['Sell Price'].str.replace('$', '').astype(float)
    item_df['Buy Price'] = item_df['Buy Price'].str.replace('$', '').astype(float)
    item_df['Lowest Price'] = item_df['Lowest Price'].str.replace('$', '').astype(float)
    item_df['Median Price'] = item_df['Median Price'].str.replace('$', '').astype(float)


    # Convert 'Date' to datetime 
    daily_df['Date'] = pd.to_datetime(daily_df['Date'], format='%b %d %Y %H:')

    
    # Split 'Buy Order Graph' and 'Sell Order Graph' into separate columns
    processed_df[['Buy Order Graph 1','Buy Order Graph 2' ]] = pd.DataFrame(processed_df['Buy Order Graph'].tolist(), index=processed_df.index)[[0, 1]]
    processed_df[['Sell Order Graph 1', 'Sell Order Graph 2']] = pd.DataFrame(processed_df['Sell Order Graph'].tolist(), index=processed_df.index)[[0, 1]]
    processed_df.columns = ["Buy Order Graph", "Sell Order Graph", "Name", "Lowest Buy", "Volume", "2nd Lowest Buy", "2nd Volume"]

    
    return item_df, daily_df, processed_df


def process_link(client, link, sessionid):
    item_df, daily_df, processed_df = process_item_links(client, link, sessionid)
    item_df, daily_df, processed_df = clean_data(item_df, daily_df, processed_df)
    
    return item_df, daily_df, processed_df

def main(): 
    # Initialize the ScrapingBee client
    client = ScrapingBeeClient(api_key=api_key)
    headers = {
        'Cookie': f'steamLoginSecure={sessionid}'
    }
    # Get item links
    item_links = get_item_links(client)
    
    item_dfs = []
    daily_dfs = []
    processed_dfs = []
    
    print(f"Found {len(item_links)} items")
    for link in item_links:
        for _ in range(3):
            try:
                item_df, daily_df, processed_df = process_link(client, link, sessionid)
                item_dfs.append(item_df)
                daily_dfs.append(daily_df)
                processed_dfs.append(processed_df)
                break
            except Exception as e:
                print(f"Failed to process link {link} due to {e}")
        else:
            print(f"Failed to process link {link} after {3} retries")

    all_items_df = pd.concat(item_dfs, ignore_index=True)
    all_daily_df = pd.concat(daily_dfs, ignore_index=True)
    all_processed_df = pd.concat(processed_dfs, ignore_index=True)

    all_items_df.to_csv('items.csv', index=False)
    all_daily_df.to_csv('daily.csv', index=False)
    all_processed_df.to_csv('processed.csv', index=False)

if __name__ == "__main__":
    main()