import requests
import time
import schedule
import random
from bs4 import BeautifulSoup
from datetime import datetime

# ================= 配置区 =================
TARGET_ACCOUNTS = [
    "lubi366", "connectfarm1", "wolfyxbt", "Crypto_He", "BroLeon", 
    "0xcryptowizard", "one_snowball", "yueya_eth", "qlonline", 
    "ai_9684xtpa", "cz_binance", "linwanwan823"
]

N8N_WEBHOOK_URL = "http://43.139.245.223:5678/webhook/6d6ea3d6-ba16-4d9d-9145-22425474ab48"
CHECK_INTERVAL_MINUTES = 20

# Nitter 实例列表 (如果一个挂了，会自动试下一个)
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.lucabased.xyz",
    "https://nitter.net"
]
# =========================================

last_seen_ids = {}

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === [Nitter RSS 轮询版] 开始检查 ===", flush=True)
    
    # 随机打乱实例顺序，负载均衡
    current_instances = list(NITTER_INSTANCES)
    random.shuffle(current_instances)

    for username in TARGET_ACCOUNTS:
        success = False
        print(f"正在检查: @{username} ...", end="", flush=True)
        
        for instance in current_instances:
            try:
                # 构造 RSS 地址
                url = f"{instance}/{username}/rss"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                
                # 尝试请求
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # 解析 RSS XML
                    soup = BeautifulSoup(response.content, "xml")
                    items = soup.find_all("item")
                    
                    if items:
                        latest_item = items[0]
                        
                        # 提取信息
                        title = latest_item.title.text
                        link = latest_item.link.text
                        pub_date = latest_item.pubDate.text
                        description = latest_item.description.text
                        
                        # 从链接中提取 ID (格式: .../status/123456789)
                        tweet_id = link.split('/')[-1].split('#')[0]
                        
                        # --- 对比逻辑 ---
                        if username not in last_seen_ids:
                            last_seen_ids[username] = tweet_id
                            print(f" -> [初始化] 最新 ID: {tweet_id} (节点: {instance})", flush=True)
                        
                        elif last_seen_ids[username] != tweet_id:
                            print(f"\n  -> ★ 发现新推文！准备推送...", flush=True)
                            
                            payload = {
                                "source": "twitter_monitor_nitter",
                                "author": username,
                                "content_raw": title, # RSS 的 title 通常就是推文内容
                                "link": link.replace(instance, "https://twitter.com"), # 替换回官方链接
                                "tweet_id": tweet_id,
                                "timestamp": pub_date
                            }
                            
                            try:
                                requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
                                print("  -> 推送成功 ✅", flush=True)
                                last_seen_ids[username] = tweet_id
                            except Exception as e:
                                print(f"  -> ❌ 推送失败: {e}", flush=True)
                        else:
                            print(f" -> 无更新 (节点: {instance})", flush=True)
                        
                        success = True
                        break # 这个节点成功了，跳出实例循环，检查下一个用户
                    else:
                        # 200 OK 但没有 item，可能是空账号或解析失败，尝试下一个节点
                        continue
                else:
                    # 状态码不是 200，尝试下一个节点
                    continue
                    
            except Exception:
                # 发生异常，尝试下一个节点
                continue
        
        if not success:
            print(" -> ❌ 所有 Nitter 节点均访问失败", flush=True)
            
        # 每个用户之间稍微停顿一下
        time.sleep(random.uniform(2, 5))

    print(f"=== 本轮检查结束，等待 {CHECK_INTERVAL_MINUTES} 分钟 ===\n", flush=True)

# 启动
get_latest_tweets()
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(get_latest_tweets)

while True:
    schedule.run_pending()
    time.sleep(1)
