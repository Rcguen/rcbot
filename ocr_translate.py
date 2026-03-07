import pytesseract
from PIL import Image
import requests
from io import BytesIO
from translator import translate_text

def translate_image(url,target):

    response = requests.get(url)

    img = Image.open(BytesIO(response.content))

    text = pytesseract.image_to_string(img)

    if not text:
        return None

    return translate_text(text,target)