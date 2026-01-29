import os
import smtplib
import feedparser
import google.generativeai as genai
from email.message import EmailMessage
from datetime import datetime
import time
import re

# --- [설정] Gmail 서버 ---
SMTP_SERVER = "smtp.gmail.com"

# --- [1단계] 환경변수 '강제' 정화 함수 (ASCII가 아니면 무조건 삭제) ---
def sanitize_env_var(value):
    if value is None:
        return ""
    # 1. 문자열 변환
    value = str(value)
    # 2. 유령 공백(\xa0)을 일반 공백으로 치환 후 strip
    value = value.replace('\xa0', '').replace('&nbsp;', '')
    # 3. [핵심] ASCII 문자가 아닌 것은 아예 삭제 (이메일 주소에 한글/특수문자 불가)
    # ignore 옵션: 해석 불가능한 문자는 그냥 버림
    return value.encode('ascii', 'ignore').decode('ascii').strip()

# --- [2단계] 일반 텍스트 세탁 (본문용 - 한글 허용) ---
def clean_text_body(text):
    if text is None: return ""
    text = str(text)
    # HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # 특수문자 치환
    text = text.replace('\xa0', ' ').replace('&nbsp;', ' ').replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<').replace('&quot;', '"')
    # 공백 정리
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# --- 환경변수 로드 및 즉시 정화 ---
# 여기서부터 모든 변수는 깨끗한 상태가 됩니다.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
EMAIL_USER = sanitize_env_var(os.environ.get("EMAIL_USER"))      # 이메일 주소 정화
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "").strip()    # 비번은 건드리지 않음
EMAIL_RECEIVER = sanitize_env_var(os.environ.get("EMAIL_RECEIVER")) # 수신자 주소 정화

# --- [디버깅] 정화된 이메일 주소 확인 (로그에는 앞자리만 표시) ---
print(f"Debug: Sanitized EMAIL_USER length: {len(EMAIL_USER)}")
print(f"Debug: Sanitized EMAIL_RECEIVER length: {len(EMAIL_RECEIVER)}")

# --- [정보 수집 어벤져스] 9개 소스 ---
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
                if hasattr(entry, 'content'):
                    content = entry.content[0].value
                elif hasattr(entry, 'summary_detail'):
                    content = entry.summary_detail.value
                elif hasattr(entry, 'summary'):
                    content = entry.summary
                
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
        
        # 모델: Gemini 3 Flash Preview (내일 아침 리셋 후 정상 작동)
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

        response = model.generate_content(
            prompt, 
            request_options={"timeout": 1000},
            safety_settings=safety_settings
        )
        return clean_text_body(response.text)
        
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    
    # 본문 세탁
    report_body = clean_text_body(report_body)
    
    msg = EmailMessage()
    msg.set_content(report_body, charset='utf-8')
    
    # 제목 세탁 (강력 정화: ASCII만 남김)
    raw_subject = f"Strategic Council Report - {datetime.now().strftime('%Y-%m-%d')}"
    safe_subject = sanitize_env_var(raw_subject)
    msg['Subject'] = safe_subject
    
    # 발신자/수신자 (이미 위에서 sanitize_env_var로 씻었음)
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER

    print("Connecting to Gmail Server...")
    print(f"Debug - Final Subject: {safe_subject}")
    
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
        
        if report and "Error" not in report:
            send_email(report)
        else:
            print("\n❌ Report generation failed!")
            print("="*30)
            print("👇 ERROR DETAILS (원인은 아래와 같습니다) 👇")
            print(report)
            print("="*30)
    else:
        print("No news found.")
