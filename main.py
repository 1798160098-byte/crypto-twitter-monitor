import requests
import json
import time
import schedule
import random
from bs4 import BeautifulSoup
from datetime import datetime

# ================= 配置区 =================
# 你的关注列表
TARGET_ACCOUNTS = [
    "lubi366",
    "connectfarm1",
    "wolfyxbt",
    "Crypto_He",
    "BroLeon",
    "0xcryptowizard",
    "one_snowball",
    "yueya_eth",
    "qlonline",
    "ai_9684xtpa",
    "cz_binance",
    "linwanwan823"
]

# n8n 的 Webhook 地址 (这是你截图里的测试地址)
# 如果你以后换了 Production URL，记得回来改这里
N8N_WEBHOOK_URL = "http://43.139.245.223:5678/webhook/6d6ea3d6-ba16-4d9d-9145-22425474ab48"

# 每一轮检查的间隔 (分钟)
CHECK_INTERVAL_MINUTES = 15

# =========================================
# 🔥🔥🔥 核心修改区：启动时强制发一条测试消息 🔥🔥🔥
# =========================================
print("🔥 [System] 正在尝试发送测试信号给 n8n...")
try:
    test_payload = {
        "source": "twitter_monitor",
        "author": "System_Test",
        "content_raw": "🎉 恭喜！Zeabur 机器人已成功连通 n8n！这是一条测试消息，说明链路畅通。",
        "link": "https://twitter.com/home",
        "tweet_id": "test_connection_001",
        "timestamp": datetime.now().strftime("%a %b %d %H:%M:%S +0000 %Y")
    }
    # 发送测试包
    requests.post(N8N_WEBHOOK_URL, json=test_payload, timeout=10)
    print("✅ [System] 测试信号发送成功！快去 n8n 看绿灯！")
except Exception as e:
    print(f"❌ [System] 测试信号发送失败: {e}")
    print("   (提示：请检查 n8n 的 Webhook 地址是否正确，或者 n8n 是否正在运行)")
# =========================================


# 记录上次的 ID
last_seen_ids = {}

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === 开始新一轮检查 ({len(TARGET_ACCOUNTS)} 位博主) ===")
    
    for username in TARGET_ACCOUNTS:
        try:
            print(f"正在检查: @{username} ...")
            
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                next_data = soup.find("script", {"id": "__NEXT_DATA__"})
                
                if next_data:
                    data = json.loads(next_data.string)
                    try:
                        entries = data['props']['pageProps']['timeline']['entries']
                        latest_tweet = None
                        for entry in entries:
                            if entry['type'] == 'Tweet':
                                latest_tweet = entry
                                break
                        
                        if not latest_tweet and entries:
                            latest_tweet = entries[0]

                        if latest_tweet:
                            tweet_content = latest_tweet['content']['tweet']
                            tweet_id = tweet_content['id_str']
                            tweet_text = tweet_content['text']
                            created_at = tweet_content['created_at']
                            
                            # 初始化：第一次只记录，不发送 (避免刷屏旧消息)
                            if username not in last_seen_ids:
                                last_seen_ids[username] = tweet_id
                                print(f"  -> 初始化状态，记录最新 ID: {tweet_id}")
                            
                            # 发现新推文
                            elif last_seen_ids[username] != tweet_id:
                                print(f"  -> ★ 发现新推文！准备推送...")
                                
                                payload = {
                                    "source": "twitter_monitor",
                                    "author": username,
                                    "content_raw": tweet_text,
                                    "link": f"https://twitter.com/{username}/status/{tweet_id}",
                                    "tweet_id": tweet_id,
                                    "timestamp": created_at
                                }
                                
                                requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
                                print("  -> 推送成功")
                                
                                last_seen_ids[username] = tweet_id
                            else:
                                print("  -> 无更新")
                                
                    except Exception as e:
                        print(f"  -> 数据解析跳过: {e}")
            else:
                print(f"  -> 接口访问失败: {response.status_code}")

        except Exception as e:
            print(f"  -> 发生异常: {e}")
            
        # 防止封禁的随机延迟
        sleep_time = random.uniform(3, 6)
        time.sleep(sleep_time)

    print(f"=== 本轮检查结束，等待 {CHECK_INTERVAL_MINUTES} 分钟 ===\n")

# 启动后立刻执行一次检查
get_latest_tweets()

# 定时任务
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(get_latest_tweets)

while True:
    schedule.run_pending()
    time.sleep(1)
