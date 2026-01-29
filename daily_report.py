import os
import smtplib
import feedparser
import google.generativeai as genai
from datetime import datetime
import time
import re
import unicodedata
from email.mime.text import MIMEText
from email.header import Header

# --- [0단계] 강력 세탁 함수 (여기가 핵심입니다) ---
def nuclear_clean(text):
    """
    눈에 안 보이는 유령 문자(\xa0)를 포함해 모든 노이즈를 제거하고
    무조건 순수 영어/숫자/기호(ASCII)만 남깁니다.
    """
    if not text: return ""
    # 1. 유령 공백(\xa0)을 일반 공백으로 치환
    text = text.replace('\xa0', ' ')
    # 2. 앞뒤 공백 제거
    text = text.strip()
    # 3. ASCII가 아닌 문자는 아예 삭제 (ignore)
    return text.encode('ascii', 'ignore').decode('ascii')

# --- [설정] Gmail 서버 ---
SMTP_SERVER = "smtp.gmail.com"

# --- [1단계] 환경변수 로드 & 즉시 세탁 ---
# 가져오자마자 바로 세탁기에 돌립니다.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
EMAIL_USER = nuclear_clean(os.environ.get("EMAIL_USER", ""))
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "").strip()
EMAIL_RECEIVER = nuclear_clean(os.environ.get("EMAIL_RECEIVER", ""))

# [진단] 세탁 결과 확인
print("="*30)
print("🔍 DNA ANALYSIS (After Cleaning):")
print(f"Sender:   '{EMAIL_USER}' (Len: {len(EMAIL_USER)})")
print(f"Receiver: '{EMAIL_RECEIVER}' (Len: {len(EMAIL_RECEIVER)})")
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
    # 본문 텍스트 정규화
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
    
    # [안전 조치] 본문 내 유령 문자(\xa0)를 일반 공백으로 치환
    if report_body:
        report_body = report_body.replace('\xa0', ' ')

    safe_date = datetime.now().strftime('%Y-%m-%d')
    subject_text = f"Strategic_Council_Report_{safe_date}"
    
    # 이메일 메시지 객체 생성 (UTF-8 강제)
    # EMAIL_USER와 RECEIVER는 이미 상단에서 nuclear_clean으로 완벽하게 세탁되었습니다.
    msg = MIMEText(report_body, 'plain', 'utf-8')
    msg['Subject'] = Header(subject_text, 'utf-8')
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER

    print("Connecting to Gmail Server...")

    try:
        server = smtplib.SMTP(SMTP_SERVER, 587, local_hostname='localhost')
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # send_message는 헤더 인코딩을 알아서 처리해줍니다.
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
