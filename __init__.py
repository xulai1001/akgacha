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
from .akgacha import *
from .weibo import *
from .prtsres import *
from .browser import *
from urllib import request

working_path = "hoshino/modules/akgacha/"
img_path = "./images"
char_data = json.load(open(working_path + "character_table.json", encoding="utf-8"))
gacha_data = json.load(open(working_path + "config.json", encoding="utf-8"))

sv_help = '''
# 抽卡模拟相关
[@机器人 方舟十连] 明日方舟抽卡
[@机器人 方舟来一井] 300抽
[查看方舟卡池] 当前卡池信息
[切换方舟卡池 x] 更改卡池到x，可用查看历史卡池命令列出可用的名字
[查看方舟历史卡池] 查看可抽的所有卡池名（长）

# 抽卡管理命令:
[更新方舟基础数据] 更新角色数据库
[更新方舟卡池] 更新卡池信息
[更新方舟资源] 下载头像包到/res/img/akgacha/，具体进程请在后台查看

# 信息查询命令：
[饼呢 x] 查看方舟官方微博消息
[蹲饼/取消蹲饼] 开启、关闭蹲饼推送
[方舟游戏公告] 查看明日方舟游戏公告
[方舟素材|材料|刷图] 显示ark.yituliu.site的素材效率一图流，实时更新。注意：此功能需要配置chromedriver和selenium
[方舟dps 干员名] 跳转到DPS计算器的指定干员
[专精收益 干员名] 跳转到专精收益计算器的指定干员页面
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
    group_banner[gid] = { "banner": "普池#70", "weibo_check": datetime.now().timestamp(), "weibo_push": False }
        
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
        current_time=datetime.now().timestamp()
        list_cur=[]
        for gacha in gacha_data["banners"]:
            if int(gacha_data["banners"][gacha]["end"])>int(current_time):
                list_cur.append(gacha)
        if list_cur:
            lines = ["当期卡池:"] + list_cur + ["", "使用命令[切换方舟卡池 （卡池名）]进行设置","使用命令[查看方舟历史卡池]查看全部往期卡池"]
            await bot.finish(ev, "\n".join(lines))
        else:
            await bot.finish(ev, "未找到正在进行中的卡池……请联系维护组更新卡池信息或使用命令[查看方舟历史卡池]查看全部往期卡池")
    else:
        if name in gacha_data["banners"].keys():
            gid = str(ev.group_id)
            group_banner[gid]["banner"] = name
            save_group_banner()
            await bot.send(ev, f"卡池已经切换为 {name}", at_sender=True)
            await gacha_info(bot, ev)
        else:
            await bot.finish(ev, f"没找到卡池: {name}")
            
@sv.on_fullmatch(("查看方舟历史卡池","查看舟游历史卡池"))
async def history_pool(bot, ev: CQEvent):
    lines = ["全部卡池:"] + list(gacha_data["banners"].keys()) + ["", "使用命令 切换方舟卡池 x（x为卡池名）进行设置"]
    await bot.finish(ev, "\n".join(lines))

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
    
@sv.on_prefix(("方舟素材", "方舟材料", "方舟一图流", "方舟刷", "方舟养成"))
async def show_mats(bot, ev: CQEvent):
    img = MessageSegment.image("base64://" + browser_yituliu())
    line = f'{img}\n明日方舟素材刷取一图流-来源：\nhttps://ark.yituliu.site/'
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
    _name = "鹰小姐"
    _uin = "2087332430"
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
    #for wb_text in blog["text"].split('\n'):
    #    nodes.append(
    #        make_cqnode(
    #            MessageSegment.text(wb_text)
    #        )
    #    )
    nodes.append(make_cqnode( MessageSegment.text(blog["text"]) )) # too long?
    if blog.get("media", None):
        nodes.append(make_cqnode( MessageSegment( {"type": "video", "data": { "file": blog["media"] } } )) )
    if blog.get("pics", None):
        for x in blog["pics"]:
            nodes.append(make_cqnode( MessageSegment.image(x)) )
    # pprint.pprint(nodes)
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
    else:
        n_new = len(result_f)
        lines.append("有 %d 张新饼" % n_new)
        for x in result_f:
            nodes += format_weibo(x)
        lines.append("一共有 %d 张饼，回复'吃饼 x'查看旧饼" % len(result))
    group_banner[gid]["weibo_check"] = t_now
    save_group_banner()
    # try send
    try:
        await bot.send(ev, "\n".join(lines))
        #print(nodes)
        #await bot.send_group_forward_msg(group_id=gid, messages=[ { "type": "node", "data": { "name": "test", "uin": "133333333", "content": "test"}}])
        if len(nodes) > 0:
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
                await asyncio.sleep(5)
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

@sv.scheduled_job("interval", seconds=300, jitter=5)
async def weibo_push():
    global ts_push
    global cnt
    # print("- get_weibo")
    hr = datetime.now().hour
    minute = datetime.now().minute
    # 判断时间。11-18点，整点附近狂暴蹲饼，否则摸鱼蹲饼
    repeat_time = 1
    repeat_interval = 15
    if (hr>=10 and hr<=20) and (minute % 30 > 24 or minute % 30 < 6):
        repeat_time = 18

    while repeat_time > 0:
        uids = [6279793937, 1652903644]
        result = []
        for x in uids:
            print("- get_weibo %d" % x) 
            result.append(get_weibo(x))
        for item in result:
            try:
                if item[0]["timestamp"] >= ts_push:
                    print("- weibo_push: 检测到微博更新")
                    await weibo_do_bcast(item[0])
            except: pass
        ts_push = datetime.now().timestamp()
        repeat_time -= 1
        await asyncio.sleep(repeat_interval)


@sv.on_fullmatch(("更新方舟基础数据","更新舟游基础数据"))
async def update_table(bot, ev: CQEvent):
    global char_data
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev,'此命令仅维护组可用，请联系维护组~')
        return
    await bot.send(ev, '正在更新请稍候……')
    try:
        result = await update_chara_db()
        if result:
            data_init()
            char_data = json.load(open(os.path.join(working_path, "character_table.json"), encoding="utf-8"))
            await bot.send(ev, '更新基础数据成功！')
        else:
            await bot.send(ev, '基础数据已是最新版本！')
    except Exception as e:
        print(traceback.format_exc())
        await bot.send(ev, f'更新失败……{e}')


@sv.on_fullmatch(("更新方舟卡池","更新舟游卡池"))
async def update_pool(bot, ev: CQEvent):
    global gacha_data
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev,'此命令仅维护组可用，请联系维护组~')
        return
    await bot.send(ev, '正在更新请稍候……')
    try:
        result = await update_config()
        if result:
            data_init()
            gacha_data = json.load(open(os.path.join(working_path, "config.json"), encoding="utf-8"))
            await bot.send(ev, '更新卡池成功！')
        else:
            data_init()
            await bot.send(ev, '卡池已是最新版本！')
    except Exception as e:
        print(traceback.format_exc())
        await bot.send(ev, f'更新失败……{e}')


@sv.on_fullmatch(("更新方舟资源","更新舟游资源"))
async def update_pool(bot, ev: CQEvent):
    if not priv.check_priv(ev, priv.SUPERUSER):
        await bot.send(ev,'此命令仅维护组可用，请联系维护组~')
        return
    await bot.send(ev, '正在更新请稍候……')
    try:
        result = await update_res()
        if result:
            await bot.send(ev, f'更新资源成功！已新增{result}张图像！')
        else:
            await bot.send(ev, '资源已是最新版本！')
    except Exception as e:
        print(format_exc())
        await bot.send(ev, f'更新失败……{e}')

@sv.on_prefix(("方舟dps"))
async def akdata_link(bot, ev: CQEvent):
    # print(ev.message)
    char = get_charid(str(ev.message))
    if not char:
        await bot.send(ev, "暂未收录该干员，敬请期待")
    else:
        await bot.send(ev, f"https://viktorlab.cn/akdata/dps/#{char}")

@sv.on_prefix(("专精收益"))
async def akdata_mastery(bot, ev: CQEvent):
    # print(ev.message)
    char = get_charid(str(ev.message))
    if not char:
        await bot.send(ev, "暂未收录该干员，敬请期待")
    else:
        await bot.send(ev, f"https://viktorlab.cn/akdata/mastery/#{char}")

@sv.on_prefix(("游戏公告", "方舟游戏公告"))
async def ak_comm(bot, ev: CQEvent):
    resp = request.urlopen(u"https://ak-conf.hypergryph.com/config/prod/announce_meta/Android/announcement.meta.json")
    result = json.loads(resp.read().decode())
    lines = []
    item = None
    gid = str(ev.group_id)
    x=0
    if len(str(ev.message))>0:
        x=int(str(ev.message))
    if x==0:
        if result.get("focusAnnounceId", None):
            aid = result["focusAnnounceId"]
            item = next(x for x in result["announceList"] if x.get("announceId", None) == aid)
    else:
        item = result["announceList"][x-1]
    
    if item:
        pprint.pprint(item)
        title = item["title"].replace("\n", " ")
        lines.append("明日方舟游戏公告: " + title)
        lines.append(f"发布日期: {item['month']}-{item['day']}")
        lines.append(f"一共有 {len(result['announceList'])} 条公告，使用[游戏公告 x]查看第x条公告'")

        text = MessageSegment.text("\n".join(lines))
        await bot.send(ev, text)

        #这样不行
        #link_node = make_cqnode({
        #    "type": "share",
        #    "data": { 
        #        "url": item["webUrl"],
        #        "title": item["title"],
        #        "content": "明日方舟游戏公告",
        #        "image": f'file:///{os.path.abspath(working_path)}/dev.png'
        #    }
        #})
        # 直接发链接也会不能生成链接或被风控。尝试使用转发
        link_node = make_cqnode(MessageSegment.text(item["webUrl"]))
        await bot.send_group_forward_msg(group_id=gid, messages=[link_node])

