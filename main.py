import requests
import json
import time
import schedule
import random
from datetime import datetime

# ================= 核心配置区 =================
# 1. 刚刚提取的 Query ID (注意大小写！)
# 根据你的截图，这里填的是大写 F 的版本。如果报错 404，请尝试改成小写 f
CURRENT_QUERY_ID = "M1jEez78PEFVfbQLvlWMvQ"

# 2. 你的 Cookie 凭证
MY_AUTH_TOKEN = "c3778b43e1705ad15fd2e8b683087db33fb3aa1e"
MY_CT0 = "368af3c63dffcc690f8557421437270654944077c8fdd21103da457e4225508284c606385efa8dd6b74c5463e87eb42c0c91b68620b1e1827e0c8e8eb1db381efcc70fdce615e3d0351dc886b27b0cf0"

# 3. 监控目标
TARGET_ACCOUNTS = [
    "lubi366", "connectfarm1", "wolfyxbt", "Crypto_He", "BroLeon", 
    "0xcryptowizard", "one_snowball", "yueya_eth", "qlonline", 
    "ai_9684xtpa", "cz_binance", "linwanwan823"
]

# 4. n8n 地址
N8N_WEBHOOK_URL = "http://43.139.245.223:5678/webhook/6d6ea3d6-ba16-4d9d-9145-22425474ab48"

# 5. 时间设置：16分钟一轮
CHECK_INTERVAL_MINUTES = 16 
# ============================================

last_seen_ids = {}

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === [Cookie 登录版] 开始检查 ===", flush=True)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
        "Content-Type": "application/json",
        "X-Csrf-Token": MY_CT0,
        "x-twitter-active-user": "yes",
        "x-twitter-auth-type": "OAuth2Session",
        "x-twitter-client-language": "en",
        "Cookie": f"auth_token={MY_AUTH_TOKEN}; ct0={MY_CT0}"
    }

    # 动态拼接 URL
    url = f"https://x.com/i/api/graphql/{CURRENT_QUERY_ID}/SearchTimeline"

    for username in TARGET_ACCOUNTS:
        try:
            print(f"正在检查: @{username} ...", end="", flush=True)
            
            # 构造参数
            params = {
                "variables": json.dumps({
                    "rawQuery": f"from:{username}",
                    "count": 5,
                    "querySource": "typed_query",
                    "product": "Latest"
                }),
                "features": json.dumps({
                    "responsive_web_graphql_exclude_directive_enabled": True,
                    "verified_phone_label_enabled": False,
                    "responsive_web_home_pinned_timelines_enabled": True,
                    "creator_subscriptions_tweet_preview_api_enabled": True,
                    "responsive_web_graphql_timeline_navigation_enabled": True,
                    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                    "c9s_tweet_anatomy_moderation_enabled": False,
                    "tweet_fyp_is_dont_mention_me_view_enabled": True,
                    "responsive_web_edit_tweet_api_enabled": True,
                    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                    "view_counts_everywhere_api_enabled": True,
                    "longform_notetweets_consumption_enabled": True,
                    "responsive_web_twitter_article_tweet_consumption_enabled": False,
                    "tweet_awards_web_tipping_enabled": False,
                    "freedom_of_speech_not_reach_fetch_enabled": True,
                    "standardized_nudges_misinfo": True,
                    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                    "rweb_video_timestamps_enabled": True,
                    "longform_notetweets_rich_text_read_enabled": True,
                    "longform_notetweets_inline_media_enabled": True,
                    "responsive_web_media_download_video_enabled": False,
                    "responsive_web_enhance_cards_enabled": False
                })
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                try:
                    # 尝试解析
                    instructions = data['data']['search_by_raw_query']['search_timeline']['timeline']['instructions']
                    entries = []
                    for instr in instructions:
                        if instr['type'] == 'TimelineAddEntries':
                            entries = instr['entries']
                            break
                    
                    found_tweet = None
                    for entry in entries:
                        if 'tweet' in entry['entryId']: 
                            item_content = entry['content']['itemContent']['tweet_results']['result']
                            if 'legacy' in item_content:
                                found_tweet = item_content['legacy']
                            elif 'tweet' in item_content: 
                                found_tweet = item_content['tweet']['legacy']
                            if found_tweet:
                                break
                    
                    if found_tweet:
                        tweet_id = found_tweet['id_str']
                        full_text = found_tweet['full_text']
                        created_at = found_tweet['created_at']
                        
                        if username not in last_seen_ids:
                            last_seen_ids[username] = tweet_id
                            print(f" -> [初始化] 最新 ID: {tweet_id}", flush=True)
                        elif last_seen_ids[username] != tweet_id:
                            print(f"\n  -> ★ 发现新推文！推送中...", flush=True)
                            payload = {
                                "source": "twitter_monitor_auth",
                                "author": username,
                                "content_raw": full_text,
                                "link": f"https://twitter.com/{username}/status/{tweet_id}",
                                "tweet_id": tweet_id,
                                "timestamp": created_at
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
                        print(" -> 未找到内容 (可能被过滤)", flush=True)

                except Exception as e:
                    print(f" -> 解析跳过: {e}", flush=True)
            elif response.status_code == 404:
                print(" -> ❌ ID 错误 (404)！请检查 QUERY_ID 的大小写！", flush=True)
                break 
            elif response.status_code == 401 or response.status_code == 403:
                print(" -> ❌ 认证失败 (Cookie失效)", flush=True)
            elif response.status_code == 429:
                print(" -> ⚠️ 访问频繁", flush=True)
            else:
                print(f" -> 请求失败: {response.status_code}", flush=True)

        except Exception as e:
            print(f" -> 异常: {e}", flush=True)
            
        # 设置为 8 到 12 秒的随机等待
        sleep_time = random.uniform(8, 12)
        time.sleep(sleep_time)

    print(f"=== 本轮结束，等待 {CHECK_INTERVAL_MINUTES} 分钟 ===\n", flush=True)

print("🔥 [System] 启动...", flush=True)
get_latest_tweets()
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(get_latest_tweets)

while True:
    schedule.run_pending()
    time.sleep(1)
