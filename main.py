import requests
import json
import time
import schedule
import random
import re
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

# n8n 的 Webhook 地址
N8N_WEBHOOK_URL = "http://43.139.245.223:5678/webhook/6d6ea3d6-ba16-4d9d-9145-22425474ab48"

# 每一轮检查的间隔 (分钟)
CHECK_INTERVAL_MINUTES = 15

# =========================================
# 🔥🔥🔥 启动测试区 🔥🔥🔥
# =========================================
print("🔥 [System] 正在尝试发送测试信号给 n8n...", flush=True)
try:
    test_payload = {
        "source": "twitter_monitor",
        "author": "System_Test",
        "content_raw": "🎉 恭喜！Zeabur 机器人已切换至 [Twstalker 模式]！这是一条测试消息。",
        "link": "https://twitter.com/home",
        "tweet_id": "test_connection_twstalker",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    requests.post(N8N_WEBHOOK_URL, json=test_payload, timeout=10)
    print("✅ [System] 测试信号发送成功！", flush=True)
except Exception as e:
    print(f"❌ [System] 测试信号发送失败: {e}", flush=True)
# =========================================


# 记录上次的 ID
last_seen_ids = {}

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === [Twstalker模式] 开始检查 ({len(TARGET_ACCOUNTS)} 位博主) ===", flush=True)
    
    for username in TARGET_ACCOUNTS:
        try:
            print(f"正在检查: @{username} ...", end="", flush=True)
            
            # === 🔥 修改点 1: 目标变成了 Twstalker ===
            url = f"https://twstalker.com/{username}"
            headers = {
                # 模拟更真实的浏览器头，试图骗过 Cloudflare
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.google.com/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9"
            }
            
            response = requests.get(url, headers=headers, timeout=20)
            
            # 检查是否被 Cloudflare 拦截
            if "Just a moment" in response.text or "Cloudflare" in response.text:
                print(" -> ⚠️ 被 Cloudflare 盾拦截 (403/503)", flush=True)
                continue

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # === 🔥 修改点 2: Twstalker 的 HTML 解析逻辑 ===
                # Twstalker 的页面结构通常包含很多链接，我们需要找到带有 /status/ 的链接
                # 这些链接通常是推文的时间戳链接
                
                found_tweets = []
                
                # 查找所有的链接
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    # 匹配推文链接格式: /username/status/1234567890
                    # 正则表达式提取 ID
                    match = re.search(r'/status/(\d+)', href)
                    if match:
                        tweet_id = match.group(1)
                        
                        # 尝试找到这个链接对应的推文文本
                        # Twstalker 的结构比较乱，通常文本在链接的父级或附近的 div 里
                        # 这里做一个简单的尝试：找这个链接所在的卡片容器
                        # 如果找不到精确的文本，我们至少拿到了 ID，文本可以先空着或者填 "点击查看"
                        
                        # 简单的抓取策略：在这个链接附近找文本
                        # 这种抓取方式不一定完美，但能拿到 ID 最重要
                        card_text = "点击链接查看详情 (Twstalker 解析限制)"
                        try:
                            # 尝试找父级容器的文本
                            parent = link.find_parent('div')
                            if parent:
                                card_text = parent.get_text(strip=True)
                                # 清理掉一些多余的按钮文字
                                card_text = card_text.replace("Reply", "").replace("Share", "").strip()[:200] + "..."
                        except:
                            pass
                            
                        found_tweets.append({
                            'id': tweet_id,
                            'text': card_text,
                            'link': f"https://twitter.com/{username}/status/{tweet_id}"
                        })

                if found_tweets:
                    # === 🔥 优化: 按 ID 倒序排列，取数值最大的（最新的） ===
                    # 这样可以自动忽略掉 ID 较小的置顶推文
                    found_tweets.sort(key=lambda x: int(x['id']), reverse=True)
                    
                    latest_tweet = found_tweets[0]
                    tweet_id = latest_tweet['id']
                    tweet_text = latest_tweet['text']
                    
                    # --- 核心对比逻辑 ---
                    if username not in last_seen_ids:
                        last_seen_ids[username] = tweet_id
                        print(f" -> [初始化] 最新 ID: {tweet_id}", flush=True)
                    
                    elif last_seen_ids[username] != tweet_id:
                        print(f"\n  -> ★ 发现新推文！(Twstalker源) 准备推送...", flush=True)
                        
                        payload = {
                            "source": "twitter_monitor_twstalker",
                            "author": username,
                            "content_raw": tweet_text,
                            "link": latest_tweet['link'],
                            "tweet_id": tweet_id,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S") # Twstalker 抓取时间不准，直接用当前时间
                        }
                        
                        try:
                            requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
                            print("  -> 推送成功 ✅", flush=True)
                            last_seen_ids[username] = tweet_id
                        except Exception as e:
                            print(f"  -> ❌ 推送失败: {e}", flush=True)
                        
                    else:
                        print(f" -> 无更新", flush=True)
                else:
                    print(" -> 未找到任何推文 ID (可能页面结构变了)", flush=True)
            
            elif response.status_code == 403:
                print(" -> 访问被拒绝 (403 Forbidden)", flush=True)
            else:
                print(f" -> 访问失败: {response.status_code}", flush=True)

        except Exception as e:
            print(f" -> 异常: {e}", flush=True)
            
        # 随机延迟
        time.sleep(random.uniform(5, 8))

    print(f"=== 本轮检查结束，等待 {CHECK_INTERVAL_MINUTES} 分钟 ===\n", flush=True)

# 启动后立刻执行一次
get_latest_tweets()

# 定时任务
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(get_latest_tweets)

while True:
    schedule.run_pending()
    time.sleep(1)
