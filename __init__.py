#encoding:utf-8
import os, random, re, pprint, json, math
from io import BytesIO
from PIL import Image
from collections import defaultdict

from hoshino import R, Service, priv, util
from hoshino.typing import *
from .akgacha import Gacha

working_path = "hoshino/modules/akgacha/"
img_path = "./images"
char_data = json.load(open(working_path + "character_table.json", encoding="utf-8"))
gacha_data = json.load(open(working_path + "config.json", encoding="utf-8"))

sv_help = '''
[@Bot方舟十连] 明日方舟抽卡
[@Bot方舟来一井] 龙门币算什么，看我18w合成玉
[查看方舟卡池] 当前卡池信息
[切换方舟卡池] 更改卡池
'''.strip()
sv = Service('akgacha', help_=sv_help, enable_on_default=True)

group_banner = {}
try:
    group_banner = json.load(open(working_path + "group_banner.json", encoding="utf-8"))
except FileNotFoundError: pass
    
def save_group_pool():
    with open(working_path + "group_banner.json", "w", encoding="utf-8") as f:
        json.dump(group_banner, f, ensure_ascii=False)
        
@sv.on_fullmatch(("查看方舟卡池"))
async def gacha_info(bot, ev: CQEvent):
    gid = str(ev.group_id)
    if not gid in group_banner:
        group_banner[gid] = "普池"
    banner = group_banner[gid]
    gacha = Gacha()
    gacha.set_banner(banner)
    line = gacha.explain_banner()
    await bot.send(ev, line)

@sv.on_prefix(("切换方舟卡池"))
async def set_pool(bot, ev: CQEvent):
    name = util.normalize_str(ev.message.extract_plain_text())
    if not name:
        # 列出当前卡池
        lines = ["当期卡池:"] + list(gacha_data["banners"].keys()) + ["使用命令 切换方舟卡池 x（x为卡池名）进行设置"]
        await bot.finish(ev, "\n".join(lines))
    else:
        if name in gacha_data["banners"].keys():
            gid = str(ev.group_id)
            group_banner[gid] = name
            save_group_pool()
            await bot.send(ev, f"卡池已经切换为 {name}", at_sender=True)
            await gacha_info(bot, ev)
        else:
            await bot.finish(ev, f"没找到卡池: {name}")

@sv.on_prefix(("方舟十连"), only_to_me=True)
async def gacha_10(bot, ev: CQEvent):
    gid = str(ev.group_id)
    b = group_banner.get(gid, "普池")
    g = Gacha()
    g.set_banner(b)
    result = g.ten_pull()
    await bot.send(ev, g.summarize_tenpull(result), at_sender=True)

@sv.on_prefix(("方舟来一井"), only_to_me=True)
async def gacha_300(bot, ev: CQEvent):
    gid = str(ev.group_id)
    b = group_banner.get(gid, "普池")
    g = Gacha()
    g.set_banner(b)
    for i in range(0, 30):
        g.ten_pull()
    await bot.send(ev, g.summarize(), at_sender=True)
