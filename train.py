import tensorflow as tf
import tensorflow_datasets as tfds
from tensorflow.keras.models import Sequential
from tensorflow.keras import layers
from tensorflow.keras.applications import EfficientNetB0

from scraper import DATA_FOLDER

WIDTH = 1174
HEIGHT = 787
BATCH_SIZE = 8
IMG_SIZE = 224
NUM_CLASSES = 2
epochs = 15
model_path = 'model'
strategy = tf.distribute.MirroredStrategy()

def process(x):
    image, label = x['image'], x['label']
    return tf.image.crop_and_resize([image], [[0, 0, 1, 0.5]], [0], crop_size=(IMG_SIZE, IMG_SIZE))[0], label

def input_preprocess(image, label):
    label = tf.one_hot(label, 2)
    return image, label

def get_datasets():
    builder = tfds.folder_dataset.ImageFolder(
        root_dir=f'{DATA_FOLDER}/'
    )
    ds_train = builder.as_dataset(split='train', shuffle_files=True)
    ds_test = builder.as_dataset(split='test', shuffle_files=True)
    ds_train = ds_train.map(process)
    ds_test = ds_test.map(process)

    
    ds_train = ds_train.map(input_preprocess, num_parallel_calls=tf.data.AUTOTUNE)
    ds_train = ds_train.batch(batch_size=BATCH_SIZE, drop_remainder=True)
    ds_train = ds_train.prefetch(tf.data.AUTOTUNE)

    ds_test = ds_test.map(input_preprocess)
    ds_test = ds_test.batch(batch_size=BATCH_SIZE, drop_remainder=True)

    return ds_train, ds_test

def build_model(num_classes):
    inputs = layers.Input(shape=(IMG_SIZE, IMG_SIZE, 3))
    img_augmentation = Sequential(
        [
            layers.RandomRotation(factor=0.10),
            layers.RandomTranslation(height_factor=0.1, width_factor=0.1),
        ],
        name="img_augmentation",
    )
    x = img_augmentation(inputs)
    model = EfficientNetB0(include_top=False, input_tensor=x, weights="imagenet")

    # Freeze the pretrained weights
    model.trainable = False

    # Rebuild top
    x = layers.GlobalAveragePooling2D(name="avg_pool")(model.output)
    x = layers.BatchNormalization()(x)

    top_dropout_rate = 0.2
    x = layers.Dropout(top_dropout_rate, name="top_dropout")(x)
    outputs = layers.Dense(NUM_CLASSES, activation="softmax", name="pred")(x)

    # Compile
    model = tf.keras.Model(inputs, outputs, name="EfficientNet")
    optimizer = tf.keras.optimizers.Adam(learning_rate=1e-3)
    model.compile(
        optimizer=optimizer, loss="categorical_crossentropy", metrics=["accuracy"]
    )
    return model

def train_model():
    with strategy.scope():
        model = build_model(num_classes=NUM_CLASSES)
    ds_train, ds_test = get_datasets()
    model.fit(ds_train, epochs=epochs, validation_data=ds_test, verbose=2)
    model.save(model_path)
