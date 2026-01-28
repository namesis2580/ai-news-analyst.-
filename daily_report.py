import os
import smtplib
import feedparser
import google.generativeai as genai
from email.message import EmailMessage
from datetime import datetime

# --- [핵심] Gmail 서버 설정 ---
SMTP_SERVER = "smtp.gmail.com"

# --- 안전장치: 데이터 세탁 ---
def safe_str(data):
    if data is None: return ""
    return str(data).strip()

# --- 설정 불러오기 ---
GEMINI_API_KEY = safe_str(os.environ.get("GEMINI_API_KEY"))
EMAIL_USER = safe_str(os.environ.get("EMAIL_USER"))      # 보내는 사람 (Gmail 주소)
EMAIL_PASSWORD = safe_str(os.environ.get("EMAIL_PASSWORD")) # 보내는 사람 비번 (Gmail 앱 비밀번호)
EMAIL_RECEIVER = safe_str(os.environ.get("EMAIL_RECEIVER")) # 받는 사람 (Outlook 주소)

RSS_URLS = {
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Google News": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en"
}

def fetch_news():
    print("Collecting news...")
    all_news = []
    for source, url in RSS_URLS.items():
        try:
            feed = feedparser.parse(url)
            print(f"Fetched {len(feed.entries)} articles from {source}")
            for entry in feed.entries[:15]:
                title = safe_str(getattr(entry, 'title', 'No Title'))
                link = safe_str(getattr(entry, 'link', 'No Link'))
                pubDate = safe_str(getattr(entry, 'published', 'No Date'))
                all_news.append(f"Source: {source} | Title: {title} | Link: {link} | Date: {pubDate}")
        except Exception as e:
            print(f"Error fetching {source}: {e}")
    return all_news

def analyze_news(news_list):
    print("Configuring AI...")
    genai.configure(api_key=GEMINI_API_KEY)
    
    news_text = "\n".join(news_list)
    
    # 1. Screener (Flash)
    print("Screening news...")
    try:
        flash_model = genai.GenerativeModel('gemini-1.5-flash')
        screening_prompt = f"Select top 10 critical financial news:\n{news_text[:40000]}"
        screened_result = flash_model.generate_content(screening_prompt).text
    except Exception as e:
        return f"Error in screening: {e}"

    # 2. Analyst (Pro)
    print("Analyzing news...")
    try:
        pro_model = genai.GenerativeModel('gemini-1.5-pro')
        analysis_prompt = f"""
        Write a financial briefing in Korean based on:
        {screened_result}
        Format:
        1. Market Sentiment (Bullish/Bearish)
        2. Top 3 Key Issues
        3. Strategic Action Plan
        """
        final_report = pro_model.generate_content(analysis_prompt).text
        return safe_str(final_report)
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    
    msg = EmailMessage()
    msg.set_content(report_body)
    
    msg['Subject'] = f"Daily AI Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER

    print("Connecting to Gmail Server...")
    try:
        with smtplib.SMTP(SMTP_SERVER, 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        print(f"Debug Info -> Server: {SMTP_SERVER}, User: {EMAIL_USER}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        print("Report Generated. Sending...")
        send_email(report)
    else:
        print("No news found.")
