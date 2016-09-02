# Simple game of touch down

A simple (read stupid) game of "touch down", over websockets.
Two devices connect to the same server and join a game.
The last one to touch the screen gets the advantage, and the score starts ticking for her.
The opponent must release and touch the screen again to gain the advantage.

Mostly built to try out websockets in Python (3).

I decided to use the [`websockets`](https://websockets.readthedocs.io/en/stable/) library, which looked nice.
It doesn't support non-websocket connections though, and I wanted to serve static files on the same port and in the same process, so I had
to hack around that (see `ws_overrides.py`).

## Dev setup

Make sure you have Python 3.5+, e.g. install it with homebrew.

```bash
pyvenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```
python run.py
```

Now go to `http://localhost:5678`
