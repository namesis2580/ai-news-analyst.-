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

# --- [1단계] 이메일 주소 '수술' 함수 (Regex Extraction) ---
def extract_pure_email(text):
    if text is None: return ""
    text = str(text)
    # 1. 모든 유령 공백 제거
    text = "".join(text.split())
    # 2. 정규표현식으로 '이메일 주소 패턴'만 강제 추출
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    if match:
        return match.group(0)
    else:
        return text.encode('ascii', 'ignore').decode('ascii').strip()

# --- [2단계] 본문 정화 ---
def clean_text_body(text):
    if text is None: return ""
    text = str(text)
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('\xa0', ' ').replace('&nbsp;', ' ').replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<').replace('&quot;', '"')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# --- 환경변수 로드 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 이메일 주소 추출
raw_user = os.environ.get("EMAIL_USER", "")
EMAIL_USER = extract_pure_email(raw_user)

EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "").strip()

raw_receiver = os.environ.get("EMAIL_RECEIVER", "")
EMAIL_RECEIVER = extract_pure_email(raw_receiver)

print(f"DEBUG: Cleaned EMAIL_USER: {repr(EMAIL_USER)}")
print(f"DEBUG: Cleaned EMAIL_RECEIVER: {repr(EMAIL_RECEIVER)}")

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
        
        # 닥터 둠과 전략 위원회 프롬프트
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
    report_body = clean_text_body(report_body)
    
    msg = MIMEMultipart()
    
    # [핵심 수정] 제목을 문자열 복사가 아니라 '조립'합니다.
    # 이렇게 하면 소스코드 복사 과정에서 유령 공백이 끼어들 틈이 없습니다.
    # "Strategic Council Report - YYYY-MM-DD"
    title_parts = ["Strategic", "Council", "Report", "-", datetime.now().strftime('%Y-%m-%d')]
    safe_subject = " ".join(title_parts)
    
    # 한번 더 안전장치: ASCII 강제 변환
    safe_subject = safe_subject.encode('ascii', 'ignore').decode('ascii').strip()
    
    msg['Subject'] = safe_subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER
    
    msg.attach(MIMEText(report_body, 'plain', 'utf-8'))

    print("Connecting to Gmail Server...")
    print(f"Debug - Final Subject: {safe_subject}")
    
    try:
        # [디버깅] SMTP 통신 과정을 로그에 출력 (문제 발생 시 원인 파악용)
        server = smtplib.SMTP(SMTP_SERVER, 587)
        server.set_debuglevel(1) # 로그 상세 출력 켜기
        
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
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
