#encoding:utf-8
import os, random, re, pprint, json, math, asyncio, threading
import traceback
from io import BytesIO
from PIL import Image
from collections import defaultdict
from datetime import datetime
import nonebot
from hoshino import R, Service, priv, util
from hoshino.typing import *
from hoshino.util import DailyNumberLimiter
from .akgacha import Gacha
from .weibo import *
from urllib import request

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

jewel_limit = DailyNumberLimiter(18000)
tenjo_limit = DailyNumberLimiter(3)

JEWEL_EXCEED_NOTICE = f"您今天已经抽过{jewel_limit.max}钻了，欢迎明早5点后再来！"

TENJO_EXCEED_NOTICE = f"您今天已经抽过{tenjo_limit.max}张天井券了，欢迎明早5点后再来！"

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
            
async def check_jewel(bot, ev):
    if not jewel_limit.check(ev.user_id):
        await bot.finish(ev, JEWEL_EXCEED_NOTICE, at_sender=True)
    elif not tenjo_limit.check(ev.user_id):
        await bot.finish(ev, TENJO_EXCEED_NOTICE, at_sender=True)

@sv.on_prefix(("方舟十连"), only_to_me=True)
async def gacha_10(bot, ev: CQEvent):
    gid = str(ev.group_id)
    if not gid in group_banner:
        ak_group_init(gid)
    b = group_banner[gid]["banner"]
    
    # barrier
    await check_jewel(bot, ev)
    jewel_limit.increase(ev.user_id, 6000)
    
    g = Gacha()
    g.set_banner(b)
    g.rare_chance = False
    result = g.ten_pull()
    await bot.send(ev, g.summarize_tenpull(result), at_sender=True)

@sv.on_prefix(("方舟来一井"), only_to_me=True)
async def gacha_300(bot, ev: CQEvent):
    gid = str(ev.group_id)
    if not gid in group_banner:
        ak_group_init(gid)
    b = group_banner[gid]["banner"]
    
    # barrier
    await check_jewel(bot, ev)
    tenjo_limit.increase(ev.user_id)
    
    g = Gacha()
    g.set_banner(b)
    if b == "r6":
        for i in range(0, 12):
            g.ten_pull()
        await bot.send(ev, g.summarize(True), at_sender=True)
    else:
        for i in range(0, 30):
            g.ten_pull()
        await bot.send(ev, g.summarize(), at_sender=True)
    
@sv.on_fullmatch(("方舟刷本效率"))
async def show_mats(bot, ev: CQEvent):
    img = MessageSegment.image(f'file:///{os.path.abspath(working_path + "ak-mats.jpg")}')
    line = f'{img}'
    await bot.send(ev, line)

def save_pic(url):
    filename = working_path + "cache/" + os.path.basename(url)
    if os.path.exists(filename):
        print("save_pic: file exists - %s" % filename)
    else:
        resp = request.urlopen(url)
        img = resp.read()
        filename = working_path + "cache/" + os.path.basename(url)
        print("save_pic %s" % filename)
        with open(filename, "wb+") as f:
            f.write(img)
    return filename

def make_cqnode(content, name=0, uin=0):
    _name = "库兰兰发饼机"
    _uin = "800830064"
    return {
        "type": "node",
        "data": {
            "name": _name,
            "uin": _uin,
            "content": content
        }
    }

# 为避免消息过长必须分段
def format_weibo(blog):
    # pprint.pprint(blog)
    lines = []
    nodes = []
    lines.append("发布者: %s, 时间: %s" % (
                  blog["username"], datetime.fromtimestamp(blog["timestamp"]).strftime("%m-%d %H:%M:%S")
                ))
    lines.append("https://m.weibo.cn/status/%s" % blog["id"])
    nodes.append(make_cqnode( MessageSegment.text("\n".join(lines)) ))
    #nodes.append(make_cqnode( MessageSegment.text(blog["text"]) )) # too long!
    if blog.get("media", None):
        nodes.append(make_cqnode( MessgeSegment( {"type": "video", "data": { "file": blog["media"] } } )) )
    if blog.get("pics", None):
        for x in blog["pics"]:
            nodes.append(make_cqnode( MessageSegment.image(x)) )
    pprint.pprint(nodes)
    return nodes

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
    nodes = []
    print(result_f)
    if len(str(ev.message)) > 0:
        x = int(str(ev.message)) - 1
        if x>=0 and x<len(result):
            lines.append("第 %d 张旧饼内容:" % (x+1))
            # lines.append(format_weibo(result[x]))
            nodes += format_weibo(result[x])
            lines.append(result[x]["text"])
    else:
        n_new = len(result_f)
        lines.append("有 %d 张新饼" % n_new)
        for x in result_f:
            nodes += format_weibo(x)
            lines.append(x["text"])
        lines.append("一共有 %d 张饼，回复'吃饼 x'查看旧饼" % len(result))
    group_banner[gid]["weibo_check"] = t_now
    save_group_banner()
    # try send
    try:
        await bot.send(ev, "\n".join(lines))
        #print(nodes)
        #await bot.send_group_forward_msg(group_id=gid, messages=[ { "type": "node", "data": { "name": "test", "uin": "133333333", "content": "test"}}])
        await bot.send_group_forward_msg(group_id=gid, messages=nodes)
    except Exception:
        print(traceback.format_exc())
        try:
            await bot.send(ev, "微博消息发送失败")
            # await bot.send(ev, traceback.format_exc())
        except Exception:
            print(traceback.format_exc())

@sv.on_fullmatch(("蹲饼"))
async def weibo_push_enable(bot, ev: CQEvent):
    gid = str(ev.group_id)
    if not gid in group_banner:
        ak_group_init(gid)
    group_banner[gid]["weibo_push"] = True
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
            try:
                print("推送至群 - %s" % gid)
                await bot.send_group_msg(group_id=gid, message="检测到微博更新\n")
                await bot.send_group_forward_msg(group_id=gid, messages=format_weibo(rst))
                await asyncio.sleep(1)
            except Exception:
                try:
                    traceback.print_exc()
                    await bot.send_group_msg(group_id=gid, message="蹲饼消息推送失败")
                except Exception:
                    print(traceback.print_exc())

            group_banner[gid]["weibo_check"] = datetime.now().timestamp()
    save_group_banner()

ts_push = datetime.now().timestamp()
cnt = 0

@sv.scheduled_job("interval", seconds=15, jitter=5)
async def weibo_push():
    global ts_push
    global cnt
    # print("- get_weibo")
    hr = datetime.now().hour
    if (hr<10 or hr>19) and (cnt % 3 != 0):
        print("- skipped")
    else:
        uids = [6279793937, 1652903644]
        result = []
        for x in uids:
            print("- get_weibo %d" % x) 
            result.append(get_weibo(x))
            await asyncio.sleep(3)
        for item in result:
            if item[0]["timestamp"] >= ts_push:
                print("- weibo_push: 检测到微博更新")
                await weibo_do_bcast(item[0])
        ts_push = datetime.now().timestamp()
        cnt += 1

