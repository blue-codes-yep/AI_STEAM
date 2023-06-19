from playwright.sync_api import sync_playwright
from collections import defaultdict
import json
import requests

def get_item_links(page):
    # Navigate to the market page
    page.goto("https://steamcommunity.com/market/")

    # Get all item elements
    item_elements = page.query_selector_all('.market_listing_row_link')

    # Extract item links
    item_links = [item.get_attribute('href') for item in item_elements]
    return item_links


def get_item_nameid(page, link):
    # Define a list to store the item nameid
    item_nameid = [None]

    # Define a callback function for the route
    def handle_route(route, request):
        # Check if the request URL matches the expected pattern
        if 'itemordershistogram' in request.url:
            # Extract the item nameid from the URL
            item_nameid[0] = request.url.split('item_nameid=')[1].split('&')[0]
            print(f"Item nameid: {item_nameid[0]}")

        # Continue the request
        route.continue_()

    # Start network interception
    page.route('**', handle_route)

    # Navigate to the item page
    page.goto(link)

    # Stop network interception
    page.unroute('**')

    return item_nameid[0]

def get_histogram_data(item_nameid, headers):
    # Define the histogram link
    histogram_link = f"https://steamcommunity.com/market/itemordershistogram?country=US&language=english&currency=1&item_nameid={item_nameid}&two_factor=0"

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
    buy_order_graph = histogram_data['buy_order_graph'][:2]
    sell_order_graph = histogram_data['sell_order_graph'][:2]
    highest_buy_order = histogram_data['highest_buy_order'][:2]
    lowest_sell_order = histogram_data['sell_order_graph'][:2]

    processed_data = {
        "Buy Order Graph": buy_order_graph,
        "Sell Order Graph": sell_order_graph,
        "Highest Buy Order": highest_buy_order,
        "Lowest Sell Order": lowest_sell_order
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

def get_priceoverview_data(name):
    # Navigate to the priceoverview route
    name_encoded = name.replace(' ', '%20').replace('&', '%26')
    priceoverview_link = f"https://steamcommunity.com/market/priceoverview/?appid=730&currency=1&market_hash_name={name_encoded}"

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

def get_pricehistory_data(name, headers):
    name_encoded = name.replace(' ', '%20').replace('&', '%26')
    # Define the pricehistory link
    pricehistory_link = f"https://steamcommunity.com/market/pricehistory/?appid=730&market_hash_name={name_encoded}"

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
    item_nameid = get_item_nameid(page, link)

    # Define your sessionid cookie

    # Define your headers
    headers = {
        'Cookie': f'steamLoginSecure={sessionid}'
    }
    # Navigate to the item page
    page.goto(link)

    # Get item details
    name, game, item_type_element, items_for_sale, sell_price, buy_requests, buy_price = get_item_details(page)
    print(name, game, item_type_element, items_for_sale, sell_price, buy_requests, buy_price)

    # Get priceoverview data
    lowest_price, volume, median_price = get_priceoverview_data(name)
    print(lowest_price, volume, median_price)

    # Get pricehistory data
    pricehistory_data = get_pricehistory_data(name, headers)
    if pricehistory_data:
        # Process pricehistory data
        daily_data = process_pricehistory_data(pricehistory_data)
        print(daily_data)
    
    # Get histogram data
    histogram_data = get_histogram_data(item_nameid, headers)
    if histogram_data:
        # Process histogram data
        processed_data = process_histogram(histogram_data)
        print(processed_data)



def main(): 
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        item_links = get_item_links(page)
        print(item_links[0:5])
        
        for link in item_links:
            process_item_links(page, link)

        browser.close()

if __name__ == "__main__":
    main()
