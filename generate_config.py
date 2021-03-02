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
            "multi": { "年": 6 }
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
            "note": "120抽保底up6星（灰烬）\n首次得到up五星后，下一个五星必定为另一个up五星"
        },
        "普池": {
            "id": 48,
            "limited": False,
            "no_other_6": False,
            "favor": None,
            "up_6": ["伊芙利特", "森蚺"],
            "up_5": ["幽灵鲨", "惊蛰", "食铁兽"],
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
    "limited_chars": ["W", "年", "迷迭香", "夕", "灰烬", "闪击", "霜华", "清流"]
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

