from playwright.sync_api import sync_playwright
from collections import defaultdict
from dotenv import load_dotenv
from itertools import cycle
from tenacity import retry, stop_after_attempt, wait_exponential
import pandas as pd
import requests
import os

# Get the username and password from environment variables
load_dotenv()
username = os.getenv("STEAM_USERNAME")
password = os.getenv("STEAM_PASSWORD")
sessionid = os.getenv("STEAM_LOGIN_SECURE")

proxies = [
    "54.237.145.145:80",
    "154.3.9.16:8081",
    "64.225.8.115:9996",
    "71.86.129.131:8080",
    "64.225.4.63:9993",
    "107.148.94.92:80",
    "47.90.162.160:8080",
    "66.135.14.166:443",
    "54.196.13.224:80",
    "103.114.219.115:3128"
]
proxy_pool = cycle(proxies)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def make_request(url, headers):
    proxy = next(proxy_pool)
    try:
        response = requests.get(url, headers=headers, proxies={"http": proxy, "https":proxy})
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException:
        raise

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


def get_item_links(page):
    # Navigate to the market page
    page.goto("https://steamcommunity.com/market/")

    # Get all item elements
    item_elements = page.query_selector_all('.market_listing_row_link')

    # Extract item links
    item_links = [item.get_attribute('href') for item in item_elements]
    return item_links


def get_item_id(page, link):
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

    return item_nameid[0], appid[0]


def get_histogram_data(item_nameid, headers):
    
    # Define the histogram link
    histogram_link = f"https://steamcommunity.com/market/itemordershistogram?country=US&language=english&currency=1&item_nameid={item_nameid[0]}&two_factor=0"
    try:
        # Send a GET request to the histogram route with the headers
        response = make_request(histogram_link, headers)

        # Parse the JSON response
        histogram_data = response.json()

        return histogram_data
    except Exception as e:
        print(f"Failed to get histogram data for item with nameid {item_nameid}: {e}")
        return None


def process_histogram(histogram_data):
    # Extract data
    buy_order_graph = histogram_data['buy_order_graph'][:2]
    sell_order_graph = histogram_data['sell_order_graph'][:2]
    processed_data = {
        "Buy Order Graph": buy_order_graph,
        "Sell Order Graph": sell_order_graph,
    }
    
    return processed_data
    

def get_item_details(page):
    name = page.locator('.market_listing_item_name').inner_text()
    game = page.locator('.market_listing_game_name').inner_text()
    item_type_element = page.locator('#largeiteminfo_item_type').inner_text()

    # Get all elements with the class 'market_commodity_orders_header_promote'
    elements = page.locator('.market_commodity_orders_header_promote')

    # Extract the data from the elements
    items_for_sale = elements.nth(0).inner_text()
    sell_price = elements.nth(1).inner_text()
    buy_requests = elements.nth(2).inner_text()
    buy_price = elements.nth(3).inner_text()

    return name, game, item_type_element, items_for_sale, sell_price, buy_requests, buy_price


def get_priceoverview_data(name,appid):
    # Navigate to the priceoverview route
    name_encoded = name.replace(' ', '%20').replace('&', '%26')
    priceoverview_link = f"https://steamcommunity.com/market/priceoverview/?appid={appid[1]}&currency=1&market_hash_name={name_encoded}"

    # Send a GET request to the priceoverview route
    response = requests.get(priceoverview_link)

    if response.status_code == 200:
        # Parse the JSON response
        priceoverview_data = response.json()
        
        # Extract and print the data
        lowest_price = priceoverview_data['lowest_price']
        volume = priceoverview_data['volume']
        median_price = priceoverview_data['median_price']

        return lowest_price, volume, median_price
    else:
        print(f"Failed to get priceoverview data for {name}")
        return None, None, None


def get_pricehistory_data(name, headers, appid):
    name_encoded = name.replace(' ', '%20').replace('&', '%26')
    print(name_encoded)
    print(appid[1])
    pricehistory_link = f"https://steamcommunity.com/market/pricehistory/?appid={appid[1]}&market_hash_name={name_encoded}"

    # Send a GET request to the pricehistory route with the headers
    response = requests.get(pricehistory_link, headers=headers)

    if response.status_code == 200:
        # Parse the JSON response
        pricehistory_data = response.json()

        return pricehistory_data['prices']
    else:
        print(f"Failed to get pricehistory data for {name}")
        return None


def process_pricehistory_data(pricehistory_data):
    # Create a dictionary to store the daily data
    daily_data = defaultdict(list)

    # Iterate over the prices data
    for price_data in pricehistory_data:
        # Extract the date, price, and volume
        date = price_data[0][:11]  # Get only the date part, excluding the time
        price = float(price_data[1])
        volume = int(price_data[2])

        # Add the price and volume to the daily data
        daily_data[date].append((price, volume))
    # Now, daily_data is a dictionary where each key is a date and the value is a list of (price, volume) tuples for that date

    # Get the last 5 days
    last_5_days = list(daily_data.keys())[-5:]

    # Prepare a dictionary to store the processed data
    processed_data = {}

    # Iterate over the last 5 days
    for day in last_5_days:
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

    return processed_data


def process_item_links(page, link):
    print(f"Processing link: {link}")
    item_nameid = get_item_id(page, link)
    appid= get_item_id(page,link)
    # Define your sessionid cookie

    # Define your headers
    headers = {
        'Cookie': f'steamLoginSecure={sessionid}'
    }

    # Navigate to the item page
    page.goto(link)

    # Get item details
    name, game, item_type_element, items_for_sale, sell_price, buy_requests, buy_price = get_item_details(page)

    # Get priceoverview data
    lowest_price, volume, median_price = get_priceoverview_data(name, item_nameid)

    # Get pricehistory data
    pricehistory_data = get_pricehistory_data(name, headers, appid)

    if pricehistory_data:
        # Process pricehistory data
        daily_data = process_pricehistory_data(pricehistory_data)
    
    # Get histogram data
    histogram_data = get_histogram_data(item_nameid, headers)

    if histogram_data:
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
    daily_df['Date'] = pd.to_datetime(daily_df['Date'])
    
    # Split 'Buy Order Graph' and 'Sell Order Graph' into separate columns
    processed_df[['Buy Order Graph 1','Buy Order Graph 2' ]] = pd.DataFrame(processed_df['Buy Order Graph'].tolist(), index=processed_df.index)[[0, 1]]
    processed_df[['Sell Order Graph 1', 'Sell Order Graph 2']] = pd.DataFrame(processed_df['Sell Order Graph'].tolist(), index=processed_df.index)[[0, 1]]
    processed_df.columns = ["Buy Order Graph", "Sell Order Graph", "Name", "Lowest Buy", "Volume", "2nd Lowest Buy", "2nd Volume"]

    
    return item_df, daily_df, processed_df

def main(): 
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        item_links = get_item_links(page)

        item_dfs = []
        daily_dfs = []
        processed_dfs = []
        
        for link in item_links:
            item_df, daily_df, processed_df = process_item_links(page, link)
            
            item_df, daily_df, processed_df = clean_data(item_df, daily_df, processed_df)
            
            item_dfs.append(item_df)
            daily_dfs.append(daily_df)
            processed_dfs.append(processed_df)

            all_items_df = pd.concat(item_dfs, ignore_index=True)
            all_daily_df = pd.concat(daily_dfs, ignore_index=True)
            all_processed_df = pd.concat(processed_dfs, ignore_index=True)
        
            all_items_df.to_csv('items.csv', index=False)
            all_daily_df.to_csv('daily.csv', index=False)
            all_processed_df.to_csv('processed.csv', index=False)
        
        browser.close()

if __name__ == "__main__":
    main()
