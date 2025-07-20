# This Python 3 environment comes with many helpful analytics libraries installed
# It is defined by the kaggle/python Docker image: https://github.com/kaggle/docker-python
# For example, here's several helpful packages to load

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

# Input data files are available in the read-only "../input/" directory
# For example, running this (by clicking run or pressing Shift+Enter) will list all files under the input directory

import os
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# You can write up to 20GB to the current directory (/kaggle/working/) that gets preserved as output when you create a version using "Save & Run All"
# You can also write temporary files to /kaggle/temp/, but they won't be saved outside of the current session
import os
import pydicom
import cv2
import numpy as np
from tqdm import tqdm

# Input and output directories
dcm_root_dir = "CT_Scans"  # Update with actual path
jpg_root_dir = "dataset_jpg"  # Output directory for JPEG images

# Function to convert DICOM to JPG
def convert_dcm_to_jpg(dcm_root, jpg_root):
    for exp_dir in ["EXP1_blind", "EXP2_open"]:  # Loop through both experiment directories
        dcm_exp_path = os.path.join(dcm_root, exp_dir)
        jpg_exp_path = os.path.join(jpg_root, exp_dir)
        os.makedirs(jpg_exp_path, exist_ok=True)

        # Traverse all patient directories
        for patient_folder in os.listdir(dcm_exp_path):
            patient_dcm_path = os.path.join(dcm_exp_path, patient_folder)
            patient_jpg_path = os.path.join(jpg_exp_path, patient_folder)
            os.makedirs(patient_jpg_path, exist_ok=True)

            for file in tqdm(os.listdir(patient_dcm_path), desc=f"Converting {exp_dir}/{patient_folder}"):
                if file.endswith(".dcm"):
                    dcm_file = os.path.join(patient_dcm_path, file)
                    jpg_file = os.path.join(patient_jpg_path, file.replace(".dcm", ".jpg"))

                    try:
                        # Read DICOM file
                        dicom_data = pydicom.dcmread(dcm_file)
                        image = dicom_data.pixel_array  # Extract pixel data

                        # Normalize and convert to 8-bit grayscale
                        image = (image - np.min(image)) / (np.max(image) - np.min(image)) * 255
                        image = image.astype(np.uint8)

                        # Save as JPEG
                        cv2.imwrite(jpg_file, image)

                    except Exception as e:
                        print(f"Error converting {dcm_file}: {e}")

# Run the conversion
# convert_dcm_to_jpg(dcm_root_dir, jpg_root_dir)

print("DICOM to JPEG conversion complete!")

import shutil
from sklearn.model_selection import train_test_split

# Base dataset directory
dataset_path = 'dataset_jpg'

# Output directories
output_dir = 'split_dataset'
train_dir = os.path.join(output_dir, 'train')
valid_dir = os.path.join(output_dir, 'valid')
test_dir = os.path.join(output_dir, 'test')

# Create output directories
os.makedirs(train_dir, exist_ok=True)
os.makedirs(valid_dir, exist_ok=True)
os.makedirs(test_dir, exist_ok=True)

# Train, Test, Validation split ratios
train_ratio = 0.7
valid_ratio = 0.15
test_ratio = 0.15

# Iterate over main classes (EXP1_blind, EXP2_open)
# for class_folder in os.listdir(dataset_path):
#     class_path = os.path.join(dataset_path, class_folder)

#     if os.path.isdir(class_path):
#         # Iterate over subdirectories (e.g., 1067, 1068, ...)
#         for sub_folder in os.listdir(class_path):
#             sub_folder_path = os.path.join(class_path, sub_folder)

#             if os.path.isdir(sub_folder_path):
#                 images = os.listdir(sub_folder_path)

#                 # Train-Test-Validation split
#                 train_imgs, temp_imgs = train_test_split(images, test_size=(1 - train_ratio), random_state=42)
#                 valid_imgs, test_imgs = train_test_split(temp_imgs, test_size=test_ratio / (test_ratio + valid_ratio), random_state=42)

#                 # Copy images to respective directories
#                 for img in train_imgs:
#                     src = os.path.join(sub_folder_path, img)
#                     dst = os.path.join(train_dir, class_folder, sub_folder)
#                     os.makedirs(dst, exist_ok=True)
#                     shutil.copy(src, dst)

#                 for img in valid_imgs:
#                     src = os.path.join(sub_folder_path, img)
#                     dst = os.path.join(valid_dir, class_folder, sub_folder)
#                     os.makedirs(dst, exist_ok=True)
#                     shutil.copy(src, dst)

#                 for img in test_imgs:
#                     src = os.path.join(sub_folder_path, img)
#                     dst = os.path.join(test_dir, class_folder, sub_folder)
#                     os.makedirs(dst, exist_ok=True)
#                     shutil.copy(src, dst)

print("Dataset successfully split into train, validation, and test sets.")

import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam

# Paths to the converted dataset
dataset_dir = "split_dataset"  # Update this path
train_dir = os.path.join(dataset_dir, "train")  # Organize dataset into train/test
test_dir = os.path.join(dataset_dir, "test")

# Image Parameters
IMG_SIZE = 224  # Image resolution
BATCH_SIZE = 32

import albumentations as A
from tensorflow.keras.utils import Sequence

# Define Albumentations transformations
transform = A.Compose([
    A.Resize(IMG_SIZE, IMG_SIZE),
    A.HorizontalFlip(p=0.5),
    A.RandomBrightnessContrast(p=0.2),
    A.ElasticTransform(p=0.2),
    A.GridDistortion(p=0.2),
    A.Normalize(mean=(0.5, 0.5, 0.5), std=(0.5, 0.5, 0.5)),
])

class CustomDataGenerator(Sequence):
    def __init__(self, directory, batch_size, transform=None, subset='training', validation_split=0.2):
        self.directory = directory
        self.batch_size = batch_size
        self.transform = transform
        self.class_mode = 'binary'

        self.image_paths = []
        self.labels = []

        self.class_indices = {'EXP1_blind': 0, 'EXP2_open': 1}

        for class_name, class_idx in self.class_indices.items():
            class_dir = os.path.join(directory, class_name)
            if not os.path.isdir(class_dir):
                continue
            for patient_folder in os.listdir(class_dir):
                patient_dir = os.path.join(class_dir, patient_folder)
                if not os.path.isdir(patient_dir):
                    continue
                for image_name in os.listdir(patient_dir):
                    self.image_paths.append(os.path.join(patient_dir, image_name))
                    self.labels.append(class_idx)

        # Shuffle and split data
        indices = np.arange(len(self.image_paths))
        np.random.shuffle(indices)
        self.image_paths = np.array(self.image_paths)[indices]
        self.labels = np.array(self.labels)[indices]

        split_index = int(len(self.image_paths) * (1 - validation_split))
        if subset == 'training':
            self.image_paths = self.image_paths[:split_index]
            self.labels = self.labels[:split_index]
        elif subset == 'validation':
            self.image_paths = self.image_paths[split_index:]
            self.labels = self.labels[split_index:]

    def __len__(self):
        return int(np.ceil(len(self.image_paths) / self.batch_size))

    def __getitem__(self, idx):
        batch_x_paths = self.image_paths[idx * self.batch_size:(idx + 1) * self.batch_size]
        batch_y = self.labels[idx * self.batch_size:(idx + 1) * self.batch_size]

        batch_x = []
        for img_path in batch_x_paths:
            img = cv2.imread(img_path)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            if self.transform:
                augmented = self.transform(image=img)
                img = augmented['image']
            batch_x.append(img)

        return np.array(batch_x), np.array(batch_y)

train_data = CustomDataGenerator(
    train_dir,
    batch_size=BATCH_SIZE,
    transform=transform,
    subset='training'
)

val_data = CustomDataGenerator(
    train_dir,
    batch_size=BATCH_SIZE,
    transform=transform,
    subset='validation'
)

from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.models import Model

# Load the pre-trained MobileNetV2 model
base_model = MobileNetV2(input_shape=(IMG_SIZE, IMG_SIZE, 3),
                         include_top=False,
                         weights='imagenet')

# Freeze the base model
base_model.trainable = False

# Add a custom classification head
x = base_model.output
x = Flatten()(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.5)(x)
predictions = Dense(1, activation='sigmoid')(x)

model = Model(inputs=base_model.input, outputs=predictions)

# Compile the model
model.compile(optimizer=Adam(learning_rate=0.0001), loss='binary_crossentropy', metrics=['accuracy'])

# Train the model
# history = model.fit(train_data, validation_data=val_data, epochs=10)

# Test the model
test_datagen = ImageDataGenerator(rescale=1./255)
# test_data = test_datagen.flow_from_directory(
#     test_dir,
#     target_size=(IMG_SIZE, IMG_SIZE),
#     batch_size=BATCH_SIZE,
#     class_mode='binary'
# )

# test_loss, test_acc = model.evaluate(test_data)
# print(f"Test Accuracy: {test_acc:.2f}")

# Save the model
model.save("deepfake_detection_model.h5")

import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array, load_img
import numpy as np

# Paths
model_path = 'deepfake_detection_model.h5'  # Path to your trained model
test_dir = '/kaggle/working/split_dataset/test'  # Path to the test dataset

# Load the model
model = load_model(model_path)

# Image preprocessing parameters
img_size = (224, 224)  # Change this to the input size of your model

# Class labels (Update based on your dataset)
class_labels = ['EXP1_blind', 'EXP2_open']

# Perform inference
def predict_image(image_path):
    # Load and preprocess the image
    img = load_img(image_path, target_size=img_size)
    img_array = img_to_array(img) / 255.0  # Normalize to [0, 1]
    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension

    # Perform prediction
    predictions = model.predict(img_array)
    predicted_class = np.argmax(predictions, axis=1)[0]
    confidence = predictions[0][predicted_class]

    return class_labels[predicted_class], confidence

# Iterate over test images and make predictions
results = []
# for class_folder in os.listdir(test_dir):
#     class_folder_path = os.path.join(test_dir, class_folder)
#     if os.path.isdir(class_folder_path):
#         for sub_folder in os.listdir(class_folder_path):
#             sub_folder_path = os.path.join(class_folder_path, sub_folder)
#             if os.path.isdir(sub_folder_path):
#                 for img_file in os.listdir(sub_folder_path):
#                     img_path = os.path.join(sub_folder_path, img_file)
#                     predicted_class, confidence = predict_image(img_path)
#                     results.append({
#                         "image": img_file,
#                         "actual_class": class_folder,
#                         "predicted_class": predicted_class,
#                         "confidence": confidence
#                     })

# # Display results
# for result in results:
#     print(f"Image: {result['image']}, Actual: {result['actual_class']}, "
#            f"Predicted: {result['predicted_class']}, Confidence: {result['confidence']:.2f}")

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# Load the trained model
model = load_model('deepfake_detection_model.h5')

# Define image size and batch size
img_size = (224, 224)
batch_size = 32

# Prepare the test data generator
test_datagen = ImageDataGenerator(rescale=1.0 / 255.0)
# test_generator = test_datagen.flow_from_directory(
#     '/kaggle/working/split_dataset/test',
#     target_size=img_size,
#     batch_size=batch_size,
#     class_mode='binary',  # For binary classification
#     shuffle=False
# )

# # Evaluate the model
# loss, accuracy = model.evaluate(test_generator, verbose=1)
# print(f"Test Loss: {loss}")
# print(f"Test Accuracy: {accuracy}")

# # Predict classes
# test_generator.reset()
# predictions = (model.predict(test_generator, verbose=1) > 0.5).astype("int32")

# # Confusion Matrix
# conf_matrix = confusion_matrix(test_generator.classes, predictions)
# plt.figure(figsize=(10, 8))
# sns.heatmap(conf_matrix, annot=True, fmt="d", cmap="Blues",
#             xticklabels=test_generator.class_indices.keys(),
#             yticklabels=test_generator.class_indices.keys())
# plt.title("Confusion Matrix")
# plt.xlabel("Predicted Labels")
# plt.ylabel("True Labels")
# plt.show()

# # Classification Report
# report = classification_report(test_generator.classes, predictions,
#                                target_names=test_generator.class_indices.keys())
# print("\nClassification Report:\n")
# print(report)
# Found 3465 images belonging to 2 classes.
