from storage import load_json, save_json

CHANNEL_FILE = "data/channels.json"

channels = load_json(CHANNEL_FILE)

def add_channel(channel_id):

    channels[str(channel_id)] = True

    save_json(CHANNEL_FILE, channels)


def remove_channel(channel_id):

    channels.pop(str(channel_id), None)

    save_json(CHANNEL_FILE, channels)


def is_enabled(channel_id):

    return str(channel_id) in channels


def get_channels():

    return channels