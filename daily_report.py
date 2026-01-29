import os
import smtplib
import feedparser
import google.generativeai as genai
from email.message import EmailMessage
from datetime import datetime
import time
import re
import unicodedata

# --- [설정] Gmail 서버 ---
SMTP_SERVER = "smtp.gmail.com"

# --- [1단계] 일반 텍스트 세탁 (본문용, 한글 보존) ---
def clean_text(text):
    if text is None: return ""
    text = str(text)
    # 1. 유니코드 정규화 (모든 특수 공백을 일반 공백으로 변환)
    text = unicodedata.normalize('NFKC', text)
    # 2. HTML 태그 제거
    text = re.sub(r'<[^>]+>', '', text)
    # 3. 유령 공백(\xa0) 하드코딩 제거
    text = text.replace('\xa0', ' ')
    # 4. 공백 정리
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# --- [2단계] 헤더용 강력 세탁 (제목/이메일용, 특수문자 아예 삭제) ---
def force_ascii_clean(text):
    if text is None: return ""
    text = str(text)
    # 유령 공백을 일반 공백으로 먼저 치환
    text = text.replace('\xa0', ' ')
    
    # ASCII 범위(영어, 숫자, 기본기호)가 아닌 문자는 모두 무시(ignore)하고 삭제
    # 이렇게 하면 한글이나 이모지, 유령 공백이 제목에 들어가면 다 사라집니다. (안정성 최우선)
    return text.encode('ascii', 'ignore').decode('ascii').strip()

# --- 환경변수 ---
# API 키는 그대로 둠
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 이메일 관련 변수는 force_ascii_clean으로 강력 세탁 (주소에 특수문자 금지)
EMAIL_USER = force_ascii_clean(os.environ.get("EMAIL_USER"))
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "").strip()
EMAIL_RECEIVER = force_ascii_clean(os.environ.get("EMAIL_RECEIVER"))

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
                title = clean_text(getattr(entry, 'title', 'No Title'))
                link = clean_text(getattr(entry, 'link', 'No Link'))
                pubDate = clean_text(getattr(entry, 'published', 'No Date'))
                
                content = ""
                if hasattr(entry, 'content'):
                    content = entry.content[0].value
                elif hasattr(entry, 'summary_detail'):
                    content = entry.summary_detail.value
                elif hasattr(entry, 'summary'):
                    content = entry.summary
                
                clean_content = clean_text(content)[:10000]
                all_news.append(f"[{source}] Title: {title} | Content: {clean_content} | Date: {pubDate} | Link: {link}")
        except Exception as e:
            print(f"Error fetching {source}: {e}")
    return all_news

def analyze_news(news_list):
    print("Configuring AI...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        news_text = "\n".join(news_list)
        
        # 모델: Gemini 3 Flash Preview (내일 아침 작동)
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
        return clean_text(response.text)
        
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    
    # [1] 본문은 한글이 있어야 하므로 clean_text 사용 (유니코드 정규화)
    report_body = clean_text(report_body)
    
    msg = EmailMessage()
    msg.set_content(report_body, charset='utf-8')
    
    # [2] 제목은 에러 방지를 위해 강제로 영어/숫자만 남김 (force_ascii_clean)
    # 이렇게 하면 "\xa0" 같은 유령 문자가 있어도 강제로 삭제되어 전송 성공함
    raw_subject = f"Strategic Council Report - {datetime.now().strftime('%Y-%m-%d')}"
    safe_subject = force_ascii_clean(raw_subject)
    
    msg['Subject'] = safe_subject
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_RECEIVER

    print("Connecting to Gmail Server...")
    print(f"Debug - Subject: {safe_subject}") # 디버깅용: 실제 전송될 제목 확인
    
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
