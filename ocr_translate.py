def translate_image(url, target):

    try:
        import pytesseract
        from PIL import Image
        import requests
        from io import BytesIO
        from translator import translate_text

        # download image
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return None

        # limit file size (Render protection)
        if len(response.content) > 3_000_000:
            return "⚠ Image too large for OCR."

        img = Image.open(BytesIO(response.content))

        # convert to grayscale for better OCR
        img = img.convert("L")

        text = pytesseract.image_to_string(img)

        if not text.strip():
            return None

        translated = translate_text(text, target)

        return translated

    except Exception as e:

        print("OCR error:", e)

        return None