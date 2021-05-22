#encoding:utf-8
import pprint, json, requests, time, re, os
from datetime import datetime
import urllib3

#working_path = "hoshino/modules/akgacha/"

home_api = "https://m.weibo.cn/api/container/getIndex?type=uid&value=%d"
weibo_api = "https://m.weibo.cn/api/container/getIndex?type=uid&value=%d&containerid=%s&count=20"

headers = {
    'Accept': 'application/json, text/plain, */*',
    'MWeibo-Pwa': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}

# turn off keep-alive
s = requests.session()
s.keep_alive = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_cid(uid, op=107603):
#    r = requests.get(home_api % uid, verify=False)
#    data = json.loads(r.text)    
#    weibo_tab = [x for x in data["data"]["tabsInfo"]["tabs"] if x["tabKey"] == "weibo"][0]
#    return int(weibo_tab["containerid"])
    return str(op) + str(uid)
    
# default to yj
def get_weibo(uid=6279793937):
    cid = get_cid(uid)  # op=230413 also ok
    ret = []
    r = requests.get(weibo_api % (uid, cid), verify=False, headers=headers)
    data = json.loads(r.text)
    cards = [x for x in data["data"]["cards"] if x["card_type"] == 9]
    for cd in cards:
       # pprint.pprint(cd)
        item = { k: cd["mblog"][k] for k in ["created_at", "text", "id"] }
        # user
        item["username"] = cd["mblog"]["user"]["screen_name"]
        # trim html
        item["text"] = re.sub(r'<br />', "\n", item["text"])
        item["text"] = re.sub(r'<[^>]+>', "", item["text"])
        # RubyTime: 'Thu Jan 28 11:05:06 +0800 2021'
        item["timestamp"] = datetime.strptime(item["created_at"], "%a %b %d %H:%M:%S %z %Y").timestamp()
        # pics
        item["pics"] = [x["url"].replace("orj360", "large") for x in cd["mblog"].get("pics", [])]
        # videos
        try:
            item["media"] = cd["mblog"]["page_info"]["media_info"]["stream_url_hd"]
        except: pass            
        ret.append(item)
        # os.system("pause")
    return sorted(ret, key=lambda x: x["timestamp"], reverse=True)

if __name__ == "__main__":
    pprint.pprint(get_weibo())
    
