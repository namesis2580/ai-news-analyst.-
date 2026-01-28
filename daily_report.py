import os
import smtplib
import feedparser
import google.generativeai as genai
from email.message import EmailMessage
from datetime import datetime

# --- [설정] Gmail 서버 ---
SMTP_SERVER = "smtp.gmail.com"

# --- 데이터 세탁 함수 ---
def clean_text(text):
    if text is None: return ""
    return str(text).replace('\xa0', ' ').strip()

# --- 환경변수 불러오기 ---
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
        
        # [최종 업그레이드] Gemini 3 Flash 프리뷰 모델 탑재
        model = genai.GenerativeModel('gemini-3-flash-preview') 
        
        print("Analyzing news with Gemini 3 Flash...")
        
        prompt = f"""
        You are a Chief Financial Strategic Architect.
        Read the following financial news headlines and write a comprehensive daily briefing in Korean.

        [NEWS DATA]
        {news_text[:50000]}

        [OUTPUT FORMAT]
        Please write in clean Markdown format (use bolding, lists).
        
        # 🚀 Daily AI Financial Briefing (Powered by Gemini 3)
        
        ## 1. 📢 Market Sentiment
        (Bullish / Bearish / Neutral) and a one-sentence summary of why.

        ## 2. 📈 Top 3 Critical Issues
        * **Event 1:** (Summary & Why it matters)
        * **Event 2:** ...
        * **Event 3:** ...

        ## 3. 💡 Strategic Action Plan
        (Specific advice for an investor: Risk On/Off, Sectors to watch)

        ## 4. 🔗 Key Sources
        (List top 3 urls from the data)
        """
        
        response = model.generate_content(prompt)
        return clean_text(response.text)
        
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    
    msg = EmailMessage()
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

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        print("Report Generated. Sending...")
        send_email(report)
    else:
        print("No news found.")
