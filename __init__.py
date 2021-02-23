#encoding:utf-8
import os, random, re, pprint, json, math, asyncio
from io import BytesIO
from PIL import Image
from collections import defaultdict
from datetime import datetime
from hoshino import R, Service, priv, util
from hoshino.typing import *
from .akgacha import Gacha
from .weibo import *

working_path = "hoshino/modules/akgacha/"
img_path = "./images"
char_data = json.load(open(working_path + "character_table.json", encoding="utf-8"))
gacha_data = json.load(open(working_path + "config.json", encoding="utf-8"))

sv_help = '''
[@Bot方舟十连] 明日方舟抽卡
[@Bot方舟来一井] 龙门币算什么，看我18w合成玉
[查看方舟卡池] 当前卡池信息
[切换方舟卡池] 更改卡池
[查饼] 查看微博消息
[蹲饼/取消蹲饼] 为本群开启/关闭蹲饼
'''.strip()
sv = Service('akgacha', help_=sv_help, bundle="akgacha", enable_on_default=True)

group_banner = {}
try:
    group_banner = json.load(open(working_path + "group_banner.json", encoding="utf-8"))
except FileNotFoundError: pass
    
def save_group_banner():
    with open(working_path + "group_banner.json", "w", encoding="utf-8") as f:
        json.dump(group_banner, f, ensure_ascii=False)
        
def ak_group_init(gid):
    group_banner[gid] = { "banner": "普池", "weibo_check": 1613000000, "weibo_push": False }
        
@sv.on_fullmatch(("查看方舟卡池"))
async def gacha_info(bot, ev: CQEvent):
    gid = str(ev.group_id)
    if not gid in group_banner:
        ak_group_init(gid)
    banner = group_banner[gid]["banner"]
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
            group_banner[gid]["banner"] = name
            save_group_banner()
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
    g.rare_chance = False
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
    
@sv.on_prefix(("查饼"))
async def weibo_check(bot, ev: CQEvent):
    gid = str(ev.group_id)
    if not gid in group_banner:
        ak_group_init(gid)
    now = datetime.now().timestamp()
    from = group_banner[gid]["weibo_check"]
    result = get_weibo()
    result_f = filter(lambda x: x["timestamp"] >= from, result)
    group_banner[gid]["weibo_check"] = now
    save_group_banner()
    await bot.send(ev, pprint.pprint([result[0], "历史消息"] + result_f[1:]))

@sv.on_prefix(("蹲饼"))
async def weibo_push_enable(bot, ev: CQEvent):
    gid = str(ev.group_id)
    if not gid in group_banner:
        ak_group_init(gid)
    group_banner[gid]["weibo_push"] = True
    save_group_banner()
    await bot.send(ev, "已开启蹲饼推送，可用'取消蹲饼'关闭")
    
async def weibo_push_disable(bot, ev: CQEvent):
    gid = str(ev.group_id)
    if not gid in group_banner:
        ak_group_init(gid)
    group_banner[gid]["weibo_push"] = False
    save_group_banner()
    await bot.send(ev, "已关闭蹲饼推送")
    
async def weibo_push():
    result = get_weibo()
    ts = result[0]["timestamp"]+1
    try:
        while True:
            result = get_weibo(2859117414)
            if result[0]["timestamp"] > ts:
                ts = result[0]["timestamp"]
                print("- 检测到微博更新")
                pprint.pprint(result[0])
            s = 30
            if datetime.now().hour > 10 and datetime.now().hour < 21:
                s = 10
            await asyncio.sleep(s)