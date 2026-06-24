import json, urllib.request, urllib.error, http.cookiejar

BASE = "http://localhost:8000/api"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

def api(method, path, body=None):
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        resp = opener.open(req)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()) if e.readable() else {"detail": str(e)}

s, r = api("POST", "/auth/login", {"username": "admin", "password": "admin123"})
assert s == 200, f"Login failed: {r}"
print(f"Login OK: {r['username']}")

groups = api("POST", "/groups", {"group_number": "123456789", "group_name": "LOL开黑群", "remark": "祖安大区", "tags": ["游戏", "LOL"]})
lol = groups[1]
ff14 = api("POST", "/groups", {"group_number": "987654321", "group_name": "FF14亲友团", "remark": "鸟区", "tags": ["游戏", "FF14"]})[1]
tech = api("POST", "/groups", {"group_number": "111222333", "group_name": "技术闲聊群", "tags": ["技术", "闲聊"]})[1]
paint = api("POST", "/groups", {"group_number": "444555666", "group_name": "绘画摸鱼群", "tags": ["绘画", "创作"]})[1]
anime = api("POST", "/groups", {"group_number": "777888999", "group_name": "新番讨论组", "tags": ["动漫", "闲聊"]})[1]
print(f"Groups: {len([g for g in [lol,ff14,tech,paint,anime]])} created")

persons_data = [
    {"name": "张三", "remark": "三哥", "signature": "上单永不言弃", "location": "广东深圳", "circle_tags": ["LOL圈", "FF14玩家"], "impression_tags": ["技术大佬", "话痨"], "importance": 4, "notes": "2024年LOL祖安排位认识的，后来发现也玩FF14。主玩上单剑姬，FF14主职战士。", "birthday": "03-15"},
    {"name": "李四", "remark": "四妹", "signature": "摸鱼中...", "location": "浙江杭州", "circle_tags": ["FF14玩家", "绘画圈"], "impression_tags": ["画师大佬", "鸽子王"], "importance": 3, "notes": "FF14部队里认识的，画技一流但经常拖稿。在鸟区，ID叫「小四画画」。", "birthday": "07-22"},
    {"name": "王五", "remark": "五爷", "signature": "写代码写到头秃", "location": "北京", "circle_tags": ["技术圈", "LOL圈"], "impression_tags": ["全栈大佬", "夜猫子"], "importance": 5, "notes": "前同事，现在跳槽去大厂了。经常半夜在线，技术问题找他基本都能解决。", "birthday": "11-08"},
    {"name": "赵六", "remark": "六六", "signature": "今天的我也在摸鱼", "location": "上海", "circle_tags": ["FF14玩家", "技术圈"], "impression_tags": ["萌新", "爱问问题"], "importance": 2, "notes": "2025年初在技术闲聊群认识的，刚入行前端。FF14是豆芽，主职白魔。", "birthday": "05-30"},
    {"name": "孙七", "remark": "阿七", "signature": "画画吃饭睡觉", "location": "四川成都", "circle_tags": ["绘画圈", "动漫"], "impression_tags": ["厚涂大佬", "社恐"], "importance": 3, "notes": "绘画摸鱼群认识的，厚涂风格很惊艳，但平时话不多。约稿很靠谱。", "birthday": "09-12"},
    {"name": "周八", "remark": "八哥", "signature": "bug不要找我", "location": "广东广州", "circle_tags": ["技术圈"], "impression_tags": ["后端大牛", "Linux狂魔"], "importance": 4, "notes": "技术群里认识的，后端架构很厉害。用Arch Linux，经常安利别人换系统。"},
    {"name": "吴九", "remark": "小九", "signature": "今天也是和平的一天", "location": "江苏南京", "circle_tags": ["LOL圈", "动漫"], "impression_tags": ["辅助专精", "番剧达人"], "importance": 2, "notes": "LOL群里的辅助玩家，锤石绝活哥。每季新番必追，经常在群里剧透。", "birthday": "12-25"},
    {"name": "郑十", "remark": "十十", "signature": "咖啡重度依赖", "location": "湖北武汉", "circle_tags": ["绘画圈", "FF14玩家"], "impression_tags": ["线稿达人", "咖啡狂"], "importance": 3, "notes": "在FF14群里发自己画的同人图认识的。每天至少三杯咖啡。", "birthday": "02-14"},
    {"name": "冯十一", "remark": "十一", "signature": "万事开头难", "location": "重庆", "circle_tags": ["技术圈", "动漫"], "impression_tags": ["前端开发", "拖延症晚期"], "importance": 2, "notes": "技术群里的前端，和赵六经常一起交流。想做很多项目但总是停留在初始化阶段。"},
    {"name": "陈十二", "remark": "十二少", "signature": "人生苦短我用Python", "location": "北京", "circle_tags": ["技术圈", "LOL圈"], "impression_tags": ["Python大神", "毒舌"], "importance": 4, "notes": "王五的前同事，Python后端。说话很直但技术过硬。LOL打中单。"},
    {"name": "林十三", "remark": "小林", "signature": "正在输入...", "location": "福建厦门", "circle_tags": ["动漫", "绘画圈"], "impression_tags": ["日系画风", "温柔"], "importance": 3, "notes": "新番讨论组认识的，画风偏日系小清新。性格很好，群里吵架时会出来调解。", "birthday": "06-01"},
    {"name": "黄十四", "remark": "十四", "signature": "打游戏不睡觉", "location": "湖南长沙", "circle_tags": ["LOL圈"], "impression_tags": ["ADCarry", "夜猫子"], "importance": 2, "notes": "LOL群的ADC，经常和张三双排。凌晨三四点还在线。"},
    {"name": "何十五", "remark": "十五", "signature": "明天一定早睡", "location": "陕西西安", "circle_tags": ["FF14玩家", "动漫"], "impression_tags": ["零式大佬", "修仙"], "importance": 3, "notes": "FF14固定队成员，零式攻略速度很快。作息极其不规律。", "birthday": "08-08"},
]

people = []
for d in persons_data:
    s, r = api("POST", "/persons", d)
    if s == 201:
        people.append(r)
    else:
        people.append(None)

print(f"Persons: {len([p for p in people if p])}/{len(persons_data)} created")

def add_acc(pid, atype, aid, nick):
    return api("POST", f"/persons/{pid}/accounts", {"account_type": atype, "account_identifier": aid, "current_nickname": nick})

acc_map = {}
for p in people:
    if not p:
        continue
    acc_map[p["id"]] = []

if people[0]:
    acc_map[people[0]["id"]].append(add_acc(people[0]["id"], "QQ", "10001", "剑断红尘")[1]["id"])
    acc_map[people[0]["id"]].append(add_acc(people[0]["id"], "微信", "zhangsan_wx", "张三")[1]["id"])
    acc_map[people[0]["id"]].append(add_acc(people[0]["id"], "游戏ID", "SwordMaster", "剑断红尘")[1]["id"])
if people[1]:
    acc_map[people[1]["id"]].append(add_acc(people[1]["id"], "QQ", "20001", "小四画画")[1]["id"])
    acc_map[people[1]["id"]].append(add_acc(people[1]["id"], "微信", "lisi_art", "四四")[1]["id"])
if people[2]:
    acc_map[people[2]["id"]].append(add_acc(people[2]["id"], "QQ", "30001", "CodeMaster")[1]["id"])
    acc_map[people[2]["id"]].append(add_acc(people[2]["id"], "微信", "wangwu_dev", "王五")[1]["id"])
if people[3]:
    acc_map[people[3]["id"]].append(add_acc(people[3]["id"], "QQ", "40001", "前端小六")[1]["id"])
if people[4]:
    acc_map[people[4]["id"]].append(add_acc(people[4]["id"], "QQ", "50001", "阿七的笔")[1]["id"])
if people[5]:
    acc_map[people[5]["id"]].append(add_acc(people[5]["id"], "QQ", "60001", "ArchLinux")[1]["id"])
    acc_map[people[5]["id"]].append(add_acc(people[5]["id"], "微信", "zhouba_dev", "老周")[1]["id"])
if people[6]:
    acc_map[people[6]["id"]].append(add_acc(people[6]["id"], "QQ", "70001", "锤石king")[1]["id"])
if people[7]:
    acc_map[people[7]["id"]].append(add_acc(people[7]["id"], "QQ", "80001", "咖啡十")[1]["id"])
    acc_map[people[7]["id"]].append(add_acc(people[7]["id"], "微信", "zheng10_art", "十十")[1]["id"])
if people[8]:
    acc_map[people[8]["id"]].append(add_acc(people[8]["id"], "QQ", "90001", "十一不会Vue")[1]["id"])
if people[9]:
    acc_map[people[9]["id"]].append(add_acc(people[9]["id"], "QQ", "11001", "Python十二")[1]["id"])
    acc_map[people[9]["id"]].append(add_acc(people[9]["id"], "微信", "chen12_py", "陈十二")[1]["id"])
if people[10]:
    acc_map[people[10]["id"]].append(add_acc(people[10]["id"], "QQ", "12001", "林间小画")[1]["id"])
if people[11]:
    acc_map[people[11]["id"]].append(add_acc(people[11]["id"], "QQ", "13001", "VN本命")[1]["id"])
if people[12]:
    acc_map[people[12]["id"]].append(add_acc(people[12]["id"], "QQ", "14001", "绝枪战士")[1]["id"])

print("Accounts created")

def join(gid, pid, nick=None):
    accs = acc_map.get(pid, [])
    if accs:
        api("POST", f"/groups/{gid}/members", {"account_id": accs[0], "group_id": gid, "group_nickname": nick})

if people[0]: join(lol["id"], people[0]["id"], "剑断红尘"); join(ff14["id"], people[0]["id"], "剑桑")
if people[1]: join(ff14["id"], people[1]["id"], "小四画画"); join(paint["id"], people[1]["id"], "四四")
if people[2]: join(lol["id"], people[2]["id"], "CodeMaster"); join(tech["id"], people[2]["id"], "王五")
if people[3]: join(tech["id"], people[3]["id"], "前端小六"); join(ff14["id"], people[3]["id"], "萌新白魔")
if people[4]: join(paint["id"], people[4]["id"], "阿七"); join(anime["id"], people[4]["id"], "阿七")
if people[5]: join(tech["id"], people[5]["id"], "老周")
if people[6]: join(lol["id"], people[6]["id"], "锤石king"); join(anime["id"], people[6]["id"], "小九")
if people[7]: join(ff14["id"], people[7]["id"], "咖啡十"); join(paint["id"], people[7]["id"], "十十")
if people[8]: join(tech["id"], people[8]["id"], "十一"); join(anime["id"], people[8]["id"], "十一")
if people[9]: join(tech["id"], people[9]["id"], "十二少"); join(lol["id"], people[9]["id"], "Python十二")
if people[10]: join(anime["id"], people[10]["id"], "小林"); join(paint["id"], people[10]["id"], "林间小画")
if people[11]: join(lol["id"], people[11]["id"], "VN本命")
if people[12]: join(ff14["id"], people[12]["id"], "绝枪战士"); join(anime["id"], people[12]["id"], "十五")

print("Memberships created")

def rel(a, b, t):
    if a and b:
        api("POST", f"/persons/{a['id']}/relations", {"person_id_2": b['id'], "relation_type": t})
rel(people[0], people[1], "FF14部队战友")
rel(people[0], people[2], "LOL开黑队友")
rel(people[0], people[11], "LOL双排搭档")
rel(people[2], people[9], "前同事")
rel(people[2], people[3], "技术群群友")
rel(people[3], people[8], "前端学习搭子")
rel(people[1], people[4], "绘画圈好友")
rel(people[1], people[7], "FF14画友")
rel(people[7], people[10], "画风互相欣赏")
rel(people[4], people[10], "绘画摸鱼群友")
rel(people[5], people[9], "技术辩论对手")
rel(people[6], people[10], "新番讨论搭子")
rel(people[8], people[3], "前后端基友")

print("Relations created")

def met(p, desc, at):
    if p:
        api("POST", f"/persons/{p['id']}/meetings", {"description": desc, "met_at": at})
met(people[0], "2024年3月LOL排位赛认识，他剑姬1v5翻盘", "2024-03")
met(people[1], "FF14部队招募时加入，说自己是画师可以画部队logo", "2024-06")
met(people[2], "上一家公司的同事，坐我旁边工位", "2023-01")
met(people[3], "技术群里一直问前端问题的新人，后来加了微信", "2025-02")
met(people[4], "在Pixiv上看到她的画，加了群发现居然在同一个绘画群", "2024-09")
met(people[5], "技术群里发了一篇Arch Linux安装教程，印象深刻", "2024-04")
met(people[6], "LOL排位遇到的辅助，锤石钩子太准了", "2024-07")
met(people[7], "FF14同人展上看到她画的部队合影，主动加了群", "2024-11")
met(people[8], "github上看到他star了我的项目，后来在技术群里相认", "2025-01")
met(people[9], "王五介绍认识的，第一次见面就在群里互怼编码风格", "2023-06")
met(people[10], "新番群里她一直在发自己画的同人，画得太好了", "2024-10")
met(people[11], "张三拉进LOL群的，说要找个靠谱ADC", "2024-05")
met(people[12], "FF14固定队招募坦克时加入的，绝枪玩得很好", "2024-08")

print("Meetings created")
print("\nSeed complete!")
print(f"  Groups: 5")
print(f"  Persons: {len([p for p in people if p])}")
print(f"  Accounts: ~25")
print(f"  Relations: 13")
print(f"  Meetings: 13")
