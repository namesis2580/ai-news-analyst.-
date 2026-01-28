import os
import smtplib
import feedparser
import google.generativeai as genai
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# --- 설정 (Secrets에서 불러옴) ---
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
EMAIL_USER = os.environ["EMAIL_USER"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]
EMAIL_RECEIVER = os.environ["EMAIL_RECEIVER"]

# --- RSS 피드 주소 ---
RSS_URLS = {
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Google News (Business)": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "Investing.com": "https://www.investing.com/rss/news.rss"
}

def fetch_news():
    print("Collecting news...")
    all_news = []
    for source, url in RSS_URLS.items():
        try:
            feed = feedparser.parse(url)
            print(f"Fetched {len(feed.entries)} articles from {source}")
            for entry in feed.entries[:20]:
                # 제목이나 링크가 없을 경우 대비
                title = getattr(entry, 'title', 'No Title')
                link = getattr(entry, 'link', 'No Link')
                pubDate = getattr(entry, 'published', 'No Date')
                
                # 데이터가 바이트(bytes)로 들어올 경우 강제로 문자열(str)로 변환
                if isinstance(title, bytes): title = title.decode('utf-8', 'ignore')
                if isinstance(link, bytes): link = link.decode('utf-8', 'ignore')
                
                all_news.append(f"Source: {source} | Title: {title} | Link: {link} | Date: {pubDate}")
        except Exception as e:
            print(f"Error fetching {source}: {e}")
            continue
    return all_news

def analyze_news(news_list):
    genai.configure(api_key=GEMINI_API_KEY)
    
    # 모델 1: Screener
    print("Screening news with Gemini")
    try:
        flash_model = genai.GenerativeModel('gemini')
        news_text = "\n".join(news_list)
        screening_prompt = f"""
        You are a professional financial news screener.
        Filter out duplicates and select the TOP 10 most critical stories.
        Output ONLY the list.
        News Data:
        {news_text[:50000]} 
        """
        # 입력 데이터가 너무 길 경우를 대비해 50000자 제한
        screened_result = flash_model.generate_content(screening_prompt).text
    except Exception as e:
        return f"Error in screening: {e}"

    # 모델 2: Analyst
    print("Analyzing with Gemini")
    try:
        pro_model = genai.GenerativeModel('gemini')
        analysis_prompt = f"""
        You are the 'Chief Strategic Architect'.
        Write a daily executive briefing based on these news:
        {screened_result}
        
        Format:
        1. Market Sentiment (Bullish/Bearish)
        2. Top 3 Key Events & Why
        3. Action Plan
        
        Translate output to Korean.
        """
        final_report = pro_model.generate_content(analysis_prompt).text
        return final_report
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print("Sending email via Outlook...")
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"🚀 Daily AI Financial Report - {datetime.now().strftime('%Y-%m-%d')}"

    # [핵심 수정] 본문을 강제로 문자열(str)로 변환하고 UTF-8 인코딩 명시
    if not isinstance(report_body, str):
        report_body = str(report_body)
    
    msg.attach(MIMEText(report_body, 'plain', 'utf-8'))

    try:
        # Outlook SMTP 서버
        server = smtplib.SMTP('smtp.outlook.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Outlook Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        print("Report Generated. Sending...")
        send_email(report)
    else:
        print("No news found.")
