import os
import smtplib
import feedparser
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- 안전장치: 모든 데이터를 무조건 문자열(str)로 변환하는 함수 ---
def safe_str(data):
    if data is None:
        return ""
    if isinstance(data, bytes):
        return data.decode('utf-8', 'ignore')
    return str(data)

# --- 설정 (Secrets에서 불러오되, 강제로 문자열 변환) ---
GEMINI_API_KEY = safe_str(os.environ.get("GEMINI_API_KEY"))
EMAIL_USER = safe_str(os.environ.get("EMAIL_USER"))
EMAIL_PASSWORD = safe_str(os.environ.get("EMAIL_PASSWORD"))
EMAIL_RECEIVER = safe_str(os.environ.get("EMAIL_RECEIVER"))

# --- RSS 피드 주소 ---
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
                # 제목과 링크를 안전하게 추출 (없으면 빈칸)
                title = safe_str(entry.get('title', 'No Title'))
                link = safe_str(entry.get('link', 'No Link'))
                pubDate = safe_str(entry.get('published', 'No Date'))
                
                # 리스트에 추가
                all_news.append(f"Source: {source} | Title: {title} | Link: {link} | Date: {pubDate}")
        except Exception as e:
            print(f"Error fetching {source}: {e}")
            continue
    return all_news

def analyze_news(news_list):
    print("Configuring AI...")
    genai.configure(api_key=GEMINI_API_KEY)
    
    # 뉴스 리스트를 하나의 긴 문자열로 합침 (중간에 깨지지 않게 방어)
    news_text = "\n".join([safe_str(n) for n in news_list])
    
    # 모델 1: Screener (Flash)
    print("Screening news...")
    try:
        flash_model = genai.GenerativeModel('gemini')
        screening_prompt = f"""
        Select top 10 critical financial news from the list below.
        Return ONLY the list.
        
        {news_text[:40000]}
        """
        screened_result = flash_model.generate_content(screening_prompt).text
    except Exception as e:
        return f"Error in screening: {safe_str(e)}"

    # 모델 2: Analyst (Pro)
    print("Analyzing news...")
    try:
        pro_model = genai.GenerativeModel('gemini')
        analysis_prompt = f"""
        You are a strict financial analyst.
        Based on these news:
        {safe_str(screened_result)}
        
        Write a report in Korean with:
        1. Market Sentiment (Bullish/Bearish)
        2. Top 3 Issues
        3. Action Plan
        """
        final_report = pro_model.generate_content(analysis_prompt).text
        return safe_str(final_report)
    except Exception as e:
        return f"Error in analysis: {safe_str(e)}"

def send_email(report_body):
    print("Preparing email...")
    
    # 본문도 혹시 모르니 다시 한번 문자열 세탁
    clean_body = safe_str(report_body)
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"Daily AI Financial Report - {datetime.now().strftime('%Y-%m-%d')}"

    # UTF-8 인코딩 명시
    msg.attach(MIMEText(clean_body, 'plain', 'utf-8'))

    print("Connecting to Outlook Server...")
    try:
        # Outlook 서버 연결
        server = smtplib.SMTP('smtp.outlook.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # 메시지를 문자열로 변환하여 전송
        text = msg.as_string()
        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, text)
        
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        print("Report Generated. Sending...")
        send_email(report)
    else:
        print("No news found.")
