# -*- coding: utf-8 -*-
"""train.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1iuxTojcLTvoPbdFZyCYr3_o-J8kuffkO
"""

!pip install flickrapi

import os
import requests
import matplotlib.pyplot as plt
import imghdr
import flickrapi
from fastai.vision import *
import os, shutil
from google.colab import drive
drive.mount('/content/drive')

"""# Data Scraping"""

FLICKR_KEY = 'XXXXXX'
FLICKR_SECRET = 'XXXXX'

def flickr_scrape_onetype(credential_key, credential_secret, query, num, path_to_save, starting_count=0):
  """scrapes one type of photo query using Flickr API and downloads it to the respective folder

  Args:
    credential_key (str) : credential key for flickr api search
    credential_secret (str) : credential secret for flickr api search
    query (str) : flickr search query
    num (int) : Number of photos to query; Max 500
    path_to_save (str) : relative path to install all the images. e.g. ./images/plastic
    starting_count (int) : the count left off from the last previously scraped image. If just first image being scraped, use 0.

  Returns:
    None

  """
  if num > 500:
    exit         # Cannot exceed 500 requests

  flickr = flickrapi.FlickrAPI(credential_key, credential_secret, format='parsed-json')
  response = flickr.photos.search(text=query, sort='relevance', per_page=num, page=1, extras='url_m')

  # Parse link to image from json file
  count = starting_count
  for i in range(len(response['photos']['photo'])):
    count += 1

    if 'url_m' not in response['photos']['photo'][i]: # if does not have url_m, skip to next search
      count -= 1
      continue
    
    img_link = response['photos']['photo'][i]['url_m']

    img = requests.get(img_link)
    file = open(f'{path_to_save}/img_{count}', "wb")    # Creating image file
    file.write(img.content)                         # Writing image into file
    file.close()

  return count

def scrape_multiple(credential_key, credential_secret, query_list, num, path_to_save, starting_count=0):
  """scrapes multiple types of photo query using Flickr API and downloads it to the respective folder

  Args:
    credential_key (str) : credential key for flickr api search
    credential_secret (str) : credential secret for flickr api search
    query_list (list of str) : flickr search queries
    num (int) : Number of photos to query; Max 500
    path_to_save (str) : relative path to install all the images. e.g. ./images/plastic
    starting_count (int) : the count left off from the last previously scraped image. If just first image being scraped, use 0.

  Returns:
    None

  """
  count = starting_count
  for query in query_list:
    count = flickr_scrape_onetype(FLICKR_KEY, FLICKR_SECRET, query, num, path_to_save, count)
    print(count)

# Scrape plastic images
PLASTICS = ['plastic containers', 'plastic wrappers', 'plastic bottle caps', 'plastic bottles', 'plastic bags', 'plastic straws', 'plastic stirrers']
scrape_multiple(FLICKR_KEY, FLICKR_SECRET, PLASTICS, 100, './content/drive/MyDrive/recycle-app/images/plastic', 0)

# Scrape glass images
GLASS=['glassware', 'glass containers', 'glass bottles', 'glass jars']
scrape_multiple(FLICKR_KEY, FLICKR_SECRET, GLASS, 150, '/content/drive/MyDrive/recycle-app/images/glass', 0)

# Scrape electronics images
ELECTRONICS = ['desktop', 'laptops', 'monitors', 'printers', 'copiers', 'hard drives', 'batteries', 'tablets', 'televisions', 'cell phones', 'digital cameras', 'cords', 'keyboards', 'toner cartridges']
scrape_multiple(FLICKR_KEY, FLICKR_SECRET, ELECTRONICS, 80, '/content/drive/MyDrive/recycle-app/images/electronics', 0)

# Scrape non-recyclables images
NON_RECYCLABLE = ['pizza box', 'plastic bag', 'take-out container', 'gift wrap', 'shredded paper', 'coffee cup', 'food waste', 'ceramics', 'kitchenware', 'windows', 'mirrors', 'plastic wrap', 'bubble wrap', 'photographs', 'medical waste', 'styrofoam', 'plastic toys', 'foam egg cartons', 'wood', 'light bulbs', 'garden tools']
scrape_multiple(FLICKR_KEY, FLICKR_SECRET, NON_RECYCLABLE, 100, '/content/drive/MyDrive/recycle-app/images/non-recyclable', 0)

"""# Data Processing"""

import matplotlib.pyplot as plt
import numpy as np
import os
from PIL import Image
import tensorflow as tf

from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential

IMG_HEIGHT = 180
IMG_WIDTH = 180
BATCH_SIZE = 32
CLASSES = ['plastic', 'glass', 'metal', 'electronics', 'paper', 'non_recyclable'] # To follow this index for outputs
CLASSES_DICT = {
    'plastic' : 0,
    'glass' : 1,
    'metal' : 2,
    'electronics' : 3,
    'paper' : 4,
    'non_recyclable' : 5 
}
NUM_CLASSES = len(CLASSES)

def process_data(path_to_folder, class_index):
  """process_data processes all data in a file and resizes it to IMG_WIDTH and IMG_HEIGHT and returns a list of
  all images in the given folder
  
  Args:
    path_to_folder (str) : absolute path to the folder that contains all the images with backslash at the end
    class_index (int) : index of the class. for eg. plastic = 0
  
  Returns:
    imgs (array of imgs) : an array of shape (n, IMG_WIDTH, IMG_HEIGHT, 3) of the numpy array of values of images with shape (IMG_WIDTH, IMG_HEIGHT, IMG_DEPTH) 

  """
  if path_to_folder[-1] != "/":  # To ensure proper formatting for path with "/" at the end
    path_to_folder += "/"
  
  imgs = []
  count = 1
  for file in os.listdir(str(path_to_folder)):
    file_path = path_to_folder + file
    img = Image.open(file_path)
    img = img.resize((IMG_HEIGHT, IMG_WIDTH), resample=Image.LANCZOS)
    img_array = np.array(img)

    # when img_array is not RGB dimensions, convert to 3D.
    if img_array.ndim != 3:
      img = Image.fromarray(img_array)
      img = img.convert('RGB')
      img_array = np.array(img)

    else:
      if np.shape(img_array)[2] > 3:          # ensure that there are no more than 3 layers of depth for rgb
        continue

    imgs.append(img_array)

    if np.shape(img_array) != (180, 180, 3):    # checking shape of img array
      print(count)

    count += 1
    if count % 100 == 0:
      print(f"appending {count}...")
  
  print(len(imgs))
  imgs = np.array(imgs)
  np.random.shuffle(imgs)
  imgs_labels = np.full((np.shape(imgs)[0], 1), class_index)

  train_size = np.shape(imgs)[0] // 100 * 80 # 80 % training size

  train_imgs = imgs[:train_size, :, :, :]
  train_labels = imgs_labels[:train_size:, :]

  test_imgs = imgs[train_size:, :, :, :]
  test_labels = imgs_labels[train_size:, :]

  return train_imgs, train_labels, test_imgs, test_labels

plastic_train_imgs, plastic_train_labels, plastic_test_imgs, plastic_test_labels = process_data('/content/drive/MyDrive/recycle-app/images/plastic/', CLASSES_DICT['plastic'])

electronics_train_imgs, electronics_train_labels, electronics_test_imgs, electronics_test_labels = process_data('/content/drive/MyDrive/recycle-app/images/electronics/', CLASSES_DICT['electronics'])

glass_train_imgs, glass_train_labels, glass_test_imgs, glass_test_labels = process_data('/content/drive/MyDrive/recycle-app/images/glass/', CLASSES_DICT['glass'])

metal_train_imgs, metal_train_labels, metal_test_imgs, metal_test_labels = process_data('/content/drive/MyDrive/recycle-app/images/metal/', CLASSES_DICT['metal'])

paper_train_imgs, paper_train_labels, paper_test_imgs, paper_test_labels = process_data('/content/drive/MyDrive/recycle-app/images/paper/', CLASSES_DICT['paper'])

non_recyclable_train_imgs, non_recyclable_train_labels, non_recyclable_test_imgs, non_recyclable_test_labels = process_data('/content/drive/MyDrive/recycle-app/images/non-recyclable/', CLASSES_DICT['non_recyclable'])

# Train data
train_images = np.concatenate((plastic_train_imgs, glass_train_imgs, metal_train_imgs, electronics_train_imgs, paper_train_imgs, non_recyclable_train_imgs), axis=0)
train_labels = np.concatenate((plastic_train_labels, glass_train_labels, metal_train_labels, electronics_train_labels, paper_train_labels, non_recyclable_train_labels), axis=0)

# Test data
test_images = np.concatenate((plastic_test_imgs, glass_test_imgs, metal_test_imgs, electronics_test_imgs, paper_test_imgs, non_recyclable_test_imgs), axis=0)
test_labels = np.concatenate((plastic_test_labels, glass_test_labels, metal_test_labels, electronics_test_labels, paper_test_labels, non_recyclable_test_labels), axis=0)

print(np.shape(train_images), np.shape(train_labels), np.shape(test_images), np.shape(test_labels))

# Data Augmentation layer
data_augmentation = keras.Sequential(
  [
    layers.experimental.preprocessing.RandomFlip("horizontal", 
                                                 input_shape=(IMG_HEIGHT, 
                                                              IMG_WIDTH,
                                                              3)),
    layers.experimental.preprocessing.RandomRotation(0.1),
    layers.experimental.preprocessing.RandomZoom(0.1),
  ]
)

# Build Model
model = Sequential([
  data_augmentation,
  layers.experimental.preprocessing.Rescaling(1./255),
  layers.Conv2D(16, 3, padding='same', activation='relu'),
  layers.MaxPooling2D(),
  layers.Conv2D(32, 3, padding='same', activation='relu'),
  layers.MaxPooling2D(),
  layers.Conv2D(64, 3, padding='same', activation='relu'),
  layers.MaxPooling2D(),
  layers.Dropout(0.2),
  layers.Flatten(),
  layers.Dense(128, activation='relu'),
  layers.Dense(NUM_CLASSES)
])

model.compile(optimizer='adam', loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True), metrics=['accuracy'])

model.summary()

epochs=15
history = model.fit(
  train_images,
  train_labels,
  epochs=epochs,
  validation_data=(test_images, test_labels),
)

"""# Evaluate Model"""

acc = history.history['accuracy']
val_acc = history.history['val_accuracy']

loss = history.history['loss']
val_loss = history.history['val_loss']

epochs_range = range(epochs)

plt.figure(figsize=(8, 8))
plt.subplot(1, 2, 1)
plt.plot(epochs_range, acc, label='Training Accuracy')
plt.plot(epochs_range, val_acc, label='Validation Accuracy')
plt.legend(loc='lower right')
plt.title('Training and Validation Accuracy')

plt.subplot(1, 2, 2)
plt.plot(epochs_range, loss, label='Training Loss')
plt.plot(epochs_range, val_loss, label='Validation Loss')
plt.legend(loc='upper right')
plt.title('Training and Validation Loss')
plt.show()

"""Save Model For Deployment"""

# save model for loading
model.save('/content/drive/MyDrive/recycle-app/recycle_detection_model.h5')

# convert model for tflite deployment
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
open("/content/drive/MyDrive/recycle-app/recycle_detection_model.tflite", "wb").write(tflite_model)

plt.imshow(plastic_train_imgs[100])

img_array = tf.expand_dims(plastic_train_imgs[41], 0)

def predict_object(img_array):
  tf.expand_dims(img_array, 0)
  prob_pred = model.predict(img_array)
  object_idx = np.argmax(prob_pred)
  
  for obj, value in CLASSES_DICT.items():
    if value == object_idx:
      return obj

a = predict_object(img_array)
print(a)

import tensorflow as tf

interpreter = tf.lite.Interpreter(model_path='/content/drive/MyDrive/recycle-app/recycle_detection_model.tflite')
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
print(input_details)

output_details = interpreter.get_output_details()

print(output_details)

