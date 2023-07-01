from tensorflow.keras.callbacks import TensorBoard
from tensorflow.keras.utils import plot_model
import numpy as np
import tensorflow as tf
import os
import datetime

os.environ['XLA_FLAGS'] = '--xla_gpu_cuda_data_dir=/home/blue/miniconda3/envs/tf/lib'

def create_model(input_shape):
    # Define the model
    model = tf.keras.models.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=input_shape),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(32, activation='relu'),
        tf.keras.layers.Dense(16, activation='relu'),
        tf.keras.layers.Dense(8, activation='relu'),
        tf.keras.layers.Dense(1)
    ])

    # Compile the model
    model.compile(optimizer='adam', loss='mean_squared_error', metrics=[tf.keras.metrics.MeanAbsoluteError()])

    return model


def train_model(model, X_train, y_train, X_test, y_test, epochs=15000):
    # Get the current time
    current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    # Initialize TensorBoard with a log directory that includes the current time
    log_dir = f'logs/{current_time}'
    os.makedirs(log_dir, exist_ok=True)  # create the directory if it does not exist
    tensorboard = TensorBoard(log_dir=log_dir)

    # Save the model architecture to a file
    plot_model(model, to_file=os.path.join(log_dir, 'model.png'), show_shapes=True)

    # Train the model with TensorBoard callback
    history = model.fit(X_train, y_train, epochs=epochs, validation_data=(X_test, y_test), callbacks=[tensorboard])

    return model, history


def test_model(model,X_train, X_test,y_train, y_test, scaler_price):
    # Ensure that data does not contain NaN values and is of type float32
    X_test = np.nan_to_num(X_test).astype('float32')
    y_test = np.nan_to_num(y_test).astype('float32')

    # Evaluate the model
    loss = model.evaluate(X_test, y_test)
    print('Test loss:', loss)

    # Make predictions
    predictions = model.predict(X_test)

    # Inverse transform the predictions and the actual values
    predictions = scaler_price.inverse_transform(predictions)
    y_test = scaler_price.inverse_transform(y_test.reshape(-1, 1))  # change this line

    return y_test, predictions

def create_and_evaluate_model(data, epochs=15000, model_path='model.h5'):
    X_train, X_test, y_train, y_test, scaler_price = data
    X_train = X_train.astype('float32')
    y_train = y_train.astype('float32')
    X_test = X_test.astype('float32')
    y_test = y_test.astype('float32')

    # Check if a trained model already exists
    if os.path.exists(model_path):
        print("Loading existing model")
        model = tf.keras.models.load_model(model_path)
    else:
        print("Creating new model")
        model = create_model([X_train.shape[1]])

    model, history = train_model(model, X_train, y_train, X_test, y_test, epochs)
    y_test, predictions = test_model(model,X_train, X_test, y_train, y_test, scaler_price)

    print('Training loss:', history.history['loss'])
    print('Validation loss:', history.history['val_loss'])

    weights = model.get_weights()
    print('Weights:', weights)

    print('First 25 predictions:', predictions[:25])
    print('First 25 actual values:', y_test[:25])   

    # Save the model
    model.save(model_path)

    return model, scaler_price, history
