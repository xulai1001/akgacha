#encoding:utf-8
import os, random, re, pprint, json, math
from io import BytesIO
from PIL import Image
from collections import defaultdict

from hoshino import Service, priv, util
from hoshino.typing import *
from .akgacha import Gacha

img_path = "./images"
char_data = json.load(open("character_table.json", encoding="utf-8"))
gacha_data = json.load(open("config.json", encoding="utf-8"))

sv_help = '''
[@Bot方舟十连] 明日方舟抽卡
[@Bot方舟来一井] 龙门币算什么，看我18w合成玉
[查看方舟卡池] 当前卡池信息
[切换方舟卡池] 更改卡池
'''.strip()
sv = Service('akgacha', help=sv_help)

group_pool = {}
try:
    group_pool = json.load(open("group_pool.json", encoding="utf-8"))
except FileNotFoundError: pass
    
def save_group_pool():
    with open("group_pool.json", encoding="utf-8") as f:
        json.dump(group_pool, f, ensure_ascii=False)
        
async def gacha_info(bot, ev: CQEvent):
    await bot.send(ev, "查看卡池命令")
    
async def set_pool(bot, ev: CQEvent):
    await bot.send(ev, "设置卡池命令")
    
async def gacha_10(bot, ev: CQEvent):
    await bot.send(ev, "10连", at_sender=True)

async def gacha_300(bot, ev: CQEvent):
    await bot.send(ev, "抽一井", at_sender=True)
    