import matplotlib.pyplot as plt
import numpy as np

def plot_loss(history):
    plt.figure(figsize=(10,6))
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model loss')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(['Train', 'Validation'], loc='upper right')
    plt.show()


def plot_predictions(y_true_day, y_pred_day, y_true_week, y_pred_week, y_true_month, y_pred_month):
    fig, axs = plt.subplots(3, figsize=(10, 18))

    # Plot for day
    axs[0].scatter(y_true_day, y_pred_day, alpha=0.3)
    axs[0].plot([min(y_true_day), max(y_true_day)], [min(y_true_day), max(y_true_day)], 'r')
    axs[0].set_title('Day Predictions', loc='left')  # adjust title position here
    axs[0].set_xlabel('Actual Values')
    axs[0].set_ylabel('Predicted Values')

    # Plot for week
    axs[1].scatter(y_true_week, y_pred_week, alpha=0.3)
    axs[1].plot([min(y_true_week), max(y_true_week)], [min(y_true_week), max(y_true_week)], 'r')
    axs[1].set_title('Week Predictions', loc='left')  # adjust title position here
    axs[1].set_xlabel('Actual Values')
    axs[1].set_ylabel('Predicted Values')

    # Plot for month
    axs[2].scatter(y_true_month, y_pred_month, alpha=0.3)
    axs[2].plot([min(y_true_month), max(y_true_month)], [min(y_true_month), max(y_true_month)], 'r')
    axs[2].set_title('Month Predictions', loc='left')  # adjust title position here
    axs[2].set_xlabel('Actual Values')
    axs[2].set_ylabel('Predicted Values')

    plt.tight_layout()
    plt.show()
