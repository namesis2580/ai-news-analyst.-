import os
import smtplib
import feedparser
import google.generativeai as genai
from email.message import EmailMessage  # <--- 신형 이메일 도구
from datetime import datetime

# --- 안전장치: 데이터 세탁 ---
def safe_str(data):
    if data is None: return ""
    return str(data).strip()

# --- 설정 불러오기 ---
GEMINI_API_KEY = safe_str(os.environ.get("GEMINI_API_KEY"))
EMAIL_USER = safe_str(os.environ.get("EMAIL_USER"))
EMAIL_PASSWORD = safe_str(os.environ.get("EMAIL_PASSWORD"))
EMAIL_RECEIVER = safe_str(os.environ.get("EMAIL_RECEIVER"))

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
    
    # 1. Screener
    print("Screening news...")
    try:
        flash_model = genai.GenerativeModel('gemini-1.5-flash')
        screening_prompt = f"Select top 10 critical financial news:\n{news_text[:40000]}"
        screened_result = flash_model.generate_content(screening_prompt).text
    except Exception as e:
        return f"Error in screening: {e}"

    # 2. Analyst
    print("Analyzing news...")
    try:
        pro_model = genai.GenerativeModel('gemini-1.5-pro')
        analysis_prompt = f"""
        Write a financial briefing in Korean based on:
        {screened_result}
        Format:
        1. Market Sentiment
        2. Key Issues
        3. Strategy
        """
        final_report = pro_model.generate_content(analysis_prompt).text
        return safe_str(final_report)
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print("Preparing email with Modern API...")
    
    # [핵심 변경] EmailMessage 객체 사용 (자동으로 인코딩 처리함)
    msg = EmailMessage()
    msg.set_content(report_body) # 본문 넣기
    
    msg['Subject'] = f"Daily AI Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER

    print("Connecting to Outlook Server...")
    try:
        with smtplib.SMTP('smtp.outlook.com', 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg) # <--- sendmail 대신 send_message 사용
            print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        # 디버깅을 위해 변수 타입 출력 (비밀번호는 숨김)
        print(f"Debug Info -> User Type: {type(EMAIL_USER)}, Receiver Type: {type(EMAIL_RECEIVER)}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        print("Report Generated. Sending...")
        send_email(report)
    else:
        print("No news found.")
