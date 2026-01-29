import os
import smtplib
import feedparser
import google.generativeai as genai
from datetime import datetime
import time
import re
import unicodedata
import traceback  # [추가] 상세 에러 추적을 위한 모듈

# --- [설정] Gmail 서버 ---
SMTP_SERVER = "smtp.gmail.com"

# --- [0단계] 철저한 무균실 세탁 함수 ---
def forensic_clean(text, var_name):
    if text is None: return ""
    text = str(text)
    
    print(f"--- Checking {var_name} ---")
    # 원본 상태에서 이상한 문자가 있는지 헥사값으로 확인
    dirty_chars = [f"{i}:{c}({hex(ord(c))})" for i, c in enumerate(text) if ord(c) > 127]
    if dirty_chars:
        print(f"⚠️ WARN: Found non-ASCII chars in {var_name}: {dirty_chars}")
    
    # 1. 유니코드 정규화
    text = unicodedata.normalize('NFKC', text)
    # 2. 유령 공백 제거
    text = text.replace('\xa0', '').replace('\u200b', '')
    # 3. ASCII가 아닌 모든 문자 강제 삭제 (화이트리스트 방식)
    # 영어, 숫자, 기본 기호(@, ., _, -)만 남김
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@._-"
    clean_text = "".join([c for c in text if c in allowed])
    
    print(f"✅ Cleaned {var_name}: '{clean_text}' (Len: {len(clean_text)})")
    return clean_text

def clean_text_body(text):
    if text is None: return ""
    text = str(text)
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# --- [1단계] 환경변수 로드 및 검증 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

# 여기서 바로 세탁 들어갑니다.
EMAIL_USER = forensic_clean(os.environ.get("EMAIL_USER", ""), "EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "").strip()
EMAIL_RECEIVER = forensic_clean(os.environ.get("EMAIL_RECEIVER", ""), "EMAIL_RECEIVER")

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
        
        # [원본 유지] 닥터 둠과 위원회 풀버전 프롬프트
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
        return clean_text_body(response.text)
    except Exception as e:
        # 에러 발생 시 상세 정보 반환
        return f"Error in analysis: {e}\n{traceback.format_exc()}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    
    # 1. 제목 생성 (언더바 사용)
    safe_date = datetime.now().strftime('%Y-%m-%d')
    subject = f"Strategic_Council_Report_{safe_date}"
    
    # 2. 본문 생성
    email_content = f"""From: {EMAIL_USER}
To: {EMAIL_RECEIVER}
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 8bit

{report_body}
"""
    
    # [진단] 전송 직전 데이터 최종 확인
    print("--- PRE-FLIGHT CHECK ---")
    print(f"Sender: '{EMAIL_USER}' (ASCII ONLY: {EMAIL_USER.isascii()})")
    print(f"Receiver: '{EMAIL_RECEIVER}' (ASCII ONLY: {EMAIL_RECEIVER.isascii()})")
    print(f"Subject: '{subject}' (ASCII ONLY: {subject.isascii()})")
    
    # 만약 여기서 ASCII가 아니라면 강제로 에러를 발생시켜서 멈춥니다. (어설프게 보내지 않음)
    if not EMAIL_USER.isascii() or not EMAIL_RECEIVER.isascii():
        raise ValueError("FATAL ERROR: Email address still contains non-ASCII characters!")

    print("Connecting to Gmail Server...")

    try:
        # local_hostname 지정으로 헬로 메시지 이슈 차단
        server = smtplib.SMTP(SMTP_SERVER, 587, local_hostname='localhost')
        server.set_debuglevel(1) # [중요] SMTP 서버와의 통신 내역을 전부 출력
        
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        
        # [최종] 바이트 전송
        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, email_content.encode('utf-8'))
        
        server.quit()
        print("✅ Email sent successfully!")
        
    except Exception:
        print("\n❌ FATAL ERROR in send_email:")
        # [핵심] 여기서 에러의 전체 족보(Stack Trace)를 출력합니다.
        traceback.print_exc()

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
