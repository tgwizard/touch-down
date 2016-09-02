#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import asyncio
import logging

import websockets

from touchdown.game import ws_handler
from touchdown.ws_overrides import GameHttpWSSProtocol

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
ws_logger = logging.getLogger('websockets.server')
ws_logger.setLevel(logging.INFO)

logger = logging.getLogger(__name__)


port = int(os.environ.get('PORT', 5678))
start_server = websockets.serve(ws_handler, '0.0.0.0', port, klass=GameHttpWSSProtocol)

logger.info('Listening on port %d', port)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
