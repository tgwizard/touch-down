# -*- coding: utf-8 -*-

import os
import logging

import websockets


logger = logging.getLogger(__name__)


class HttpWSSProtocol(websockets.WebSocketServerProtocol):
    ws_path = '/ws'

    async def handler(self):
        print(self.reader)

        try:
            request_line, headers = await websockets.http.read_message(self.reader)
            method, path, version = request_line[:-2].decode().split(None, 2)
        except:
            self.writer.close()
            self.ws_server.unregister(self)
            raise

        if path == self.ws_path:
            # HACK: Put the read data back, to continue with normal WS handling. Would be nicer if
            # the WebSocketServerProtocol would allow for subclasses to read the headers and then
            # process as regular HTTP or WS, according to headers etc.
            self.reader.feed_data(bytes(request_line))
            self.reader.feed_data(headers.as_bytes().replace(b'\n', b'\r\n'))
            return await super(HttpWSSProtocol, self).handler()
        else:
            try:
                return self.http_handler(method, path, version)
            finally:
                self.writer.close()
                self.ws_server.unregister(self)

    def http_handler(self, method, path, version):
        logger.info('%s %s %s', method, path, version)
        response = '\r\n'.join([
            'HTTP/1.1 404 Not Found',
            'Content-Type: text/plain',
            '',
            '404 Not Found\n%s %s.' % (method, path),
        ])
        self.writer.write(response.encode())


def read_static_file(name):
    with open(os.path.join(os.path.dirname(__file__), '../static/', name), encoding='utf-8') as f:
        return ''.join(f.readlines())


class GameHttpWSSProtocol(HttpWSSProtocol):
    def http_handler(self, method, path, version):
        if path == '/':
            index_data = read_static_file('index.html')
            response = '\r\n'.join([
                'HTTP/1.1 200 OK',
                'Content-Type: text/html',
                '',
                index_data
            ])
            self.writer.write(response.encode())
        else:
            return super(GameHttpWSSProtocol, self).http_handler(method, path, version)


