import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

DEFAULT_PREFIX = "!"

LANGUAGES = {
"en":"English",
"vi":"Vietnamese",
"ja":"Japanese",
"zh-CN":"Chinese",
"ko":"Korean",
"es":"Spanish",
"fr":"French",
"de":"German",
"ru":"Russian",
"pt":"Portuguese",
"it":"Italian",
"ar":"Arabic",
"hi":"Hindi",
"th":"Thai",
"id":"Indonesian",
"tr":"Turkish",
"pl":"Polish",
"nl":"Dutch",
"sv":"Swedish",
"fi":"Finnish",
"da":"Danish",
"no":"Norwegian"
}

FLAG_LANGUAGES = {
"🇺🇸":"en",
"🇻🇳":"vi",
"🇯🇵":"ja",
"🇨🇳":"zh-CN",
"🇰🇷":"ko",
"🇪🇸":"es",
"🇫🇷":"fr",
"🇩🇪":"de",
"🇷🇺":"ru",
"🇮🇹":"it",
"🇮🇳":"hi"
}