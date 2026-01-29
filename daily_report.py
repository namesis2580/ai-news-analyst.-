import os
import smtplib
import feedparser
import google.generativeai as genai
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import time
import re
import unicodedata

# --- [설정] Gmail 서버 ---
SMTP_SERVER = "smtp.gmail.com"

# --- [1단계] 문자열 무균실 세탁 (유령문자 박멸) ---
def clean_str(text):
    if text is None: return ""
    text = str(text)
    # 1. 유니코드 정규화 (이상한 공백을 표준 공백으로)
    text = unicodedata.normalize('NFKC', text)
    # 2. 모든 종류의 공백/탭/줄바꿈을 일반 스페이스(ASCII 32)로 단일화
    text = re.sub(r'\s+', ' ', text)
    # 3. 유령 공백(\xa0, \u200b) 하드코딩 제거
    text = text.replace('\xa0', '').replace('\u200b', '')
    return text.strip()

def extract_email(text):
    text = clean_str(text)
    # 정규식으로 순수 이메일만 추출
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

# --- [3단계] 정보 수집 ---
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
        return clean_str(response.text)
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    report_body = clean_str(report_body)
    
    msg = MIMEMultipart()
    
    # [핵심 변경 1] 제목을 안전한 ASCII 문자로만 구성 (공백 대신 언더바 사용)
    # "Strategic_Council_Report_YYYY-MM-DD"
    # 띄어쓰기가 에러의 주범이므로 아예 없애버립니다.
    safe_date = datetime.now().strftime('%Y-%m-%d')
    safe_subject = f"Strategic_Council_Report_{safe_date}"
    
    msg['Subject'] = safe_subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER
    
    # 본문은 UTF-8로 지정
    msg.attach(MIMEText(report_body, 'plain', 'utf-8'))

    print("Connecting to Gmail Server...")
    print(f"Debug - Final Subject: {safe_subject}")

    try:
        server = smtplib.SMTP(SMTP_SERVER, 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # [핵심 변경 2] 'Bytes' 강제 주입 (파이썬 인코딩 검사 우회)
        # 1. 메시지 전체를 문자열로 만듭니다.
        full_msg_str = msg.as_string()
        
        # 2. 혹시 남아있을지 모를 유령 공백을 바이트 변환 직전에 최후 제거
        full_msg_str = full_msg_str.replace('\xa0', ' ')
        
        # 3. UTF-8 'Bytes'로 변환합니다. (이러면 파이썬은 ASCII 검사를 안 합니다)
        full_msg_bytes = full_msg_str.encode('utf-8')
        
        # 4. 바이트 상태 그대로 전송합니다.
        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, full_msg_bytes)
        
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
