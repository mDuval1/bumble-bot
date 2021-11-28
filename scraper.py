import time
import os
import random
import json
import itertools
import uuid

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait

WINDOW_PARAMETERS = './window.json'
DATA_FOLDER = 'profiles'
MAX_PROFILES_TO_SEE = 1000
RATIO_TEST_TRAIN = 0.4

attach = True

def get_driver(reattach):
    global driver
    if reattach:
        with open('./window.json', 'r') as file:
            parameters = json.load(file)
        driver = attach_to_session(parameters['url'], parameters['session_id'])
    else:
        chrome_path = '/usr/local/bin/chromedriver'
        options = Options()
        options.headless = False
        # options.add_experimental_option("detach", True)
        driver = webdriver.Chrome(chrome_path, options=options)
    url = driver.command_executor._url
    session_id = driver.session_id
    print(f'Driver info | url: {url}, session_id: {session_id}')
    with open('./window.json', 'w') as file:
        parameters = {
            "url": url,
            "session_id": session_id
        }
        json.dump(parameters, file)
    return driver


def attach_to_session(executor_url, session_id):
    options = Options()
    options.headless = True
    driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={}, options=options)
    driver.session_id = session_id
    return driver


def signin(driver: WebDriver):
    driver.get('https://bumble.com/app')
    driver.implicitly_wait(5)
    print('Using cell phone number...')
    cellphone = driver.find_element_by_xpath("//*[contains(text(), 'Use cell phone number')]")
    time.sleep(3)
    print('Clicking and filling phone...')
    cellphone.click()
    time.sleep(3)
    number = driver.find_element_by_xpath('//input[@name="phone"]')
    mobile_phone = os.getenv('MOBILE_PHONE')
    number.send_keys(mobile_phone)
    print('Validating...')
    time.sleep(3)
    validate = driver.find_element_by_xpath('//button[@type="submit"]')
    validate.click()
    print('Waiting 30s for user to fill code...')
    WebDriverWait(driver, timeout=30).until(lambda d: d.find_element_by_xpath('//article[@class="encounters-album"]'))
    print('Connected !')


def change_div_on_key_down(driver: WebDriver):
    javaScript = """
document.addEventListener('keydown', event => {
    const keyName = event.key;
    if (keyName === 'ArrowRight') {
    const newdiv = document.createElement('div');
    newdiv.id = 'onArrowRight';
    newdiv.style.display = 'none';
    document.body.appendChild(newdiv);
    }
    if (keyName === 'ArrowLeft') {
    const newdiv = document.createElement('div');
    newdiv.id = 'onArrowLeft';
    newdiv.style.display = 'none';
    document.body.appendChild(newdiv);
    }
});
    """
    driver.execute_script(javaScript)


def get_number_of_okko(driver: WebDriver):
    try:
        kos = len(driver.find_elements_by_xpath('//div[@id="onArrowLeft"]'))
    except:
        kos = 0
    try:
        oks = len(driver.find_elements_by_xpath('//div[@id="onArrowRight"]'))
    except:
        oks = 0
    return kos, oks

def get_tmp_path(profile_id):
    return f'{DATA_FOLDER}/{profile_id}.png'

def get_train_or_test():
    if random.random() < RATIO_TEST_TRAIN:
        return 'test'
    return 'train'

def get_ok_path(profile_id):
    folder = get_train_or_test()
    return f'{DATA_FOLDER}/{folder}/ok/{profile_id}.png'

def get_ko_path(profile_id):
    folder = get_train_or_test()
    return f'{DATA_FOLDER}/{folder}/ko/{profile_id}.png'


def save_profile_info(driver: WebDriver):
    profile_id = str(uuid.uuid4())
    driver.find_element_by_xpath('//div[@class="encounters-album__stories-container"]').screenshot(get_tmp_path(profile_id))
    panels = driver.find_elements_by_xpath('//div[@class="encounters-album__story"]')
    n_panels = len(panels)
    print(f'She has {n_panels} sections in her profile.')
    return profile_id


def prepare_to_crawl(driver: WebDriver):
    change_div_on_key_down(driver)
    for folder, label in itertools.product(['train', 'test'], ['ok', 'ko']):
        os.makedirs(os.path.join(DATA_FOLDER, folder, label), exist_ok=True)


def crawl(driver: WebDriver):
    print('Starting crawler...')
    prepare_to_crawl(driver)
    print('Prepared to crawl.')
    kos, oks = get_number_of_okko(driver)
    total_div_added = kos + oks
    profiles_seen = 0
    while profiles_seen < MAX_PROFILES_TO_SEE:
        profiles_seen += 1
        print(f'Saw {profiles_seen} profiles')
        time.sleep(1)
        profile_id = save_profile_info(driver)
        current_div_added = sum(get_number_of_okko(driver))
        while current_div_added <= total_div_added:
            # print(f'Waiting for user action (current_profiles_seen={current_div_added})')
            time.sleep(0.5)
            current_div_added = sum(get_number_of_okko(driver))
        print('Registered user action')
        new_kos, new_oks = get_number_of_okko(driver)
        if new_kos > kos:
            print('Registered a ko')
            os.rename(get_tmp_path(profile_id), get_ko_path(profile_id))
        else:
            print('Registered a ok')
            os.rename(get_tmp_path(profile_id), get_ok_path(profile_id))
        kos, oks = new_kos, new_oks
        total_div_added = kos + oks

if __name__ == '__main__':
    driver = get_driver()
    crawl(driver)