#encoding:utf-8
import os, random, re, pprint, json, math, asyncio, threading
from io import BytesIO
from PIL import Image
from collections import defaultdict
from datetime import datetime
import nonebot
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
[饼呢/吃饼] 查看微博消息
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

@sv.on_fullmatch(("切换方舟卡池"))
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

def format_weibo(blog):
    pprint.pprint(blog)
    lines = []
    lines.append("发布者: %s, 时间: %s" % (blog["username"], 
                 datetime.fromtimestamp(blog["timestamp"]).strftime("%m-%d %H:%M:%S")
                ))
    if blog.get("pics", None):
        lines += [f'{MessageSegment.image(x)}' for x in blog["pics"]]
    if blog.get("media", None):
        lines += ["视频链接: %s" % blog["media"]]
    lines.append(blog["text"])
    lines.append("https://m.weibo.cn/status/%s" % blog["id"])
 #   pprint.pprint(lines)
    return "\n".join(lines)
    
@sv.on_prefix(("吃饼", "饼呢"))
async def weibo_check(bot, ev: CQEvent):
    gid = str(ev.group_id)
    if not gid in group_banner:
        ak_group_init(gid)
    t_now = datetime.now().timestamp()
    t_from = group_banner[gid]["weibo_check"]
    result = get_weibo()
    result_f = list(filter(lambda x: x["timestamp"] >= t_from, result))
    lines = []
    if len(str(ev.message)) > 0:
        x = int(str(ev.message)) - 1
        if x>=0 and x<len(result):
            lines.append("第 %d 张旧饼内容:" % (x+1))
            lines.append(format_weibo(result[x]))
    else:
        n_new = len(result_f)
        lines.append("有 %d 张新饼" % n_new)
        lines += [format_weibo(x) for x in result_f]
        lines.append("一共有 %d 张饼，回复'吃饼 x'查看旧饼" % len(result))
    group_banner[gid]["weibo_check"] = t_now
    save_group_banner()
    await bot.send(ev, "\n".join(lines))

@sv.on_fullmatch(("蹲饼"))
async def weibo_push_enable(bot, ev: CQEvent):
    gid = str(ev.group_id)
    if not gid in group_banner:
        ak_group_init(gid)
    group_banner[gid]["weibo_push"] = True
    save_group_banner()
    await bot.send(ev, "已开启蹲饼推送，可用'取消蹲饼'关闭")

@sv.on_fullmatch(("取消蹲饼"))
async def weibo_push_disable(bot, ev: CQEvent):
    gid = str(ev.group_id)
    if not gid in group_banner:
        ak_group_init(gid)
    group_banner[gid]["weibo_push"] = False
    save_group_banner()
    await bot.send(ev, "已关闭蹲饼推送")
    
async def weibo_do_bcast(rst):
    bot = nonebot.get_bot()
    for gid in group_banner.keys():
        if (group_banner[gid].get("weibo_push", None)):
            print("推送至群 - %s" % gid)
            await bot.send_group_msg(group_id=gid, message="检测到微博更新\n" + format_weibo(rst))

ts_push = datetime.now().timestamp()

@sv.scheduled_job("interval", seconds=15, jitter=5)
async def weibo_push():
    global ts_push
    # print("- get_weibo")
    uids = [6279793937]
    result = [get_weibo(x) for x in uids]
    for item in result:
        if item[0]["timestamp"] >= ts_push:
            print("- weibo_push: 检测到微博更新")
            await weibo_do_bcast(item[0])
    ts_push = datetime.now().timestamp()

