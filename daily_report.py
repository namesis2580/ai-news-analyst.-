import os
import smtplib
import feedparser
import google.generativeai as genai
from datetime import datetime
import time
import re
import unicodedata
# [수정 1] 이메일 표준 라이브러리 추가
from email.mime.text import MIMEText
from email.header import Header

# --- [설정] Gmail 서버 ---
SMTP_SERVER = "smtp.gmail.com"

# --- [1단계] 환경변수 로드 & DNA 분석 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "").strip()
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER", "")

# [진단] 유령 문자 색출
print("="*30)
print("🔍 EMAIL_USER DNA ANALYSIS:")
print(f"Original: '{EMAIL_USER}'")
print(f"ASCII Codes: {[ord(c) for c in EMAIL_USER]}") 
print("="*30)

# --- [정보 수집] ---
RSS_URLS = {
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Investing.com": "https://www.investing.com/rss/news.rss",
    "Google News (Biz)": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "Google News (Tech)": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    "Hacker News": "https://news.ycombinator.com/rss",     
    "TechCrunch": "https://techcrunch.com/feed/",          
    "Project Syndicate": "https://www.project-syndicate.org/rss", 
    "OilPrice": "https://oilprice.com/rss/main",           
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/" 
}

def clean_text_body(text):
    if text is None: return ""
    text = str(text)
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def fetch_news():
    print("Collecting news from The Avengers Squad...")
    all_news = []
    for source, url in RSS_URLS.items():
        try:
            feed = feedparser.parse(url)
            print(f"Fetched {len(feed.entries)} articles from {source}")
            for entry in feed.entries[:10]: 
                title = clean_text_body(getattr(entry, 'title', 'No Title'))
                link = clean_text_body(getattr(entry, 'link', 'No Link'))
                pubDate = clean_text_body(getattr(entry, 'published', 'No Date'))
                content = ""
                if hasattr(entry, 'content'): content = entry.content[0].value
                elif hasattr(entry, 'summary_detail'): content = entry.summary_detail.value
                elif hasattr(entry, 'summary'): content = entry.summary
                clean_content = clean_text_body(content)[:10000]
                all_news.append(f"[{source}] Title: {title} | Content: {clean_content} | Date: {pubDate} | Link: {link}")
        except Exception as e:
            print(f"Error fetching {source}: {e}")
    return all_news

def analyze_news(news_list):
    print("Configuring AI...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        news_text = "\n".join(news_list)
        # Gemini 3.0 모델
        model = genai.GenerativeModel('gemini-3-flash-preview') 
        print("Summoning The Strategic Council (Analysis Avengers)...")
        print(f"Input Data Length: {len(news_text)} characters") 
        
        prompt = f"""
        # 🌌 STRATEGIC COUNCIL: THE AVENGERS PROTOCOL

        **CONTEXT:** You are the **'Chief Architect'** presiding over a high-stakes roundtable.
        **INPUT:** The provided `[RSS_RAW_DATA]` (Cleaned, High-Quality).
        **OUTPUT LANGUAGE:** Korean (한국어).

        **👥 THE COUNCIL MEMBERS (Your Internal Personas):**
        1.  **🐻 Dr. Doom (Risk):** Pessimistic. Focuses on flaws, bubbles, debt, and regulatory threats.
        2.  **🐂 The Visionary (Growth):** Optimistic. Focuses on innovation, adoption, and 10x opportunities.
        3.  **🦅 The Hawk (Macro):** Realist. Focuses on Fed rates, Oil, Wars, and Liquidity.
        4.  **🦊 The Fox (Contrarian):** Skeptic of the crowd. Looks for information asymmetry (Hacker News vs Yahoo).

        ---

        ## 📝 REPORT STRUCTURE (Strictly follow this)

        ### CHAPTER 1. 👑 The Architect's Verdict (최종 결론)
        * **Strategic Vector:** (The single most important trend today).
        * **Market Stance:** [Aggressive Buy / Cautious Buy / Neutral / Sell / Short].
        * **Confidence Score:** [0-100%].
        * **The Bottom Line:** (Synthesize the council's debate into one actionable directive).

        ### CHAPTER 2. 🗣️ The Council's Debate (심층 분석)
        *In this section, simulate a short, intense debate between the personas based on the data.*
        
        * **🐻 Dr. Doom says:** "Wait, look at the risks in..."
        * **🐂 The Visionary counters:** "But you are missing the growth signal in..."
        * **🦅 The Hawk interrupts:** "Actually, the macro environment in suggests..."
        * **🦊 The Fox whispers:** "The crowd is wrong about because..."

        ### CHAPTER 3. 👁️ Evidence & Triangulation (근거 데이터)
        *Validate the debate with specific data points from the 9 Sources.*
        * **[Macro/Energy]:** (Project Syndicate/OilPrice)
        * **[Tech/VC]:** (Hacker News/TechCrunch)
        * **[Market/Money]:** (Yahoo/CoinDesk)
        * **[Conflict]:** (Where do the sources disagree?)

        ### CHAPTER 4. ⚔️ Action Plan (Execution)
        * **Step 1 (Defense):** (How to not lose money today).
        * **Step 2 (Offense):** (Where to attack for profit).
        * **Kill Switch:** (Condition to exit immediately).

        ---
        **[RSS_RAW_DATA]**
        {news_text}
        """
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        response = model.generate_content(prompt, request_options={"timeout": 1000}, safety_settings=safety_settings)
        return clean_text_body(response.text)
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    
    # [안전 조치 1] 본문 내 유령 문자(\xa0)를 일반 공백으로 치환
    if report_body:
        report_body = report_body.replace('\xa0', ' ')

    safe_date = datetime.now().strftime('%Y-%m-%d')
    subject_text = f"Strategic_Council_Report_{safe_date}"
    
    # 이메일 주소 세탁
    safe_user = EMAIL_USER.encode('ascii', 'ignore').decode('ascii').strip()
    safe_receiver = EMAIL_RECEIVER.encode('ascii', 'ignore').decode('ascii').strip()
    
    print(f"DEBUG: Final Safe Sender: '{safe_user}'")
    
    # [수정 2] MIMEText 객체 사용하여 UTF-8 강제
    # 'plain'은 일반 텍스트, 'html'을 원하면 'html'로 변경
    msg = MIMEText(report_body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject_text, 'utf-8')
    msg['From'] = safe_user
    msg['To'] = safe_receiver

    print("Connecting to Gmail Server...")

    try:
        server = smtplib.SMTP(SMTP_SERVER, 587, local_hostname='localhost')
        server.starttls()
        server.login(safe_user, EMAIL_PASSWORD)
        
        # [수정 3] send_message 사용 (인코딩 자동 처리)
        server.send_message(msg)
        
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    news_data = fetch_news()
    if news_data:
        report = analyze_news(news_data)
        if report and "Error" not in report:
            send_email(report)
        else:
            print("\n❌ Report generation failed!")
            print(report)
    else:
        print("No news found.")
