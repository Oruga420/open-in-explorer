"""Native messaging host for the "Open in Explorer" Chrome extension.

Chrome speaks to this over stdin/stdout using the native messaging framing:
a 4-byte little-endian length followed by that many bytes of UTF-8 JSON.

Request:  {"action": "open", "path": "C:\\\\Users\\\\me\\\\file.txt"}
Response: {"ok": true, "path": "...", "mode": "select"|"folder"}
          {"ok": false, "error": "..."}

A file path opens its folder with the file selected; a folder path just opens
the folder. Nothing else is ever executed.
"""

import json
import os
import struct
import subprocess
import sys
import traceback
from datetime import datetime

LOG_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "open-in-explorer"
)
LOG_FILE = os.path.join(LOG_DIR, "host.log")


def log(message):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write("%s  %s\n" % (datetime.now().isoformat(timespec="seconds"), message))
    except Exception:
        pass  # logging must never break the protocol


def read_message():
    header = sys.stdin.buffer.read(4)
    if len(header) < 4:
        return None
    (length,) = struct.unpack("<I", header)
    if length == 0 or length > 1024 * 1024:
        return None
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))


def send_message(payload):
    data = json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("<I", len(data)))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def normalize(raw):
    path = (raw or "").strip().strip('"').strip("'")
    path = os.path.expandvars(os.path.expanduser(path))
    if path.startswith("\\\\"):
        path = "\\\\" + path[2:].replace("/", "\\")
    else:
        path = path.replace("/", "\\")
    # Keep the trailing separator only for a bare drive root ("C:\").
    if len(path) > 3:
        path = path.rstrip("\\")
    return path


def open_path(raw):
    path = normalize(raw)
    if not path:
        return {"ok": False, "error": "Empty path"}

    if os.path.isdir(path):
        args, mode = ["explorer.exe", path], "folder"
    elif os.path.isfile(path):
        args, mode = ["explorer.exe", "/select,%s" % path], "select"
    else:
        parent = os.path.dirname(path)
        if parent and os.path.isdir(parent):
            args, mode = ["explorer.exe", parent], "parent"
        else:
            return {"ok": False, "error": "Path not found: %s" % path}

    # explorer.exe habitually exits with code 1 even on success, so the launch
    # itself is the success signal.
    subprocess.Popen(args, close_fds=True)
    log("opened (%s) %s" % (mode, path))
    return {"ok": True, "path": path, "mode": mode}


def handle(request):
    if not isinstance(request, dict):
        return {"ok": False, "error": "Malformed request"}
    action = request.get("action", "open")
    if action == "ping":
        return {"ok": True, "pong": True}
    if action != "open":
        return {"ok": False, "error": "Unsupported action: %s" % action}
    return open_path(request.get("path"))


def main():
    while True:
        try:
            request = read_message()
        except Exception as exc:
            log("read error: %s" % exc)
            return
        if request is None:
            return
        try:
            response = handle(request)
        except Exception as exc:
            log("handler error: %s\n%s" % (exc, traceback.format_exc()))
            response = {"ok": False, "error": str(exc)}
        try:
            send_message(response)
        except Exception as exc:
            log("write error: %s" % exc)
            return


if __name__ == "__main__":
    main()
