from enum import Enum

import click

from scraper import get_driver, signin, crawl
from inference import infer
from train import train_model


class Mode(str, Enum):
    GATHER_DATA = 'GATHER_DATA'
    TRAIN = 'TRAIN'
    INFER = 'INFER'

class StartUp(str, Enum):
    FRESH = 'FRESH'
    RECONNECT = 'RECONNECT'


@click.command()
@click.option('--mode', type=click.Choice([Mode.GATHER_DATA, Mode.TRAIN, Mode.INFER]))
@click.option('--start', type=click.Choice([StartUp.FRESH, StartUp.RECONNECT]), default=StartUp.RECONNECT)
def main(mode, start):
    if mode == Mode.TRAIN:
        train_model()
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
    """
    main()
