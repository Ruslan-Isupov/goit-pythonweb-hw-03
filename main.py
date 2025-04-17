import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from jinja2 import FileSystemLoader, Environment
from datetime import datetime
from abc import ABC, abstractmethod
import urllib.parse
import mimetypes
import pathlib


def format_date(data: str):
    time = datetime.fromisoformat(data)
    return time.strftime("%b %d, %Y %H:%M:%S")


class Vault(ABC):
    @abstractmethod
    def read_messages(self):
        pass

    @abstractmethod
    def write_message(self):
        pass


class Storage(Vault):
    __file: pathlib.Path

    def __init__(self, file: str):
        self.__file = pathlib.Path(file)

    def init(self):
        if not self.__file.exists():
            storage = {}
            try:
                with open(self.__file, "w", encoding="utf-8") as fh:
                    json.dump(storage, fh, ensure_ascii=False, indent=2)
            except Exception as error:
                print(f"Error of creating a file: {error}")

    def read_messages(self):
        messages = {}
        try:
            with open(self.__file, "r", encoding="utf-8") as file:
                messages = json.load(file)
        except Exception as error:
            print(f"Error of reading a file: {error}")
        finally:
            return messages

    def write_message(self, new_message):
        storage = {}
        try:
            if self.__file.exists():
                with open(self.__file, "r", encoding="utf-8") as file:
                    storage = json.load(file)
            timestamp = f"{datetime.now()}"
            storage[timestamp] = new_message
            with open(self.__file, "w", encoding="utf-8") as file:
                json.dump(storage, file, ensure_ascii=False, indent=2)
                print(f"Message was added ")
        except Exception as error:
            print(f"Error during writing a file: {error}")


class HttpHandler(BaseHTTPRequestHandler):
    __storage = Storage("./storage/data.json")

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)

        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == "/message":
            self.send_html_file("message.html")
        elif pr_url.path == "/read":
            env = Environment(loader=FileSystemLoader("."))
            template = env.get_template("read.html")
            messages = self.__storage.read_messages()
            rendered = template.render(messages=messages, format_date=format_date)

            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(rendered.encode("utf-8"))

        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file("error.html", 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        data_parsed = urllib.parse.unquote_plus(data.decode())
        message = {
            key: value
            for key, value in [el.split("=") for el in data_parsed.split("&")]
        }
        self.__storage.write_message(message)
        self.send_response(302)
        self.send_header("Location", "/")
        self.end_headers()

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        with open(filename, "rb") as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", "text/plain")
        self.end_headers()
        with open(f".{self.path}", "rb") as file:
            self.wfile.write(file.read())


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ("", 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == "__main__":
    run_http_server()
