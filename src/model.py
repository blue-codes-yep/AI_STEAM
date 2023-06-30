from data_preprocessing import preprocess_data
import os
os.environ['XLA_FLAGS'] = '--xla_gpu_cuda_data_dir=/home/blue/miniconda3/envs/tf/lib'
import tensorflow as tf

# Get preprocessed data
X_train, X_test, y_train, y_test = preprocess_data()
X_train = X_train.astype('float32')
y_train = y_train.astype('float32')
X_test = X_test.astype('float32')
y_test = y_test.astype('float32')


# Continue with model definition, compilation, and training...

# Define the model
model = tf.keras.models.Sequential([
    tf.keras.layers.Dense(1, input_shape=[X_train.shape[1]])
])

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
model.fit(X_train, y_train, epochs=10)

# Evaluate the model
loss = model.evaluate(X_test, y_test)
print('Test loss:', loss)

# Make predictions
predictions = model.predict(X_test)

history = model.fit(X_train, y_train, epochs=10, validation_data=(X_test, y_test))
print('Training loss:', history.history['loss'])
print('Validation loss:', history.history['val_loss'])

weights = model.get_weights()
print('Weights:', weights)

print('First 10 predictions:', predictions[:10])
print('First 10 actual values:', y_test[:10])
