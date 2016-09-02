# -*- coding: utf-8 -*-

import logging
import asyncio
import json
from datetime import datetime


logger = logging.getLogger(__name__)


connections = {}
games = {}

dirs = {
    'blue': 1,
    'pink': -1,
}


def join_game(game_name, websocket):
    if game_name not in games:
        games[game_name] = {
            'score': 0.5,
            'players': {},
            'task': None,
        }

    g = games[game_name]
    # Reset score when new player joins.
    g['score'] = 0.5
    g['changed'] = True

    if len(g['players']) == 2:
        # TODO: Error handling
        logger.error('TOO MANY PLAYERS')
        raise Exception(u'Too many players for game: %s', game_name)

    player_name = 'blue' if len(g['players']) == 0 else 'pink'
    g['players'][player_name] = {
        'player_name': player_name,
        'ws': websocket,
        'last_touch_at': None,
    }

    connections[websocket] = {
        'game': g,
        'player_name': player_name
    }

    if len(g['players']) == 2:
        logger.info(u'Starting game: %s', game_name)
        assert g['task'] is None
        g['task'] = asyncio.ensure_future(game_task(g))
    else:
        logger.info('Game has too few players: %s', g)

    return g, player_name


def leave_game(websocket):
    c = connections.pop(websocket, None)
    if c:
        g = c['game']
        g['players'].pop(c['player_name'], None)
        if g['task']:
            g['task'].cancel()
            g['task'] = None


def handle_event(g, player_name, data, websocket):
    step_game(g)

    if data['event'] == 'touch_start':
        g['players'][player_name]['last_touch_at'] = datetime.utcnow()

    elif data['event'] == 'touch_end':
        g['players'][player_name]['last_touch_at'] = None


def step_game(g):
    now = datetime.utcnow()
    # logger.info('Stepping game: now=%s, g=%s', now, g)

    leader = find_leader_player(g)
    if leader:
        logger.warning(u'LEADER: %s', leader['player_name'])
        new_score = g['score'] + dirs[leader['player_name']] * (now - leader['last_touch_at']).total_seconds() * 0.1
        new_score = max(min(new_score, 1.0), 0.0)
        if new_score != g['score']:
            g['score'] = new_score
            g['changed'] = True

        leader['last_touch_at'] = now


def find_leader_player(g):
    leader = None
    for player_name, p in g['players'].items():
        if p['last_touch_at'] is None:
            continue
        if leader is None or leader['last_touch_at'] < p['last_touch_at']:
            leader = p
    return leader


async def game_task(g):
    while True:
        await asyncio.sleep(0.1)
        step_game(g)

        if not g['changed']:
            continue

        # logger.info(u'Game task: game data=%s', g)

        leader = None
        base_data = {
            'event': 'g',
            'score': g['score'],
            'leader': leader['player_name'] if leader else None,
        }
        try:
            await asyncio.wait([
                p['ws'].send(json.dumps(dict(player_name=player_name, **base_data)))
                for player_name, p in g['players'].items()
            ])
        except:
            logger.error('IGNORING WEB SOCKET WRITE ERROR')

        g['changed'] = False


async def ws_handler(websocket, path):
    logger.info('Client connecting: %s, %s', websocket, path)
    game_name = 'g1'

    try:
        g, player_name = join_game(game_name, websocket)

        await websocket.send(
            json.dumps({'event': 'init', 'player_name': player_name, 'score': g['score']})
        )

        while True:
            data = await websocket.recv()

            logger.info('data: %s', data)
            data = json.loads(data)

            handle_event(g, player_name, data, websocket)

    finally:
        logger.info(u'Disconnecting client and leaving game')
        leave_game(websocket)

