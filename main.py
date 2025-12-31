from curl_cffi import requests
import time
import schedule
import random
import json
from datetime import datetime

# ================= 配置区域 =================

TARGET_ACCOUNTS = [
    "lubi366", "connectfarm1", "wolfyxbt", "Crypto_He", "BroLeon", 
    "0xcryptowizard", "one_snowball", "yueya_eth", "qlonline", 
    "ai_9684xtpa", "cz_binance", "linwanwan823"
]

N8N_WEBHOOK_URL = "http://43.139.245.223:5678/webhook/6d6ea3d6-ba16-4d9d-9145-22425474ab48"

# ================= 🔴 核心凭证 (请确认 Cookie 是最新的) =================

raw_cookie_str = """
guest_id=v1%3A176710344905549891; auth_token=c3778b43e1705ad15fd2e8b683087db33fb3aa1e; ct0=368af3c63dffcc690f8557421437270654944077c8fdd21103da457e4225508284c606385efa8dd6b74c5463e87eb42c0c91b68620b1e1827e0c8e8eb1db381efcc70fdce615e3d0351dc886b27b0cf0; lang=en; twid=u%3D2006001874949009408; personalization_id="v1_H+HZUYrPDKtvqjYJt3R+rw=="
"""

cookies = {}
for item in raw_cookie_str.split(';'):
    if '=' in item:
        name, value = item.split('=', 1)
        cookies[name.strip()] = value.strip()

csrf_token = cookies.get('ct0')

headers = {
    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
    'content-type': 'application/json',
    'x-csrf-token': csrf_token,
    'x-twitter-auth-type': 'OAuth2Session',
    'x-twitter-client-language': 'en',
    'referer': 'https://x.com/',
    'origin': 'https://x.com',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

# ================= ⚡️ 移植自开源项目的最新 ID =================

# 1. 获取 ID: UserByScreenName
URL_ID = 'https://x.com/i/api/graphql/xc8f1g7BYqr6VTzTbvNlGw/UserByScreenName'

# 2. 获取推文: UserTweets
URL_TWEETS = 'https://x.com/i/api/graphql/9zyyd1hebl7oNWIPdA8HRw/UserTweets'

user_id_cache = {} 
last_seen_ids = {}

def get_user_id(username):
    """根据用户名换取数字ID"""
    if username in user_id_cache:
        return user_id_cache[username]
    
    # 严格按照开源项目的参数配置
    variables = {
        "screen_name": username, 
        "withSafetyModeUserFields": False
    }
    features = {
        "hidden_profile_likes_enabled": False, 
        "hidden_profile_subscriptions_enabled": False, 
        "responsive_web_graphql_exclude_directive_enabled": True, 
        "verified_phone_label_enabled": False, 
        "subscriptions_verification_info_verified_since_enabled": True, 
        "highlights_tweets_tab_ui_enabled": True, 
        "creator_subscriptions_tweet_preview_api_enabled": True, 
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False, 
        "responsive_web_graphql_timeline_navigation_enabled": True
    }
    fieldToggles = {"withAuxiliaryUserLabels": False}
    
    try:
        # 这里把 fieldToggles 也加进去了，确保万无一失
        params = {
            'variables': json.dumps(variables), 
            'features': json.dumps(features),
            'fieldToggles': json.dumps(fieldToggles)
        }
        r = requests.get(URL_ID, params=params, cookies=cookies, headers=headers, impersonate="chrome110", timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            # 路径: data -> user -> result -> rest_id
            uid = data.get('data', {}).get('user', {}).get('result', {}).get('rest_id')
            if uid:
                user_id_cache[username] = uid
                return uid
        else:
            print(f"   ❌ ID接口报错 [{r.status_code}]: {r.text[:50]}", flush=True)
            
    except Exception as e:
        print(f"   ❌ ID网络异常: {e}", flush=True)
    
    return None

def fetch_tweets(username, uid):
    """获取该ID的推文"""
    variables = {
        "userId": uid,
        "count": 20,
        "includePromotedContent": True,
        "withQuickPromoteEligibilityTweetFields": True,
        "withVoice": True,
        "withV2Timeline": True
    }
    # 这里的 features 也是直接从那个项目中提取的，非常完整
    features = {
        "rweb_tipjar_consumption_enabled": True,
        "responsive_web_graphql_exclude_directive_enabled": True,
        "verified_phone_label_enabled": False,
        "creator_subscriptions_tweet_preview_api_enabled": True,
        "responsive_web_graphql_timeline_navigation_enabled": True,
        "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
        "communities_web_enable_tweet_community_results_fetch": True,
        "c9s_tweet_anatomy_moderator_badge_enabled": True,
        "articles_preview_enabled": True,
        "tweetypie_unmention_optimization_enabled": True,
        "responsive_web_edit_tweet_api_enabled": True,
        "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
        "view_counts_everywhere_api_enabled": True,
        "longform_notetweets_consumption_enabled": True,
        "responsive_web_twitter_article_tweet_consumption_enabled": True,
        "tweet_awards_web_tipping_enabled": False,
        "creator_subscriptions_quote_tweet_preview_enabled": False,
        "freedom_of_speech_not_reach_fetch_enabled": True,
        "standardized_nudges_misinfo": True,
        "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
        "tweet_with_visibility_results_prefer_gql_media_interstitial_enabled": True,
        "rweb_video_timestamps_enabled": True,
        "longform_notetweets_rich_text_read_enabled": True,
        "longform_notetweets_inline_media_enabled": True,
        "responsive_web_enhance_cards_enabled": False
    }
    fieldToggles = {"withArticlePlainText": False}

    try:
        params = {
            'variables': json.dumps(variables), 
            'features': json.dumps(features),
            'fieldToggles': json.dumps(fieldToggles)
        }
        return requests.get(URL_TWEETS, params=params, cookies=cookies, headers=headers, impersonate="chrome110", timeout=15)
    except Exception as e:
        return None

def main_loop():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === 启动开源项目移植版 ===", flush=True)
    
    if not csrf_token:
        print("❌ 错误: Cookie 无效！", flush=True)
        return

    for username in TARGET_ACCOUNTS:
        print(f"Checking: @{username} ... ", end="", flush=True)
        
        # 1. 尝试获取 ID
        uid = get_user_id(username)
        if not uid:
            print(" -> ❌ 无法获取ID", flush=True)
            time.sleep(2)
            continue
            
        # 2. 获取推文
        resp = fetch_tweets(username, uid)
        
        if resp and resp.status_code == 200:
            try:
                timeline = resp.json().get('data', {}).get('user', {}).get('result', {}).get('timeline_v2', {}).get('timeline', {})
                instructions = timeline.get('instructions', [])
                
                entries = []
                for i in instructions:
                    if i.get('type') == 'TimelineAddEntries':
                        entries = i.get('entries', [])
                        break
                
                new_tweets = []
                for entry in entries:
                    if 'tweet' in entry['entryId']:
                        legacy = entry.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {}).get('legacy')
                        if legacy:
                            tid = legacy['id_str']
                            if username not in last_seen_ids:
                                last_seen_ids[username] = tid
                                print(f"✅ 初始化: {tid}", flush=True)
                                break
                            
                            if tid > last_seen_ids[username]:
                                new_tweets.append(legacy)

                if new_tweets:
                    new_tweets.sort(key=lambda x: x['id_str'])
                    print(f"🚀 新推文: {len(new_tweets)}条", flush=True)
                    for t in new_tweets:
                        tid = t['id_str']
                        payload = {
                            "source": "monitor_v5_opensource",
                            "author": username,
                            "content_raw": t['full_text'],
                            "link": f"https://x.com/{username}/status/{tid}",
                            "timestamp": t['created_at']
                        }
                        try:
                            requests.post(N8N_WEBHOOK_URL, json=payload, timeout=5)
                        except:
                            pass
                        last_seen_ids[username] = tid
                elif username in last_seen_ids:
                    print("无更新", flush=True)

            except Exception as e:
                print(f"解析异常: {e}", flush=True)

        elif resp and resp.status_code == 429:
            print("⚠️ 限流 (休息60s)", flush=True)
            time.sleep(60)
        else:
            msg = resp.text[:50] if resp else "Error"
            code = resp.status_code if resp else "Err"
            print(f"❌ 获取失败 [{code}]: {msg}", flush=True)

        time.sleep(random.uniform(8, 15))

    print("=== 休息 12 分钟 ===", flush=True)

if __name__ == "__main__":
    print("🔥 [System] 开源移植版启动...", flush=True)
    main_loop()
    schedule.every(12).minutes.do(main_loop)

    while True:
        schedule.run_pending()
        time.sleep(1)
