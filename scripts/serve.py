import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
PREFIX = "/XR-Software-Engineering-Survey"


class ProjectHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        route = urlsplit(path).path
        if route == PREFIX or route.startswith(PREFIX + "/"):
            path = path[len(PREFIX):] or "/"
        return super().translate_path(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=4174)
    args = parser.parse_args()
    handler = partial(ProjectHandler, directory=str(ROOT / "dist"))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"http://127.0.0.1:{args.port}{PREFIX}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
