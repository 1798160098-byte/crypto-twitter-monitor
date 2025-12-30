import cloudscraper
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

# Nitter 实例池 (精选比较稳的)
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.lucabased.xyz",
    "https://nitter.net"
]
# =========================================

last_seen_ids = {}

# 创建一个能够绕过 Cloudflare 的 scraper 实例
# browser 参数模拟 Chrome 桌面版
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === [Cloudscraper 破盾版] 开始检查 ===", flush=True)
    
    # 随机打乱节点顺序
    current_instances = list(NITTER_INSTANCES)
    random.shuffle(current_instances)

    for username in TARGET_ACCOUNTS:
        success = False
        print(f"正在检查: @{username} ...", end="", flush=True)
        
        for instance in current_instances:
            try:
                # 目标：Nitter 的 RSS 页面
                url = f"{instance}/{username}/rss"
                
                # 使用 scraper 发送请求，而不是 requests
                response = scraper.get(url, timeout=15)
                
                if response.status_code == 200:
                    # 解析 XML
                    soup = BeautifulSoup(response.content, "xml")
                    items = soup.find_all("item")
                    
                    if items:
                        latest_item = items[0]
                        title = latest_item.title.text
                        link = latest_item.link.text
                        pub_date = latest_item.pubDate.text
                        
                        # ID 提取
                        tweet_id = link.split('/')[-1].split('#')[0]
                        
                        # --- 对比逻辑 ---
                        if username not in last_seen_ids:
                            last_seen_ids[username] = tweet_id
                            print(f" -> [初始化] 最新 ID: {tweet_id} (节点: {instance})", flush=True)
                        
                        elif last_seen_ids[username] != tweet_id:
                            print(f"\n  -> ★ 发现新推文！推送中...", flush=True)
                            
                            payload = {
                                "source": "twitter_monitor_cloudscraper",
                                "author": username,
                                "content_raw": title,
                                "link": f"https://twitter.com/{username}/status/{tweet_id}",
                                "tweet_id": tweet_id,
                                "timestamp": pub_date
                            }
                            
                            try:
                                # Webhook 依然用普通 requests 发送即可
                                import requests 
                                requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
                                print("  -> 推送成功 ✅", flush=True)
                                last_seen_ids[username] = tweet_id
                            except Exception as e:
                                print(f"  -> ❌ 推送失败: {e}", flush=True)
                        else:
                            print(f" -> 无更新 (节点: {instance})", flush=True)
                        
                        success = True
                        break # 成功则跳出实例循环
                    else:
                        # 200 但无内容
                        continue
                else:
                    # 如果不是 200，说明这个节点可能也被封了，试下一个
                    continue

            except Exception as e:
                # print(f" (节点 {instance} 异常: {e}) ", end="") # 调试用
                continue
        
        if not success:
            print(" -> ❌ 全节点失败 (IP可能被暂时拉黑)", flush=True)
            
        time.sleep(random.uniform(3, 6))

    print(f"=== 本轮结束，等待 {CHECK_INTERVAL_MINUTES} 分钟 ===\n", flush=True)

# 启动
get_latest_tweets()
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(get_latest_tweets)

while True:
    schedule.run_pending()
    time.sleep(1)
