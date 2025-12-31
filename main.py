import requests
import time
import schedule
import random
import json
from datetime import datetime

# ================= 配置区域 =================

# 1. 监控名单
TARGET_ACCOUNTS = [
    "lubi366", "connectfarm1", "wolfyxbt", "Crypto_He", "BroLeon", 
    "0xcryptowizard", "one_snowball", "yueya_eth", "qlonline", 
    "ai_9684xtpa", "cz_binance", "linwanwan823"
]

# 2. n8n 回调地址
N8N_WEBHOOK_URL = "http://43.139.245.223:5678/webhook/6d6ea3d6-ba16-4d9d-9145-22425474ab48"

# ================= 核心身份 (净化版) =================

# 你的 Cookie (保持不变)
cookies = {
    'auth_token': 'c3778b43e1705ad15fd2e8b683087db33fb3aa1e',
    'ct0': '368af3c63dffcc690f8557421437270654944077c8fdd21103da457e4225508284c606385efa8dd6b74c5463e87eb42c0c91b68620b1e1827e0c8e8eb1db381efcc70fdce615e3d0351dc886b27b0cf0',
}

# 你的 Headers (净化版：去掉了所有容易导致被封的指纹信息)
headers = {
    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
    'content-type': 'application/json',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'x-csrf-token': '368af3c63dffcc690f8557421437270654944077c8fdd21103da457e4225508284c606385efa8dd6b74c5463e87eb42c0c91b68620b1e1827e0c8e8eb1db381efcc70fdce615e3d0351dc886b27b0cf0',
    # 下面这三个是必须的，但不要带具体的 transaction ID
    'x-twitter-active-user': 'yes',
    'x-twitter-auth-type': 'OAuth2Session',
    'x-twitter-client-language': 'en',
}

# 基础 URL (SearchTimeline 接口)
BASE_URL = 'https://x.com/i/api/graphql/M1jEez78PEfVfbQLvlWMvQ/SearchTimeline'

# 静态参数
features_json = '{"rweb_video_screen_enabled":false,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":false,"rweb_tipjar_consumption_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"responsive_web_grok_show_grok_translated_post":false,"responsive_web_grok_analysis_button_from_backend":true,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,"responsive_web_enhance_cards_enabled":false}'

# 记录上次推文ID
last_seen_ids = {}

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === 开始新一轮检查 (Lite版) ===", flush=True)

    for username in TARGET_ACCOUNTS:
        try:
            print(f"Checking: @{username} ... ", end="", flush=True)
            
            # 动态参数
            current_variables = '{"rawQuery":"from:USERNAME","count":20,"querySource":"typed_query","product":"Latest","withGrokTranslatedBio":false}'.replace("USERNAME", username)

            params = {
                'variables': current_variables,
                'features': features_json,
            }

            response = requests.get(
                BASE_URL,
                params=params,
                cookies=cookies, # 使用精简版 Cookie
                headers=headers, # 使用精简版 Header
                timeout=15
            )

            # === 状态码检查 ===
            if response.status_code == 200:
                data = response.json()
                try:
                    # 路径解析
                    instructions = data.get('data', {}).get('search_by_raw_query', {}).get('search_timeline', {}).get('timeline', {}).get('instructions', [])
                    entries = []
                    for instr in instructions:
                        if instr.get('type') == 'TimelineAddEntries':
                            entries = instr.get('entries', [])
                            break
                    
                    found_tweet = None
                    for entry in entries:
                        if 'tweet' in entry['entryId']:
                            res = entry.get('content', {}).get('itemContent', {}).get('tweet_results', {}).get('result', {})
                            if 'legacy' in res:
                                found_tweet = res['legacy']
                            elif 'tweet' in res and 'legacy' in res['tweet']:
                                found_tweet = res['tweet']['legacy']
                            if found_tweet:
                                break
                    
                    if found_tweet:
                        tweet_id = found_tweet['id_str']
                        full_text = found_tweet['full_text']
                        created_at = found_tweet['created_at']

                        if username not in last_seen_ids:
                            last_seen_ids[username] = tweet_id
                            print(f"✅ 初始化 ID: {tweet_id}", flush=True)
                        elif last_seen_ids[username] != tweet_id:
                            print(f"🚀 新推文! ID: {tweet_id}", flush=True)
                            payload = {
                                "source": "twitter_monitor_lite",
                                "author": username,
                                "content_raw": full_text,
                                "link": f"https://x.com/{username}/status/{tweet_id}",
                                "tweet_id": tweet_id,
                                "timestamp": created_at
                            }
                            try:
                                requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
                                print("   -> Webhook 发送成功", flush=True)
                                last_seen_ids[username] = tweet_id
                            except Exception as e:
                                print(f"   -> Webhook 发送失败: {e}", flush=True)
                        else:
                            print("无更新", flush=True)
                    else:
                        print("空列表/无数据", flush=True)

                except Exception as parse_error:
                    print(f"解析错误: {parse_error}", flush=True)

            elif response.status_code == 404:
                # 404 Empty Body 最常见于 Header 被风控
                print("⚠️ 404 (可能被风控，尝试跳过...)", flush=True)
            elif response.status_code == 429:
                print("⚠️ 429 Rate Limit (休息 30s)", flush=True)
                time.sleep(30)
            elif response.status_code == 403:
                 print(f"❌ 403 CSRF Error (检查 CT0)", flush=True)
            else:
                print(f"❌ Error: {response.status_code}", flush=True)

        except Exception as e:
            print(f"❌ 异常: {e}", flush=True)
        
        # 随机等待 8-12 秒
        sleep_time = random.uniform(8, 12)
        print(f"   (等待 {sleep_time:.1f}s)", flush=True)
        time.sleep(sleep_time)

    print("=== 等待 16 分钟 ===", flush=True)

if __name__ == "__main__":
    print("🔥 [System] 净化版监控启动...", flush=True)
    get_latest_tweets()
    schedule.every(16).minutes.do(get_latest_tweets)

    while True:
        schedule.run_pending()
        time.sleep(1)
