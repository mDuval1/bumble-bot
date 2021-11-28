# Bumble Automation Bot - BumbleBot

Tired of swiping countless profiles on Bumble ? Let a bot do it for you !
This simple Python/selenium bot learns your tastes from the first picture, then fine tunes an image classifier. Once trained, you can let the bot swipe.

### Installation

- Get a Bumble account
- Get [chromedriver](https://chromedriver.chromium.org/)
- `pip install -r requirements.txt`

### Usage

**1 - Gather data**.

This launches a new window. You should first export your mobile phone variable. The window will prompt you for a code you receive on your phone.

```
export MOBILE_PHONE=xxx
python main.py --mode GATHER_DATA --start FRESH
```

Note : quitting the console won't close the window ; you can reconnect with `--start RECONNECT`.

**2 - Train the model**

```
python main.py --mode TRAIN
```

**3 - Crack a cold one**

```
python main.py --mode INFER --start FRESH
```

This will look at 200 profiles.

### Todo

- Connect with other methods than mobile phone
- Upload infered data to [Kili Technology](https://kili-technology.com/) to have human in the loop and correct the model's mistakes.
- Save other information
  - Save other pictures
  - Do NLP / OCR on profile content