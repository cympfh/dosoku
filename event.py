import click
import requests
import json
import tornado.ioloop
import tornado.web


CONFIG = json.load(open('config.json'))['memo']


def memo(data):
    url = CONFIG['url']
    headers = {'X-KEY': CONFIG['key']}
    requests.post(url, data=data, headers=headers)
    click.secho('POST ', fg='red', nl=False)
    print(url, data, headers)


class MainHandler(tornado.web.RequestHandler):

    def post(self):

        data = json.loads(self.request.body.decode('UTF-8'))
        click.secho('CHUNKED DATA ', fg='yellow', nl=False)
        print(data)

        if data['type'] == 'url_verification':
            self.write(data['challenge'])
            return

        if data['type'] == 'event_callback':

            event = data['event']
            click.secho('EVENT ', fg='green', nl=False)
            print(event)

            if event['type'] == 'message':

                if 'bot_id' in event or 'text' not in event:
                    click.secho('BOT ', fg='red')
                    self.write('BOT')
                    return

                memo(event['text'].encode('UTF-8'))
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
    app = make_app()
    app.listen(1234)
    tornado.ioloop.IOLoop.current().start()
