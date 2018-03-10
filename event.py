import html
import subprocess
import click
import requests
import json
import tornado.ioloop
import tornado.web
import tornado.options


CONFIG = json.load(open('config.json'))['memo']


def tw(msg):
    username = CONFIG['twitter']['username']
    subprocess.call(["tw-cd", username])
    msg = msg if msg[0] == ':' else f".{msg}"
    print(["tw", msg])
    subprocess.call(["tw", msg])
    click.secho('TW ', fg='red', nl=False)
    print(username, msg)


def ik(data):
    url = CONFIG['url']
    headers = {'X-KEY': CONFIG['key']}
    requests.post(url, data=data.encode('UTF-8'), headers=headers)
    click.secho('POST ', fg='red', nl=False)
    print(url, data, headers)


def memo(data):
    """Entry point
    """
    click.secho('MEMO ', fg='green', nl=False)
    msg = html.unescape(data)
    print(msg)
    ik(msg)
    tw(msg)


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

                memo(event['text'])
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
