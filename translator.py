from deep_translator import GoogleTranslator

translation_cache = {}

def translate_text(text,target):

    key = (text,target)

    if key in translation_cache:
        return translation_cache[key]

    try:

        translated = GoogleTranslator(
            source="auto",
            target=target
        ).translate(text)

        translation_cache[key] = translated

        return translated

    except:
        return None