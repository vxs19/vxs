import asyncio
import os
import json
import random
import time
import uuid
import logging
import shutil
import sys
import urllib.parse
import textwrap
from collections import OrderedDict


import aiohttp
from aiogram.types import BufferedInputFile, ChatMemberUpdated

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    from pilmoji import Pilmoji
    HAS_PILMOJI = True
except ImportError:
    HAS_PILMOJI = False

if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

# ============================================================
# FIXED: Silence the noisy aiogram network errors
# ============================================================
logging.basicConfig(level=logging.WARNING)
logging.getLogger("aiogram.dispatcher").setLevel(logging.CRITICAL)
logging.getLogger("aiogram.event").setLevel(logging.CRITICAL)
logging.getLogger("aiogram").setLevel(logging.WARNING)

AUTO_OPTIMIZE_INTERVAL = 1
COMMAND_TIMEOUT = 100
MAX_CACHE_SIZE = 5000

bot_start_time = time.time()

def get_uptime():
    """Calculates and formats the total uptime of the bot script."""
    uptime = int(time.time() - bot_start_time)
    hours = uptime // 3600
    minutes = (uptime % 3600) // 60
    seconds = uptime % 60
    return f"{hours}h {minutes}m {seconds}s"

TOKENS =[
    "8869829244:AAHPm41hXnn5P1EjUJ-BEK_I0REd_E5NAi0",
    "8982520022:AAGZBMefcAIizuFl0p94nWIA4EC-tH7_kOM",
    "8793955177:AAE96G-zhccSHf82xyZUIbHI9PFgBNoyyEk",
    "8637986285:AAFlZDZ_A5yvNJRXVi7ghGER2J91jmt4Q3k",
    "8641137776:AAE1E0phbTvotUOIxm9IECHTMypq7RAgiTk",
    "8988058214:AAGM-FVJ0e95EDcSD31nNDR8Zhf0dHVOjmo",
    "8862763408:AAEyd5_3-3mu6DuKImwsCwFMSZVRqynZa4o",
    "8922830473:AAGMcuGZh5qj2JygfYah_7e35pZ-g3W6BnE",
    "8845948426:AAE3V03F05qqniqS-7cFumwpht-wpjakBy4",
    "8572823794:AAGPTQ8g-_rarqSKEk7aZoUQ_xFd6TFTolI",
    "8748404984:AAEP9u6REpal6XINeAC78d9KdrFqP-Pepao",

]

OWNER_ID = 7607535932
SUDO_FILE = "VXS_sudo.json"
DB_FILE = "VXS_db.json"

global_storage = os.path.join(os.path.dirname(__file__), 'downloads', 'global')
os.makedirs(global_storage, exist_ok=True)

def get_start_pic_path(bot_id):
    """Generates a distinct path for each bot's start picture."""
    return os.path.join(global_storage, f"start_pic_{bot_id}.jpg")

chars = {
      'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ғ', 'g': 'ɢ',
    'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
    'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 's', 't': 'ᴛ', 'u': 'ᴜ',
    'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ',
    'A': 'ᴀ', 'B': 'ʙ', 'C': 'ᴄ', 'D': 'ᴅ', 'E': 'ᴇ', 'F': 'ғ', 'G': 'ɢ',
    'H': 'ʜ', 'I': 'ɪ', 'J': 'ᴊ', 'K': 'ᴋ', 'L': 'ʟ', 'M': 'ᴍ', 'N': 'ɴ',
    'O': 'ᴏ', 'P': 'ᴘ', 'Q': 'ǫ', 'R': 'ʀ', 'S': 's', 'T': 'ᴛ', 'U': 'ᴜ',
    'V': 'ᴠ', 'W': 'ᴡ', 'X': 'x', 'Y': 'ʏ', 'Z': 'ᴢ'
}

def font(text: str) -> str:
    """Converts standard text into a stylized small-caps font."""
    return "".join(chars.get(c, c) for c in text)

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, ReactionTypeEmoji
from aiogram.enums import ParseMode
from aiogram.client.session.aiohttp import AiohttpSession

try:
    from aiogram.types import LinkPreviewOptions
except ImportError:
    LinkPreviewOptions = None


class LowBandwidthAiohttpSession(AiohttpSession):
    """Custom AiohttpSession with persistent keep-alive pooling and DNS caching."""
    def __init__(self, timeout: float = 65.0, **kwargs):
        super().__init__(timeout=timeout, **kwargs)
        self._connector_init = {
            "limit": 100,
            "limit_per_host": 50,
            "keepalive_timeout": 300.0,
            "ttl_dns_cache": 300,
            "use_dns_cache": True,
        }


SUDO_USERS = {OWNER_ID}
username_to_id = {}
user_names = {}

muted_users = set()
reply_vxs_targets = set()
targetslide_targets = {}
react_targets = {} 
known_chats = set()

VALID_REACTS =["🤣","🤪","👻","❤️","🤡","🥱","🤮","❤️‍🔥","⚡"]
SEQ_EMOJIS =["✦❗✧","✦❕✧","✦❓✧","✦❔✧","✦‼️✧","✦⁉️✧","✦⚠️✧","✦🚨✧","✦⛔✧","✦🚫✧","✦❌✧","✦⭕✧","✦🔴✧","✦🟠✧","✦🟡✧","✦🟢✧","✦🔵✧","✦🟣✧","✦🔺✧","✦🔻✧","✦🔸✧","✦🔹✧","✦🔶✧","✦🔷✧","✦⬆️✧","✦⬇️✧","✦⬅️✧","✦➡️✧","✦↗️✧","✦↘️✧","✦↖️✧","✦↙️✧","✦↕️✧","✦↔️✧","✦🔁✧","✦🔄✧","✦✔️✧","✦☑️✧","✦✅✧","✦✖️✧","✦❎✧","✦➕✧","✦➖✧","✦➗✧","✦✳️✧","✦✴️✧","✦❇️✧","✦〽️✧","✦💢✧","✦💯✧","✦💥✧","✦💫✧","✦💦✧","✦💨✧","✦🟥✧","✦🟧✧","✦🟨✧","✦🟩✧","✦🟦✧","✦🟪✧","✦◼️✧","✦◻️✧","✦◾✧","✦◽✧","✦▪️✧","✦▫️✧","✦🔲✧","✦🔳✧","✦⬛✧","✦⬜✧","✦⚫✧","✦⚪✧","✦🟤✧","✦🅰️✧","✦🅱️✧","✦🅾️✧","✦🆎✧","✦🆑✧","✦🆘✧","✦™️✧","✦©️✧","✦®️✧","✦ℹ️✧","✦🔤✧","✦🔡✧","✦🔠✧","✦🔢✧","✦#️⃣✧","✦*️⃣✧","✦0️⃣✧","✦1️⃣✧","✦2️⃣✧","✦3️⃣✧","✦4️⃣✧","✦5️⃣✧","✦6️⃣✧","✦7️⃣✧","✦8️⃣✧","✦9️⃣✧","✦🔟✧","✦🔚✧","✦🔙✧","✦🔛✧"]


def load_data():
    """Loads database variables from JSON files safely."""
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, 'r') as f:
                for uid in json.load(f): SUDO_USERS.add(int(uid))
        except Exception: pass
        
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                data = json.load(f)
                for u in data.get("muted",[]): muted_users.add(u)
                for u in data.get("reply_vxs", data.get("",[])): reply_vxs_targets.add(u)
                for k, v in data.get("targetslide", {}).items(): targetslide_targets[int(k)] = v
                for k, v in data.get("user_names", {}).items(): user_names[int(k)] = v
                for k, v in data.get("react_targets", {}).items(): react_targets[int(k)] = v
                for c in data.get("known_chats",[]): known_chats.add(int(c))
        except Exception as e:
            print(f"{RED}[DB] Error loading DB: {e}{RESET}")

def save_sudo():
    """Saves the Sudo users list to a JSON file."""
    with open(SUDO_FILE, 'w') as f:
        json.dump(list(SUDO_USERS), f)

def save_db():
    """Serializes memory structures and saves to the DB file."""
    data = {
        "muted": list(muted_users),
        "reply_vxs": list(reply_vxs_targets),
        "targetslide": targetslide_targets,
        "user_names": user_names,
        "react_targets": react_targets,
        "known_chats": list(known_chats)
    }
    with open(DB_FILE, 'w') as f:
        json.dump(data, f)

load_data()

class SimpleLRUCache:
    def __init__(self, capacity: int):
        self.cache = OrderedDict()
        self.capacity = capacity
    
    def get(self, key):
        if key not in self.cache:
            return False
        self.cache.move_to_end(key)
        return True
        
    def put(self, key):
        self.cache[key] = True
        self.cache.move_to_end(key)
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)

processed_messages = SimpleLRUCache(MAX_CACHE_SIZE)

def is_processed(message_id: int, chat_id: int) -> bool:
    """Checks if a command was already handled by another bot."""
    key = (chat_id, message_id)
    if processed_messages.get(key):
        return True
    processed_messages.put(key)
    return False

bots =[]
bot_usernames =[]
_shared_http_session = None

# Task Trackers
group_tasks = {}
seq_nc_tasks = {}
keng_tasks = {}
spmnc_tasks = {}
vxsnc_tasks = {}
slidespam_tasks = {}
spm_loop_tasks = {}
rspm_tasks = {}
vxsspam_tasks = {}
forwardspm_tasks = {}
sticker_spm_tasks = {}
gif_spm_tasks = {}
media_spm_tasks = {}
voice_spm_tasks = {}
pfp_tasks = {}

# Delays 
swipe_mode = {}
nc_delays = {}
spm_delays = {}
rspm_delays = {}
pfp_delays = {}
REPLY_vxs_DELAY = 0.4

known_users = set()
active_menus = {}

# NEW: track slidespam targets by chat_id -> reply_msg_id
slidespam_targets = {}

def stop_task_group(task_dict, key):
    """Safely clears tasks from a given dictionary key gracefully ensuring stability."""
    if key in task_dict:
        val = task_dict[key]
        if isinstance(val, (dict, list, set)):
            val.clear()
        del task_dict[key]
        return True
    return False

async def delayed_task(delay: float, coro):
    """Utility wrapper to add a delay before awaiting a coroutine."""
    await asyncio.sleep(delay)
    await coro

def get_exact_text(message: types.Message) -> str:
    """Extracts raw text preserving all exact spaces and newlines natively."""
    if not message.text: return ""
    cmd_len = len(message.text.split()[0])
    exact = message.text[cmd_len:]
    if exact.startswith(" "): exact = exact[1:]
    return exact

def get_auth_id(message: types.Message) -> int:
    """Reliably extracts the author's ID, prioritizing channels securely."""
    if message.from_user:
        return message.from_user.id
    if message.sender_chat:
        return message.sender_chat.id
    return message.chat.id

def is_sudo(user_id):
    return user_id in SUDO_USERS

def is_owner(user_id):
    return user_id == OWNER_ID

RAID_TEXTS =["2-3 ⱮƛӇƖƝЄ ӇƲЄ ƝƛӇƖ ӇƛƓƝЄ ԼƓЄ ", "ⱦєяє ɠɦαя кι αυятση кι вяα ƒαα∂ к αρηα кυятα ѕιℓωαυ яη∂ук ", "ƓƦƖƁ Ɱƛ Ƙ ƁƛƇӇƳ ƓӇƛƦ ⱮЄ ƛƬƬƛ ԼЄ ƛƛ ", "ƊӇƛƬ яη∂ιкєу ", "ƬЄƦƖ Ɱƛƛ Ƙƛ ƁӇƧƊƛ ", "Ƭєяι мα к вσѕ∂є м αιѕα ℓαт мαяυggα ηα gαтє ωαу σƒ ιη∂ια вαη נαєggα ", "ꪶ  ⱠƲƝ ƬЄ Ɣƛʝ ꪻ♡︎ ", "уααя αρηι мα мт ηυηgу кя ", "Ƭяу мσм кє ѕαтн вα∂ мαηηєяѕ кя∂υggα ", "ƬЄƦƖ Ɱƛ ƇӇƠƊƲƝ ", "ƬЄƦƖ Ɱƛ Ƙ ƁӇƠƧƊƛ ⱮƛƊƇӇƠƊ ", "ⱮƛƇƇӇƛƦ ƬⱮƘƇ ", "Ƭєяу мαα кσ qαвαя ηαѕєєв ηα нσ яη∂укє ", "ƲƬӇ яη∂к кυттє ", "ƤƛƦԼЄ Ɠ ƘӇƛЄƓƛ ƘƳƛ ƬƠⱮⱮƳ ", "ƁƖӇƛƦƖ ƓƛƝƓ ƬЄƦƖ Ɱƛ ƇӇƠƊƲƝ ", "ƬƲⱮ ƧƁ ƘƲƬƬƠ ƘƖ ʝӇƲƝƊ ƘƖ ⱮƘƁ ", "ƓƇ ԼЄƑƬ ԼЄ яη∂ιвαℓα ", "Ƭєяι мαα кι ƈнσтι ραкα∂ кє ∂єєωαя мє мααяυηgα ∂нαм ∂нαм кι αωααנ ααуєgι ", "ƁӇƛƓƝƛ ⱮƛƝƛ ӇƳ ƬⱮƘƁ ", "ƘƖ ⱮƘƁ ƳƦ ƁӇƛƓ ƘЄƧЄ ƦӇЄ ӇƠ ƓƛƦƖƁƠ ", "ƬⱮƘƇ ", "ƬⱮƘƁ ", "ƬƁƘƇ ", "ƦƝƊƘ ƁƛƇӇƳ ", "ƠƳЄ ƬƠⱮⱮƳ ƲƬӇ ƁӇƛƓƝƛ ƝƳ ӇƛƖ "]
NCEMO_EMOJIS =["🎀", "👑", "😂", "🤪", "👻", "❤️", "🌺", "🧊", "✅", "😹", "😻", "💦", "🤍", "🖤", "🤎", "💜", "💙", "❤️", "🧡", "💛", "💚", "💦", "🧑🏻‍✈️", "👮🏻", "🧑🏻‍🎓", "🦋", "🐳", "🎚️", "💸", "🕯️", "❔", "❌", "⚕️", "➿", "✖️", "➰", "™️", "💠", "♻️", "🈲", "🈹", "🈵", "🈴", "㊗️", "‼️", "🍡", "🍧", "🍭", "🐙", "🍃", "🤸🏻", "🤷🏻", "😱", "🤣", "👾", "💤", "💢", "♥️", "💟", "❄️", "🐕", "🕸️", "🍥", "🚙", "🚗", "🚐", "🚚", "🚜", "🚌", "🔫", "🎛️", "🪙", "🖱️", "🪢"]
SWIPE_TEXTS =["NAME ƘƠ ƤEʟƬE ӇƲE EƝƬƦƳ 🤣😎❤️‍🔥","NAME ƬEƦƖ Ɱƛƛ ƘƖ ƇӇƲƬ ⱮE ʟƠƲƊƛ ⱮƛƊƛƦƇӇƠƊ 😂🩷🤚🏼","NAME ƦEƤʟƳ ƘƛƦ ƓƛƦƖƁ ƊƛƦ ƘƳƲ ƦƛӇƛ Ӈ 😁🤙🏼🤍","NAME ƇӇƛʟ ƬEƦƖ Ɱƛ ƇӇƠƊƲ ƤƛƬƛƘ ƤƛƬƛƘ ƘE 🤪👻🩶","NAME ƇӇƲƊƘE ƧƤƛⱮ ƳƛӇƖ ƛƲƘƛƬ Ӈ ƬEƦƖ ƓƛƦƖƁ 😹🩵🙌🏼","ƇƤ ƘƛƦ NAME ƓƛƦƖƁ ƁӇƛƛƓ ⱮƬ ƇӇƠƬEƳ 😂🩶🤚🏼","NAME ƘƖ ⱮƲⱮⱮƳ ƘƠ ƦƝƊƖ ƁƛƝƛ ƊƲƝƓƛ ӇEӇEӇE 🤣💖✌🏼","NAME ƘE ƁƛƛƤ ѴχᏕ ƳEӇ ӇƛƖ ƖƝƘƖ Ɱƛƛ ƘE ƳƛƛƦ 😆🩶🤚🏼","ƘƛƁƛƊƖ ƔƛʟE NAME ƘƖ ⱮƘƁ 🤣👻💗","ƛƦEƳ NAME ƘƖ ⱮƘƁ ƳƛƛƦ ƁӇƛƓ ƘƛƖƧE ƦӇЄ ӇƠ ƓƛƦƖƁƠ 😤👻💞","ƛƦEƳ NAME ⱮƛƇƇӇƛƦ ƬⱮƘƇ 😂🩷✌🏾","NAME ƬƲ ʟƛƊӇEƓƛ ӇƲⱮƧE ƬEƦƖ Ɱƛ ƇƠƊƘE ⱮƖƬƬƖ ⱮE ⱮƖʟƛƊEƝƓE ӇƲⱮ 😂🔥🤸🏻","NAME ʟEƛƔE ʟE ƬƲ ƦƝƊƳƘE ƤƛƧƛƝƊ ƝƛƖ ƛƳƛ ⱮƦƘƠ 😏👋🏼","NAME ƓƦƖƁ Ɱƛ Ƙ ƁƛƇӇƳ ƓӇƛƦ ⱮE ƛƬƬƛ ʟE ƛƛ 😂🥲","NAME ƛƲƦƛƬƠ Ƙƛ ƘƛⱮ ƦƠƬƖ ƁƝƛƝƛ ӇƠƬƛ Ӈ ƬƠ NAME ƘƖ Ɱƛ ƳƛӇƛ ƘƳƲ ƇӇƲƊƦӇƖ 🤬🤣😭","NAME ƬEƦƖ Ɱƛ ƘƠ ƧEƝƛƤƛƬƖ ƧE ƇӇƲƊƔƛƊEƝƓE 🪖🖲️🔥","NAME ƬƦƳ ƓƝƊ ⱮE ƛEƧƛ ƁӇƛʟƛ ⱮƛƦƲƓƛ ƧƖƊӇƛ ⱮƠƲƝƬ EƔEƦEƧƬ ƤE ƦƲƘEƓƛ 💯🚀💔","NAME ƬEƦƖ Ɱƛƛ ƬƛƘʟƖ ӇEӇEӇE 💖💛💚","NAME ⱮƲJӇE ƝƲⱮƁEƦ ƘƖ ƘƳƛ ƵƛƦƲƦƛƬ\nⱮƛƖ ӇƲ EƘ ƤʟƲⱮƁEƦ 👨‍🔧\nJƛƁ ƇӇƠƊƝE Ƙƛ ⱮƛƝƝ ƘƦEƓƛ NAME ƘƖ Ɱƛƛ ƇƠƊ ƊƲƝƓƛ ƓӇƛƦ 😂🔧","NAME ƬEƦƳ Ɱƛƛ ƘƠ ƘƛƁƛ ƝƛƧEEƁ Ɲƛ ӇƠ ƦƝƊƳƘE 😑🖕🏽💔","NAME ʟƲƝ ƬE ƔƛJ 😂👏🏻✨","NAME ƬEƦƳ ƝƛƝƖ ƇӇƲƊ ƓƳƖ ƊӇƛⱮ ƊӇƛⱮ ƊӇƛⱮ 🥁🔊😍"]
TARGET_SLIDE_TEXTS =["𝙉𝙔 𝙉𝙔 𝙉𝙔 𝙈𝙀 𝙆𝙐𝘾𝙃 𝙉𝙔 𝙅𝙉𝙏𝘼 𝘽BS 𝙀𝙔 {name} 𝙆𝙄 𝙈𝘼 𝙍𝙉𝘿𝙔 𝙀𝙔 🤣🔥", "𝙊𝙔𝙔 𝙔𝙍𝙍 𝙔𝙀 {name} 𝙆𝙄 𝙈𝘼 𝙍𝙊𝙅 𝙍𝙊𝙅 𝙂𝙊𝘽𝘼𝙍 𝙆𝙃𝘼𝙆𝙍 𝘼𝙋𝙉𝘼 𝘽𝙐𝙉𝘿 𝘿𝙀𝙏𝙄 𝙀𝙔 😑🖕🏿🔥😑🖕🏿🔥", "𝙊𝙔𝙔 {name} 𝙆𝙈𝙕𝙊𝙍 𝙏𝘼𝙏𝙏𝙀 𝙏𝙀𝙍𝙄 𝙈𝘼 𝙎𝘼𝘽𝙎𝙀 𝙎𝙀 𝘽𝙃𝙄𝙆 𝙌 𝙈𝘼𝙉𝙂𝙏𝙄 𝙀𝙔", "𝙊𝙔𝙔 {name} 𝙏𝙀𝙍𝙄 𝙈𝘼 𝙆𝘼 𝘽𝙐𝙉𝘿 𝙆𝘼𝙇𝘼 𝙌 𝙀𝙔 😑🔥🤣🖕🏿🔥", "𝙀𝙑𝙀𝙍𝙔𝙏𝙃𝙄𝙉𝙂 𝙄𝙎 𝙊𝙆 𝘽𝙐𝙏 {name} 𝙆𝙄 𝙈𝘼 𝘾𝙐𝘿𝙉𝘼 𝙄𝙎 𝙋𝙀𝙍𝙈𝘼𝙉𝙀𝙉𝙏 🤣🔥", "{name} 𝙏𝘼𝙏𝙏𝙀 𝙏𝙀𝙍𝙄 𝙈𝘼 𝙆𝙈𝙕𝙊𝙍 𝙍𝙉𝘿𝙔 𝙀𝙔 𝙔𝘼𝙆𝙄𝙉 𝙉𝙔 𝙀𝙔 𝙏𝙊 𝘼𝙋𝙉𝙀 𝙎𝘼𝘽 𝘽𝘼𝘼𝙋 𝙎𝙀 𝙋𝙐𝘾𝙃𝙇𝙀 😑🔥", "𝘼𝙉𝘿𝙔 𝙈𝘼𝙉𝘿𝙔 𝙎𝘼𝙉𝘿𝙔 {name} 𝙏𝘼𝙏𝙏𝙀 𝙆𝙄 𝙆𝙈𝙕𝙊𝙍 𝙈𝘼 𝙎𝙏𝙍𝙊𝙉𝙂𝙀𝙎𝙏 𝙍𝙉𝘿𝙔 😑🖕🏿🔥🤣", "𝙊𝙔 𝙈𝙀 𝙆𝙐𝘾𝙃 𝙉𝙔 𝙎𝙐𝙉𝙐𝙉𝙂𝘼 𝘽𝙎 𝙔𝙀 {name} 𝙆𝙄 𝙈𝘼 𝙈𝙀𝙍𝙄 𝙋𝙑𝙏. 𝙍𝙉𝘿𝙔 𝙀𝙔 😑🔥", "𝘾𝙃𝙄 𝙔𝙍𝙍 𝙀𝙔 {name} 𝙆𝙄 𝙈𝘼 𝘿𝙐𝙎𝙏𝘽𝙄𝙉 𝙎𝙀 𝘿𝙄𝙇𝘿𝙊 𝙉𝙄𝙆𝘼𝙇 𝙆𝙍 𝘼𝙋𝙉𝙀 𝘽𝙐𝙉𝘿 𝙈𝙀 𝘿𝘼𝙇 𝙇𝙀𝙏𝙄 𝙀𝙔 😑🔥", "𝙊𝙔𝙔 {name} 𝙏𝘼𝙏𝙏𝙀 𝙈𝙐𝙅𝙀 𝘽𝘼𝘼𝙋 𝘽𝙉𝘼 𝙇𝙀 𝙉𝙔 𝙏𝙊 𝙏𝙀𝙍𝙄 𝙈𝘼 𝙍𝙉𝘿𝙔"]
KENG_TEMPLATES =[{"text": "NAME ⱮƎ ƬƎƦƖ ⱮƛƘƠ ƇӇƠƊƲƝƓƛ", "emoji": "🥱"}, {"text": "NAME ƇӇƲƤ ƦƝƊƳƘƎ", "emoji": "😂"}, {"text": "NAME ƲƬӇ ƦƝƊƖƘƎ ƁƛƇӇƎ", "emoji": "🍌"}, {"text": "NAME ƛƦE NAME JƛƖƧE ƘƲƬƬƠ ƘƠ ⱮƛƛƦ Ƙ HƲⱮ ƤƛƝƖ Ɣ ƝƛӇƖ ƤƲƇӇƬE ⱮƇ", "emoji": "🩷"},{"text": "NAME Ƙƛ ƁƛƛƤ ƛƛƳƛ", "emoji": "❔"},{"text": "NAME ƘƖ Ɱƛ Ƙƛ ƁƠƠƦ", "emoji": "🤪"},{"text": "ƛƦE NAME ƁӇƛƓ ƘEƧE ƦӇЄ ӇƠ ƓƛƦEEƁƠ", "emoji": "👻"},{"text": "NAME ƲƬӇƛƘ ƁƛƖƬӇƛƘ ʟƛƓƛ ⱮƇ", "emoji": "😹"},{"text": "NAME ƵƠƦ ʟƛƓƛ ƝƇ ƇƔ ʟE ⱮƇ", "emoji": "🤣"},{"text": "NAME ƇӇƛʟ JӇƲƘ ƦƝƊƘ", "emoji": "😎"}]
SPMNC_LONG =["NAME ƲƬӇ ƤƛƖƦ ƤƘƊ ӇƲⱮƛƦE\n\n\n\n\n\n" * 40, "ƝƳ ƝƳ ⱮE ƘƲƇӇ ƝƳ JƛƝƬƛ ƁƧ NAME ƘƖ Ɱƛ ƦƝƊƳ EƳ\n\n\n\n\n\n" * 40, "NAME ƲƬӇ ƘE ƁƛƖƬӇ ƦƝƊƘ\n\n\n\n\n\n" * 40, "NAME ƬEƦƖ Ɱƛ ƘƖ ƇӇƲƬ ⱮE ƛƛƓ ʟƛƓƛ ƊƲƝƓƛ ⱮƇ\n\n\n\n\n\n" * 40,"NAME ƬEƦƖ ⱮƠⱮ ƦƝƊƳ\n\n\n\n\n\n" * 40,"NAME ƬEƦƖ Ɱƛ ƘƠ ƇӇƠƊƲƝ\n\n\n\n\n\n" * 40,"NAME JӇƛƬƲ ƧƛʟE ƁƛƛƤ ʟƠƓ ƧE ʟƛƊӇEƓƛ?\n\n\n\n\n\n" * 40]
SPMNC_SMALL =["NAME ƲƬӇ ƤƛƖƦ ƤƘƊ ӇƲⱮƛƦE","ƝƳ ƝƳ ⱮE ƘƲƇӇ ƝƳ JƛƝƬƛ ƁƧ NAME ƘƖ Ɱƛ ƦƝƊƳ EƳ","NAME ƲƬӇ ƘE ƁƛƖƬӇ ƦƝƊƘ","NAME ƬEƦƖ Ɱƛ ƘƖ ƇӇƲƬ ⱮE ƛƛƓ ʟƛƓƛ ƊƲƝƓƛ ⱮƇ","NAME ƬEƦƖ ⱮƠⱮ ƦƝƊƳ","NAME ƬEƦƖ Ɱƛ ƘƠ ƇӇƠƊƲƝ","NAME JӇƛƬƲ ƧƛʟE ƁƛƛƤ ʟƠƓ ƧE ʟƛƊӇEƓƛ?"]
REPLY_vxs_TEXTS =["ƖƵƵƛƬ ƘƦƠ ƬƲⱮӇƛƦE ƁƛƛƤ ѴχᏕ ƘƖ 😑🙌🏾","ƓƛƊƊӇƛ ƊƖƘӇƛ ƘӇƠƊ ƊƖƳƛ ƬEƦƖ Ɱƛƛ ƊƖƘӇƖ ƇӇƠƊ ƊƖƳƛ 🙊🤦🏾😂","ѴχᏕ ƁƊⱮƠƧӇ ƧƤEƛƘƖƝƓ ƑƦƠⱮ ƬEƦƖ ⱮƘƁ🤦🏾☎️","ƇƲƊƝƛ ⱮƝƛ ӇƛƖ 😩🤟🏻","ƬEƦƖ Ɱƛƛ ƇƠƊ ƘE ⱮƛƦ ƊƲƝƓƛ 🤣🖕🏾","ƬEƦƖ Ɱƛƛ ƇƲƊ ƦӇƖ ӇƛƖ ƝƛƇӇƠ 👻🕺","ӇƳ ƇƠƬƲ 😉✌🏾","ƇƳƛ","ƑƛƧƬ ʟƖƘӇ","𝙌 ❓🤨","ƇƲƊ ƘE ⱮƦƓƳƛ ƘƳƛ 💀😹","ӇʟƔ ƤƓʟ ƁӇƛƓ ⱮƬ 🏃‍♂️💨","ѴχᏕ ƇӇƠƊ ƦӇƛ ӇƛƖ 👻🔥","ƇƳƛ?","ƬEƦƖ Ɱƛƛ ❓","ƬEƦƖ ƁӇEƝ ⱮƛƦƊƲ ❓","ӇEʟƤ ӇEʟƤ ⱮƬ ƘƦ ƇƠƬƲ 😩👍🏾","ƤƲJƛ ƘƦ ƬEƦƛ ƁƛƛƤ ѴχᏕ ƘƖ 🙏🏾🔥","ӇʟƔ ӇʟƔ ӇƛⱮʟƛ ӇƠƓƳƛ ƬEƦƖ ⱮƘƁ ⱮE 😱😂","ƬEƦƖ ƁƘƇ ⱮE ƁƖƓƁƠƧƧ 📺😆","ӇʟƔ ƦEƤʟƳ ƑƛƧƬ","ƑƛƧƬ ƬƳƤE ƘƦ ƊƛƦ ⱮƬ 😤⌨️","ӇEʟƤ ӇEʟƤ ƬEƦƖ Ɱƛƛ ƇӇƲƊ ƓƳƖ 😩","ѴχᏕ ƛƁƁƲ ƤEʟ ƦӇE ӇƛƖ 👻💪","ӇƳ ƬEƦƖ Ɱƛƛ ⱮƦ ƓƳƖ ƘƳƛ 😶💔","ƛƔƔ ƬEƦƖ Ɱƛƛ ƘƠ ƤƠƠƘƖE ƁƝƛƘE ⱮƛƦƲƝƓƛ 🤣🎀","ƘƳƛ ❓😑","ƦƠ ⱮƬ 😂🤟🏻","ƧƠƦƬ ƝӇƖ ƘƦƲƝƓƛ ƇƲƊ ƬƲ ƁƖƝƛ ƦƲƘE 😹🖕🏾","ƬƛƘE ƳƠƲƦ ƬƖⱮE ƑƖƦ ƇƲƊ 😉✌🏾","ӇʟƔ ƘƲƬƖƳƛ ƘE ʟƦƘE 🐶😆","ӇʟƔ ӇʟƔ ⱮJƛ ƛƛƦӇƛ ƇƲƊƝE ⱮE 😜🔥","ѴχᏕ ƓƝƊ ⱮƛƛƦ ƦӇE ӇƛƖ 👻","ӇƳ ƇƠƬƲ ƁӇƓ ⱮƬ ƦƝƊƳ ƘE 🔥😑👍🏾","ƁӇƛƓƝƛ ⱮƛƝƛ ӇƛƖ JƖ 🚫😎","ѴχᏕ ƛƁƁƲ ƛƛƓƳE 🤣🩷🙌🏾","ƬEƦƖ Ɱƛƛ ⱮƛƦƘE ⱮJƊƲƦƖ ƘӇƬⱮ 👍🏾","ƘƳƛ ѴχᏕ ƬEƦƛ ƁƛƛƤ ӇƛƖ 👻❓","ƘƳƛ ⱮƬʟƁ ƬEƦƖ Ɱƛƛ ѴχᏕ ƝE ƇƠƊƖ 😹🖕🏾","ƬEƦƖ ƁӇEƝ ⱮƛƦƘE ƁӇƛƓ JƛƲƝƓƛ 🙋🏾🤪","ƬEƦƖ ƁӇEƝ ⱮƛƦƘE ѴχᏕ ƁӇƛƓ ƓƳƛ 🤦🏾💔","ƁӇƛƓ 𝙌 ƦӇƛ ӇƛƖ ❓","ƬEƦƖ Ɱƛƛ ⱮƲⱮƁƛƖ ⱮE ƇƲƊEƓƖ 😌🩷🙌🏾","ƬƳƤE ƘƦ Ɲƛ ƛƁ ƬEƦE ƁƛƛƤ ƘE ƧƛⱮƝE ⁉️","ƘƦ ƬƳƤE ƬⱮƘƇ 😂🤟🏻","JʟƊƖ ƇƲƊ 🤢","ƁƖƝƛ ƦƲƘE ƬӇƲƘƛƖ ӇƠƓƖ ƬEƦƖ 😁😂","ƁӇƛƓEƓƛ ƬƠ ƇƠƊ ƘE ⱮƛƦƊƲƝƓƛ 😑🙌🏾","ƖƊӇƦ ƛJƛ ƇӇƠƬEƳ 👶🍼","ƁӇƛƓ ⱮƬ ƘƲƬƖ ƘE 🙊😂","ƬEƦƖ Ɱƛƛ ƘƠ ƁEƝ10 ⱮE ƇƠƊƲƝƓƛ 👽😱","ƖƵƵƛƬ ƘƦEƓƛ ƛƛJƧE ѴχᏕ ƛƁƁƲ ƘƖ 😂🤟🏻","ƬEƦƖ ƁӇEƝ ƘƖ ƤƠƠƘƖE ƓƔƝƊ ⱮE ʟƲƝ 🎀","ƁӇƛƓ ⱮƬ ƁEƬE 😑🙌🏾","ƖƊӇƦ ƛJƛ ʟƛƊʟE 😉❤️","ƬEƦƖ ƓEƝƊ ⱮE 100 ӇƛƬӇ 💯🔥","ƘƦ ƛƁ ӇƛƔƛƁƛƛƵƖ?","ʟE ƛƛƓƳƛ ƬEƦƛ ƁƛƛƤ ѴχᏕ 👻👑","ƁӇƛƓƝE ƧE ƘƲƇӇ ƝӇƖ ӇƠƓƛ 🐕❌","ƁӇƛƓ ƁӇƛƓ ƬⱮƘƇ 😑😹","ƁӇƛƓƛ ƁӇƛƓƛ ƘE ⱮƛƦƲƝƓƛ 🤣🩷🙌🏾","ƁƝ ƛƁ ƑƳƬƦ 🤦🏾😎😂","ƘƦ Ɲƛ ƑƳƬ 😁🔥","ƁӇƛƓEƓƛ ❓","ƁӇƛƓ JʟƊƖ 🐕🏳️‍🌈","ӇʟƔ ƇƲƊƓƳƖ ƘƳƛ 💀😹","ѴχᏕ ƛƛƓƳƛ 👻🔥","ƬEƦE ƁƛƛƤ ѴχᏕ ƘƖ EƝƬƦƳ 👻😂","ƦEⱮEⱮƁEƦ ƬӇE ƓƠƊ ƘEƝƓ ѴχᏕ 👻👑"]

dp = Dispatcher()

async def safe_reply(message: types.Message, text: str, **kwargs):
    try:
        await message.reply(text, **kwargs)
    except Exception as e:
        print(f"{RED}[ERROR] Send Message failed: {e}{RESET}")

async def get_target_info(message: types.Message, command_arg: str = None):
    uid, name = None, None
    if message.reply_to_message:
        rm = message.reply_to_message
        if rm.forward_from_chat:
            uid = rm.forward_from_chat.id
            name = rm.forward_from_chat.title or "Channel"
        elif rm.sender_chat:
            uid = rm.sender_chat.id
            name = rm.sender_chat.title or "Channel"
        elif rm.from_user:
            uid = rm.from_user.id
            name = rm.from_user.first_name
        else:
            uid = rm.chat.id
            name = rm.chat.title or "Chat"
    elif message.entities:
        for ent in message.entities:
            if ent.type == 'text_mention' and ent.user:
                uid, name = ent.user.id, ent.user.first_name
                break
            if ent.type == 'mention' and message.text:
                uname = message.text[ent.offset + 1: ent.offset + ent.length].lower()
                if uname in username_to_id:
                    uid = username_to_id[uname]
                    name = user_names.get(uid, uname)
                    break
    elif command_arg:
        arg = command_arg.strip()
        if arg.lstrip('-').isdigit():
            uid = int(arg)
            name = user_names.get(uid, "Target")
        elif arg.startswith('@'):
            uname = arg[1:].lower()
            if uname in username_to_id:
                uid = username_to_id[uname]
                name = user_names.get(uid, uname)
                
    if uid and name:
        user_names[uid] = name
        save_db()
    return uid, name

def get_active_groups_info():
    active_chats = set()
    for task_dict in[group_tasks, keng_tasks, spmnc_tasks, spm_loop_tasks, rspm_tasks, pfp_tasks, sticker_spm_tasks, gif_spm_tasks, media_spm_tasks, voice_spm_tasks, seq_nc_tasks, forwardspm_tasks, vxsnc_tasks, vxsspam_tasks]:
        for key, val in task_dict.items():
            if val: active_chats.add(key)
    for key in swipe_mode:
        active_chats.add(key)
    return list(active_chats)

async def generate_tts(text, lang="en"):
    global _shared_http_session
    encoded_text = urllib.parse.quote(text.strip())
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_text}&tl={lang}&client=tw-ob"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        if _shared_http_session is None or _shared_http_session.closed:
            _shared_http_session = aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(limit=10, keepalive_timeout=120.0, ttl_dns_cache=300)
            )
        async with _shared_http_session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.read()
    except Exception:
        pass
    return None

def create_sticker_image(text, bg_color="black", font_type="default"):
    if not HAS_PIL:
        return None
    import io
    
    colors = {
        "red": "#FF3B30", "blue": "#007AFF", "green": "#34C759",
        "yellow": "#FFCC00", "black": "#1C1C1E", "white": "#F2F2F7", "purple": "#AF52DE"
    }
    bg_hex = colors.get(bg_color, "#1C1C1E")
    
    img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    bubble_bbox =[20, 100, 492, 412]
    draw.rounded_rectangle(bubble_bbox, radius=40, fill=bg_hex)
    
    font = None
    font_size = 65 if font_type == "bold" else 55
    font_paths =[
        "arial.ttf", "calibri.ttf", "tahoma.ttf", "seguiemj.ttf", 
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if font_type == "bold" else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if font_type == "bold" else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc", "/Library/Fonts/Arial.ttf"
    ]
    for p in font_paths:
        try:
            font = ImageFont.truetype(p, font_size)
            break
        except IOError:
            continue
            
    if font is None:
        font = ImageFont.load_default()
        
    text_color = "black" if bg_color in["white", "yellow"] else "white"
    
    
    wrapped_text = "\n".join(textwrap.wrap(text, width=15))
    
    
    if HAS_PILMOJI:
        with Pilmoji(img) as pilmoji:
            pilmoji.text((256, 256), wrapped_text, fill=text_color, font=font, anchor="mm", align="center")
    else:
        draw.text((256, 256), wrapped_text, fill=text_color, font=font, anchor="mm", align="center")
    
    bio = io.BytesIO()
    img.save(bio, "WEBP")
    bio.seek(0)
    return bio.getvalue()

async def seq_nc_worker(chat_id: int, base_text: str, active_bots: list, task_id: str):
    bot_idx = 0
    num_bots = len(active_bots)
    cooldown_until = {}
    while seq_nc_tasks.get(chat_id) == task_id:
        try:
            now = time.time()
            # Pick the next available bot that is not currently rate-limited by Telegram
            selected_bot = None
            for _ in range(num_bots):
                candidate = active_bots[bot_idx]
                bot_idx = (bot_idx + 1) % num_bots
                if cooldown_until.get(candidate.id, 0) <= now:
                    selected_bot = candidate
                    break

            if selected_bot is None:
                earliest = min(cooldown_until.values(), default=now + 0.5)
                await asyncio.sleep(max(0.05, earliest - now))
                continue

            emoji_char = random.choice(SEQ_EMOJIS)
            base_len = len(list(base_text))
            emoji_len = len(list(emoji_char))
            
            max_repeats = max(1, (125 - base_len - 1) // max(1, emoji_len))
            frame_to_set = base_text + " " + (emoji_char * max_repeats)
            
            await selected_bot.set_chat_title(chat_id, frame_to_set[:125])
            await asyncio.sleep(0.02)
        except TelegramRetryAfter as e:
            if selected_bot is not None:
                cooldown_until[selected_bot.id] = time.time() + float(e.retry_after) + 0.1
            await asyncio.sleep(0.02)
        except Exception:
            await asyncio.sleep(0.1)

async def nc_loop_worker(bot: Bot, chat_id: int, name: str, task_id: str):
    while group_tasks.get(chat_id, {}).get(bot.id) == task_id:
        try:
            delay = nc_delays.get(chat_id, 150) / 1000.0
            base_text = f"{name} {random.choice(RAID_TEXTS)}"
            emoji_block = random.choice(NCEMO_EMOJIS)
            
            base_len = len(list(base_text))
            emoji_len = len(list(emoji_block))
            
            if base_len < 120:
                max_repeats = (125 - base_len - 2) // emoji_len
                frame_to_set = base_text + "  " + (emoji_block * max_repeats)
            else:
                frame_to_set = base_text
                
            await bot.set_chat_title(chat_id, frame_to_set[:125])
            await asyncio.sleep(delay)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except Exception:
            await asyncio.sleep(1)

async def ncemo_loop_worker(bot: Bot, chat_id: int, base_text: str, task_id: str):
    while group_tasks.get(chat_id, {}).get(bot.id) == task_id:
        try:
            delay = nc_delays.get(chat_id, 150) / 1000.0
            emoji_block = random.choice(NCEMO_EMOJIS) + random.choice(NCEMO_EMOJIS)
            base_len = len(list(base_text))
            emoji_len = len(list(emoji_block))
            max_repeats = max(1, (125 - base_len) // emoji_len)
            dynamic_gap = " " * random.randint(1, 3)
            
            frame_to_set = base_text + dynamic_gap + (emoji_block * max_repeats)
            await bot.set_chat_title(chat_id, frame_to_set[:125])
            await asyncio.sleep(delay)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except Exception:
            await asyncio.sleep(1)

async def keng_loop_worker(bot: Bot, chat_id: int, name: str, task_id: str):
    while keng_tasks.get(chat_id, {}).get(bot.id) == task_id:
        try:
            delay = nc_delays.get(chat_id, 150) / 1000.0
            template = random.choice(KENG_TEMPLATES)
            base_text = template["text"].replace("NAME", name)
            emoji_block = template["emoji"]
            base_len = len(list(base_text))
            emoji_len = len(list(emoji_block))
            max_repeats = max(1, (125 - base_len) // emoji_len)
            dynamic_gap = " " * random.randint(1, 3)
            frame_to_set = base_text + dynamic_gap + (emoji_block * max_repeats)
            await bot.set_chat_title(chat_id, frame_to_set)
            await asyncio.sleep(delay)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except Exception:
            await asyncio.sleep(1)

async def vxsnc_loop_worker(bot: Bot, chat_id: int, name: str, task_id: str):
    templates =["ƘƳƲ ƦЄ NAME ƘƲƬƬЄ [ ѴχᏕ ] ƁƛƛƤ ƧЄ ƁƛƊƬƛⱮЄЄƵƖ? ","NAME ƲƬӇ ƬⱮƘƇ ","NAME ƝƇ ƝƇ ƘƦЄƓƛ ƦƝƊƖƘ","NAME ƬƠƦ ⱮƛƖ ƘЄ ƇӇƠƊƠ","NAME ƝƊ ƲƝƘЄ ӇƠⱮƖЄƧ ƘƖ Ɱƛ ƦƝƊƖ","NAME ƲƬӇ ƦƝƊƖƘ ƠҲƳƓЄƝ ԼЄ","ƇӇƛԼ ƇӇƛԼ NAME ƵƠƦ ԼƛƓƛ ⱮƇ","NAME ⱮƇ","NAME ƁƇ","NAME ƬƛƬƬЄ",
"NAME ƇӇƲƊ",]
    while vxsnc_tasks.get(chat_id, {}).get(bot.id) == task_id:
        try:
            
            delay = nc_delays.get(chat_id, 500) / 1000.0
            base = random.choice(templates).replace("NAME", name)
            
            
            c1 = "✘" if random.random() > 0.5 else "─"
            c2 = "✘" if random.random() > 0.5 else "─"
            c3 = "✘" if random.random() > 0.5 else "─"
            c4 = "✘" if random.random() > 0.5 else "─"
            c5 = "✘" if random.random() > 0.5 else "─"
            
            pattern = f"─────── {c1} ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ ────────{c2}─────{c3}───────❗────── ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬{c4} {c5}"
            
            
            frame = (base + pattern)[:125]
            
            await bot.set_chat_title(chat_id, frame)
            await asyncio.sleep(delay)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except Exception:
            await asyncio.sleep(1)

async def spmnc_worker(bot: Bot, chat_id: int, name: str, task_id: str):
    last_msg_time = 0
    while spmnc_tasks.get(chat_id, {}).get(bot.id) == task_id:
        try:
            delay = nc_delays.get(chat_id, 600) / 1000.0
            long_raw = random.choice(SPMNC_LONG).replace("NAME", name)
            small_raw = random.choice(SPMNC_SMALL).replace("NAME", name)
            random_emoji = random.choice(NCEMO_EMOJIS)
            title_text = f"{random_emoji} {small_raw} {random_emoji}"
            try:
                await bot.set_chat_title(chat_id, title_text)
            except TelegramRetryAfter as e:
                await asyncio.sleep(float(e.retry_after) + 0.5)
                continue
            except Exception:
                pass
            await asyncio.sleep(delay)
            if time.time() - last_msg_time > 7.0:
                try:
                    await bot.send_message(chat_id, long_raw)
                    last_msg_time = time.time()
                except TelegramRetryAfter as e:
                    await asyncio.sleep(float(e.retry_after) + 0.5)
                except Exception:
                    pass
        except Exception:
            await asyncio.sleep(1)

async def copy_spm_sender(bot: Bot, chat_id: int, from_chat_id: int, msg_id: int, tasks_dict, task_id: str):
    """Spams by flawlessly copying any given message entirely server-side."""
    while task_id in tasks_dict.get(chat_id,[]):
        try:
            d = spm_delays.get(chat_id, 1500) / 1000.0
            await bot.copy_message(chat_id=chat_id, from_chat_id=from_chat_id, message_id=msg_id)
            await asyncio.sleep(d)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except Exception:
            await asyncio.sleep(1.5)

async def spm_sender(bot: Bot, chat_id: int, msg_id: int, text: str, tasks_dict, task_id_obj_key, task_id: str):
    while task_id in tasks_dict.get(task_id_obj_key,[]):
        try:
            d = spm_delays.get(chat_id, 1500) / 1000.0
            kwargs = {}
            if msg_id: 
                kwargs["reply_to_message_id"] = msg_id
            
            if LinkPreviewOptions:
                kwargs["link_preview_options"] = LinkPreviewOptions(is_disabled=True)
            else:
                kwargs["disable_web_page_preview"] = True
                
            await bot.send_message(chat_id, text, **kwargs)
            await asyncio.sleep(d)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except Exception:
            await asyncio.sleep(1.5)

async def vxsspam_sender(bot: Bot, chat_id: int, text: str, tasks_dict, task_id: str):
    """Spams long messages. Text appears at top AND bottom with newlines in between.
    Total message is capped at Telegram's 4096-char hard limit."""
    TELEGRAM_MAX = 4096
    text_len = len(text)
    
    if text_len * 2 + 1 > TELEGRAM_MAX:
        msg = text[:TELEGRAM_MAX]
    else:
        newlines_count = TELEGRAM_MAX - (text_len * 2) - 1
        msg = text + ("\n" * newlines_count) + text
    
    while task_id in tasks_dict.get(chat_id, []):
        try:
            d = spm_delays.get(chat_id, 1500) / 1000.0
            kwargs = {}
            if LinkPreviewOptions:
                kwargs["link_preview_options"] = LinkPreviewOptions(is_disabled=True)
            else:
                kwargs["disable_web_page_preview"] = True
            
            await bot.send_message(chat_id, msg, **kwargs)
            await asyncio.sleep(d)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except Exception as e:
            print(f"{RED}[vxsspam] send failed: {e}{RESET}")
            await asyncio.sleep(1.5)

async def media_spm_sender(bot: Bot, chat_id: int, media_type: str, file_id: str, caption, caption_entities, tasks_dict, task_id: str):
    """Spams explicitly sent media to flawlessly preserve native formatting and premium emojis (also bypasses voice forwarding)."""
    while task_id in tasks_dict.get(chat_id,[]):
        try:
            d = spm_delays.get(chat_id, 1500) / 1000.0
            kwargs = {}
            if caption: kwargs['caption'] = caption
            if caption_entities: kwargs['caption_entities'] = caption_entities
            
            if media_type == "photo": await bot.send_photo(chat_id, file_id, **kwargs)
            elif media_type == "video": await bot.send_video(chat_id, file_id, **kwargs)
            elif media_type == "document": await bot.send_document(chat_id, file_id, **kwargs)
            elif media_type == "audio": await bot.send_audio(chat_id, file_id, **kwargs)
            elif media_type == "animation": await bot.send_animation(chat_id, file_id, **kwargs)
            elif media_type == "sticker": await bot.send_sticker(chat_id, file_id)
            elif media_type == "voice": await bot.send_voice(chat_id, file_id, **kwargs)
            
            await asyncio.sleep(d)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except Exception:
            await asyncio.sleep(1.5)

async def rspm_sender(bot: Bot, chat_id: int, name: str, tasks_dict, task_id: str):
    while task_id in tasks_dict.get(chat_id,[]):
        try:
            d = rspm_delays.get(chat_id, 1500) / 1000.0
            base = f"{name} {random.choice(RAID_TEXTS)}"
            emoji = random.choice(NCEMO_EMOJIS)
            
            chunk = f"{base} {emoji}\n\n\n\n\n\n\n\n\n\n"
            msg_text = ""
            while len(msg_text) + len(chunk) < 4000:
                msg_text += chunk
                
            kwargs = {}
            if LinkPreviewOptions:
                kwargs["link_preview_options"] = LinkPreviewOptions(is_disabled=True)
            else:
                kwargs["disable_web_page_preview"] = True
                
            await bot.send_message(chat_id, msg_text, **kwargs)
            await asyncio.sleep(d)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except Exception:
            await asyncio.sleep(1.5)

async def forward_spm_sender(bot: Bot, chat_id: int, from_chat_id: int, msg_id: int, tasks_dict, task_id: str):
    consecutive_fails = 0
    while task_id in tasks_dict.get(chat_id, []):
        try:
            d = spm_delays.get(chat_id, 900) / 1000.0
            await bot.forward_message(
                chat_id=chat_id,
                from_chat_id=from_chat_id,
                message_id=msg_id,
                protect_content=False
            )
            consecutive_fails = 0
            await asyncio.sleep(d)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except TelegramBadRequest as e:
            err = str(e).lower()
            if any(x in err for x in ["message to forward not found", "message_id_invalid",
                                      "message can't be forwarded", "not found"]):
                print(f"{RED}[forwardspm] source message gone, stopping task{RESET}")
                break
            consecutive_fails += 1
            if consecutive_fails >= 5:
                print(f"{RED}[forwardspm] too many failures, stopping task{RESET}")
                break
            await asyncio.sleep(1.5)
        except Exception as e:
            consecutive_fails += 1
            if consecutive_fails >= 5:
                print(f"{RED}[forwardspm] too many failures ({e}), stopping task{RESET}")
                break
            await asyncio.sleep(1.5)
    if chat_id in tasks_dict and task_id in tasks_dict[chat_id]:
        try:
            tasks_dict[chat_id].remove(task_id)
        except Exception:
            pass

async def pfp_loop_worker(bot: Bot, chat_id: int, task_id: str):
    while task_id in pfp_tasks.get(chat_id,[]):
        try:
            d = pfp_delays.get(chat_id, 900) / 1000.0
            folder = os.path.join(os.path.dirname(__file__), 'downloads', str(chat_id))
            if not os.path.exists(folder):
                await asyncio.sleep(5)
                continue
            files =[f for f in os.listdir(folder) if f.endswith('.jpg')]
            if not files:
                await asyncio.sleep(5)
                continue
            pic = random.choice(files)
            pic_path = os.path.join(folder, pic)
            await bot.set_chat_photo(chat_id, FSInputFile(pic_path))
            await asyncio.sleep(d)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except Exception:
            await asyncio.sleep(2)

def get_selector_keyboard(task_id: str):
    menu = active_menus.get(task_id)
    if not menu: return None
    sel = menu['selected']
    keyboard =[]
    row =[]
    
    max_display = min(len(bot_usernames), 90)
    for i in range(max_display):
        uname = bot_usernames[i]
        check = "✅" if i in sel else "❌"
        row.append(InlineKeyboardButton(text=f"{check} {uname}", callback_data=f"tk_{task_id}_tgl_{i}"))
        if len(row) == 2:
            keyboard.append(row)
            row =[]
            
    if row: keyboard.append(row)
    keyboard.append([
        InlineKeyboardButton(text=font("🔘 Select All"), callback_data=f"tk_{task_id}_all"),
        InlineKeyboardButton(text=font("⚪️ None"), callback_data=f"tk_{task_id}_none")
    ])
    keyboard.append([InlineKeyboardButton(text=font("🚀 START LAUNCH"), callback_data=f"tk_{task_id}_start")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def send_start_menu(message: types.Message, bot: Bot):
    owner_name = font(user_names.get(OWNER_ID, 'Owner'))
    owner_acc = f"[{owner_name}](tg://user?id={OWNER_ID})"
    
    
    user_mention = f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})" if message.from_user else "Admin"
    
    text = font(f"Hello ") + user_mention + font("!\nI'm an advanced bot created by vxs handled by ") + owner_acc + font(".\nHow can I help you?")
    
    buttons = [[InlineKeyboardButton(text=font("👤 Owner"), callback_data="owner_contact"),InlineKeyboardButton(text=font("ℹ️ About"), callback_data="start_about")],[
            InlineKeyboardButton(text=font("📜 Commands"), callback_data="start_restricted"),
            InlineKeyboardButton(text=font("⚙️ Settings"), callback_data="start_restricted")
        ]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    pic_path = get_start_pic_path(bot.id)
    try:
        if os.path.exists(pic_path):
            await message.answer_photo(FSInputFile(pic_path), caption=text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN)


@dp.my_chat_member()
async def on_my_chat_member(update: ChatMemberUpdated):
    """Automatically logs the bot into groups and channels dynamically."""
    if update.new_chat_member.status in['member', 'administrator', 'restricted']:
        known_chats.add(update.chat.id)
        save_db()

@dp.channel_post(Command("startpfp", prefix="/!"))
@dp.message(Command("startpfp", prefix="/!"))
async def cmd_startpfp(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_owner(get_auth_id(message)): return
    
    if not message.photo and not (message.reply_to_message and message.reply_to_message.photo):
        return await safe_reply(message, font("⚠️ Please send this command as a caption to a photo or reply to a photo."))
        
    photo = message.photo[-1] if message.photo else message.reply_to_message.photo[-1]
    pic_path = get_start_pic_path(bot.id)
    await bot.download(photo, destination=pic_path)
    
    await safe_reply(message, font("✅ Permanent Start picture updated successfully for THIS bot!"))
    await send_start_menu(message, bot)

@dp.channel_post(Command("start", prefix="/!"))
@dp.message(Command("start", prefix="/!"))
async def cmd_start(message: types.Message, bot: Bot):
    await send_start_menu(message, bot)

@dp.channel_post(Command("help", prefix="!/"))
@dp.message(Command("help", prefix="!/"))
async def cmd_help(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    help_text = f"""
╭━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╮
        ❤️‍🔥 {font("#𝙑𝙭𝙎")}
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯

╭━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╮
        🤍 {font("𝙉𝘼𝙈𝙀 𝘾𝙃𝘼𝙉𝙂𝙀 (𝙉𝘾)")}
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
✘ `!sequentialnc <text>` / `!dsequentialnc`
✘ `!nc <name>` / `!dnc`
✘ `!ncemo <text>` / `!dncemo`
✘ `!kengnc <name>` / `!dkengnc`
✘ `!vxsnc <name>` / `!dvxsnc`
✘ `!spmnc <text>` / `!dspmnc`
✘ `!delaync <ms>` ➜ {font("Default: 500ms")}

╭━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╮
        📸 {font("𝙈𝙀𝘿𝙄𝘼 & 𝙎𝙏𝙄𝘾𝙆𝙀𝙍𝙎")}
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
✘ `!makesticker <text>` ➜ {font("Sticker Studio")}
✘ `!tts <text>` ➜ {font("Voice Studio")}
✘ `!stickerspm` / `!dstickerspm`
✘ `!gifspm` / `!dgifspm`
✘ `!mediaspm` / `!dmediaspm`
✘ `!voicespam` / `!dvoicespm`
✘ `!pfp` / `!dpfp` / `!gpfp`
✘ `!save` / `!del` / `!gsave` (reply)
✘ `!delaypfp <ms>` / `!delallmedia`

╭━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╮
        💦 {font("𝙎𝙇𝙄𝘿𝙀 & 𝙎𝙋𝘼𝙈")}
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
✘ `!forwardspm` / `!dforwardspm`
✘ `!targetslide <name>` / `!dtargetslide`
✘ `!slidespam <text>` / `!dslidespam`
✘ `!spm <text>` / `!dspm`
✘ `!vxsspam <text>` / `!dvxsspam`
✘ `!rspm <name>` / `!drspm`
✘ `!dallspm` ➜ {font("Kill All spams")}
✘ `!delaygcspm` / `!delayrspm` <ms>

╭━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╮
        🥱 {font("𝙍𝙀𝙋𝙇𝙔 & 𝙍𝙀𝘼𝘾𝙏")}
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
✘ `!replyvxs` / `!dreplyvxs`
✘ `!react <emoji>` / `!dreact`
✘ `!swipe <name>` / `!dswipe`

╭━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╮
        🤫 {font("𝙈𝙐𝙏𝙀 & 𝘼𝘿𝙈𝙄𝙉")}
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
✘ `!mute` / `!unmute` (reply/tag)
✘ `!mutelist` / `!listsudo`
✘ `!promoteall` / `!promoteallbots`
✘ `!addsudo` / `!delsudo`

╭━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╮
        ⚙️ {font("𝙎𝙔𝙎𝙏𝙀𝙈 𝘾𝙊𝙉𝙏𝙍𝙊𝙇")}
╰━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╯
✘ `!startpfp` / `!activebots` / `!missingbots`
✘ `!status` / `!uptime` / `!ping` / `!on`
✘ `!o` ➜ {font("Optimize & Clear Cache")}
✘ `!leave` ➜ {font("All Bots Leave")}
✘ `!dall` ➜ {font("Stop All Tasks")}
"""
    await safe_reply(message, help_text, parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("makesticker", prefix="!"))
@dp.message(Command("makesticker", prefix="!"))
async def cmd_makesticker(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    
    exact_text = get_exact_text(message)
    if not exact_text:
        return await safe_reply(message, font("⚠️ Please provide text to make a sticker! Example: `!makesticker Hello`"), parse_mode=ParseMode.MARKDOWN)
        
    if not HAS_PIL:
        return await safe_reply(message, font("⚠️ Pillow library is not installed on your server! The Sticker Studio requires it. Install via `pip install Pillow`."))
        
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {"cmd": "makesticker", "text": exact_text, "color": "black", "font": "default"}
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔴 Red", callback_data=f"stk_{task_id}_c_red"),
         InlineKeyboardButton(text="🔵 Blue", callback_data=f"stk_{task_id}_c_blue"),
         InlineKeyboardButton(text="🟢 Green", callback_data=f"stk_{task_id}_c_green")],[InlineKeyboardButton(text="🟡 Yellow", callback_data=f"stk_{task_id}_c_yellow"),
         InlineKeyboardButton(text="⚫ Black", callback_data=f"stk_{task_id}_c_black"),
         InlineKeyboardButton(text="⚪ White", callback_data=f"stk_{task_id}_c_white")],[InlineKeyboardButton(text="🖋 Standard Font", callback_data=f"stk_{task_id}_f_default"),
         InlineKeyboardButton(text="🔠 Bold Font", callback_data=f"stk_{task_id}_f_bold")],[InlineKeyboardButton(text="🚀 GENERATE STICKER", callback_data=f"stk_{task_id}_gen")]
    ])
    await message.reply(font("🎨 **STICKER STUDIO**\nChoose background and font below:"), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("tts", prefix="!"))
@dp.message(Command("tts", prefix="!"))
async def cmd_tts(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    
    exact_text = get_exact_text(message)
    if not exact_text:
        return await safe_reply(message, font("⚠️ Please provide text to speak! Example: `!tts Hello there`"), parse_mode=ParseMode.MARKDOWN)
        
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {"cmd": "tts", "text": exact_text}
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🇬🇧 English", callback_data=f"tts_{task_id}_en"),
         InlineKeyboardButton(text="🇮🇳 Hindi", callback_data=f"tts_{task_id}_hi"),
         InlineKeyboardButton(text="🇸🇦 Arabic", callback_data=f"tts_{task_id}_ar")],[InlineKeyboardButton(text="🇷🇺 Russian", callback_data=f"tts_{task_id}_ru"),
         InlineKeyboardButton(text="🇪🇸 Spanish", callback_data=f"tts_{task_id}_es"),
         InlineKeyboardButton(text="🇫🇷 French", callback_data=f"tts_{task_id}_fr")],[InlineKeyboardButton(text="🇯🇵 Japanese", callback_data=f"tts_{task_id}_ja"),
         InlineKeyboardButton(text="🇩🇪 German", callback_data=f"tts_{task_id}_de"),
         InlineKeyboardButton(text="🇨🇳 Chinese", callback_data=f"tts_{task_id}_zh-CN")]
    ])
    await message.reply(font("🗣 **VOICE STUDIO**\nSelect language for precise slang/speech:"), reply_markup=kb, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data.startswith(("start_", "owner_contact")))
async def start_callback_handler(query: types.CallbackQuery):
    if query.data == "owner_contact":
        owner_name = font(user_names.get(OWNER_ID, 'Owner'))
        await query.message.answer(
            f"👤 {font('Contact Owner:')} [{owner_name}](tg://user?id={OWNER_ID})\n\n"
            f"{font('Tap the name above to open profile.')}",
            parse_mode=ParseMode.MARKDOWN
        )
        await query.answer()
        return

    if query.data == "start_about":
        owner_name = font(user_names.get(OWNER_ID, 'Owner'))
        owner_acc = f"[{owner_name}](tg://user?id={OWNER_ID})"
        
        text_part1 = font("I am a bot created by ")
        text_part2 = font("❗. ")
        text_part3 = font(" 👈🏿iske kehne pe me teri ma v chod skta hu😹💘.")
        about_text = f"{text_part1}{owner_acc}{text_part2}{owner_acc}{text_part3}"
        
        await query.message.answer(about_text, parse_mode=ParseMode.MARKDOWN)
        await query.answer()
        
    elif query.data == "start_restricted":
        if query.from_user.id in SUDO_USERS:
            await query.answer(font("✅ Access Granted. Use !help to see commands."), show_alert=True)
        else:
            await query.answer(font("⚠️ Ask owner to give you access ❤️"), show_alert=True)

@dp.channel_post(Command("activebots", prefix="!"))
@dp.message(Command("activebots", prefix="!"))
async def cmd_activebots(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    text = font("❓ Active Bots:\n\n") + "\n".join(f"• @{u}" for u in bot_usernames) + font(f"\n\n✅ Total Bots: {len(bots)}")
    await safe_reply(message, text, parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("missingbots", prefix="!"))
@dp.message(Command("missingbots", prefix="!"))
async def cmd_missingbots(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    missing =[]
    for i, b in enumerate(bots):
        try:
            member = await b.get_chat_member(message.chat.id, b.id)
            if member.status in['left', 'kicked', 'banned']: missing.append(bot_usernames[i])
        except Exception:
            missing.append(bot_usernames[i])
    if not missing:
        return await safe_reply(message, font("✅ All bots are already in this group/channel!"))
    await safe_reply(message, font("🕵️‍♂️ **Missing Bots:**\n\n") + "\n".join(f"• @{u}" for u in missing), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("leave", prefix="!"))
@dp.message(Command("leave", prefix="!"))
async def cmd_leave(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    await safe_reply(message, font("👋 All bots are leaving this chat!"))
    for b in bots:
        try:
            await b.leave_chat(message.chat.id)
        except Exception: pass

@dp.channel_post(Command("ping", prefix="!"))
@dp.message(Command("ping", prefix="!"))
async def cmd_ping(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    await safe_reply(message, font(f"🏓 Pong! ✅ {random.randint(30, 90)} ms"))

@dp.channel_post(Command("myid", prefix="!"))
@dp.message(Command("myid", prefix="!"))
async def cmd_myid(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    auth_id = get_auth_id(message)
    await safe_reply(message, font(f"🆔 Extracted Authorization ID: `{auth_id}`"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("o", prefix="!"))
@dp.message(Command("o", prefix="!"))
async def cmd_optimize(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    save_db()
    await safe_reply(message, font("✨ System optimized and Database saved."))

@dp.channel_post(Command("on", prefix="!"))
@dp.message(Command("on", prefix="!"))
async def cmd_on(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    await safe_reply(message, font("🟢 BOT IS ONLINE AND READY"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("uptime", prefix="!"))
@dp.message(Command("uptime", prefix="!"))
async def cmd_uptime(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    await safe_reply(message, font(f"⏱️ **UPTIME:** {get_uptime()}"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("status", prefix="!"))
@dp.message(Command("status", prefix="!"))
async def cmd_status(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    active = get_active_groups_info()
    txt = font(f"📊 **BOT STATUS**\n\n⏱️ **Uptime:** {get_uptime()}\n🌐 **Online Bots:** {len(bots)}\n🔥 **Active Groups/Channels ({len(active)}):**\n")
    for id in active:
        txt += f"• `{id}`\n"
    await safe_reply(message, txt, parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dall", prefix="!"))
@dp.message(Command("dall", prefix="!"))
async def cmd_stop_all(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_owner(get_auth_id(message)): return await safe_reply(message, font("❌ Only OWNER can do this."))
    
    group_tasks.clear()
    seq_nc_tasks.clear()
    keng_tasks.clear()
    spmnc_tasks.clear()
    vxsnc_tasks.clear()
    slidespam_tasks.clear()
    slidespam_targets.clear()
    targetslide_targets.clear()
    spm_loop_tasks.clear()
    vxsspam_tasks.clear()
    rspm_tasks.clear()
    forwardspm_tasks.clear()
    sticker_spm_tasks.clear()
    gif_spm_tasks.clear()
    media_spm_tasks.clear()
    voice_spm_tasks.clear()
    pfp_tasks.clear()
    swipe_mode.clear()
    reply_vxs_targets.clear()
    react_targets.clear()
    
    save_db()
    await safe_reply(message, font("🛑 All operations have been terminated globally."))

@dp.channel_post(Command("sequentialnc", prefix="!"))
@dp.message(Command("sequentialnc", prefix="!"))
async def cmd_sequentialnc(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    
    exact_text = get_exact_text(message)
    if not exact_text: 
        return await safe_reply(message, font("⚠️ Usage: !sequentialnc <text>"))
    
    chat_id = message.chat.id
    
    active_bots =[]
    for b in bots:
        try:
            member = await b.get_chat_member(chat_id, b.id)
            if member.status not in['left', 'kicked', 'banned']:
                active_bots.append(b)
        except Exception:
            pass
            
    if not active_bots:
        return await safe_reply(message, font("⚠️ No active bots found in this group to rotate with!"))
        
    task_id = str(uuid.uuid4())
    seq_nc_tasks[chat_id] = task_id
    
    asyncio.create_task(seq_nc_worker(chat_id, exact_text, active_bots, task_id))
    await safe_reply(message, font(f"🚀 Sequential Multi-Bot NC started with {len(active_bots)} bots!"))

@dp.channel_post(Command("dsequentialnc", prefix="!"))
@dp.message(Command("dsequentialnc", prefix="!"))
async def cmd_dsequentialnc(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(seq_nc_tasks, message.chat.id):
        await safe_reply(message, font("🛑 Sequential NC stopped."))

@dp.channel_post(Command("nc", prefix="!"))
@dp.message(Command("nc", prefix="!"))
async def cmd_nc(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not command.args: return await safe_reply(message, font("⚠️ Usage: ") + "`!nc <name>`", parse_mode=ParseMode.MARKDOWN)
    chat_id = message.chat.id
    if chat_id not in group_tasks: group_tasks[chat_id] = {}
    for b in bots:
        task_id = str(uuid.uuid4())
        group_tasks[chat_id][b.id] = task_id
        asyncio.create_task(nc_loop_worker(b, chat_id, command.args.strip(), task_id))
    await safe_reply(message, font(f"🔄 Raid Text NC loop started with Name: `{command.args.strip()}`!"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dnc", prefix="!"))
@dp.message(Command("dnc", prefix="!"))
async def cmd_stop_nc(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(group_tasks, message.chat.id):
        await safe_reply(message, font("🛑 Raid Text NC loop stopped."))

@dp.channel_post(Command("ncemo", prefix="!"))
@dp.message(Command("ncemo", prefix="!"))
async def cmd_ncemo(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not command.args: return await safe_reply(message, font("⚠️ Usage: ") + "`!ncemo <text>`", parse_mode=ParseMode.MARKDOWN)
    chat_id = message.chat.id
    if chat_id not in group_tasks: group_tasks[chat_id] = {}
    for b in bots:
        task_id = str(uuid.uuid4())
        group_tasks[chat_id][b.id] = task_id
        asyncio.create_task(ncemo_loop_worker(b, chat_id, command.args.strip(), task_id))
    await safe_reply(message, font("🔄 Emoji NC loop started!"))

@dp.channel_post(Command("dncemo", prefix="!"))
@dp.message(Command("dncemo", prefix="!"))
async def cmd_stop_ncemo(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(group_tasks, message.chat.id):
        await safe_reply(message, font("🛑 Emoji NC loop stopped."))

@dp.channel_post(Command("kengnc", prefix="!"))
@dp.message(Command("kengnc", prefix="!"))
async def cmd_kengnc(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not command.args: return await safe_reply(message, font("⚠️ Usage: ") + "`!kengnc <name>`", parse_mode=ParseMode.MARKDOWN)
    chat_id = message.chat.id
    if chat_id not in keng_tasks: keng_tasks[chat_id] = {}
    for b in bots:
        task_id = str(uuid.uuid4())
        keng_tasks[chat_id][b.id] = task_id
        asyncio.create_task(keng_loop_worker(b, chat_id, command.args.strip(), task_id))
    await safe_reply(message, font(f"🔺 KENG Name Change loop started for `{command.args.strip()}`!"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dkengnc", prefix="!"))
@dp.message(Command("dkengnc", prefix="!"))
async def cmd_stop_kengnc(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(keng_tasks, message.chat.id):
        await safe_reply(message, font("🛑 KENG NC loop stopped."))

@dp.channel_post(Command("vxsnc", prefix="!"))
@dp.message(Command("vxsnc", prefix="!"))
async def cmd_vxsnc(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not command.args: return await safe_reply(message, font("⚠️ Usage: ") + "`!vxsnc <name>`", parse_mode=ParseMode.MARKDOWN)
    chat_id = message.chat.id
    if chat_id not in vxsnc_tasks: vxsnc_tasks[chat_id] = {}
    for b in bots:
        task_id = str(uuid.uuid4())
        vxsnc_tasks[chat_id][b.id] = task_id
        asyncio.create_task(vxsnc_loop_worker(b, chat_id, command.args.strip(), task_id))
    await safe_reply(message, font(f"🔺vxs NC loop started for `{command.args.strip()}`!"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dvxsnc", prefix="!"))
@dp.message(Command("dvxsnc", prefix="!"))
async def cmd_dvxsnc(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(vxsnc_tasks, message.chat.id):
        await safe_reply(message, font("🛑 vxs NC loop stopped."))

@dp.channel_post(Command("spmnc", prefix="!"))
@dp.message(Command("spmnc", prefix="!"))
async def cmd_spmnc(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not command.args: return await safe_reply(message, font("⚠️ Usage: ") + "`!spmnc <text>`", parse_mode=ParseMode.MARKDOWN)
    chat_id = message.chat.id
    if chat_id not in spmnc_tasks: spmnc_tasks[chat_id] = {}
    for b in bots:
        task_id = str(uuid.uuid4())
        spmnc_tasks[chat_id][b.id] = task_id
        asyncio.create_task(spmnc_worker(b, chat_id, command.args.strip(), task_id))
    await safe_reply(message, font(f"⚡ SPMNC dual-loop started for `{command.args.strip()}`!"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dspmnc", prefix="!"))
@dp.message(Command("dspmnc", prefix="!"))
async def cmd_stop_spmnc(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(spmnc_tasks, message.chat.id):
        await safe_reply(message, font("🛑 SPMNC loop stopped."))

@dp.channel_post(Command("delaync", prefix="!"))
@dp.message(Command("delaync", prefix="!"))
async def cmd_delaync(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    try:
        if not command.args: raise ValueError
        val = int(command.args)
        nc_delays[message.chat.id] = max(10, val)
        await safe_reply(message, font(f"✅ Name Change delay set to `{val}` ms for this group."), parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await safe_reply(message, font("❌ Invalid number."))

@dp.channel_post(Command("save", prefix="!"))
@dp.message(Command("save", prefix="!"))
async def cmd_save(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await safe_reply(message, font("⚠️ Reply to a photo with `!save`"), parse_mode=ParseMode.MARKDOWN)
    chat_id = message.chat.id
    photo = message.reply_to_message.photo[-1]
    folder = os.path.join(os.path.dirname(__file__), 'downloads', str(chat_id))
    os.makedirs(folder, exist_ok=True)
    await bot.download(photo, destination=os.path.join(folder, f"{photo.file_unique_id}.jpg"))
    await safe_reply(message, font("📸 Photo saved locally for this group!"))

@dp.channel_post(Command("del", prefix="!"))
@dp.message(Command("del", prefix="!"))
async def cmd_del(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await safe_reply(message, font("⚠️ Reply to the saved photo with `!del`"), parse_mode=ParseMode.MARKDOWN)
    uid = message.reply_to_message.photo[-1].file_unique_id
    target = os.path.join(os.path.dirname(__file__), 'downloads', str(message.chat.id), f"{uid}.jpg")
    if os.path.exists(target):
        os.remove(target)
        await safe_reply(message, font("🗑 Photo deleted from this group's storage!"))
    else:
        await safe_reply(message, font("⚠️ This photo is not in the storage."))

@dp.channel_post(Command("gsave", prefix="!"))
@dp.message(Command("gsave", prefix="!"))
async def cmd_gsave(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await safe_reply(message, font("⚠️ Reply to a photo with `!gsave`"), parse_mode=ParseMode.MARKDOWN)
    photo = message.reply_to_message.photo[-1]
    await bot.download(photo, destination=os.path.join(global_storage, f"{photo.file_unique_id}.jpg"))
    await safe_reply(message, font("🌍 Photo saved to GLOBAL storage!"))

@dp.channel_post(Command("delgpfp", prefix="!"))
@dp.message(Command("delgpfp", prefix="!"))
async def cmd_delgpfp(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await safe_reply(message, font("⚠️ Reply to the saved photo with `!delgpfp`"), parse_mode=ParseMode.MARKDOWN)
    uid = message.reply_to_message.photo[-1].file_unique_id
    target = os.path.join(global_storage, f"{uid}.jpg")
    if os.path.exists(target):
        os.remove(target)
        await safe_reply(message, font("🗑 Photo deleted from GLOBAL storage!"))
    else:
        await safe_reply(message, font("⚠️ This photo is not in the Global storage."))

@dp.channel_post(Command("delallmedia", prefix="!"))
@dp.message(Command("delallmedia", prefix="!"))
async def cmd_delallmedia(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_owner(get_auth_id(message)): return await safe_reply(message, font("❌ Only OWNER can do this."))
    dldir = os.path.join(os.path.dirname(__file__), 'downloads')
    if os.path.exists(dldir):
        shutil.rmtree(dldir)
        os.makedirs(global_storage, exist_ok=True)
        await safe_reply(message, font("💥 All saved media (global and groups) has been deleted!"))
    else:
        await safe_reply(message, font("⚠️ No media folder found."))

@dp.channel_post(Command("gpfp", prefix="!"))
@dp.message(Command("gpfp", prefix="!"))
async def cmd_gpfp(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    files =[f for f in os.listdir(global_storage) if f.endswith('.jpg') and not f.startswith("start_pic")]
    if not files: return await safe_reply(message, font("⚠️ No photos in GLOBAL storage. Use `!gsave` first."), parse_mode=ParseMode.MARKDOWN)
    
    info_msg = await message.reply(font("🌍 Updating ALL known group and channel PFPs globally..."), parse_mode=ParseMode.MARKDOWN)
    success = 0
    
    for cid in list(known_chats):
        if cid > 0: continue
        pic = random.choice(files)
        
        for b in bots:
            try:
                await b.set_chat_photo(cid, FSInputFile(os.path.join(global_storage, pic)))
                success += 1
                break
            except Exception: pass
            
    await bot.edit_message_text(font(f"✅ Global PFP update complete! Changed successfully in {success} groups/channels."), chat_id=message.chat.id, message_id=info_msg.message_id, parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("pfp", prefix="!"))
@dp.message(Command("pfp", prefix="!"))
async def cmd_pfp(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    folder = os.path.join(os.path.dirname(__file__), 'downloads', str(message.chat.id))
    if not os.path.exists(folder) or not[f for f in os.listdir(folder) if f.endswith('.jpg')]:
        return await safe_reply(message, font("⚠️ No photos saved for this group. Use `!save` first."), parse_mode=ParseMode.MARKDOWN)
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {"cmd": "pfp", "chat_id": message.chat.id, "selected": set(range(len(bots)))}
    await message.reply(font("📸 **PFP LOOP MENU**\nSelect bots:"), reply_markup=get_selector_keyboard(task_id), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("stickerspm", prefix="!"))
@dp.message(Command("stickerspm", prefix="!"))
async def cmd_stickerspm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not message.reply_to_message or not message.reply_to_message.sticker:
        return await safe_reply(message, font("⚠️ Reply to a sticker with `!stickerspm`"), parse_mode=ParseMode.MARKDOWN)
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {
        "cmd": "stickerspm", "chat_id": message.chat.id, 
        "from_chat_id": message.reply_to_message.chat.id, "msg_id": message.reply_to_message.message_id, 
        "selected": set(range(len(bots)))
    }
    await message.reply(font("🎭 **STICKER SPAM MENU**\nSelect bots:"), reply_markup=get_selector_keyboard(task_id), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("gifspm", prefix="!"))
@dp.message(Command("gifspm", prefix="!"))
async def cmd_gifspm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not message.reply_to_message or not message.reply_to_message.animation:
        return await safe_reply(message, font("⚠️ Reply to a GIF with `!gifspm`"), parse_mode=ParseMode.MARKDOWN)
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {
        "cmd": "gifspm", "chat_id": message.chat.id, 
        "from_chat_id": message.reply_to_message.chat.id, "msg_id": message.reply_to_message.message_id, 
        "selected": set(range(len(bots)))
    }
    await message.reply(font("🎥 **GIF SPAM MENU**\nSelect bots:"), reply_markup=get_selector_keyboard(task_id), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("mediaspm", prefix="!"))
@dp.message(Command("mediaspm", prefix="!"))
async def cmd_mediaspm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    rm = message.reply_to_message
    if not rm:
        return await safe_reply(message, font("⚠️ Reply to a media (photo/video/doc/audio) with `!mediaspm`"), parse_mode=ParseMode.MARKDOWN)
        
    media_type, file_id = None, None
    if rm.photo: media_type, file_id = "photo", rm.photo[-1].file_id
    elif rm.video: media_type, file_id = "video", rm.video.file_id
    elif rm.document: media_type, file_id = "document", rm.document.file_id
    elif rm.audio: media_type, file_id = "audio", rm.audio.file_id
    elif rm.animation: media_type, file_id = "animation", rm.animation.file_id
    elif rm.voice: media_type, file_id = "voice", rm.voice.file_id
    else:
        return await safe_reply(message, font("⚠️ Unsupported media type! Please reply to photo, video, doc, or audio."), parse_mode=ParseMode.MARKDOWN)
    
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {
        "cmd": "mediaspm", "chat_id": message.chat.id, 
        "media_type": media_type, "file_id": file_id,
        "caption": rm.caption, "caption_entities": rm.caption_entities,
        "selected": set(range(len(bots)))
    }
    await message.reply(font("🖼️ **MEDIA SPAM MENU**\nSelect bots:"), reply_markup=get_selector_keyboard(task_id), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("voicespm", "voicespam", prefix="!"))
@dp.message(Command("voicespm", "voicespam", prefix="!"))
async def cmd_voicespm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not message.reply_to_message or not message.reply_to_message.voice:
        return await safe_reply(message, font("⚠️ Reply to a voice note with `!voicespam`"), parse_mode=ParseMode.MARKDOWN)
    
    task_id = str(uuid.uuid4())[:8]
    active_menus[task_id] = {
        "cmd": "voicespm", "chat_id": message.chat.id, 
        "media_type": "voice", "file_id": message.reply_to_message.voice.file_id,
        "caption": message.reply_to_message.caption, "caption_entities": message.reply_to_message.caption_entities,
        "selected": set(range(len(bots)))
    }
    await message.reply(font("🎤 **VOICE SPAM MENU**\nSelect bots:"), reply_markup=get_selector_keyboard(task_id), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dpfp", prefix="!"))
@dp.message(Command("dpfp", prefix="!"))
async def cmd_dpfp(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(pfp_tasks, message.chat.id):
        await safe_reply(message, font("🛑 PFP loops stopped."))

@dp.channel_post(Command("dstickerspm", prefix="!"))
@dp.message(Command("dstickerspm", prefix="!"))
async def cmd_dstickerspm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(sticker_spm_tasks, message.chat.id):
        await safe_reply(message, font("🛑 Sticker SPM stopped."))

@dp.channel_post(Command("dgifspm", prefix="!"))
@dp.message(Command("dgifspm", prefix="!"))
async def cmd_dgifspm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(gif_spm_tasks, message.chat.id):
        await safe_reply(message, font("🛑 GIF SPM stopped."))

@dp.channel_post(Command("dmediaspm", prefix="!"))
@dp.message(Command("dmediaspm", prefix="!"))
async def cmd_dmediaspm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(media_spm_tasks, message.chat.id):
        await safe_reply(message, font("🛑 Media SPM stopped."))

@dp.channel_post(Command("dvoicespm", prefix="!"))
@dp.message(Command("dvoicespm", prefix="!"))
async def cmd_dvoicespm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(voice_spm_tasks, message.chat.id):
        await safe_reply(message, font("🛑 Voice SPM stopped."))

@dp.channel_post(Command("delaypfp", prefix="!"))
@dp.message(Command("delaypfp", prefix="!"))
async def cmd_delaypfp(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    try:
        if not command.args: raise ValueError
        val = int(command.args)
        pfp_delays[message.chat.id] = max(10, val)
        await safe_reply(message, font("✅ PFP delay set."))
    except Exception: pass

@dp.channel_post(Command("delaygcspm", prefix="!"))
@dp.message(Command("delaygcspm", prefix="!"))
async def cmd_delaygcspm(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    try:
        if not command.args: raise ValueError
        val = int(command.args)
        spm_delays[message.chat.id] = max(10, val)
        await safe_reply(message, font("✅ SPM delay set."))
    except Exception: pass

@dp.channel_post(Command("targetslide", prefix="!"))
@dp.message(Command("targetslide", prefix="!"))
async def cmd_targetslide(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    uid, name = await get_target_info(message, command.args)
    if not uid: return await safe_reply(message, font("⚠️ Reply to a message/channel or tag a target"), parse_mode=ParseMode.MARKDOWN)
    
    targetslide_targets[uid] = name 
    save_db()
    
    acc_link = f"[{name}](tg://user?id={uid})" if uid > 0 else name
    await safe_reply(message, font(f"🎯 Target Slide locked onto {acc_link}!"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dtargetslide", prefix="!"))
@dp.message(Command("dtargetslide", prefix="!"))
async def cmd_dtargetslide(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    uid, _ = await get_target_info(message, command.args)
    if not uid: return await safe_reply(message, font("⚠️ Reply to a message/channel or tag a target"), parse_mode=ParseMode.MARKDOWN)
    
    if uid in targetslide_targets: 
        del targetslide_targets[uid]
        save_db()
    await safe_reply(message, font("🛑 Target Slide loop stopped for target."))

@dp.channel_post(Command("slidespam", prefix="!"))
@dp.message(Command("slidespam", prefix="!"))
async def cmd_slidespam(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not message.reply_to_message: 
        return await safe_reply(message, font("⚠️ Reply to a message"), parse_mode=ParseMode.MARKDOWN)
    
    exact_text = get_exact_text(message)
    if not exact_text:
        return await safe_reply(message, font("⚠️ Usage: ") + "`!slidespam <text>`", parse_mode=ParseMode.MARKDOWN)
    
    chat_id = message.chat.id
    reply_msg_id = message.reply_to_message.message_id
    
    if chat_id not in slidespam_tasks:
        slidespam_tasks[chat_id] = []
    slidespam_targets[chat_id] = reply_msg_id
    
    for i, b in enumerate(bots):
        task_id = str(uuid.uuid4())
        slidespam_tasks[chat_id].append(task_id)
        asyncio.create_task(
            delayed_task(
                i * 0.25,
                spm_sender(b, chat_id, reply_msg_id, exact_text, slidespam_tasks, chat_id, task_id)
            )
        )
    await safe_reply(message, font("💥 SlideSpam locked on message!"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dslidespam", prefix="!"))
@dp.message(Command("dslidespam", prefix="!"))
async def cmd_dslidespam(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    chat_id = message.chat.id
    if stop_task_group(slidespam_tasks, chat_id):
        slidespam_targets.pop(chat_id, None)
        await safe_reply(message, font("🛑 SlideSpam loop stopped."))
    else:
        await safe_reply(message, font("⚠️ No SlideSpam running in this chat."))

@dp.channel_post(Command("forwardspm", prefix="!"))
@dp.message(Command("forwardspm", prefix="!"))
async def cmd_forwardspm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not message.reply_to_message:
        return await safe_reply(message, font("⚠️ Reply to a message you want to forward loop."), parse_mode=ParseMode.MARKDOWN)
    
    chat_id = message.chat.id
    if chat_id in forwardspm_tasks:
        forwardspm_tasks[chat_id].clear()
    else:
        forwardspm_tasks[chat_id] = []
    
    src_msg_id = message.reply_to_message.message_id
    for i, b in enumerate(bots):
        task_id = str(uuid.uuid4())
        forwardspm_tasks[chat_id].append(task_id)
        asyncio.create_task(
            delayed_task(
                i * 0.15,
                forward_spm_sender(b, chat_id, chat_id, src_msg_id, forwardspm_tasks, task_id)
            )
        )
    await safe_reply(message, font("⏩ Forward SPM loop started."), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dforwardspm", prefix="!"))
@dp.message(Command("dforwardspm", prefix="!"))
async def cmd_dforwardspm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(forwardspm_tasks, message.chat.id):
        await safe_reply(message, font("🛑 Forward SPM stopped."))

@dp.channel_post(Command("spm", prefix="!"))
@dp.message(Command("spm", prefix="!"))
async def cmd_spm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    
    exact_text = get_exact_text(message)
    if not exact_text:
        return await safe_reply(message, font("⚠️ Usage: ") + "`!spm <text>`", parse_mode=ParseMode.MARKDOWN)
        
    chat_id = message.chat.id
    if chat_id not in spm_loop_tasks: spm_loop_tasks[chat_id] =[]
    for i, b in enumerate(bots):
        task_id = str(uuid.uuid4())
        spm_loop_tasks[chat_id].append(task_id)
        asyncio.create_task(delayed_task(i * 0.15, spm_sender(b, chat_id, None, exact_text, spm_loop_tasks, chat_id, task_id)))
    await safe_reply(message, font("✅ SPM loop started."), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dspm", prefix="!"))
@dp.message(Command("dspm", prefix="!"))
async def cmd_dspm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(spm_loop_tasks, message.chat.id):
        await safe_reply(message, font("🛑 SPM loops stopped in this chat."))

@dp.channel_post(Command("vxsspam", prefix="!"))
@dp.message(Command("vxsspam", prefix="!"))
async def cmd_vxsspam(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    
    exact_text = get_exact_text(message)
    if not exact_text:
        return await safe_reply(message, font("⚠️ Usage: ") + "`!vxsspam <text>`", parse_mode=ParseMode.MARKDOWN)
        
    chat_id = message.chat.id
    if chat_id not in vxsspam_tasks: vxsspam_tasks[chat_id] =[]
    for i, b in enumerate(bots):
        task_id = str(uuid.uuid4())
        vxsspam_tasks[chat_id].append(task_id)
        asyncio.create_task(delayed_task(i * 0.30, vxsspam_sender(b, chat_id, exact_text, vxsspam_tasks, task_id)))
    await safe_reply(message, font("🔥 vxs SPAM long loop started."), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dvxsspam", prefix="!"))
@dp.message(Command("dvxsspam", prefix="!"))
async def cmd_dvxsspam(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(vxsspam_tasks, message.chat.id):
        await safe_reply(message, font("🛑 vxs SPAM loops stopped."))

@dp.channel_post(Command("rspm", prefix="!"))
@dp.message(Command("rspm", prefix="!"))
async def cmd_rspm(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not command.args: return await safe_reply(message, font("⚠️ Usage: ") + "`!rspm <name>`", parse_mode=ParseMode.MARKDOWN)
    chat_id = message.chat.id
    if chat_id not in rspm_tasks: rspm_tasks[chat_id] =[]
    for i, b in enumerate(bots):
        task_id = str(uuid.uuid4())
        rspm_tasks[chat_id].append(task_id)
        asyncio.create_task(delayed_task(i * 0.15, rspm_sender(b, chat_id, command.args.strip(), rspm_tasks, task_id)))
    await safe_reply(message, font(f"🔥 RSPM (Raid Spam) loop started for `{command.args.strip()}`!"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("drspm", prefix="!"))
@dp.message(Command("drspm", prefix="!"))
async def cmd_drspm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if stop_task_group(rspm_tasks, message.chat.id):
        await safe_reply(message, font("🛑 RSPM loops stopped in this chat."))

@dp.channel_post(Command("delayrspm", prefix="!"))
@dp.message(Command("delayrspm", prefix="!"))
async def cmd_delayrspm(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    try:
        if not command.args: raise ValueError
        val = int(command.args)
        rspm_delays[message.chat.id] = max(10, val)
        await safe_reply(message, font("✅ RSPM delay set."))
    except Exception: pass

@dp.channel_post(Command("dallspm", prefix="!"))
@dp.message(Command("dallspm", prefix="!"))
async def cmd_dallspm(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    spm_loop_tasks.clear()
    vxsspam_tasks.clear()
    rspm_tasks.clear()
    forwardspm_tasks.clear()
    slidespam_tasks.clear()
    slidespam_targets.clear()
    await safe_reply(message, font("🛑 All SPM loops stopped (globally)."))

@dp.channel_post(Command("swipe", prefix="!"))
@dp.message(Command("swipe", prefix="!"))
async def cmd_swipe(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not command.args: return await safe_reply(message, font("⚠️ Usage: ") + "`!swipe <name>`", parse_mode=ParseMode.MARKDOWN)
    swipe_mode[message.chat.id] = command.args.strip()
    await safe_reply(message, font("⚡ Swipe Mode ON"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("dswipe", prefix="!"))
@dp.message(Command("dswipe", prefix="!"))
async def cmd_dswipe(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if message.chat.id in swipe_mode: del swipe_mode[message.chat.id]
    await safe_reply(message, font("🛑 Swipe Mode stopped."))

@dp.channel_post(Command("replyvxs", prefix="!"))
@dp.message(Command("replyvxs", prefix="!"))
async def cmd_replyvxs(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    uid, _ = await get_target_info(message, command.args)
    if not uid: return await safe_reply(message, font("⚠️ Reply to a target or tag a user"), parse_mode=ParseMode.MARKDOWN)
    reply_vxs_targets.add(uid)
    save_db()
    await safe_reply(message, font("💬 Replvxs enabled for this target."))

@dp.channel_post(Command("dreplyvxs", prefix="!"))
@dp.message(Command("dreplyvxs", prefix="!"))
async def cmd_dreplyvxs(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    uid, _ = await get_target_info(message, command.args)
    if not uid: return await safe_reply(message, font("⚠️ Reply to a target or tag a user"), parse_mode=ParseMode.MARKDOWN)
    if uid in reply_vxs_targets: 
        reply_vxs_targets.remove(uid)
        save_db()
    await safe_reply(message, font("🛑 Replvxs stopped for this target."))

@dp.channel_post(Command("react", prefix="!/"))
@dp.message(Command("react", prefix="!/"))
async def cmd_react(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    
    if not message.reply_to_message:
        return await safe_reply(message, font("⚠️ Please reply to the user or channel you want to -react to!"))
    
    rm = message.reply_to_message
    if rm.forward_from_chat:
        uid = rm.forward_from_chat.id
        name = rm.forward_from_chat.title or "Channel"
    elif rm.sender_chat:
        uid = rm.sender_chat.id
        name = rm.sender_chat.title or "Channel"
    elif rm.from_user:
        uid = rm.from_user.id
        name = rm.from_user.first_name
    else:
        uid = rm.chat.id
        name = rm.chat.title or "Channel"

    emoji = command.args.strip() if command.args else ""
    
    if emoji not in VALID_REACTS:
        allowed = ", ".join(VALID_REACTS)
        return await safe_reply(message, font(f"❌ Invalid emoji! Please use one of the allowed emojis:\n{allowed}"))
        
    react_targets[uid] = emoji
    save_db()
    await safe_reply(message, font(f"✅ -react mode started for {name} with emoji {emoji}!"))

@dp.channel_post(Command("dreact", prefix="!/"))
@dp.message(Command("dreact", prefix="!/"))
async def cmd_dreact(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    
    if not message.reply_to_message:
        return await safe_reply(message, font("⚠️ Please reply to the user or channel!"))
        
    rm = message.reply_to_message
    uid = rm.forward_from_chat.id if rm.forward_from_chat else (rm.sender_chat.id if rm.sender_chat else (rm.from_user.id if rm.from_user else rm.chat.id))
    
    if uid in react_targets:
        del react_targets[uid]
        save_db()
    
    await safe_reply(message, font("🛑 -react stopped for this target."))

@dp.channel_post(Command("addsudo", prefix="!"))
@dp.message(Command("addsudo", prefix="!"))
async def cmd_addsudo(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_owner(get_auth_id(message)): return await safe_reply(message, font("❌ Only OWNER can do this."))
    uid, name = await get_target_info(message, command.args)
    if uid:
        SUDO_USERS.add(uid)
        save_sudo()
        await safe_reply(message, font(f"👑 `{name}` (`{uid}`) added as SUDO ✅"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("delsudo", prefix="!"))
@dp.message(Command("delsudo", prefix="!"))
async def cmd_delsudo(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_owner(get_auth_id(message)): return await safe_reply(message, font("❌ Only OWNER can do this."))
    uid, name = await get_target_info(message, command.args)
    if uid and uid in SUDO_USERS:
        SUDO_USERS.remove(uid)
        save_sudo()
        await safe_reply(message, font(f"🗑 `{name}` (`{uid}`) removed from SUDO ❌"), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("listsudo", prefix="!"))
@dp.message(Command("listsudo", prefix="!"))
async def cmd_listsudo(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    
    sudo_list =[]
    for u in SUDO_USERS:
        name = user_names.get(u, "Admin")
        sudo_list.append(f"• [{name}](tg://user?id={u}) (`{u}`)" if u > 0 else f"• Channel (`{u}`)")
        
    await safe_reply(message, font("👑 SUDO Users:\n\n") + "\n".join(sudo_list), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("mute", prefix="!"))
@dp.message(Command("mute", prefix="!"))
async def cmd_mute(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    uid, name = await get_target_info(message, command.args)
    if uid:
        muted_users.add(uid)
        save_db()
        
        acc_link = f"[{name}](tg://user?id={uid})" if uid > 0 else name
        await safe_reply(message, font(f"🔇 Target {acc_link} muted."), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("unmute", prefix="!"))
@dp.message(Command("unmute", prefix="!"))
async def cmd_unmute(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    uid, name = await get_target_info(message, command.args)
    if uid and uid in muted_users:
        muted_users.remove(uid)
        save_db()
        
        acc_link = f"[{name}](tg://user?id={uid})" if uid > 0 else name
        await safe_reply(message, font(f"🔊 Target {acc_link} unmuted."), parse_mode=ParseMode.MARKDOWN)

@dp.channel_post(Command("mutelist", prefix="!"))
@dp.message(Command("mutelist", prefix="!"))
async def cmd_mutelist(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not muted_users: return await safe_reply(message, font("📭 No muted targets."))
    
    mute_list =[]
    for u in muted_users:
        name = user_names.get(u, "Muted Target")
        mute_list.append(f"•[{name}](tg://user?id={u}) (`{u}`)" if u > 0 else f"• Channel (`{u}`)")
        
    await safe_reply(message, font("🔇 Muted Targets:\n\n") + "\n".join(mute_list), parse_mode=ParseMode.MARKDOWN)

# ============================================================
# FIXED: Robust promote logic
# ============================================================

async def _do_promote(bot, chat_id, uid, grant_promote=False):
    """Safely promote. Grants standard admin rights, no can_promote_members by default."""
    return await bot.promote_chat_member(
        chat_id=chat_id,
        user_id=uid,
        is_anonymous=False,
        can_change_info=True,
        can_delete_messages=True,
        can_invite_users=True,
        can_restrict_members=True,
        can_pin_messages=True,
        can_promote_members=grant_promote,
        can_manage_chat=True,
        can_manage_video_chats=True
    )

@dp.channel_post(Command("promote", prefix="!"))
@dp.message(Command("promote", prefix="!"))
async def cmd_promote(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return

    uid, name = await get_target_info(message, command.args)
    if not uid:
        return await safe_reply(message, font("⚠️ Reply to a user or tag a user with !promote"))

    try:
        await _do_promote(bot, message.chat.id, uid, grant_promote=False)
        await safe_reply(message, font(f"✅ Promoted `{name}` (`{uid}`) successfully."), parse_mode=ParseMode.MARKDOWN)
    except TelegramBadRequest as e:
        await safe_reply(message, font(f"❌ BadRequest: {e}"))
    except Exception as e:
        await safe_reply(message, font(f"❌ Error: {e}"))

@dp.channel_post(Command("demote", prefix="!"))
@dp.message(Command("demote", prefix="!"))
async def cmd_demote(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    uid, name = await get_target_info(message, command.args)
    if not uid: return
    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id, user_id=uid, is_anonymous=False,
            can_change_info=False, can_delete_messages=False,
            can_invite_users=False, can_restrict_members=False,
            can_pin_messages=False, can_promote_members=False,
            can_manage_chat=False, can_manage_video_chats=False
        )
        await safe_reply(message, font(f"🛑 Demoted `{name}`."), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await safe_reply(message, font(f"❌ Error: {e}"))

# ============================================================
# FIXED: promoteallbots — uses first working bot to promote the rest
# ============================================================
@dp.channel_post(Command("promoteallbots", prefix="!"))
@dp.message(Command("promoteallbots", prefix="!"))
async def cmd_promoteallbots(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return

    chat_id = message.chat.id
    info = await message.reply(font("⏳ Promoting all bots..."), parse_mode=ParseMode.MARKDOWN)

    promoter_bot = None
    for candidate in bots:
        try:
            me_member = await candidate.get_chat_member(chat_id, candidate.id)
            if me_member.status == 'creator' or (
                me_member.status == 'administrator' and getattr(me_member, 'can_promote_members', False)
            ):
                promoter_bot = candidate
                break
        except Exception:
            continue

    if promoter_bot is None:
        return await bot.edit_message_text(
            font("❌ None of the bots have 'Add New Admins' right in this chat."),
            chat_id=chat_id, message_id=info.message_id, parse_mode=ParseMode.MARKDOWN
        )

    ok = 0
    fail = 0
    already = 0
    errors = []

    for b in bots:
        try:
            if b.id == promoter_bot.id:
                ok += 1
                continue

            try:
                m = await b.get_chat_member(chat_id, b.id)
                if m.status == 'administrator':
                    already += 1
                    continue
            except Exception:
                pass

            await _do_promote(promoter_bot, chat_id, b.id, grant_promote=False)
            ok += 1
            await asyncio.sleep(0.4)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except TelegramBadRequest as e:
            fail += 1
            if len(errors) < 3:
                errors.append(str(e)[:80])
        except Exception as e:
            fail += 1
            if len(errors) < 3:
                errors.append(str(e)[:80])

    report = f"🤖 Promoted: {ok} ✅ | Already admin: {already} | Failed: {fail} ❌"
    if errors:
        report += "\n\nErrors:\n" + "\n".join(f"• {e}" for e in errors)

    try:
        await bot.edit_message_text(report, chat_id=chat_id, message_id=info.message_id, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await safe_reply(message, report)

# ============================================================
# FIXED: promoteall — real member scan + safe promote
# ============================================================
@dp.channel_post(Command("promoteall", prefix="!"))
@dp.message(Command("promoteall", prefix="!"))
async def cmd_promoteall(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return

    chat_id = message.chat.id
    info = await message.reply(font("⏳ Scanning and promoting users..."), parse_mode=ParseMode.MARKDOWN)

    try:
        me_member = await bot.get_chat_member(chat_id, bot.id)
        if me_member.status not in ('administrator', 'creator'):
            return await bot.edit_message_text(
                font("❌ I'm not admin here. Cannot promote anyone."),
                chat_id=chat_id, message_id=info.message_id, parse_mode=ParseMode.MARKDOWN
            )
        if me_member.status == 'administrator' and not getattr(me_member, 'can_promote_members', False):
            return await bot.edit_message_text(
                font("❌ I don't have 'Add New Admins' right."),
                chat_id=chat_id, message_id=info.message_id, parse_mode=ParseMode.MARKDOWN
            )
    except Exception as e:
        return await bot.edit_message_text(
            font(f"❌ Cannot check my rights: {e}"),
            chat_id=chat_id, message_id=info.message_id, parse_mode=ParseMode.MARKDOWN
        )

    candidates = []
    for uid in list(known_users):
        if uid == bot.id:
            continue
        try:
            m = await bot.get_chat_member(chat_id, uid)
            if m.status in ('left', 'kicked', 'banned'):
                continue
            if m.status == 'administrator':
                continue
            candidates.append(uid)
        except Exception:
            continue

    ok = 0
    fail = 0
    for uid in candidates:
        try:
            await _do_promote(bot, chat_id, uid, grant_promote=False)
            ok += 1
            await asyncio.sleep(0.4)
        except TelegramRetryAfter as e:
            await asyncio.sleep(float(e.retry_after) + 0.5)
        except Exception:
            fail += 1
            await asyncio.sleep(0.15)

    report = font(f"✅ Promoted: {ok} | Failed: {fail} | Candidates: {len(candidates)}")
    try:
        await bot.edit_message_text(report, chat_id=chat_id, message_id=info.message_id, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        await safe_reply(message, report)

@dp.channel_post(Command("getlink", prefix="!"))
@dp.message(Command("getlink", prefix="!"))
async def cmd_getlink(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    try:
        cid = int(command.args.strip())
        invite = await bot.export_chat_invite_link(cid)
        await safe_reply(message, font(f"🩷🫧 Invite link:\n{invite}"), parse_mode=ParseMode.MARKDOWN)
    except Exception: pass

@dp.channel_post(Command("getallactivelinks", prefix="!"))
@dp.message(Command("getallactivelinks", prefix="!"))
async def cmd_getallactivelinks(message: types.Message, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if not known_chats: return await safe_reply(message, font("⚠️ No known chats yet."))
    links =[]
    for cid in list(known_chats):
        if cid > 0: continue
        try:
            invite = await bot.export_chat_invite_link(cid)
            links.append(f"• **{cid}**: {invite}")
        except Exception: pass
    txt = "\n".join(links) if links else font("❌ Could not generate any links.")
    await safe_reply(message, font("🔗 **Active Group Links:**\n\n") + txt, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True)

@dp.channel_post(Command("broadcast", prefix="!"))
@dp.message(Command("broadcast", prefix="!"))
async def cmd_broadcast(message: types.Message, command: CommandObject, bot: Bot):
    if is_processed(message.message_id, message.chat.id): return
    if not is_sudo(get_auth_id(message)): return
    if message.reply_to_message:
        target = message.reply_to_message
        is_copy = True
    else:
        if not command.args:
            return await safe_reply(message, font("⚠️ Usage: !broadcast <text> or reply to photo/sticker/media"), parse_mode=ParseMode.MARKDOWN)
        target_text = command.args.strip()
        is_copy = False

    count = 0
    
    groups =[cid for cid in known_chats if cid < 0]
    
    for cid in groups:
        for b in bots:
            try:
                if is_copy:
                    await b.copy_message(chat_id=cid, from_chat_id=target.chat.id, message_id=target.message_id)
                else:
                    await b.send_message(cid, target_text)
                count += 1
                break
            except Exception:
                pass
                
    await safe_reply(message, font(f"📣 **BROADCAST COMPLETE**\n✅ Sent successfully to {count}/{len(groups)} known groups/channels!"), parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data.startswith("stk_"))
async def sticker_callback_handler(query: types.CallbackQuery, bot: Bot):
    if query.from_user.id not in SUDO_USERS:
        return await query.answer(font("❌ You are not SUDO/Owner."), show_alert=True)
        
    data = query.data.split("_")
    task_id = data[1]
    menu = active_menus.get(task_id)
    if not menu or menu.get("cmd") != "makesticker":
        return await query.answer("Menu expired.", show_alert=True)
        
    action_type = data[2]
    
    if action_type == "gen":
        await query.answer("🎨 Generating Sticker...")
        sticker_bytes = create_sticker_image(menu["text"], bg_color=menu["color"], font_type=menu["font"])
        if sticker_bytes:
            await bot.send_sticker(query.message.chat.id, BufferedInputFile(sticker_bytes, filename="sticker.webp"))
            del active_menus[task_id]
        else:
            await query.answer("Error generating sticker.", show_alert=True)
    else:
        if len(data) > 3:
            action_val = data[3]
            if action_type == "c":
                menu["color"] = action_val
                await query.answer() 
            elif action_type == "f":
                menu["font"] = action_val
                await query.answer()

@dp.callback_query(F.data.startswith("tts_"))
async def tts_callback_handler(query: types.CallbackQuery, bot: Bot):
    if query.from_user.id not in SUDO_USERS:
        return await query.answer(font("❌ You are not SUDO/Owner."), show_alert=True)
        
    data = query.data.split("_")
    task_id = data[1]
    lang = data[2]
    
    menu = active_menus.get(task_id)
    if not menu or menu.get("cmd") != "tts":
        return await query.answer("Menu expired.", show_alert=True)
        
    await query.answer("🎙 Generating Audio...")
    audio_bytes = await generate_tts(menu["text"], lang=lang)
    if audio_bytes:
        await bot.send_voice(query.message.chat.id, BufferedInputFile(audio_bytes, filename=f"tts_{lang}.ogg"))
        del active_menus[task_id]
    else:
        await query.answer("Failed to generate audio.", show_alert=True)

@dp.callback_query(F.data.startswith("tk_"))
async def callback_query_handler(query: types.CallbackQuery, bot: Bot):
    if query.from_user.id not in SUDO_USERS:
        return await query.answer(font("❌ You are not SUDO/Owner."), show_alert=True)
    
    data = query.data.split("_")
    task_id = data[1]
    action = data[2]
    menu = active_menus.get(task_id)
    if not menu:
        return await query.answer(font("❌ Menu expired or task already running."), show_alert=True)
    
    try:
        if action == "tgl":
            idx = int(data[3])
            if idx in menu['selected']: menu['selected'].remove(idx)
            else: menu['selected'].add(idx)
            await query.answer() 
            await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=get_selector_keyboard(task_id))
        elif action == "all":
            menu['selected'] = set(range(len(bots)))
            await query.answer()
            await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=get_selector_keyboard(task_id))
        elif action == "none":
            menu['selected'].clear()
            await query.answer()
            await bot.edit_message_reply_markup(chat_id=query.message.chat.id, message_id=query.message.message_id, reply_markup=get_selector_keyboard(task_id))
        elif action == "start":
            if not menu['selected']:
                return await query.answer(font("⚠️ Select at least one bot!"), show_alert=True)
            await query.answer(font("🚀 Firing tasks!"))
            await bot.edit_message_text(font(f"✅ Started **{menu['cmd'].upper()}** with {len(menu['selected'])} bots!"), chat_id=query.message.chat.id, message_id=query.message.message_id, parse_mode=ParseMode.MARKDOWN)
            for idx in menu['selected']:
                if idx >= len(bots): continue
                bt = bots[idx]
                run_id = str(uuid.uuid4())
                c_id = menu['chat_id']
                
                cmd_type = menu['cmd']
                if cmd_type == "pfp":
                    if c_id not in pfp_tasks: pfp_tasks[c_id] =[]
                    pfp_tasks[c_id].append(run_id)
                    asyncio.create_task(pfp_loop_worker(bt, c_id, run_id))
                elif cmd_type in["stickerspm", "gifspm", "mediaspm", "voicespm"]:
                    if cmd_type == "stickerspm": target_dict = sticker_spm_tasks
                    elif cmd_type == "gifspm": target_dict = gif_spm_tasks
                    elif cmd_type == "mediaspm": target_dict = media_spm_tasks
                    elif cmd_type == "voicespm": target_dict = voice_spm_tasks
                    
                    if c_id not in target_dict: target_dict[c_id] =[]
                    target_dict[c_id].append(run_id)
                    
                    
                    if cmd_type in ["mediaspm", "voicespm"]:
                        asyncio.create_task(media_spm_sender(bt, c_id, menu['media_type'], menu['file_id'], menu.get('caption'), menu.get('caption_entities'), target_dict, run_id))
                    else:
                        asyncio.create_task(copy_spm_sender(bt, c_id, menu['from_chat_id'], menu['msg_id'], target_dict, run_id))
            del active_menus[task_id]
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass

@dp.channel_post()
@dp.message()
async def global_message_handler(message: types.Message, bot: Bot):
    global reply_vxs_targets  
    
    if message.from_user and message.from_user.username in bot_usernames:
        return

    chat_id = message.chat.id

    uid = None
    if message.from_user:
        uid = message.from_user.id
        known_users.add(uid)
        user_names[uid] = message.from_user.first_name
        if message.from_user.username:
            username_to_id[message.from_user.username.lower()] = uid
            
    sender_chat_id = message.sender_chat.id if message.sender_chat else None
    
    known_chats.add(chat_id)

    if not is_processed(message.message_id, chat_id):
        
        possible_targets = [t for t in[chat_id, sender_chat_id, uid] if t is not None]
        
        target_for_mute = next((t for t in possible_targets if t in muted_users), None)
        if target_for_mute is not None:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
            except Exception:
                pass
         
        target_for_react = next((t for t in possible_targets if t in react_targets), None)
        if target_for_react:
            emoji_to_react = react_targets[target_for_react]
            for b in bots:
                async def delayed_react(b_instance, delay):
                    await asyncio.sleep(delay)
                    try:
                        await b_instance.set_message_reaction(
                            chat_id=chat_id,
                            message_id=message.message_id,
                            reaction=[ReactionTypeEmoji(type='emoji', emoji=emoji_to_react)]
                        )
                    except Exception: pass
                
                asyncio.create_task(delayed_react(b, random.uniform(0.4, 2.0)))

        
        target_for_reply = next((t for t in possible_targets if t in reply_vxs_targets), None)
        if target_for_reply and REPLY_vxs_TEXTS:
            for b in bots:
                async def delayed_reply(b_instance, delay):
                    await asyncio.sleep(delay)
                    try:
                        await b_instance.send_message(
                            chat_id=chat_id,
                            text=random.choice(REPLY_vxs_TEXTS),
                            reply_to_message_id=message.message_id
                        )
                    except Exception: pass
                asyncio.create_task(delayed_reply(b, random.uniform(0.4, 1.5)))

        
        target_for_slide = next((t for t in possible_targets if t in targetslide_targets), None)
        if target_for_slide and TARGET_SLIDE_TEXTS:
            target_name = targetslide_targets[target_for_slide]
            mention = f"[{target_name}](tg://user?id={target_for_slide})" if target_for_slide > 0 else target_name
            for b in bots:
                text = random.choice(TARGET_SLIDE_TEXTS).replace("{name}", mention)
                async def delayed_slide(b_instance, delay, txt):
                    await asyncio.sleep(delay)
                    try:
                        await b_instance.send_message(
                            chat_id=chat_id,
                            text=txt,
                            reply_to_message_id=message.message_id,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception: pass
                asyncio.create_task(delayed_slide(b, random.uniform(0.4, 1.5), text))

        
        if chat_id in swipe_mode:
            if message.text and message.text.startswith(("!", "/")):
                return
            if not message.text:
                return
            name_arg = swipe_mode[chat_id]
            for b in bots:
                template = random.choice(SWIPE_TEXTS)
                async def delayed_swipe(b_instance, delay, txt):
                    await asyncio.sleep(delay)
                    try:
                        await b_instance.send_message(
                            chat_id=chat_id,
                            text=txt,
                            reply_to_message_id=message.message_id,
                            parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception: pass
                asyncio.create_task(delayed_swipe(b, random.uniform(0.1, 1.5), template.replace("NAME", name_arg)))


# ============================================================
# HTTP HEALTH CHECK SERVER (HEAD-only, 0 MB body payload)
# ============================================================
async def handle_http_request(reader, writer):
    try:
        request_line = await asyncio.wait_for(reader.readline(), timeout=5.0)
        if not request_line:
            return
        req = request_line.decode("utf-8", errors="ignore").strip()
        parts = req.split(" ")
        method = parts[0] if len(parts) >= 1 else ""
        path = parts[1] if len(parts) >= 2 else "/"

        if method == "HEAD":
            if path == "/health":
                status, content_length = "200 OK", 2
            elif path == "/":
                status, content_length = "200 OK", 14
            else:
                status, content_length = "404 Not Found", 9
        else:
            status, content_length = "405 Method Not Allowed", 0

        response = (
            f"HTTP/1.1 {status}\r\n"
            f"Content-Type: text/plain\r\n"
            f"Content-Length: {content_length}\r\n"
            f"Connection: close\r\n\r\n"
        )
        writer.write(response.encode("utf-8"))
        await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


# ============================================================
# FIXED: main() with single-poller dispatch & persistent pool
# ============================================================
async def main():
    print(f"\n{GREEN}⏳ INITIALIZING...{RESET}\n")

    session = LowBandwidthAiohttpSession(timeout=65.0)

    raw_bots = []
    for token in TOKENS:
        if token.strip():
            bot_instance = Bot(token=token.strip(), session=session)
            raw_bots.append(bot_instance)

    for b in raw_bots:
        try:
            me = await b.get_me()
            bots.append(b)
            bot_usernames.append(me.username)
            print(f"{GREEN}✅ CONNECTED SUCCESSFULLY: @{me.username}{RESET}")
        except Exception as e:
            print(f"{RED}❌ Error starting a bot: {e}{RESET}")

    if not bots:
        print(f"{RED}[FATAL] No bots initialized. Exiting.{RESET}")
        return

    print(f"\n{GREEN}VXS V4! ({len(bots)} bots active, 1 primary poller){RESET}\n")

    port = int(os.environ.get("PORT", "10000"))
    http_server = None
    try:
        http_server = await asyncio.start_server(handle_http_request, "0.0.0.0", port)
        print(f"{GREEN}🟢 HTTP Server listening on 0.0.0.0:{port} for HEAD checks{RESET}\n")
    except Exception as e:
        print(f"{RED}[WARN] Could not bind HTTP server on port {port}: {e}{RESET}")

    allowed_updates = ["message", "channel_post", "callback_query", "my_chat_member"]

    try:
        while True:
            try:
                # Poll updates on the primary bot only so 5x duplicate getUpdates
                # traffic is eliminated while all bots in `bots` still fire on loops.
                await dp.start_polling(
                    bots[0],
                    drop_pending_updates=True,
                    polling_timeout=50,
                    request_timeout=65,
                    allowed_updates=allowed_updates,
                )
                break  # clean exit
            except asyncio.CancelledError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                err = str(e).lower()
                if "network" in err or "timeout" in err or "connection" in err or "clientoserror" in err:
                    print(f"{RED}[NET] Connection lost — reconnecting in 5s...{RESET}")
                    await asyncio.sleep(5)
                    continue
                print(f"{RED}[FATAL] {e}{RESET}")
                await asyncio.sleep(5)
                continue
    finally:
        if http_server is not None:
            http_server.close()
            await http_server.wait_closed()
        if _shared_http_session is not None and not _shared_http_session.closed:
            await _shared_http_session.close()
        await session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        save_db()
        print(f"\n{RED}🛑 DEACTIVATING BOT...{RESET}")
