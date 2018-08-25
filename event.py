import html
import json
import re
import subprocess

import click
import requests
import tornado.ioloop
import tornado.options
import tornado.web

CONFIG = json.load(open('config.json'))['memo']


def normalize(text):
    text = re.sub(r'<(http[^|]*)\|[^>]+>', r'\1', text)
    text = re.sub(r'<(http[^>]*)>', r'\1', text)
    return text


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
        if msg[0] == '!' or msg[0] == '！':
            msg = msg[1:]
            Report.ik(msg)
        else:
            Report.tw(msg)
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

                print(f"Report: {data}")
                Report(normalize(event['text']))
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
    app.listen(1234)
    print('ready on 1234')
    tornado.ioloop.IOLoop.current().start()
