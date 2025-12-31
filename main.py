import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
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

# ================= 核心指纹 (身份对齐版) =================

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
    # Referer 动态生成
    # 【关键修改】改为 Linux UA，与服务器真实环境一致，减少被踢下线的概率
    'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"', 
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'x-client-transaction-id': 'xm5MEP54SgkDfStWNr627qPC1r6owJYc1dCKgiVwchXZiTbG2VnM1QYYSUOjBPNpNRL0w8MgGglhtnznK4jLUYOptoeoxQ',
    'x-csrf-token': '368af3c63dffcc690f8557421437270654944077c8fdd21103da457e4225508284c606385efa8dd6b74c5463e87eb42c0c91b68620b1e1827e0c8e8eb1db381efcc70fdce615e3d0351dc886b27b0cf0',
    'x-twitter-active-user': 'yes',
    'x-twitter-auth-type': 'OAuth2Session',
    'x-twitter-client-language': 'en',
}

features_json = '{"rweb_video_screen_enabled":false,"profile_label_improvements_pcf_label_in_post_enabled":true,"responsive_web_profile_redirect_enabled":false,"rweb_tipjar_consumption_enabled":true,"verified_phone_label_enabled":false,"creator_subscriptions_tweet_preview_api_enabled":true,"responsive_web_graphql_timeline_navigation_enabled":true,"responsive_web_graphql_skip_user_profile_image_extensions_enabled":false,"premium_content_api_read_enabled":false,"communities_web_enable_tweet_community_results_fetch":true,"c9s_tweet_anatomy_moderator_badge_enabled":true,"responsive_web_grok_analyze_button_fetch_trends_enabled":false,"responsive_web_grok_analyze_post_followups_enabled":true,"responsive_web_jetfuel_frame":true,"responsive_web_grok_share_attachment_enabled":true,"articles_preview_enabled":true,"responsive_web_edit_tweet_api_enabled":true,"graphql_is_translatable_rweb_tweet_is_translatable_enabled":true,"view_counts_everywhere_api_enabled":true,"longform_notetweets_consumption_enabled":true,"responsive_web_twitter_article_tweet_consumption_enabled":true,"tweet_awards_web_tipping_enabled":false,"responsive_web_grok_show_grok_translated_post":false,"responsive_web_grok_analysis_button_from_backend":true,"creator_subscriptions_quote_tweet_preview_enabled":false,"freedom_of_speech_not_reach_fetch_enabled":true,"standardized_nudges_misinfo":true,"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled":true,"longform_notetweets_rich_text_read_enabled":true,"longform_notetweets_inline_media_enabled":true,"responsive_web_grok_image_annotation_enabled":true,"responsive_web_grok_imagine_annotation_enabled":true,"responsive_web_grok_community_note_auto_translation_is_enabled":false,"responsive_web_enhance_cards_enabled":false}'

BASE_URL = 'https://x.com/i/api/graphql/M1jEez78PEfVfbQLvlWMvQ/SearchTimeline'
last_seen_ids = {}

# === 核心升级：创建自动重试的 Session ===
def create_session():
    session = requests.Session()
    # 定义重试策略：遇到连接错误、500/502/503/504 等错误时，自动重试 3 次
    retries = Retry(
        total=3,
        backoff_factor=1, # 重试间隔 1秒, 2秒, 4秒...
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    # 将重试策略挂载到 https 请求上
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    return session

# 初始化全局 Session
http_session = create_session()

def fetch_data(username):
    try:
        headers['referer'] = f'https://x.com/search?q=from%3A{username}&src=typed_query'
        current_variables = '{"rawQuery":"from:USERNAME","count":20,"querySource":"typed_query","product":"Latest","withGrokTranslatedBio":false}'.replace("USERNAME", username)
        
        # 使用 http_session 而不是直接用 requests
        response = http_session.get(
            BASE_URL,
            params={'variables': current_variables, 'features': features_json},
            cookies=cookies,
            headers=headers,
            timeout=20 # 稍微增加超时时间
        )
        return response
    except Exception as e:
        # 打印具体的错误信息，方便我们彻底根治
        print(f"   🔥 严重错误: {type(e).__name__} - {e}", flush=True)
        return None

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === 开始新一轮 (防断连加强版) ===", flush=True)

    for username in TARGET_ACCOUNTS:
        print(f"Checking: @{username} ... ", end="", flush=True)
        
        response = fetch_data(username)

        # 404 处理 (这次我们不立刻重试，因为 Session 层面已经处理了连接错误)
        # 如果还是 404，说明是推特因为频率拒绝了，我们需要更长的休息
        if response and response.status_code == 404:
            print("⚠️ 404 (流控), 稍微休息...", end="", flush=True)
            time.sleep(6)
            response = fetch_data(username) # 最后试一次

        if response and response.status_code == 200:
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
                        print(f"   -> 发送: {tid}", flush=True)
                        payload = {
                            "source": "twitter_monitor_final",
                            "author": username,
                            "content_raw": t['full_text'],
                            "link": f"https://x.com/{username}/status/{tid}",
                            "tweet_id": tid,
                            "timestamp": t['created_at']
                        }
                        try:
                            requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
                        except:
                            pass
                        last_seen_ids[username] = tid
                elif username in last_seen_ids:
                    print("无更新", flush=True)

            except Exception as e:
                print(f"解析失败: {e}", flush=True)

        elif response and response.status_code == 429:
            print("⚠️ 429 Rate Limit", flush=True)
            time.sleep(30)
        else:
            code = response.status_code if response else "ConnectFail"
            print(f"❌ 失败: {code}", flush=True)

        sleep_time = random.uniform(15, 20) # 保持慢速
        print(f"   (冷却 {sleep_time:.1f}s)", flush=True)
        time.sleep(sleep_time)

    print("=== 等待 12 分钟 ===", flush=True)

if __name__ == "__main__":
    print("🔥 [System] 防断连加强版启动...", flush=True)
    get_latest_tweets()
    schedule.every(12).minutes.do(get_latest_tweets)

    while True:
        schedule.run_pending()
        time.sleep(1)
