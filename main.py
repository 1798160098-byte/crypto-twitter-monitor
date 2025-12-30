import requests
import json
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

# 建议稍微调长一点，15-20分钟，太频繁容易触发 Rate Limit
CHECK_INTERVAL_MINUTES = 20 

# 随机 User-Agent 池，伪装成不同设备
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
]
# =========================================

last_seen_ids = {}

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === [官方接口复活版] 开始检查 ===", flush=True)
    
    for username in TARGET_ACCOUNTS:
        try:
            print(f"正在检查: @{username} ...", end="", flush=True)
            
            # 随机参数 + 官方 syndication 接口
            ts = int(time.time())
            url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{username}?t={ts}"
            
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Referer": "https://twitter.com/",
                "Accept-Language": "en-US,en;q=0.9"
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                next_data = soup.find("script", {"id": "__NEXT_DATA__"})
                
                if next_data:
                    data = json.loads(next_data.string)
                    try:
                        # 官方路径提取
                        entries = data['props']['pageProps']['timeline']['entries']
                        tweets = [e for e in entries if e['type'] == 'Tweet']
                        
                        if tweets:
                            latest_tweet = tweets[0]
                            content = latest_tweet['content']['tweet']
                            tweet_id = content['id_str']
                            tweet_text = content['text']
                            created_at = content['created_at'] # e.g., Thu Apr 06 15:28:43 +0000 2023
                            
                            # 时间格式美化
                            try:
                                dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
                                readable_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                readable_time = created_at

                            # --- 对比逻辑 ---
                            if username not in last_seen_ids:
                                last_seen_ids[username] = tweet_id
                                print(f" -> [初始化] 最新 ID: {tweet_id}", flush=True)
                            
                            elif last_seen_ids[username] != tweet_id:
                                print(f"\n  -> ★ 发现新推文！推送中...", flush=True)
                                
                                payload = {
                                    "source": "twitter_monitor_official",
                                    "author": username,
                                    "content_raw": tweet_text,
                                    "link": f"https://twitter.com/{username}/status/{tweet_id}",
                                    "tweet_id": tweet_id,
                                    "timestamp": readable_time
                                }
                                
                                try:
                                    requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
                                    print("  -> 推送成功 ✅", flush=True)
                                    last_seen_ids[username] = tweet_id
                                except Exception as e:
                                    print(f"  -> ❌ 推送失败: {e}", flush=True)
                            else:
                                print(f" -> 无更新 ({readable_time})", flush=True)
                        else:
                            print(" -> 列表为空", flush=True)
                    except Exception as e:
                        print(f" -> 解析跳过: {e}", flush=True)
                else:
                    print(" -> 未找到数据标签", flush=True)
            elif response.status_code == 429:
                print(" -> ⚠️ 限流 (Rate Limit)，休息一会", flush=True)
            else:
                print(f" -> 访问失败: {response.status_code}", flush=True)

        except Exception as e:
            print(f" -> 异常: {e}", flush=True)
            
        # 增加延迟，防止触发 429
        time.sleep(random.uniform(10, 15))

    print(f"=== 本轮结束，等待 {CHECK_INTERVAL_MINUTES} 分钟 ===\n", flush=True)

# 启动
print("🔥 [System] 机器人已复活，使用官方接口通道...", flush=True)
get_latest_tweets()
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(get_latest_tweets)

while True:
    schedule.run_pending()
    time.sleep(1)
