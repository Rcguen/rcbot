cache = {}

def get_cache(text, lang):

    key = (text, lang)

    return cache.get(key)

def set_cache(text, lang, value):

    key = (text, lang)

    cache[key] = value