import functools
import html
import json
import re
import subprocess
from typing import Tuple

import click
import requests
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

CONFIG = json.load(open("config.json"))


def normalize(text):
    text = re.sub(r"<(http[^|]*)\|[^>]+>", r"\1", text)
    text = re.sub(r"<(http[^>]*)>", r"\1", text)
    return text


class PostServices:
    def __init__(self, ik=False, tw=False, mast=False, eth=False):
        self.ik = ik
        self.tw = tw
        self.mast = mast
        self.eth = eth

    def __repr__(self):
        return f"PostServices(ik={self.ik}, tw={self.tw}, mast={self.mast}, eth={self.eth})"


def parse(text: str, services: PostServices) -> Tuple[str, PostServices]:
    while True:
        if text.startswith(" "):
            text = text[1:]
            continue
        if text.startswith("+t"):
            text = text[2:]
            services.tw = True
            continue
        if text.startswith("-t"):
            text = text[2:]
            services.tw = False
            continue
        if text.startswith("=t"):
            text = text[2:]
            services = PostServices(tw=True)
            continue
        if text.startswith("+i"):
            text = text[2:]
            services.ik = True
            continue
        if text.startswith("-i"):
            text = text[2:]
            services.ik = True
            continue
        if text.startswith("=i"):
            text = text[2:]
            services = PostServices(ik=True)
            continue
        if text.startswith("+m"):
            text = text[2:]
            services.mast = True
            continue
        if text.startswith("-m"):
            text = text[2:]
            services.mast = False
            continue
        if text.startswith("=m"):
            text = text[2:]
            services = PostServices(mast=True)
            continue
        if text.startswith("+e"):
            text = text[2:]
            services.eth = True
            continue
        if text.startswith("-e"):
            text = text[2:]
            services.eth = False
            continue
        if text.startswith("=e"):
            text = text[2:]
            services = PostServices(eth=True)
            continue
        break
    if text == "":
        text = "."
    return text, services


def test_parse():
    assert parse("    hoge", PostServices())[0] == "hoge"

    text, services = parse(" -m hoge", PostServices())
    assert text == "hoge"
    assert services.mast == False

    text, services = parse("+t", PostServices())
    assert text == "."
    assert services.tw == True

    text, services = parse("-m +i -t hoge", PostServices(mast=False, tw=True, ik=False))
    assert text == "hoge"
    assert services.mast == False
    assert services.ik == True
    assert services.tw == False
    assert services.eth == False

    text, services = parse(
        "+e -m -i =t hoge", PostServices(mast=True, tw=False, ik=True)
    )
    assert text == "hoge"
    assert services.mast == False
    assert services.ik == False
    assert services.tw == True
    assert services.eth == False


test_parse()


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
        print("delete", channel, ts)
        token = CONFIG["slack"]["token"]
        a = requests.post(
            "https://slack.com/api/chat.delete",
            data={"token": token, "channel": channel, "ts": ts, "as_user": "true"},
        )
        print(a)

    @classmethod
    def fetch_image(cls, url, out):
        print("fetch", url, out)
        token = CONFIG["slack"]["token"]
        commands = [
            "wget",
            "--header",
            f"Authorization: Bearer {token}",
            url,
            "-O",
            out,
        ]
        subprocess.call(commands)

    @classmethod
    @functools.lru_cache(None)
    def channel_name(cls, channel_id: str) -> str:
        token = CONFIG["slack"]["token"]
        res = requests.get(
            f"https://slack.com/api/channels.info?token={token}&channel={channel_id}"
        ).json()
        return res["channel"]["name"]


class Report:
    @classmethod
    def ik(cls, text):
        url = CONFIG["memo"]["url"]
        headers = {"X-KEY": CONFIG["memo"]["key"]}
        click.secho("POST ", fg="green", nl=False)
        click.secho(text)
        requests.post(url, data=text.encode("UTF-8"), headers=headers)
        click.secho("")

    @classmethod
    def mast(cls, text, unlisted=False, images=[]):

        commands = ["mast", "toot"]
        if unlisted:
            commands.append("--unlisted")
        for img in images:
            commands.append("-f")
            commands.append(img)
        commands.append(text)

        click.secho(" ".join(commands), fg="green")
        subprocess.call(commands)
        click.secho("")

    @classmethod
    def tw(cls, text, images=[]):

        username = CONFIG["twitter"]["username"]
        commands = ["tw", "--by", username, text]
        for img in images:
            commands.append("-f")
            commands.append(img)

        click.secho(" ".join(commands), fg="green")
        subprocess.call(commands)
        click.secho("")

    @classmethod
    def eth(cls, text, images=[]):
        commands = ["ethsend", text]
        click.secho(" ".join(commands), fg="green")
        subprocess.call(commands)
        click.secho("")

    def __init__(self, text, channel, ts, images=None):

        images = images or []
        channel_name = Slack.channel_name(channel)

        if channel_name == "memo":
            text, services = parse(text, PostServices(tw=True, ik=True))
            text += " #memo"
            click.secho(f"Request({channel_name}, {text}, {services})", fg="yellow")

        elif channel_name == "timeline":
            text, services = parse(text, PostServices(tw=True, mast=False, ik=False))
            click.secho(f"Request({channel_name}, {text}, {services})", fg="yellow")
            Slack.delete(channel, ts)

        else:
            text, services = parse("", PostServices(tw=False, ik=False))

        if services.ik:
            Report.ik(text)
        if services.tw:
            Report.tw(text, images=images)
        if services.mast:
            Report.mast(text, images=images)
        if services.eth:
            Report.eth(text, images=images)


class MainHandler(tornado.web.RequestHandler):
    def post(self):

        data = json.loads(self.request.body.decode("UTF-8"))
        print("POST", data)

        if data["type"] == "url_verification":
            print("challenge", data["challenge"])
            self.write(data["challenge"])
            return

        if data["type"] == "event_callback":

            self.finish("Accepted")

            event = data["event"]
            click.secho(f"Event: {event}", fg="yellow")

            if event["type"] == "message":

                if "bot_id" in event or "text" not in event:
                    click.secho("message from bot", fg="red")
                    return

                text = normalize(event["text"])
                text = html.unescape(text)
                channel = event["channel"]
                ts = event["event_ts"]
                image_urls = (
                    [file["url_private"] for file in event["files"]]
                    if "files" in event
                    else []
                )

                key = f"{text} {image_urls}"
                if History.contains(key):
                    click.secho(f"Duplicate: {key}", fg="red")
                else:
                    click.secho(f"Report: {text} {image_urls}", fg="yellow")
                    History.add(key)
                    images = []
                    for i, url in enumerate(image_urls):
                        images.append(f"/tmp/slack_image_{i}")
                        Slack.fetch_image(url, images[-1])
                    Report(text, channel, ts, images=images)

    def get(self):
        self.write("Hello, world")


def make_app():
    return tornado.web.Application(
        [
            (r"/", MainHandler),
        ]
    )


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = make_app()

    server = tornado.httpserver.HTTPServer(app)
    server.bind(1234)
    server.start(1)
    print("ready on 1234")
    tornado.ioloop.IOLoop.current().start()
