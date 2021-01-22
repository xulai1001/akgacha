#encoding:utf-8
import json, pprint, os
chars = json.load(open("character_table.json", encoding="utf-8"))

banners = {
    "麦穗与赞美诗": {
        "limited": False,
        "up_6": ["空弦"],
        "up_5": ["贾维", "爱丽丝"],
        "up_4": ["豆苗"],
        "exclude": []
    },
    "地生五金-复刻": {
        "limited": True,
        "up_6": ["年", "阿"],
        "up_5": ["吽"],
        "up_4": [],
        "exclude": []
    },
    "普池": {
        "id": 46,
        "limited": False,
        "up_6": ["陈", "推进之王"],
        "up_5": ["临光", "可颂", "燧石"],
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
    "limited_chars": ["W", "年", "迷迭香"]
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

os.system("config.json")