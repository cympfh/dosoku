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


# def tw(msg):
#     username = CONFIG['twitter']['username']
#     print(["tw", msg])
#     subprocess.call(["tw", msg, '--by', username])
#     click.secho('TW ', fg='red', nl=False)
#     print(username, msg)


def ik(msg):
    url = CONFIG['url']
    headers = {'X-KEY': CONFIG['key']}
    requests.post(url, data=msg.encode('UTF-8'), headers=headers)
    click.secho('POST ', fg='red', nl=False)
    print(url, msg, headers)


def memo(data):
    """Entry point
    """
    click.secho('MEMO ', fg='green', nl=False)
    msg = html.unescape(data)
    print(msg)
    ik(msg)


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
                    return

                memo(normalize(event['text']))
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
