import requests
import json
import time
import schedule
import random
import urllib.parse
from datetime import datetime

# ================= 核心配置区 =================

# 1. 【粘贴处】请再次粘贴那条长链接（确保是 Copy URL 得到的完整链接）
#    这一版代码会自动读取链接里的所有参数，不再手写，防止出错。
Browser_Link = "https://x.com/i/api/graphql/M1jEez78PEfVfbQLvlWMvQ/SearchTimeline?variables=%7B%22rawQuery%22%3A%22from%3Alubi366%22%2C%22count%22%3A20%2C%22querySource%22%3A%22typed_query%22%2C%22product%22%3A%22Top%22%2C%22withGrokTranslatedBio%22%3Afalse%7D&features=%7B%22rweb_video_screen_enabled%22%3Afalse%2C%22profile_label_improvements_pcf_label_in_post_enabled%22%3Atrue%2C%22responsive_web_profile_redirect_enabled%22%3Afalse%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22premium_content_api_read_enabled%22%3Afalse%2C%22communities_web_enable_tweet_community_results_fetch%22%3Atrue%2C%22c9s_tweet_anatomy_moderator_badge_enabled%22%3Atrue%2C%22responsive_web_grok_analyze_button_fetch_trends_enabled%22%3Afalse%2C%22responsive_web_grok_analyze_post_followups_enabled%22%3Atrue%2C%22responsive_web_jetfuel_frame%22%3Atrue%2C%22responsive_web_grok_share_attachment_enabled%22%3Atrue%2C%22articles_preview_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22responsive_web_twitter_article_tweet_consumption_enabled%22%3Atrue%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22responsive_web_grok_show_grok_translated_post%22%3Afalse%2C%22responsive_web_grok_analysis_button_from_backend%22%3Atrue%2C%22creator_subscriptions_quote_tweet_preview_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Atrue%2C%22longform_notetweets_rich_text_read_enabled%22%3Atrue%2C%22longform_notetweets_inline_media_enabled%22%3Atrue%2C%22responsive_web_grok_image_annotation_enabled%22%3Atrue%2C%22responsive_web_grok_imagine_annotation_enabled%22%3Atrue%2C%22responsive_web_grok_community_note_auto_translation_is_enabled%22%3Afalse%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D" 

# 2. 你的 Cookie (如果浏览器刷新过，建议重新去 Application 栏看一眼有没有变)
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

# 5. 时间设置
CHECK_INTERVAL_MINUTES = 16 
# ============================================

last_seen_ids = {}

def parse_browser_link(full_url):
    """
    深度解析长链接，提取所有“原生”参数
    """
    try:
        parsed = urllib.parse.urlparse(full_url)
        # 1. 提取基础 URL (包含 ID)
        base_url = f"https://x.com{parsed.path}"
        
        # 2. 提取参数
        qs = urllib.parse.parse_qs(parsed.query)
        
        # 3. 提取 features (原样保留)
        features_json = qs.get('features', ['{}'])[0]
        
        # 4. 提取 variables (这是关键！我们要用它做模板)
        variables_str = qs.get('variables', ['{}'])[0]
        variables_template = json.loads(variables_str)
        
        return base_url, features_json, variables_template
    except Exception as e:
        print(f"❌ 链接解析失败: {e}")
        return None, None, None

def get_latest_tweets():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] === [完全寄生版] 开始检查 ===", flush=True)
    
    # 动态解析链接
    base_url, features_json, variables_template = parse_browser_link(Browser_Link)
    
    if not base_url or not variables_template:
        print("❌ 错误：Browser_Link 解析失败，请检查是否完整粘贴！", flush=True)
        return

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

    for username in TARGET_ACCOUNTS:
        try:
            print(f"正在检查: @{username} ...", end="", flush=True)
            
            # === 核心逻辑修改 ===
            # 我们不再手写 variables，而是复制一份浏览器的模板，只改 "rawQuery"
            current_variables = variables_template.copy()
            current_variables["rawQuery"] = f"from:{username}"
            
            # 构造请求参数
            params = {
                "variables": json.dumps(current_variables),
                "features": features_json
            }
            
            # 发送请求
            response = requests.get(base_url, headers=headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                try:
                    # 尝试解析推文
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
                                "link": f"https://x.com/{username}/status/{tweet_id}",
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
                        print(" -> 列表为空 (正常)", flush=True)

                except Exception as e:
                    # 有时候搜索结果为空结构会不一样，忽略即可
                    print(f" -> 解析跳过 (可能无结果): {e}", flush=True)

            elif response.status_code == 404:
                print(" -> ❌ 404 错误！", flush=True)
                # 如果还是 404，大概率是 Cookie 过期了，或者链接里的 variables 还是不对
                break 
            elif response.status_code == 401 or response.status_code == 403:
                print(" -> ❌ 认证失败 (Cookie 失效)", flush=True)
                break
            else:
                print(f" -> 请求失败: {response.status_code}", flush=True)

        except Exception as e:
            print(f" -> 异常: {e}", flush=True)
            
        sleep_time = random.uniform(5, 8)
        time.sleep(sleep_time)

    print(f"=== 本轮结束，等待 {CHECK_INTERVAL_MINUTES} 分钟 ===\n", flush=True)

# 检查是否粘贴了链接
if "graphql" not in Browser_Link:
     print("❌❌❌ 警告：你还没有填入正确的 Browser_Link！请去浏览器复制！❌❌❌")
else:
    print("🔥 [System] 启动...", flush=True)
    get_latest_tweets()
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(get_latest_tweets)

    while True:
        schedule.run_pending()
        time.sleep(1)
