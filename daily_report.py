import os
import smtplib
import feedparser
import google.generativeai as genai
from email.message import EmailMessage
from datetime import datetime

# --- [핵심] Gmail 서버 설정 ---
SMTP_SERVER = "smtp.gmail.com"

# --- [초강력] 데이터 세탁 함수 (유령 문자 제거) ---
def clean_text(text):
    if text is None: return ""
    # \xa0(투명 공백)을 일반 공백으로 바꾸고, 양쪽 공백 제거
    return str(text).replace('\xa0', ' ').strip()

# --- 설정 불러오기 (세탁기 돌림) ---
GEMINI_API_KEY = clean_text(os.environ.get("GEMINI_API_KEY"))
EMAIL_USER = clean_text(os.environ.get("EMAIL_USER"))
EMAIL_PASSWORD = clean_text(os.environ.get("EMAIL_PASSWORD"))
EMAIL_RECEIVER = clean_text(os.environ.get("EMAIL_RECEIVER"))

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
                title = clean_text(getattr(entry, 'title', 'No Title'))
                link = clean_text(getattr(entry, 'link', 'No Link'))
                pubDate = clean_text(getattr(entry, 'published', 'No Date'))
                all_news.append(f"Source: {source} | Title: {title} | Link: {link} | Date: {pubDate}")
        except Exception as e:
            print(f"Error fetching {source}: {e}")
    return all_news

def analyze_news(news_list):
    print("Configuring AI...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        news_text = "\n".join(news_list)
        
        # 1. Screener (Flash)
        print("Screening news...")
        flash_model = genai.GenerativeModel('gemini-1.5-flash')
        screening_prompt = f"Select top 10 critical financial news:\n{news_text[:40000]}"
        screened_result = flash_model.generate_content(screening_prompt).text

        # 2. Analyst (Pro)
        print("Analyzing news...")
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
        return clean_text(final_report)
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    
    msg = EmailMessage()
    # 본문 인코딩을 UTF-8로 강제 고정
    msg.set_content(report_body, charset='utf-8')
    
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
        # 디버깅: 값의 길이와 타입을 출력해서 숨은 문자 확인
        print(f"Debug -> User Len: {len(EMAIL_USER)}, Receiver Len: {len(EMAIL_RECEIVER)}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        print("Report Generated. Sending...")
        send_email(report)
    else:
        print("No news found.")
