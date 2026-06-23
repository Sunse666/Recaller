"""种子数据：通过 API 写入示例群友/账号/群"""
import requests

BASE = "http://localhost:8000/api"


def post(path, data):
    r = requests.post(f"{BASE}{path}", json=data)
    if r.status_code not in range(200, 300):
        print(f"  FAIL {path}: {r.status_code} {r.text}")
        return None
    return r.json()


def main():
    # ── 1. 创建群 ──
    print("创建群...")
    lol_group = post("/groups", {
        "group_number": "123456789",
        "group_name": "LOL开黑群",
        "remark": "祖安大区",
        "tags": ["游戏", "LOL"],
    })
    ff14_group = post("/groups", {
        "group_number": "987654321",
        "group_name": "FF14亲友团",
        "remark": "鸟区",
        "tags": ["游戏", "FF14"],
    })
    work_group = post("/groups", {
        "group_number": "111222333",
        "group_name": "技术闲聊群",
        "remark": "",
        "tags": ["技术", "闲聊"],
    })

    # ── 2. 创建群友 ──
    print("创建群友...")

    # 张三
    zhangsan = post("/persons", {
        "name": "张三",
        "remark": "三哥",
        "signature": "上单永不言弃",
        "location": "广东深圳",
        "circle_tags": ["LOL圈", "FF14玩家"],
        "impression_tags": ["技术大佬", "话痨"],
        "importance": 4,
        "notes": "2024年LOL祖安排位认识的，后来发现也玩FF14。主玩上单剑姬，FF14主职战士。",
        "birthday": "03-15",
    })

    # 李四
    lisi = post("/persons", {
        "name": "李四",
        "remark": "四妹",
        "signature": "摸鱼中...",
        "location": "浙江杭州",
        "circle_tags": ["FF14玩家", "绘画圈"],
        "impression_tags": ["画师大佬", "鸽子王"],
        "importance": 3,
        "notes": "FF14部队里认识的，画技一流但经常拖稿。在鸟区，ID叫「小四画画」。",
        "birthday": "07-22",
    })

    # 王五
    wangwu = post("/persons", {
        "name": "王五",
        "remark": "五爷",
        "signature": "写代码写到头秃",
        "location": "北京",
        "circle_tags": ["技术圈", "LOL圈"],
        "impression_tags": ["全栈大佬", "夜猫子"],
        "importance": 5,
        "notes": "前同事，现在跳槽去大厂了。经常半夜在线，技术问题找他基本都能解决。",
        "birthday": "11-08",
    })

    # 赵六
    zhaoliu = post("/persons", {
        "name": "赵六",
        "remark": "六六",
        "signature": "今天的我也在摸鱼",
        "location": "上海",
        "circle_tags": ["FF14玩家", "技术圈"],
        "impression_tags": ["萌新", "爱问问题"],
        "importance": 2,
        "notes": "2025年初在技术闲聊群认识的，刚入行前端。FF14是豆芽，主职白魔。",
        "birthday": "05-30",
    })

    # ── 3. 创建账号 ──
    print("创建账号...")

    def add_account(person_id, acc_type, acc_id, nickname):
        return post(f"/persons/{person_id}/accounts", {
            "account_type": acc_type,
            "account_identifier": acc_id,
            "current_nickname": nickname,
        })

    if zhangsan:
        a1 = add_account(zhangsan["id"], "QQ", "10001", "剑断红尘")
        add_account(zhangsan["id"], "微信", "zhangsan_wx", "张三")
        add_account(zhangsan["id"], "游戏ID", "SwordMaster", "剑断红尘")

    if lisi:
        a2 = add_account(lisi["id"], "QQ", "20001", "小四画画")
        add_account(lisi["id"], "微信", "lisi_art", "四四")

    if wangwu:
        a3 = add_account(wangwu["id"], "QQ", "30001", "CodeMaster")
        add_account(wangwu["id"], "微信", "wangwu_dev", "王五")
        add_account(wangwu["id"], "游戏ID", "TopKing", "上单之王")

    if zhaoliu:
        a4 = add_account(zhaoliu["id"], "QQ", "40001", "前端小六")
        add_account(zhaoliu["id"], "微信", "zhaoliu_fe", "赵六")

    # ── 4. 账号加入群 ──
    print("账号加入群...")

    def join_group(group_id, account_id, nickname=None):
        return post(f"/groups/{group_id}/members", {
            "account_id": account_id,
            "group_id": group_id,
            "group_nickname": nickname,
        })

    # 获取创建的账号 ID（前几个账号）
    if zhangsan and lol_group:
        accs = requests.get(f"{BASE}/persons/{zhangsan['id']}/accounts").json()
        if len(accs) >= 1:
            join_group(lol_group["id"], accs[0]["id"], "剑断红尘")  # QQ号加入LOL群
        if len(accs) >= 3 and ff14_group:
            join_group(ff14_group["id"], accs[2]["id"], "剑桑")  # 游戏ID加入FF14群

    if lisi and ff14_group:
        accs = requests.get(f"{BASE}/persons/{lisi['id']}/accounts").json()
        if len(accs) >= 1:
            join_group(ff14_group["id"], accs[0]["id"], "小四画画")

    if wangwu:
        accs = requests.get(f"{BASE}/persons/{wangwu['id']}/accounts").json()
        if lol_group and len(accs) >= 1:
            join_group(lol_group["id"], accs[0]["id"], "CodeMaster")
        if work_group and len(accs) >= 2:
            join_group(work_group["id"], accs[1]["id"], "王五")

    if zhaoliu and work_group:
        accs = requests.get(f"{BASE}/persons/{zhaoliu['id']}/accounts").json()
        if len(accs) >= 1:
            join_group(work_group["id"], accs[0]["id"], "前端小六")
        if ff14_group and len(accs) >= 1:
            join_group(ff14_group["id"], accs[0]["id"], "萌新白魔")

    # ── 5. 人物关系 ──
    print("创建人物关系...")
    if zhangsan and lisi:
        post(f"/persons/{zhangsan['id']}/relations", {"person_id_2": lisi["id"], "relation_type": "FF14部队战友"})
    if zhangsan and wangwu:
        post(f"/persons/{zhangsan['id']}/relations", {"person_id_2": wangwu["id"], "relation_type": "LOL开黑队友"})
    if wangwu and zhaoliu:
        post(f"/persons/{wangwu['id']}/relations", {"person_id_2": zhaoliu["id"], "relation_type": "前同事"})
    if lisi and zhaoliu:
        post(f"/persons/{lisi['id']}/relations", {"person_id_2": zhaoliu["id"], "relation_type": "FF14导师-豆芽"})

    # ── 6. 相遇记录 ──
    print("创建相遇记录...")
    if zhangsan:
        post(f"/persons/{zhangsan['id']}/meetings", {"description": "2024年3月LOL排位赛认识，他剑姬1v5翻盘", "met_at": "2024-03"})
    if lisi:
        post(f"/persons/{lisi['id']}/meetings", {"description": "FF14部队招募时加入，说自己是画师可以画部队logo", "met_at": "2024-06"})
    if wangwu:
        post(f"/persons/{wangwu['id']}/meetings", {"description": "上一家公司的同事，坐我旁边工位", "met_at": "2023-01"})
    if zhaoliu:
        post(f"/persons/{zhaoliu['id']}/meetings", {"description": "技术群里一直问前端问题的新人，后来加了微信", "met_at": "2025-02"})

    print("\n种子数据导入完成！")
    print(f"群友: {zhangsan and zhangsan['name']}, {lisi and lisi['name']}, {wangwu and wangwu['name']}, {zhaoliu and zhaoliu['name']}")
    print("群: LOL开黑群, FF14亲友团, 技术闲聊群")


if __name__ == "__main__":
    main()
