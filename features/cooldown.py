import time

cooldowns = {}

COOLDOWN_SECONDS = 2

def check_cooldown(user_id):

    now = time.time()

    last = cooldowns.get(user_id, 0)

    if now - last < COOLDOWN_SECONDS:
        return False

    cooldowns[user_id] = now

    return True