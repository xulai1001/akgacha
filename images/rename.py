#encoding: utf-8
import json, urllib.request, os, sys, time, random
from fake_useragent import UserAgent

gamedata_path = "../../../resources/gamedata/excel"
f = open(gamedata_path + "/character_table.json", "r", encoding="utf-8")
chardb = json.load(f)
ids = {}
for k in chardb.keys():
    ids[chardb[k]["name"]] = k
ids["阿米娅(近卫)"] = "char_1001_amiya2"

filelist = os.listdir(".")
# print(filelist)

for fn in filelist:
    info = fn.replace("头像_", "").replace(".png", "").split("_")
    new_name = ""
    if info[0].endswith(".py"): continue
    elif ids[info[0]]:
        info[0] = ids[info[0]]
        new_name = "_".join(info) + ".png"
        print("%s -> %s" % (fn, new_name))
        os.rename(fn, new_name)
    else:
        print("x %s" % info[0])