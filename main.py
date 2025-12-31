import requests
import json

print("=== 🕵️‍♂️ 深度调试模式启动 ===")

# ================= 配置区 =================
# 1. 你的 Token (不要带 "token:" 前缀，只要那一串乱码)
MY_AUTH_TOKEN = "c3778b43e1705ad15fd2e8b683087db33fb3aa1e"

# 2. 你的 CT0 (不要带 "CT0 :" 前缀，只要那一长串)
MY_CT0 = "368af3c63dffcc690f8557421437270654944077c8fdd21103da457e4225508284c606385efa8dd6b74c5463e87eb42c0c91b68620b1e1827e0c8e8eb1db381efcc70fdce615e3d0351dc886b27b0cf0"

# 3. 刚才那个链接
TARGET_URL = "https://x.com/i/api/graphql/M1jEez78PEfVfbQLvlWMvQ/SearchTimeline?variables=%7B%22rawQuery%22%3A%22from%3Alubi366%22%2C%22count%22%3A20%2C%22querySource%22%3A%22typed_query%22%2C%22product%22%3A%22Top%22%2C%22withGrokTranslatedBio%22%3Afalse%7D&features=%7B%22rweb_video_screen_enabled%22%3Afalse%2C%22profile_label_improvements_pcf_label_in_post_enabled%22%3Atrue%2C%22responsive_web_profile_redirect_enabled%22%3Afalse%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22premium_content_api_read_enabled%22%3Afalse%2C%22communities_web_enable_tweet_community_results_fetch%22%3Atrue%2C%22c9s_tweet_anatomy_moderator_badge_enabled%22%3Atrue%2C%22responsive_web_grok_analyze_button_fetch_trends_enabled%22%3Afalse%2C%22responsive_web_grok_analyze_post_followups_enabled%22%3Atrue%2C%22responsive_web_jetfuel_frame%22%3Atrue%2C%22responsive_web_grok_share_attachment_enabled%22%3Atrue%2C%22articles_preview_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22responsive_web_twitter_article_tweet_consumption_enabled%22%3Atrue%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22responsive_web_grok_show_grok_translated_post%22%3Afalse%2C%22responsive_web_grok_analysis_button_from_backend%22%3Atrue%2C%22creator_subscriptions_quote_tweet_preview_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Atrue%2C%22longform_notetweets_rich_text_read_enabled%22%3Atrue%2C%22longform_notetweets_inline_media_enabled%22%3Atrue%2C%22responsive_web_grok_image_annotation_enabled%22%3Atrue%2C%22responsive_web_grok_imagine_annotation_enabled%22%3Atrue%2C%22responsive_web_grok_community_note_auto_translation_is_enabled%22%3Afalse%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D"

# ============================================

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
    "Content-Type": "application/json",
    "X-Csrf-Token": MY_CT0,
    "Cookie": f"auth_token={MY_AUTH_TOKEN}; ct0={MY_CT0}"
}

try:
    print("\n👉 1. 正在发送请求...")
    response = requests.get(TARGET_URL, headers=headers)
    
    print(f"👉 2. 状态码: {response.status_code}")
    
    # 打印返回的详细内容（这才是关键！）
    print("👉 3. 返回的详细信息 (Error Body):")
    print("-" * 30)
    print(response.text[:1000]) # 打印前1000个字符
    print("-" * 30)

    if response.status_code == 200:
        print("✅ 奇迹出现了！链接居然通了！")
    elif response.status_code == 404:
        print("❌ 依然是 404。请看上面的【返回详细信息】。")
        if "No status found" in response.text:
            print("💡 分析: 看起来像是推文没找到，但接口通了。")
        elif "Not found" in response.text:
            print("💡 分析: API 端点 ID (M1jE...) 可能过期了，或者参数签名不对。")
    elif response.status_code == 403:
        print("❌ 403 禁止访问。Token 或 CSRF 验证失败。")

except Exception as e:
    print(f"❌ 程序出错: {e}")
