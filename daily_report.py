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

# --- RSS 피드 주소 (가장 빠르고 무료인 소스들) ---
RSS_URLS = {
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Google News (Business)": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "Investing.com": "https://www.investing.com/rss/news.rss"
}

def fetch_news():
    print("Collecting news...")
    all_news = []
    for source, url in RSS_URLS.items():
        feed = feedparser.parse(url)
        print(f"Fetched {len(feed.entries)} articles from {source}")
        for entry in feed.entries[:20]: # 소스당 최신 20개만 (너무 옛날거 제외)
            title = entry.title
            link = entry.link
            summary = entry.summary if 'summary' in entry else ""
            pubDate = entry.published if 'published' in entry else ""
            all_news.append(f"Source: {source} | Title: {title} | Link: {link} | Date: {pubDate}")
    return all_news

def analyze_news(news_list):
    # Gemini 설정
    genai.configure(api_key=GEMINI_API_KEY)
    
    # 모델 1: Screener (Gemini) - 물량 처리용
    # 수백 개의 뉴스 중 핵심만 골라내는 역할
    print("Screening news with Gemini")
    flash_model = genai.GenerativeModel('gemini')
    
    news_text = "\n".join(news_list)
    
    screening_prompt = f"""
    You are a professional financial news screener.
    Here are {len(news_list)} recent financial news headlines.
    
    Task:
    1. Filter out duplicates, ads, and noise.
    2. Select the TOP 10 most critical stories that impact global markets, interest rates, or major tech stocks right now.
    3. Output ONLY the selected 10 news items in a clean list format.
    
    News Data:
    {news_text}
    """
    
    try:
        screened_result = flash_model.generate_content(screening_prompt).text
    except Exception as e:
        return f"Error in screening: {e}"

    # 모델 2: Analyst (Gemini) - 심층 분석용
    # 골라낸 뉴스를 분석하여 보고서 작성
    print("Analyzing with Gemini")
    pro_model = genai.GenerativeModel('gemini')
    
    analysis_prompt = f"""
    You are the 'Chief Strategic Architect', a top-tier financial analyst.
    
    Input Data (Top 10 Filtered News):
    {screened_result}
    
    Mandate:
    Write a daily executive briefing for me.
    1. **Market Sentiment:** (Bullish/Bearish/Neutral) based on these news.
    2. **Key Events:** Summarize the 3 most important events and *why* they matter.
    3. **Strategic Implication:** What should an investor do? (Risk on/off, sectors to watch).
    4. **Original Sources:** List the original links for the top 3 stories.
    
    Format: Use Markdown. Be concise, professional, and insightful. Translate the final output into Korean.
    """
    
    try:
        final_report = pro_model.generate_content(analysis_prompt).text
        return final_report
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print("Sending email...")
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"🚀 Daily AI Financial Report - {datetime.now().strftime('%Y-%m-%d')}"

    # Markdown을 HTML로 변환하면 좋지만, 간단하게 텍스트로 보냄
    msg.attach(MIMEText(report_body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent successfully!")
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
