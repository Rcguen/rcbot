import json
import os


def load_json(file):

    # create file if it does not exist
    if not os.path.exists(file):

        folder = os.path.dirname(file)

        if folder and not os.path.exists(folder):
            os.makedirs(folder)

        with open(file, "w") as f:
            json.dump({}, f)

        return {}

    try:

        with open(file, "r") as f:

            content = f.read().strip()

            # if file is empty
            if content == "":
                return {}

            return json.loads(content)

    except Exception as e:

        print(f"JSON load error in {file}: {e}")

        return {}


def save_json(file, data):

    folder = os.path.dirname(file)

    if folder and not os.path.exists(folder):
        os.makedirs(folder)

    try:

        with open(file, "w") as f:
            json.dump(data, f, indent=4)

    except Exception as e:

        print(f"JSON save error in {file}: {e}")