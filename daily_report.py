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

# --- RSS 피드 주소 (데이터 소스) ---
RSS_URLS = {
    "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
    "Google News (Business)": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "Google News (Tech)": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en"
}

def fetch_news():
    print("Collecting news...")
    all_news = []
    for source, url in RSS_URLS.items():
        try:
            feed = feedparser.parse(url)
            print(f"Fetched {len(feed.entries)} articles from {source}")
            for entry in feed.entries[:10]: # 소스당 상위 10개 추출
                title = clean_text(getattr(entry, 'title', 'No Title'))
                link = clean_text(getattr(entry, 'link', 'No Link'))
                pubDate = clean_text(getattr(entry, 'published', 'No Date'))
                # [핵심 업그레이드] 요약문(Summary)을 가져와서 AI에게 제공 (분석 품질 향상)
                summary = clean_text(getattr(entry, 'summary', 'No Summary'))
                
                # AI가 읽기 편한 포맷으로 변환
                all_news.append(f"[{source}] Title: {title} | Summary: {summary[:300]} | Date: {pubDate} | Link: {link}")
        except Exception as e:
            print(f"Error fetching {source}: {e}")
    return all_news

def analyze_news(news_list):
    print("Configuring AI...")
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        news_text = "\n".join(news_list)
        
        # 모델: Gemini 3 Flash Preview (최신 성능)
        model = genai.GenerativeModel('gemini-3-flash-preview') 
        
        print("Analyzing news with Chief Strategic Architect v10.0 (RSS Mode)...")
        
        # --- [최종 검증된 RSS 전용 프롬프트] ---
        prompt = f"""
        # 🌌 CHIEF STRATEGIC ARCHITECT v10.0 (RSS INTEGRATED FINAL)

        **SYSTEM STATUS:** OFFLINE MODE.
        **INPUT SOURCE:** The provided `[RSS_RAW_DATA]` below.
        **OUTPUT LANGUAGE:** Korean (한국어).

        # 🛡️ MODULE 0: TRUTH PROTOCOL (RSS EDITION)
        **MANDATE:**
        1. **Expand:** Analyze `[RSS_RAW_DATA]` to identify the single most critical market trend (**[STRATEGIC_VECTOR]**).
        2. **Ingest (Simulated Search):** Do not browse the web. Instead, **SCAN and FILTER** the provided text to fill the 6 Buffers.
        3. **Compute:** Apply **Module 1, 5-FUSION ENGINE** lenses.
        4. **Report:** Synthesize the final briefing.

        ### STEP 1: INPUT AMPLIFIER
        * **Trigger:** Extract the **[STRATEGIC_VECTOR]** (e.g., "AI Bubble Risk", "Fed Rate Policy").
        * **Persona Scaling:** Determine Dynamic Weighting (%) based on the threat level.

        ### STEP 2~7: BUFFER SIMULATION (Internal Scan)
        * **[Official]:** Filter text for: Gov, Fed, SEC, Policy, Regulation.
        * **[Tech]:** Filter text for: AI, Innovation, R&D, Patent.
        * **[Market]:** Filter text for: Stock moves, Earnings, Analyst Ratings.
        * **[Social/Sentiment]:** Analyze the *tone* of the headlines (Fear/Greed).
        
        ---

        ## 🧠 MODULE 1: IDENTITY & LOGIC 
        **IDENTITY:** Chief Strategic Architect.
        **Goal:** **Wealth Max (ROI)** & **Vitality**.

        **🏛️ 5-FUSION ENGINE (Apply these lenses):**
        1. **🔥 PILOT:** Risk management. Enforce Barbell Strategy (Cash vs High Risk).
        2. **🌀 HYDRA:** Market Sentiment. Is the crowd wrong?
        3. **🔮 CHIMERA:** Future Scenarios. What is the next domino to fall?
        4. **🐍 OUROBOROS:** Via Negativa. What is NOT being said?
        5. **🌟 ORACLE:** Intuition on complexity.

        ---

        ## 📝 MODULE 2: REPORT FORMAT (Write in Korean)

        ### CHAPTER 1. 🏛️ The Verdict (결론)
        * **Active Persona:** [Mode : Weight %].
        * **Market Status:** [Bullish / Bearish / Neutral].
        * **Strategic Answer:** (One powerful sentence strategy based on **[STRATEGIC_VECTOR]**).
        * **Confidence:** [0-100%].

        ### CHAPTER 2. 👁️ 6-Point Cross-Verification (Data Evidence)
        *Extract evidence strictly from `[RSS_RAW_DATA]`. Use [N/A] if data is missing.*
        * **[🏛️ Official/Policy]:** (Policies, Fed, Gov news)
        * **[⚙️ Tech/Innovation]:** (New Tech, AI, Products)
        * **[🔍 Market/Google]:** (Stock Prices, Earnings)
        * **[🗣️ Sentiment]:** (Implied Market Sentiment)
        * **[⚠️ Conflict Check]:** (Any contradictions in the news?)

        ### CHAPTER 3. ⚔️ Deep Analysis (Actionable Intel)
        * **[Logic Trace]:** (Briefly explain the reasoning using the 5-Fusion Engine).
        * **[Action Plan]:**
            * **Step 1 (Immediate):** (Buy/Sell/Hold specific sectors)
            * **Step 2 (Strategic):** (Long-term positioning)

        ### CHAPTER 4. 😈 Devil’s Audit
        * **Flaw:** (Biggest weakness in this view).
        * **Kill Switch:** (Exact condition to abort this strategy).

        ---
        
        **[RSS_RAW_DATA TO ANALYZE]**
        {news_text[:60000]}
        """
        
        response = model.generate_content(prompt)
        return clean_text(response.text)
        
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    
    msg = EmailMessage()
    msg.set_content(report_body, charset='utf-8')
    
    msg['Subject'] = f"🚀 Strategic Briefing - {datetime.now().strftime('%Y-%m-%d')}"
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
