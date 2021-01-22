#encoding:utf-8
import pprint, json, random, copy, math
from io import BytesIO
from PIL import Image

img_path = "./images"
char_data = json.load(open("character_table.json", encoding="utf-8"))
gacha_data = json.load(open("config.json", encoding="utf-8"))

probs = {
    "up_6": 50,
    "other_6": 50,
    "up_5": 50,
    "other_5": 50,
    "up_4": 20,
    "other_4": 80,
    "limited_up_6": 70,
    "star_6": 2,
    "star_5": 8,
    "star_4": 50,
    "star_3": 40
}

def get_charid(name):
    ret = [k for k in char_data.keys() if char_data[k]["name"] == name]
    return ret[0] if len(ret) > 0 else None

def roll(n):
    return random.randint(0, n-1)

def pull_naive(rate_6=2, limited=False, must_rare=False):
    star = 3
    up = False
    
    x1 = roll(100)
    if x1 < rate_6:
        x2 = roll(100)
        star = 6
        if limited:
            up = (x2 < probs["limited_up_6"])
        else:
            up = (x2 < probs["up_6"])
    else:
        x2 = roll(98)
        x3 = roll(100)
        if must_rare or x2 < probs["star_5"]:
            star = 5
            up = (x3 < probs["up_5"])
        elif x2 < probs["star_5"] + probs["star_4"]:
            star = 4
            up = (x3 < probs["up_4"])
        else:
            pass # 3-star
    return { "star": star, "up": up }
    
# learn from HoshinoBot
def gen_team_pic(team, size=64, ncol=5):
    nrow = math.ceil(len(team)/ncol)
    des = Image.new("RGBA", (ncol * size, nrow * size), (255, 255, 255, 255))
    for i, id in enumerate(team):
        face = Image.open("%s/%s.png" % (img_path, id)).convert("RGBA").resize((size, size), Image.LANCZOS)
        x = i % ncol
        y = math.floor(i / ncol)
        des.paste(face, (x * size, y * size), face)
    return des
    
class Gacha:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.count = {}
        self.char_count = {}
        self.result_list = []
        self.rare_list = { 5: [], 6: [] }
        self.rare_chance = True
        self.nth = 0
        self.nth_target = 0
        self.n6count = 0;
    
    def set_banner(self, b):
        self.banner = gacha_data["banners"][b]
        self.banner["name"] = b
        self.pool = {}
        for key in ["up_6", "up_5", "up_4"]:
            self.pool[key] = self.banner[key]
        exclude = self.banner["up_6"] + self.banner["up_5"] + self.banner["up_4"] + self.banner["exclude"]
        for key in ["star_6", "star_5", "star_4", "star_3"]:
            self.pool[key] = [x for x in gacha_data["pool"][key] if x not in exclude]
    
    def rate_6(self):
        return 2 if self.n6count < 50 else 2 * (self.n6count - 49)
        
    def pull(self):
        self.nth += 1
        # 抽类型
        if (self.nth >= 10 and self.rare_chance):
            result = pull_naive(self.rate_6(), self.banner["limited"], True)
            result["保底"] = True
        else:
            result = pull_naive(self.rate_6(), self.banner["limited"], False)
        # 抽人
        char_key = "%s_%d" % ("up" if result["up"] else "star", result["star"])
        if len(self.pool[char_key]) == 0:
            result["up"] = False
            char_key = "star_%d" % result["star"]
        result["char"] = cname = random.sample(self.pool[char_key], 1)[0]
        self.result_list.append(cname)
        # 记录抽卡类型
        type = ("up_%d" if result["up"] else "other_%d") % result["star"]
        self.count[type] = self.count.get(type, 0) + 1
        self.count[result["star"]] = self.count.get(result["star"], 0) + 1
        # 记录首次获得up角色
        if (type=="up_6" or (len(self.pool["up_6"])==0 and type=="up_5")) and self.nth_target == 0:
            self.nth_target = self.nth
        # 记录角色
        self.char_count[cname] = self.char_count.get(cname,
            { "id": get_charid(cname), "star": result["star"], "count": 0 })
        self.char_count[cname]["count"] += 1
        # 记录保底概率
        if self.n6count >= 50:
            result["rate_6"] = self.rate_6()
        # 清除必得五星   
        if result["star"] >= 5:
            self.rare_chance = False
            self.rare_list[result["star"]].append(cname)
        # 清除软保底
        if result["star"] == 6:
            print("6星!")            
            if self.n6count >= 50:
                print("软保底 - %d" % (self.n6count+1))
                result["软保底"] = True
            self.n6count = 0
        else:
            self.n6count += 1
        return result
    
    def ten_pull(self):
        return [self.pull() for x in range(0, 10)]
        
    def count_tickets(self):
        green = yellow = 0
        for ch in self.char_count.values():
            g = y = 0
            s = ch["star"]
            c = ch["count"]
            c2 = min(max(c-1, 0), 5)
            c7 = max(c-6, 0)
            
            if s == 3:
                g = 10*c # 3星以满潜计算
            elif s == 4:
                g = 30 * c2
                y = 1 + c7
            elif s == 5:
                y = 1 + c2*5 + c7*13
            elif s == 6:
                y = 1 + c2*10 + c7*25
            #ch["green"] = g
            #ch["yellow"] = y
            green += g
            yellow += y
        return (green, yellow)
    
    def summarize(self):
        team6 = [get_charid(x) for x in self.rare_list[6]]
        #team5 = [get_charid(x) for x in self.rare_list[5]]
        pic = gen_team_pic(team6)
        
        print("寻访结果:")
        print("☆6×%d ☆5×%d ☆4×%d ☆3×%d" % (self.count[6], self.count[5], self.count[4], self.count[3]))
        print("获得绿票×%d，黄票×%d！" % self.count_tickets())
        if self.nth_target > 0:
            print("第%d抽首次获得up角色" % self.nth_target)
        else:
            print("up呢？我的up呢？")
        pic.show()
        
    def summarize_tenpull(self):
        team = [get_charid(x) for x in self.result_list]
        pic = gen_team_pic(team, 64)
        print(self.result_list)
        pic.show()
        
if __name__ == "__main__":
    g = Gacha()
    g.set_banner("麦穗与赞美诗")
    pprint.pprint(g.banner)
    #pprint.pprint(g.pool)
    # 抽一井
    for i in range(0, 30):
        g.ten_pull()
    g.summarize()

    #g.ten_pull()
    #g.summarize_tenpull()
