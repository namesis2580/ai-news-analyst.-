import os
import smtplib
import feedparser
import google.generativeai as genai
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# [핵심] 헤더를 인코딩 처리하는 전용 모듈 호출
from email.header import Header
from email.utils import formataddr
from datetime import datetime
import time
import re
import unicodedata

# --- [설정] Gmail 서버 ---
SMTP_SERVER = "smtp.gmail.com"

# --- [1단계] 이메일 주소 및 문자열 정밀 세탁 ---
def clean_str(text):
    if text is None: return ""
    text = str(text)
    # 유니코드 정규화 (NFKC)
    text = unicodedata.normalize('NFKC', text)
    # 모든 종류의 공백을 일반 스페이스(ASCII 32)로 치환
    text = re.sub(r'\s+', ' ', text)
    # 제어 문자 및 유령 공백 제거
    text = text.replace('\xa0', '').replace('\u200b', '')
    return text.strip()

def extract_email(text):
    # 정규식으로 이메일 주소만 핀셋으로 뽑아냄
    text = clean_str(text)
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if match:
        return match.group(0)
    return ""

# --- [2단계] 환경변수 로드 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
EMAIL_USER = extract_email(os.environ.get("EMAIL_USER", ""))
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "").strip()
EMAIL_RECEIVER = extract_email(os.environ.get("EMAIL_RECEIVER", ""))

print(f"DEBUG: Sender: {repr(EMAIL_USER)}")
print(f"DEBUG: Receiver: {repr(EMAIL_RECEIVER)}")

# --- [정보 수집 어벤져스] ---
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
                title = clean_str(getattr(entry, 'title', 'No Title'))
                link = clean_str(getattr(entry, 'link', 'No Link'))
                pubDate = clean_str(getattr(entry, 'published', 'No Date'))
                content = ""
                if hasattr(entry, 'content'): content = entry.content[0].value
                elif hasattr(entry, 'summary_detail'): content = entry.summary_detail.value
                elif hasattr(entry, 'summary'): content = entry.summary
                clean_content = clean_str(content)[:10000]
                all_news.append(f"[{source}] Title: {title} | Content: {clean_content} | Date: {pubDate} | Link: {link}")
        except Exception as e:
            print(f"Error fetching {source}: {e}")
    return all_news

def analyze_news(news_list):
    print("Configuring AI...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        news_text = "\n".join(news_list)
        # 내일 아침 리셋 후 정상 작동 (Gemini 3.0)
        model = genai.GenerativeModel('gemini-3-flash-preview') 
        print("Summoning The Strategic Council (Analysis Avengers)...")
        print(f"Input Data Length: {len(news_text)} characters") 
        
        # 닥터 둠과 친구들 (완전체)
        prompt = f"""
        # 🌌 STRATEGIC COUNCIL: THE AVENGERS PROTOCOL

        **CONTEXT:** You are the **'Chief Architect'** presiding over a high-stakes roundtable.
        **INPUT:** The provided `[RSS_RAW_DATA]` (Cleaned, High-Quality).
        **OUTPUT LANGUAGE:** Korean (한국어).

        **👥 THE COUNCIL MEMBERS (Your Internal Personas):**
        1.  **🐻 Dr. Doom (Risk):** Pessimistic. Focuses on flaws, bubbles, debt, and regulatory threats.
        2.  **🐂 The Visionary (Growth):** Optimistic. Focuses on innovation, adoption, and 10x opportunities.
        3.  **🦅 The Hawk (Macro):** Realist. Focuses on Fed rates, Oil, Wars, and Liquidity.
        4.  **🦊 The Fox (Contrarian):** Skeptic of the crowd. Looks for information asymmetry.

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
        return clean_str(response.text)
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    report_body = clean_str(report_body)
    
    msg = MIMEMultipart()
    
    # [Protocol 10.0 핵심 기술]
    # 일반 문자열 대입이 아니라, 'Header' 객체를 사용하여 UTF-8 인코딩을 명시합니다.
    # 이렇게 하면 파이썬이 내부적으로 ASCII로 변환하려다 실패하는 것을 원천 차단합니다.
    subject_text = f"Strategic Council Report - {datetime.now().strftime('%Y-%m-%d')}"
    msg['Subject'] = Header(subject_text, 'utf-8')
    
    # From/To 헤더도 안전하게 처리
    msg['From'] = Header(EMAIL_USER, 'utf-8')
    msg['To'] = Header(EMAIL_RECEIVER, 'utf-8')
    
    msg.attach(MIMEText(report_body, 'plain', 'utf-8'))

    print("Connecting to Gmail Server...")
    # 디버깅: 인코딩된 헤더가 어떻게 보이는지 확인
    print(f"Debug - Encoded Subject: {msg['Subject']}")

    try:
        server = smtplib.SMTP(SMTP_SERVER, 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # send_message 메서드는 Header 객체가 설정된 msg를 가장 안전하게 처리합니다.
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
