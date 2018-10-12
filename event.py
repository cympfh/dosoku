import html
import json
import re
import subprocess

import click
import requests
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.httpserver

CONFIG = json.load(open('config.json'))['memo']


def normalize(text):
    text = re.sub(r'<(http[^|]*)\|[^>]+>', r'\1', text)
    text = re.sub(r'<(http[^>]*)>', r'\1', text)
    return text


class History:

    items = []
    items_set = set()
    hist_size = 100

    @classmethod
    def contains(cls, item):
        return item in cls.items_set

    @classmethod
    def add(cls, item):
        cls.items.append(item)
        cls.items_set.add(item)
        if len(cls.items) > cls.hist_size:
            remove_item = cls.items[0]
            cls.items_set.remove(remove_item)
            cls.items = cls.items[1:]


class Report:

    @classmethod
    def tw(cls, msg):
        username = CONFIG['twitter']['username']
        click.secho('TW ', fg='red', nl=False)
        click.secho(msg)
        subprocess.call(["tw", msg, '--by', username])
        click.secho('')

    @classmethod
    def ik(cls, msg):
        url = CONFIG['url']
        headers = {'X-KEY': CONFIG['key']}
        click.secho('POST ', fg='red', nl=False)
        click.secho(msg)
        requests.post(url, data=msg.encode('UTF-8'), headers=headers)
        click.secho('')

    @classmethod
    def mast(cls, msg):
        click.secho('mast ', fg='red', nl=False)
        click.secho(msg)
        subprocess.call(["mast", "toot", msg])
        click.secho('')

    def __init__(self, data):
        msg = html.unescape(data)
        if msg[0:2] == '!!' or msg[0:2] == '！！':
            msg = msg[2:]
            Report.ik(msg)
        elif msg[0] == '!' or msg[0] == '！':
            msg = msg[1:]
            Report.ik(msg)
            Report.mast(msg)
        else:
            Report.mast(msg)


class MainHandler(tornado.web.RequestHandler):

    def post(self):

        data = json.loads(self.request.body.decode('UTF-8'))

        if data['type'] == 'url_verification':
            self.write(data['challenge'])
            return

        if data['type'] == 'event_callback':

            event = data['event']

            if event['type'] == 'message':

                if 'bot_id' in event or 'text' not in event:
                    print("message from bot")
                    self.finish("You are bot")
                    return

                data = normalize(event['text'])
                if History.contains(data):
                    print(f"Duplicate: {data}")
                    self.finish("Duplicate Data")
                    return

                print(f"Report: {data}")
                History.add(data)
                Report(data)
                self.write('OK')

            else:
                self.write('?')

        else:
            self.write('?')

    def get(self):
        self.write("Hello, world")

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = make_app()

    server = tornado.httpserver.HTTPServer(app)
    server.bind(1234)
    server.start(2)
    print('ready on 1234')
    tornado.ioloop.IOLoop.current().start()
