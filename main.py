import requests
import json
import time
import schedule
import random
from bs4 import BeautifulSoup
from datetime import datetime

# ================= 配置区 =================
# 你的关注列表 (不带 @)
TARGET_ACCOUNTS = [
    "cz_binance",
    "elonmusk",
    "connectfarm1",
    "ai_9684xtpa",
    "coindesk",
    "lookonchain",
    "cryptoquant_com",
    "yueya_eth",
    "wolfyxbt"
]

# n8n 的 Webhook 地址 (从 n8n 获取的那个 Test/Production URL)
N8N_WEBHOOK_URL = "http://43.139.57.215:5678/webhook-test/6d6ea3d6-ba16-4d9d-9145-22425474ab48"

# 每一轮检查的间隔 (分钟) - 建议 15-20 分钟
CHECK_INTERVAL_MINUTES = 15
# =========================================

# 用字典来记录每个博主上次的推文 ID: {"elonmusk": "12345", "cz_binance": "67890"}
last_seen_ids = {}

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === 开始新一轮检查 ({len(TARGET_ACCOUNTS)} 位博主) ===")
    
    for username in TARGET_ACCOUNTS:
        try:
            print(f"正在检查: @{username} ...")
            
            # 使用 Syndication 接口
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
                        # 尝试提取最新推文
                        entries = data['props']['pageProps']['timeline']['entries']
                        # 找到第一条是推文的内容（跳过可能的置顶广告）
                        latest_tweet = None
                        for entry in entries:
                            if entry['type'] == 'Tweet':
                                latest_tweet = entry
                                break
                        
                        # 如果上面的循环没找到，有时候结构不同，直接取第一个试试
                        if not latest_tweet and entries:
                            latest_tweet = entries[0]

                        if latest_tweet:
                            tweet_content = latest_tweet['content']['tweet']
                            tweet_id = tweet_content['id_str']
                            tweet_text = tweet_content['text']
                            created_at = tweet_content['created_at']
                            
                            # 初始化：如果这是脚本第一次运行，只记录ID不发送，避免刚启动就狂发旧消息
                            if username not in last_seen_ids:
                                last_seen_ids[username] = tweet_id
                                print(f"  -> 初始化状态，记录最新 ID: {tweet_id}")
                            
                            # 如果发现新 ID
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
                                
                                # 推送给 n8n
                                try:
                                    requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
                                    print("  -> 推送成功")
                                except Exception as e:
                                    print(f"  -> 推送失败: {e}")
                                
                                # 更新记录
                                last_seen_ids[username] = tweet_id
                            else:
                                print("  -> 无更新")
                                
                    except (KeyError, IndexError, TypeError) as e:
                        print(f"  -> 数据解析跳过: {e}")
            else:
                print(f"  -> 接口访问失败: {response.status_code}")

        except Exception as e:
            print(f"  -> 发生异常: {e}")
            
        # --- 关键：每检查完一个人，休息 3~6 秒 ---
        # 这样能极大降低被封 IP 的概率
        sleep_time = random.uniform(3, 6)
        time.sleep(sleep_time)

    print(f"=== 本轮检查结束，等待 {CHECK_INTERVAL_MINUTES} 分钟 ===\n")

# 启动时立刻运行一次
get_latest_tweets()

# 定时任务
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(get_latest_tweets)

while True:
    schedule.run_pending()
    time.sleep(1)
