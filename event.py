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

CONFIG = json.load(open('config.json'))


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


class Slack:

    @classmethod
    def delete(cls, channel, ts):
        print('delete', channel, ts)
        token = CONFIG['slack']['token']
        a = requests.post('https://slack.com/api/chat.delete', data={
            'token': token, 'channel': channel, 'ts': ts, 'as_user': 'true'})
        print(a)


    @classmethod
    def fetch_image(cls, url, out):
        print('fetch', url, out)
        token = CONFIG['slack']['token']
        commands = ['wget', '--header', f"Authorization: Bearer {token}", url, '-O', out]
        subprocess.call(commands)


class Report:

    @classmethod
    def ik(cls, text):
        url = CONFIG['memo']['url']
        headers = {'X-KEY': CONFIG['memo']['key']}
        click.secho('POST ', fg='red', nl=False)
        click.secho(text)
        requests.post(url, data=text.encode('UTF-8'), headers=headers)
        click.secho('')

    @classmethod
    def mast(cls, text, unlisted=False, images=[]):

        commands = ['mast', 'toot']
        if unlisted:
            commands.append('--unlisted')
        for img in images:
            commands.append('-f')
            commands.append(img)
        commands.append(text)

        click.secho(' '.join(commands), fg='red')
        subprocess.call(commands)
        click.secho('')

    @classmethod
    def tw(cls, text, images=[]):

        username = CONFIG['twitter']['username']
        commands = ["tw", "--by", username, text]
        for img in images:
            commands.append('-f')
            commands.append(img)

        click.secho(' '.join(commands), fg='green')
        subprocess.call(commands)
        click.secho('')

    def __init__(self, text, channel, ts, images=[]):
        if len(text) > 0 and (text[0] == '!' or text[0] == '！'):
            text = text[1:]
            Report.ik(text)
        if len(text) == 0:
            text = '.'
        Report.mast(text, images=images)
        Report.tw(text, images=images)
        Slack.delete(channel, ts)


class MainHandler(tornado.web.RequestHandler):

    def post(self):

        data = json.loads(self.request.body.decode('UTF-8'))

        if data['type'] == 'url_verification':
            self.write(data['challenge'])
            return

        if data['type'] == 'event_callback':

            event = data['event']
            print(f"Event: {event}")

            if event['type'] == 'message':

                if 'bot_id' in event or 'text' not in event:
                    print("message from bot")
                    self.finish("You are bot")
                    return

                text = normalize(event['text'])
                text = html.unescape(text)
                channel = event['channel']
                ts = event['event_ts']
                image_urls = [file['url_private'] for file in event['files']] if 'files' in event else []

                key = f"{text} {image_urls}"
                if History.contains(key):
                    print(f"Duplicate: {key}")
                    self.finish("Duplicate Data")
                else:
                    print(f"Report: {text} {image_urls}")
                    History.add(key)
                    images = []
                    for i, url in enumerate(image_urls):
                        images.append(f"/tmp/slack_image_{i}")
                        Slack.fetch_image(url, images[-1])
                    Report(text, channel, ts, images=images)
                    self.finish('OK')

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
    server.start(1)
    print('ready on 1234')
    tornado.ioloop.IOLoop.current().start()
