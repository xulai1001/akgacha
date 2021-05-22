#encoding:utf-8
import json, pprint, os
working_path = "hoshino/modules/akgacha/"
try:
    chars = json.load(open("character_table.json", encoding="utf-8"))
    banners = {
        "麦穗与赞美诗": {
            "limited": False,
            "no_other_6": False,
            "favor": None,
            "up_6": ["空弦"],
            "up_5": ["贾维", "爱丽丝"],
            "up_4": ["豆苗"],
            "exclude": []
        },
        "往日幻象": {
            "limited": False,
            "no_other_6": False,
            "favor": None,
            "up_6": ["傀影"],
            "up_5": ["白面鸮", "巫恋"],
            "up_4": ["刻刀"],
            "exclude": []
        },
        "地生五金-复刻": {
            "limited": True,
            "no_other_6": False,
            "favor": "年",
            "up_6": ["年", "阿"],
            "up_5": ["吽"],
            "up_4": [],
            "exclude": []
        },
        "月隐晦明": {
            "limited": True,
            "no_other_6": False,
            "favor": "夕",
            "up_6": ["夕", "嵯峨"],
            "up_5": ["乌有"],
            "up_4": [],
            "exclude": [],
            "multi": { "年": 5 }
        },
        "r6": {
            "limited": "r6",
            "no_other_6": False,
            "favor": None,
            "up_6": ["灰烬"],
            "up_5": ["闪击", "霜华"],
            "up_4": [],
            "exclude": [],
            "tenjou_5": True,
            "tenjou": { "n": 120, "name": "灰烬" },
            "note": "在本卡池抽一井为120抽\n120抽保底up6星（灰烬）\n首次得到up五星后，下一个五星必定为另一个up五星"
        },
        "沙海过客": {
            "limited": False,
            "no_other_6": False,
            "favor": None,
            "up_6": ["异客"],
            "up_5": ["慑砂", "熔泉"],
            "up_4": [],
            "exclude": []
        },
        "深悼": {
            "limited": True,
            "no_other_6": False,
            "favor": "浊心斯卡蒂",
            "up_6": ["浊心斯卡蒂", "凯尔希"],
            "up_5": ["赤冬"],
            "up_4": [],
            "exclude": [],
            "multi": { "W": 5 },
            "note": "有W"
        },
        "联合行动04": {
            "limited": False,
            "no_other_6": True,
            "favor": None,
            "up_6": ["棘刺", "温蒂", "铃兰", "夜莺"],
            "up_5": ["临光", "芙兰卡", "赫默", "极境", "莱恩哈特", "安哲拉"],
            "up_4": [],
            "exclude": []
        },
        "普池": {
            "id": 54,
            "limited": False,
            "no_other_6": False,
            "favor": "森蚺",
            "up_6": ["森蚺", "阿"],
            "up_5": ["白面鸮", "蓝毒", "真理"],
            "up_4": [],
            "exclude": []
        }
    }

    # 生成普池数据
    pool = {
    "star_6": [],
    "star_5": [],
    "star_4": [],
    "star_3": [],
    "other_chars": [],
    "recruit_chars": ["艾丝黛尔", "火神", "因陀罗"],
    "limited_chars": ["W", "年", "迷迭香", "夕", "灰烬", "闪击", "霜华", "浊心斯卡蒂", "凯尔希"]
    }

    for k in chars.keys():
        name = chars[k]["name"]
        if not k.startswith("char"):
            pass
        elif chars[k]["itemObtainApproach"] != "招募寻访" or chars[k]["rarity"] < 2:
            pool["other_chars"].append(name)
        elif not name in (pool["recruit_chars"] + pool["limited_chars"]):
            pool["star_%d" % (chars[k]["rarity"]+1)].append(name)

    result = { "banners": banners, "pool": pool }
        
    with open("config.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=2, ensure_ascii=False))
except:
    pass
# os.system("config.json")

