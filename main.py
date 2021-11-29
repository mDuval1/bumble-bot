from enum import Enum

import click

from scraper import get_driver, signin, crawl
from inference import infer
from train import train_model
from feedback import upload, download


class Mode(str, Enum):
    GATHER_DATA = 'GATHER_DATA'
    TRAIN = 'TRAIN'
    INFER = 'INFER'
    UPLOAD_DATA = 'UPLOAD'
    DOWNLOAD_DATA = 'DOWNLOAD'

class StartUp(str, Enum):
    FRESH = 'FRESH'
    RECONNECT = 'RECONNECT'


@click.command()
@click.option('--mode', type=click.Choice([Mode.GATHER_DATA, Mode.TRAIN, Mode.INFER, Mode.UPLOAD_DATA, Mode.DOWNLOAD_DATA]))
@click.option('--start', type=click.Choice([StartUp.FRESH, StartUp.RECONNECT]), default=StartUp.RECONNECT)
def main(mode, start):
    if mode == Mode.TRAIN:
        train_model()
        return
    if mode == Mode.UPLOAD_DATA:
        upload()
        return
    if mode == Mode.DOWNLOAD_DATA:
        download()
        return
    should_attach = start == StartUp.RECONNECT
    driver = get_driver(should_attach)
    if not should_attach:
        signin(driver)
    if mode == Mode.GATHER_DATA:
        crawl(driver)
    if mode == Mode.INFER:
        infer(driver)


if __name__ == '__main__':
    """
    # train
    python main.py --mode GATHER_DATA --start FRESH
    python main.py --mode GATHER_DATA --start RECONNECT
    python main.py --mode TRAIN
    python main.py --mode INFER --start FRESH
    python main.py --mode INFER --start RECONNECT
    python main.py --mode UPLOAD
    python main.py --mode DOWNLOAD
    """
    main()
