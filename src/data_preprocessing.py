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
    
    # One-hot encode 'Name' column
    data = pd.get_dummies(data, columns=['Name'])

    # Normalize 'Average Price' and 'Total Volume' columns
    scaler_price = MinMaxScaler()
    scaler_volume = MinMaxScaler()
    data['Average Price'] = scaler_price.fit_transform(data[['Average Price']])
    data['Total Volume'] = scaler_volume.fit_transform(data[['Total Volume']])

    # Create daily dataset
    daily_data = data.copy()
    daily_data.set_index('Date', inplace=True)
    daily_data['Avg Price Last Day'] = daily_data['Average Price'].shift(1)
    daily_data['Total Volume Last Day'] = daily_data['Total Volume'].shift(1)

    # Create weekly dataset
    weekly_data = data.resample('W', on='Date').mean()
    weekly_data['Avg Price Last Week'] = weekly_data['Average Price'].shift(1)
    weekly_data['Total Volume Last Week'] = weekly_data['Total Volume'].shift(1)

    # Create monthly dataset
    monthly_data = data.resample('M', on='Date').mean()
    monthly_data['Avg Price Last Month'] = monthly_data['Average Price'].shift(1)
    monthly_data['Total Volume Last Month'] = monthly_data['Total Volume'].shift(1)

    # Drop rows with NaN values caused by the shifting
    daily_data = daily_data.dropna()
    weekly_data = weekly_data.dropna()
    monthly_data = monthly_data.dropna()

    # Split data into features and target
    X_daily = daily_data.drop('Average Price', axis=1)
    y_daily = daily_data['Average Price']
    X_weekly = weekly_data.drop('Average Price', axis=1)
    y_weekly = weekly_data['Average Price']
    X_monthly = monthly_data.drop('Average Price', axis=1)
    y_monthly = monthly_data['Average Price']

    # Split data into training and testing sets
    X_train_daily, X_test_daily, y_train_daily, y_test_daily = train_test_split(X_daily, y_daily, test_size=0.2, random_state=42, shuffle=False)
    X_train_weekly, X_test_weekly, y_train_weekly, y_test_weekly = train_test_split(X_weekly, y_weekly, test_size=0.2, random_state=42, shuffle=False)
    X_train_monthly, X_test_monthly, y_train_monthly, y_test_monthly = train_test_split(X_monthly, y_monthly, test_size=0.2, random_state=42, shuffle=False)

    return (X_train_daily, X_test_daily, y_train_daily, y_test_daily, scaler_price), (X_train_weekly, X_test_weekly, y_train_weekly, y_test_weekly, scaler_price), (X_train_monthly, X_test_monthly, y_train_monthly, y_test_monthly, scaler_price)
