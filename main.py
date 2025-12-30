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
        "content_raw": "🎉 恭喜！Zeabur 机器人已切换至 [Sotwe镜像模式]！这是一条测试消息。",
        "link": "https://twitter.com/home",
        "tweet_id": "test_connection_sotwe",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    # 发送测试包
    requests.post(N8N_WEBHOOK_URL, json=test_payload, timeout=10)
    print("✅ [System] 测试信号发送成功！快去 n8n 看绿灯！", flush=True)
except Exception as e:
    print(f"❌ [System] 测试信号发送失败: {e}", flush=True)
    print("   (提示：请检查 n8n 的 Webhook 地址是否正确，或者 n8n 是否正在运行)", flush=True)
# =========================================


# 记录上次的 ID
last_seen_ids = {}

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === [Sotwe模式] 开始检查 ({len(TARGET_ACCOUNTS)} 位博主) ===", flush=True)
    
    for username in TARGET_ACCOUNTS:
        try:
            print(f"正在检查: @{username} ...", end="", flush=True)
            
            # === 🔥 修改点 1: 目标变成了 Sotwe 镜像站 ===
            url = f"https://www.sotwe.com/{username}"
            headers = {
                # 伪装成普通浏览器，防止 Cloudflare 拦截
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.google.com/"
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # === 🔥 修改点 2: Sotwe 的数据也在 __NEXT_DATA__ 里，但结构不同 ===
                next_data = soup.find("script", {"id": "__NEXT_DATA__"})
                
                if next_data:
                    data = json.loads(next_data.string)
                    try:
                        # Sotwe 的 JSON 路径: props -> pageProps -> data -> posts
                        # 注意：Sotwe 有时候会返回空列表，需要判断
                        user_data = data.get('props', {}).get('pageProps', {}).get('data', {})
                        posts = user_data.get('posts', [])
                        
                        if posts:
                            # === 🔥 优化: 强制按时间倒序排列，防止置顶推文干扰 🔥 ===
                            # Sotwe 的时间字段是 createdAt (毫秒时间戳)
                            posts.sort(key=lambda x: int(x['createdAt']), reverse=True)
                            
                            # 取最新的一条
                            latest_post = posts[0]
                            
                            # 提取字段 (Sotwe 的字段名和推特官方不一样)
                            tweet_id = latest_post['id']   # Sotwe 直接用推特 ID
                            tweet_text = latest_post['text']
                            
                            # 时间处理：毫秒转字符串
                            created_at_ts = int(latest_post['createdAt']) / 1000
                            created_at_str = datetime.fromtimestamp(created_at_ts).strftime('%Y-%m-%d %H:%M:%S')

                            # --- 核心对比逻辑 ---
                            # 初始化
                            if username not in last_seen_ids:
                                last_seen_ids[username] = tweet_id
                                print(f" -> [初始化] 最新 ID: {tweet_id}", flush=True)
                            
                            # 发现新推文
                            elif last_seen_ids[username] != tweet_id:
                                print(f"\n  -> ★ 发现新推文！(Sotwe源) 准备推送...", flush=True)
                                
                                payload = {
                                    "source": "twitter_monitor_sotwe",
                                    "author": username,
                                    "content_raw": tweet_text,
                                    # 链接我们还是拼凑成推特官方的，方便你点击跳转
                                    "link": f"https://twitter.com/{username}/status/{tweet_id}",
                                    "tweet_id": tweet_id,
                                    "timestamp": created_at_str
                                }
                                
                                try:
                                    requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
                                    print("  -> 推送成功 ✅", flush=True)
                                    last_seen_ids[username] = tweet_id
                                except Exception as e:
                                    print(f"  -> ❌ 推送失败: {e}", flush=True)
                                
                            else:
                                print(f" -> 无更新 ({created_at_str})", flush=True)
                        else:
                            print(" -> 未找到推文 (可能是空号或被隐藏)", flush=True)
                                
                    except Exception as e:
                        # 捕获解析错误，防止程序崩溃
                        print(f" -> 解析结构异常: {e}", flush=True)
                else:
                    print(" -> 未找到数据标签 (__NEXT_DATA__)", flush=True)
            else:
                print(f" -> 访问失败: {response.status_code}", flush=True)

        except Exception as e:
            print(f" -> 网络或其他异常: {e}", flush=True)
            
        # 随机延迟，虽然 Sotwe 不怎么封号，但保持礼貌是好习惯
        sleep_time = random.uniform(5, 8)
        time.sleep(sleep_time)

    print(f"=== 本轮检查结束，等待 {CHECK_INTERVAL_MINUTES} 分钟 ===\n", flush=True)

# 启动后立刻执行一次检查
get_latest_tweets()

# 定时任务
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(get_latest_tweets)

while True:
    schedule.run_pending()
    time.sleep(1)
