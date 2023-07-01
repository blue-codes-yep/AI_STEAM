import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

def preprocess_data():
    # Load the data
    data = pd.read_csv('../data/daily.csv')
    print("Data preprocessing module loaded.")

    # Convert 'Date' column to datetime
    data['Date'] = pd.to_datetime(data['Date'])

    # Sort data by date
    data = data.sort_values('Date')
    data['Hour'] = data['Date'].dt.hour
    data['DayOfWeek'] = data['Date'].dt.dayofweek
    data = data.drop('Date', axis=1)
    
    # One-hot encode 'Name' column
    data = pd.get_dummies(data, columns=['Name'])

    # Normalize 'Average Price' and 'Total Volume' columns
    scaler_price = MinMaxScaler()
    scaler_volume = MinMaxScaler()
    data['Average Price'] = scaler_price.fit_transform(data[['Average Price']])
    data['Total Volume'] = scaler_volume.fit_transform(data[['Total Volume']])

    # Create new features for the average price and total volume for the past week and past month
    data['Avg Price Last Week'] = data['Average Price'].rolling(window=7).mean()
    data['Total Volume Last Week'] = data['Total Volume'].rolling(window=7).sum()
    data['Avg Price Last Month'] = data['Average Price'].rolling(window=30).mean()
    data['Total Volume Last Month'] = data['Total Volume'].rolling(window=30).sum()

    # Drop rows with NaN values caused by the rolling window calculations
    data = data.dropna()

    # Split data into features and target
    X = data.drop('Average Price', axis=1)
    y = data['Average Price']

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

    return X_train, X_test, y_train, y_test, scaler_price