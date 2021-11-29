import os
import time
from PIL import Image
import numpy as np
from enum import Enum

from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.keys import Keys
import tensorflow as tf

from train import model_path, IMG_SIZE
from scraper import save_profile_info, get_tmp_path, DATA_FOLDER, get_ko_path, get_ok_path

MAX_PROFILE_SEEN = 400
SLEEP_BETWEEN_AVG = 4
PREDICTION_FOLDER = 'prediction'

class Label(str, Enum):
    OK = 'ok'
    KO = 'ko'

def get_train_path(profile_id, label):
    if label == Label.OK:
        return get_ok_path(profile_id)
    return get_ko_path(profile_id)


def get_infer_path(profile_id, label):
    return f'{DATA_FOLDER}/{PREDICTION_FOLDER}/{label}/{profile_id}.png'

def load_model():
    return tf.keras.models.load_model(model_path)

def prepare_inference():
    for predicted_label in [Label.OK, Label.KO]:
        os.makedirs(os.path.join(DATA_FOLDER, PREDICTION_FOLDER, predicted_label), exist_ok=True)

def predict(image_path, model):
    im = Image.open(image_path)
    im_array = np.array(im)
    tfim = tf.image.crop_and_resize([im_array], [[0, 0, 1, 0.5]], [0], crop_size=(IMG_SIZE, IMG_SIZE))[0, :, :, :3]
    prediction = model.predict(tf.expand_dims(tfim, 0))
    ko_proba = prediction[0][0]
    if ko_proba > 0.7:
        return Label.KO
    return Label.OK

def swipe(driver: WebDriver, label):
    body = driver.find_element_by_xpath("//body")
    if label == Label.OK:
        print('Swiping right :)')
        body.send_keys(Keys.ARROW_RIGHT)
    else:
        print('Swiping left ><')
        body.send_keys(Keys.ARROW_LEFT)


def infer(driver: WebDriver):
    model = load_model()
    prepare_inference()
    seen = 0
    while seen < MAX_PROFILE_SEEN:
        print(f'Seen {seen} profiles')
        profile_id = save_profile_info(driver)
        photo_path = get_tmp_path(profile_id)
        label = predict(photo_path, model)
        os.rename(get_tmp_path(profile_id), get_infer_path(profile_id, label))
        swipe(driver, label)
        time.sleep(np.random.poisson(SLEEP_BETWEEN_AVG)+2)
        seen += 1