#encoding: utf-8
import json, urllib.request, os, sys, time, random
from shutil import move

filelist = os.listdir(".")
# print(filelist)

for fn in filelist:
    if not fn.endswith(".png"): continue
    if not fn.startswith("char"): continue
    parts = fn.split("_")
    if len(parts) >= 4:
        new_name = "%s.png" % "_".join(parts[:3])
        print("%s -> %s" % (fn, new_name))
        move(fn, new_name)