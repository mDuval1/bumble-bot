"""
This is where we upload and download labeled data, to improve the model as it sees more people. 
"""
import os
import glob

from kili.client import Kili
from tqdm import tqdm

from scraper import DATA_FOLDER
from inference import PREDICTION_FOLDER, get_train_path
from kili.mutations import project

JOB_ID = 'JOB_0'


def get_kili_client() -> Kili:
    return Kili(api_key=os.getenv('KILI_API_KEY'))

def get_profiles_in_prediction():
    return glob.glob(f'./{DATA_FOLDER}/{PREDICTION_FOLDER}/**/**.png')

def upload():
    kili = get_kili_client()
    project_id = os.getenv('BUMBLE_PROJECT_ID')
    current_assets_uploaded = kili.assets(project_id=project_id, fields=['externalId'])
    external_ids_uploaded = [asset['externalId'] for asset in current_assets_uploaded]
    profiles_in_prediction = get_profiles_in_prediction()
    profiles_to_upload = [x for x in profiles_in_prediction if not os.path.basename(x) in external_ids_uploaded]
    print(f'Uploading {len(profiles_to_upload)} profiles...')
    data_to_upload = []
    for profile in profiles_to_upload:
        asset = {
            "externalId": os.path.basename(profile),
            "content": profile
        }
        label = profile.split('/')[-2:-1][0].upper()
        label_data = {
            "externalId": os.path.basename(profile),
            "response": {
                "JOB_0": {"categories": [{ "name": label }]}
            },
            "modelName": "v0"
        }
        data_to_upload.append({"asset": asset, "label": label_data})

    content_array = [x["asset"]["content"] for x in data_to_upload]
    external_id_array = [x["asset"]["externalId"] for x in data_to_upload]
    response_array = [x["label"]["response"] for x in data_to_upload]
    model_name = [x["label"]["modelName"] for x in data_to_upload]

    batch_size = 100
    for skip in tqdm(range(0, len(data_to_upload), batch_size)):
        kili.append_many_to_dataset(project_id=project_id,
            content_array=content_array[skip:skip+batch_size],
            external_id_array=external_id_array[skip:skip+batch_size])
        kili.create_predictions(project_id=project_id,
            external_id_array=external_id_array[skip:skip+batch_size], 
            model_name_array=model_name[skip:skip+batch_size],
            json_response_array=response_array[skip:skip+100])
    print('Done !')


def download():
    kili = get_kili_client()
    project_id = os.getenv('BUMBLE_PROJECT_ID')
    assets = kili.assets(project_id=project_id, fields=['externalId', 'labels.jsonResponse'], status_in=['LABELED', 'REVIEWED'])
    profiles_in_prediction = get_profiles_in_prediction()
    profiles_id_to_path = {os.path.basename(profile): profile for profile in profiles_in_prediction}
    print('Moving labeled assets to the right training data...')
    for asset in tqdm(assets):
        profile_id = asset['externalId']
        if profile_id in profiles_id_to_path.keys():
            label = asset['labels'][-1]['jsonResponse'][JOB_ID]['categories'][0]['name'].lower()
            os.rename(profiles_id_to_path[profile_id], get_train_path(profile_id, label))
    print('Done.')