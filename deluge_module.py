from deluge_client import DelugeRPCClient


class DelugeClient:
    def __init__(self, host: str, port: str, username: str, password: str):
        self.client = DelugeRPCClient(
            host=host, port=port, username=username, password=password
        )

    def connect(self):
        print("in connect")
        try:
            self.client.connect()
            return "connected", None
        except Exception as e:
            try:
                self.client.disconnect()
                self.client.connect()
                return "connected", None
            except Exception as e:
                return None, e

    def disconnect(self):
        try:
            self.client.disconnect()
            return "disconnected"
        except Exception as e:
            return "failed: " + str(e)

    def get_torrents(self):
        if not self.client.connected:
            _, err = self.connect()
            if err:
                return None, err
        try:
            torrents = self.client.core.get_torrents_status(
                {}, ["name", "progress", "eta"]
            )

        except Exception as e:
            return None, e

        torrent_objs = []

        for t in torrents:
            torrent_objs.append(Torrent(t, torrents[t]))
        return "\n".join(map(str, torrent_objs)), None

    def add_torrent(self, link, location):
        if not self.client.connected:
            _, err = self.connect()
            if err:
                return None, err

        try:
            id = self.client.core.add_torrent_magnet(
                link,
                {
                    "stop_at_ratio": True,
                    "stop_ratio": 2.0,
                    "download_location": location,
                },
            )
            return f"Successfully added as {id}", None
        except Exception as e:
            return None, e

    def pause_all(self):
        if not self.connected:
            _, err = self.connect()
            if err:
                return None, err

        try:
            self.client.core.pause_all_torrents()
            return "Successfully paused all torrents", None
        except Exception as e:
            return None, e


class Torrent:
    def __init__(self, id: bytes, attributes: dict):
        self.id = id
        self.name = attributes[b"name"].decode()
        self.progress = attributes[b"progress"]
        self.eta = attributes[b"eta"]

    def __str__(self):
        return f"{self.name[:20].center(20)} | {round(self.progress,2)} | {seconds_to_nice_string(self.eta)}"


def seconds_to_nice_string(s: int) -> str:
    s = int(s)
    h = s // 3600
    s %= 3600
    m = s // 60
    s %= 60
    s = s
    timestring = ""
    if h > 0:
        timestring += f"{h}h "
    if m > 0:
        timestring += f"{m}min "
    if s > 0:
        timestring += f"{s}s"
    return timestring
