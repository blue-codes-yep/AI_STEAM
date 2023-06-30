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
    
    data['Date'] = (data['Date'] - data['Date'].min()).dt.days

    # One-hot encode 'Name' column
    data = pd.get_dummies(data, columns=['Name'])

    # Normalize 'Average Price' and 'Total Volume' columns
    scaler = MinMaxScaler()
    data[['Average Price', 'Total Volume']] = scaler.fit_transform(data[['Average Price', 'Total Volume']])

    # Split data into features and target
    X = data.drop('Average Price', axis=1)
    y = data['Average Price']

    # Split data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=False)

    return X_train, X_test, y_train, y_test
