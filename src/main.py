from model import create_and_evaluate_model, test_model
from data_preprocessing import preprocess_data
from visualization import plot_predictions, plot_loss


def main():
    # Get preprocessed data
    daily_data, weekly_data, monthly_data = preprocess_data()

    # Train a model on the daily data
    print("Training Model:")
    model, scaler_price, history = create_and_evaluate_model(daily_data)

    # Plot the loss for each epoch
    plot_loss(history)
    
    # Make predictions for daily, weekly, and monthly data
    print("\nMaking Predictions:")
    y_true_day, y_pred_day = test_model(model, *daily_data)
    y_true_week, y_pred_week = test_model(model, *weekly_data)
    y_true_month, y_pred_month = test_model(model, *monthly_data)

    # Plot predictions
    plot_predictions(
        y_true_day, y_pred_day, y_true_week, y_pred_week, y_true_month, y_pred_month
    )


if __name__ == "__main__":
    main()
