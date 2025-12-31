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

# ================= 核心凭证 (已更新) =================

# 1. 这里填入你刚刚提供的最新 Cookie
# 包含了认证所需的最核心三个值
cookies = {
    'guest_id': 'v1%3A176710344905549891',
    'auth_token': 'c3778b43e1705ad15fd2e8b683087db33fb3aa1e',
    'ct0': '368af3c63dffcc690f8557421437270654944077c8fdd21103da457e4225508284c606385efa8dd6b74c5463e87eb42c0c91b68620b1e1827e0c8e8eb1db381efcc70fdce615e3d0351dc886b27b0cf0',
    # 补充一些通常不会变的辅助 Cookie，增加真实度
    'lang': 'en',
    'twid': 'u%3D2006001874949009408', 
    'personalization_id': '"v1_H+HZUYrPDKtvqjYJt3R+rw=="',
}

# 2. Header 设置
# 注意：这里删除了 User-Agent，完全交给 curl_cffi 生成，防止指纹冲突
headers = {
    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
    'content-type': 'application/json',
    'x-csrf-token': cookies['ct0'],  # 🔥 关键：必须与 Cookie 中的 ct0 一致
    'x-twitter-auth-type': 'OAuth2Session',
    'x-twitter-client-language': 'en',
}

features_json = '{"rweb_video_screen_enabled":false,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":false,"rweb_tipjar_consumption_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"responsive_web_grok_show_grok_translated_post":false,"responsive_web_grok_analysis_button_from_backend":true,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,"responsive_web_enhance_cards_enabled":false}'

BASE_URL = 'https://x.com/i/api/graphql/M1jEez78PEfVfbQLvlWMvQ/SearchTimeline'
last_seen_ids = {}

def fetch_data(username):
    try:
        # 动态 Referer
        headers['referer'] = f'https://x.com/search?q=from%3A{username}&src=typed_query'
        
        current_variables = '{"rawQuery":"from:USERNAME","count":20,"querySource":"typed_query","product":"Latest","withGrokTranslatedBio":false}'.replace("USERNAME", username)
        
        # 使用 chrome110 伪装
        # 注意：impersonate 会自动填充正确的 User-Agent 和 TLS 指纹
        response = requests.get(
            BASE_URL,
            params={'variables': current_variables, 'features': features_json},
            cookies=cookies,
            headers=headers,
            timeout=30,
            impersonate="chrome110" 
        )
        return response
    except Exception as e:
        print(f"   🔥 连接错误: {e}", flush=True)
        return None

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === 开始新一轮 (Fix 404版) ===", flush=True)

    for username in TARGET_ACCOUNTS:
        print(f"Checking: @{username} ... ", end="", flush=True)
        
        response = fetch_data(username)

        # 404 容错逻辑
        if response and response.status_code == 404:
            print("⚠️ 404 (Cookie可能失效或指纹被拒)", flush=True)
            # 如果连续404，不重试，直接跳过，保护账号
        
        elif response and response.status_code == 200:
            try:
                data = response.json()
                instructions = data.get('data', {}).get('search_by_raw_query', {}).get('search_timeline', {}).get('timeline', {}).get('instructions', [])
                
                entries = []
                for instr in instructions:
                    if instr.get('type') == 'TimelineAddEntries':
                        entries = instr.get('entries', [])
                        break
                
                new_tweets_list = []
                for entry in entries:
                    if 'tweet' in entry['entryId']:
                        res = entry.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
                        tweet_data = None
                        if 'legacy' in res:
                            tweet_data = res['legacy']
                        elif 'tweet' in res and 'legacy' in res['tweet']:
                            tweet_data = res['tweet']['legacy']
                            
                        if tweet_data:
                            tid = tweet_data['id_str']
                            if username not in last_seen_ids:
                                last_seen_ids[username] = tid
                                print(f"✅ 初始化: {tid}", flush=True)
                                break
                            
                            if tid > last_seen_ids[username]:
                                new_tweets_list.append(tweet_data)

                if new_tweets_list:
                    new_tweets_list.sort(key=lambda x: x['id_str'])
                    print(f"🚀 发现 {len(new_tweets_list)} 条新推文!", flush=True)
                    for t in new_tweets_list:
                        tid = t['id_str']
                        # Webhook 发送
                        payload = {
                            "source": "twitter_monitor_fix",
                            "author": username,
                            "content_raw": t['full_text'],
                            "link": f"https://x.com/{username}/status/{tid}",
                            "tweet_id": tid,
                            "timestamp": t['created_at']
                        }
                        try:
                            # 这里的 timeout 设小一点
                            requests.post(N8N_WEBHOOK_URL, json=payload, timeout=5)
                        except:
                            pass
                        last_seen_ids[username] = tid
                elif username in last_seen_ids:
                    print("无更新", flush=True)

            except Exception as e:
                print(f"解析失败: {e}", flush=True)

        elif response and response.status_code == 429:
            print("⚠️ 429 限流 (休息60s)", flush=True)
            time.sleep(60)
        else:
            code = response.status_code if response else "ConnectError"
            print(f"❌ 失败: {code}", flush=True)

        # 冷却时间：15-25秒，模拟人类阅读
        sleep_time = random.uniform(15, 25)
        print(f"   (冷却 {sleep_time:.1f}s)", flush=True)
        time.sleep(sleep_time)

    print("=== 等待 12 分钟 ===", flush=True)

if __name__ == "__main__":
    print("🔥 [System] 修复版启动...", flush=True)
    get_latest_tweets()
    schedule.every(12).minutes.do(get_latest_tweets)

    while True:
        schedule.run_pending()
        time.sleep(1)
