import requests
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

# ================= 核心指纹 (重回完整版) =================
# 我们必须带上这些复杂的指纹，否则就是全员 404

cookies = {
    '__cuid': '5f0ccf0c997d476585709a15a55155fc',
    'kdt': 'zQcRRRVU9Cpj3Z10qnGCTLrcHhgaScSKC3AiPM5v',
    'dnt': '1',
    'personalization_id': '"v1_H+HZUYrPDKtvqjYJt3R+rw=="',
    'g_state': '{"i_l":0,"i_ll":1767103355956,"i_b":"jNGzmTOup1KHZTKnM72zuOnP5WBk0z1ltwkRwCOfDjY","i_e":{"enable_itp_optimization":0}}',
    'auth_multi': '"1880857682313441280:89ef05b69c1e822971c9c58e24271982a5d3d1dc|1829058267118743553:b7b25b10ddc4e798f0d2795b2689d93028e018a1"',
    'auth_token': 'c3778b43e1705ad15fd2e8b683087db33fb3aa1e',
    'guest_id_ads': 'v1%3A176710344905549891',
    'guest_id_marketing': 'v1%3A176710344905549891',
    'guest_id': 'v1%3A176710344905549891',
    'twid': 'u%3D2006001874949009408',
    'ct0': '368af3c63dffcc690f8557421437270654944077c8fdd21103da457e4225508284c606385efa8dd6b74c5463e87eb42c0c91b68620b1e1827e0c8e8eb1db381efcc70fdce615e3d0351dc886b27b0cf0',
    'lang': 'en',
    '__cf_bm': 'KLKBilIUG6Xkn1kxV9gTUwhEIAP7JYk7sZkZiIKzleE-1767151171.606414-1.0.1.1-wTBa8dLCRDiSdGy6_rvP9UxtbD.R81b46aekGrQCFOuJblbLL9bBxi9lMCIozRv7Bj1pkJtWI8434ayZmuWVBBn.rU31XjKthPcBFRjl30DVJIAH_pt7NXuGV5Io2ijW',
}

headers = {
    'accept': '*/*',
    'accept-language': 'zh-CN,zh;q=0.9',
    'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
    'content-type': 'application/json',
    'priority': 'u=1, i',
    # 'referer': 'https://x.com/search?q=from%3Alubi366&src=typed_query',  <-- 这个我们将在循环里动态改
    'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
    'x-client-transaction-id': 'xm5MEP54SgkDfStWNr627qPC1r6owJYc1dCKgiVwchXZiTbG2VnM1QYYSUOjBPNpNRL0w8MgGglhtnznK4jLUYOptoeoxQ', # 没办法，必须带这个，赌它不是强制绑定的
    'x-csrf-token': '368af3c63dffcc690f8557421437270654944077c8fdd21103da457e4225508284c606385efa8dd6b74c5463e87eb42c0c91b68620b1e1827e0c8e8eb1db381efcc70fdce615e3d0351dc886b27b0cf0',
    'x-twitter-active-user': 'yes',
    'x-twitter-auth-type': 'OAuth2Session',
    'x-twitter-client-language': 'en',
    'x-xp-forwarded-for': 'e1a28cf4aba4aa62c8b10a83a8b869071253ff61904532dac76d9ece73ac76c235b36c79065dd6d68122bec5a7aca127d3a6e1dbd919abd748a6c22f24ce0ed7d1b9d30177fe19c24c97364e06e1579ea00736e59589a3700b0e26e56db88a64f2654460fa714e55a2e4677a49a1da83bf25a345b528b8382f87c44d3aee0ac0a15092c281a62383a1460c47198b4c996b12a968604495dd6e1cfc68551d37405d8bea7c4732d4eee2ec5287a00078f717246fc1e053e450346979ae3a18cdf772129ca665d20bc3962f08515b71a1b055929128bd392902d9da394d735267e7dec6f2c295683278b4446256c394ba844b5c1280841e3e4bea9b',
}

features_json = '{"rweb_video_screen_enabled":false,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":false,"rweb_tipjar_consumption_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"responsive_web_grok_show_grok_translated_post":false,"responsive_web_grok_analysis_button_from_backend":true,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,"responsive_web_enhance_cards_enabled":false}'

BASE_URL = 'https://x.com/i/api/graphql/M1jEez78PEfVfbQLvlWMvQ/SearchTimeline'

last_seen_ids = {}

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === 开始新一轮检查 (动态 Referer 版) ===", flush=True)

    for username in TARGET_ACCOUNTS:
        try:
            print(f"Checking: @{username} ... ", end="", flush=True)
            
            # === 关键修正：动态伪装 Referer ===
            # 让推特觉得你是刚刚搜索了这个用户，而不是一直停留在 lubi366 的页面
            headers['referer'] = f'https://x.com/search?q=from%3A{username}&src=typed_query'
            
            current_variables = '{"rawQuery":"from:USERNAME","count":20,"querySource":"typed_query","product":"Latest","withGrokTranslatedBio":false}'.replace("USERNAME", username)

            params = {
                'variables': current_variables,
                'features': features_json,
            }

            response = requests.get(
                BASE_URL,
                params=params,
                cookies=cookies,
                headers=headers,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                try:
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
                                "source": "twitter_monitor_final",
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
                        print("空数据 (可能被过滤)", flush=True)

                except Exception as parse_error:
                    print(f"解析错误: {parse_error}", flush=True)

            elif response.status_code == 429:
                print("⚠️ 429 Rate Limit (休息 30s)", flush=True)
                time.sleep(30)
            elif response.status_code == 404:
                # 如果带了全套指纹还是 404，那就是 IP 或者指纹被标记了
                print("❌ 404 (指纹不匹配)", flush=True)
            else:
                print(f"❌ Error: {response.status_code}", flush=True)

        except Exception as e:
            print(f"❌ 异常: {e}", flush=True)
        
        # 保持随机间隔
        sleep_time = random.uniform(8, 12)
        print(f"   (休息 {sleep_time:.1f}s)", flush=True)
        time.sleep(sleep_time)

    print("=== 等待 16 分钟 ===", flush=True)

if __name__ == "__main__":
    print("🔥 [System] 动态 Referer 修复版启动...", flush=True)
    get_latest_tweets()
    schedule.every(16).minutes.do(get_latest_tweets)

    while True:
        schedule.run_pending()
        time.sleep(1)
