import requests
import json
import time
import schedule
from bs4 import BeautifulSoup
from datetime import datetime

# ================= 配置区 =================
# 目标博主 ID (不带 @)
TARGET_USERNAME = "elonmusk"

# 你的 n8n Webhook 地址
N8N_WEBHOOK_URL = "https://你的n8n地址/webhook-test/twitter-monitor"

# 检测频率 (分钟) - 建议不低于 10 分钟，保护 IP
CHECK_INTERVAL = 15
# =========================================

# 记录上一次发送的推文 ID，防止重复推送
last_seen_id = None

def get_latest_tweet():
    global last_seen_id
    print(f"[{datetime.now()}] 正在检查 @{TARGET_USERNAME} 的推文...")
    
    try:
        # 使用 Syndication 接口 (模拟网页嵌入访问)
        url = f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{TARGET_USERNAME}"
        
        # 伪装成普通浏览器
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return

        # 解析 HTML 里的隐藏 JSON 数据
        soup = BeautifulSoup(response.text, "html.parser")
        next_data = soup.find("script", {"id": "__NEXT_DATA__"})
        
        if not next_data:
            print("未找到数据标记，接口可能变动")
            return

        data = json.loads(next_data.string)
        
        # 提取推文列表 (路径可能会随推特前端更新微调，但 Syndication 相对稳定)
        try:
            timeline = data['props']['pageProps']['timeline']['entries']
            # 取第一条最新的
            latest_entry = timeline[0]
            tweet_content = latest_entry['content']['tweet']
            
            tweet_id = tweet_content['id_str']
            tweet_text = tweet_content['text']
            created_at = tweet_content['created_at']
            
            print(f"最新推文 ID: {tweet_id}")

            # 检查是否是新的
            if last_seen_id != tweet_id:
                print("发现新推文！准备推送...")
                
                # 构造发送给 n8n 的数据
                payload = {
                    "username": TARGET_USERNAME,
                    "tweet_text": tweet_text,
                    "tweet_url": f"https://twitter.com/{TARGET_USERNAME}/status/{tweet_id}",
                    "created_at": created_at,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 推送
                requests.post(N8N_WEBHOOK_URL, json=payload)
                
                # 更新缓存
                last_seen_id = tweet_id
                print("推送成功！")
            else:
                print("暂无新推文。")
                
        except KeyError as e:
            print(f"数据解析错误 (可能是广告或置顶干扰): {e}")
            
    except Exception as e:
        print(f"发生未知错误: {e}")

# 初始化运行一次
get_latest_tweet()

# 设定定时任务
schedule.every(CHECK_INTERVAL).minutes.do(get_latest_tweet)

print(f"监控服务已启动... 每 {CHECK_INTERVAL} 分钟检查一次")

# 死循环维持服务运行 (24/7)
while True:
    schedule.run_pending()
    time.sleep(1)
