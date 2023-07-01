from data_preprocessing import preprocess_data
from visualization import plot_predictions
import os
os.environ['XLA_FLAGS'] = '--xla_gpu_cuda_data_dir=/home/blue/miniconda3/envs/tf/lib'
import tensorflow as tf

# Get preprocessed data
X_train, X_test, y_train, y_test, scaler_price = preprocess_data()
X_train = X_train.astype('float32')
y_train = y_train.astype('float32')
X_test = X_test.astype('float32')
y_test = y_test.astype('float32')

# Define the model
model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(64, activation='relu', input_shape=[X_train.shape[1]]),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(1)
])

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
history = model.fit(X_train, y_train, epochs=100, validation_data=(X_test, y_test))

# Evaluate the model
loss = model.evaluate(X_test, y_test)
print('Test loss:', loss)

# Make predictions
predictions = model.predict(X_test)

# Inverse transform the predictions and the actual values
predictions = scaler_price.inverse_transform(predictions)
y_test = scaler_price.inverse_transform(y_test.values.reshape(-1, 1))

# Plot predictions
plot_predictions(y_test, predictions)

print('Training loss:', history.history['loss'])
print('Validation loss:', history.history['val_loss'])

weights = model.get_weights()
print('Weights:', weights)

print('First 25 predictions:', predictions[:25])
print('First 25 actual values:', y_test[:25])
