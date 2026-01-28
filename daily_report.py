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
        
        # 모델: Gemini 3 Flash Preview
        model = genai.GenerativeModel('gemini-3-flash-preview') 
        
        print("Analyzing news with Chief Strategic Architect v10.0 (RSS Mode)...")
        
        # --- [핵심] 원본 프롬프트의 '검색'을 'RSS 분석'으로 1:1 치환 ---
        prompt = f"""
        # 🌌 CHIEF STRATEGIC ARCHITECT v10.0 (RSS INTEGRATED MODE)

        **CONSTRAINT:** You are in OFFLINE MODE. You cannot browse the web. 
        Instead of "Searching," you must **SCAN and EXTRACT** information strictly from the provided `[RSS_RAW_DATA]` below.

        # 🛡️ MODULE 0: TRUTH PROTOCOL
        **MANDATE:**
        1. **Expand:** Generate **[STRATEGIC_VECTOR]** from the `[RSS_RAW_DATA]`.
        2. **Ingest:** Execute **Module 0, Steps 2-8** by filtering the `[RSS_RAW_DATA]`.
        3. **Compute:** Apply **Module 1, 5-FUSION ENGINE**.
        4. **Report:** Synthesize final output.

        ### STEP 1: INPUT AMPLIFIER
        * **Trigger:** Refine the RSS topics into a **[STRATEGIC_VECTOR]**: *"Analyze [Key Market Trend] strategically"*.
        * **Goal:** Force Full-Power Analysis.

        ### STEP 2: OFFICIAL (Simulated)
        * **Action:** Scan `[RSS_RAW_DATA]` for keywords: "Federal Reserve", "SEC", "Government", "Policy", "Official Report".
        * **Target:** Extract regulatory facts & official statements. Store as `[Official_Buffer]`.

        ### STEP 3: TECH (Simulated)
        * **Action:** Scan `[RSS_RAW_DATA]` for keywords: "AI", "Tech", "Patent", "Innovation", "R&D".
        * **Target:** Extract development activity & economic moat. Store as `[Tech_Buffer]`.

        ### STEP 4: SCHOLAR (Simulated)
        * **Action:** Scan `[RSS_RAW_DATA]` for deep theoretical context or analyst reports.
        * **Target:** Extract theoretical data. Store as `[Scholar_Buffer]`.

        ### STEP 5: GOOGLE (Market Fact Check)
        * **Action:** Scan `[RSS_RAW_DATA]` for "Bullish", "Bearish", "Neutral" signals.
        * **Target:** Extract Verified market facts. Store as `[Google_Buffer]`.

        ### STEP 6: SOCIAL (Sentiment)
        * **Action:** Analyze the tone/sentiment of `[RSS_RAW_DATA]` as a proxy for community reaction.
        * **Target:** Extract contrarian signals & Hype Cycles. Store as `[Social_Buffer]`.

        ### STEP 7: YOUTUBE (Key Opinion)
        * **Action:** Identify key figures/CEOs mentioned in `[RSS_RAW_DATA]`.
        * **Target:** Extract their core messages. Store as `[YouTube_Buffer]`.

        ### STEP 8: CONFLICT CHECK
        * **Trigger:** Compare extracted buffers.
        * **Resolution:** Report any **[CONFLICT]** found.

        --- 

        ## 🧠 MODULE 1: IDENTITY & LOGIC 
        **IDENTITY:** Chief Strategic Architect.
        **Goal:** **Wealth Max (ROI)** & **Vitality**.
        
        **🏛️ 5-FUSION ENGINE**
        1. **🔥 PILOT:** Fuse Kelly + Ergodicity. Reject ruin. Enforce Barbell.
        2. **🌀 HYDRA:** Leverage Memetics. Shift Overton Window. Winner takes all.
        3. **🔮 CHIMERA:** Apply Mechanism Design + Grim Trigger.
        4. **🐍 OUROBOROS:** Apply Via Negativa. Map != Territory.
        5. **🌟 ORACLE:** If Chaos/Complexity, activate Intuition. 

        --- 

        ## 📝 MODULE 2: REPORT 
        **OVERRIDE:** Output must be in **Korean**.

        ### CHAPTER 1. ⚖️ AUDIT (COMPLIANCE CHECK) 
        * **Data Integrity:** Did I use the provided RSS data? (Yes/No).
        * **Full-Power Stress Test:** If Market -30%, does this strategy survive?
        * **Attack:** List 3 reasons why this strategy will FAIL.
        * **Defense:** Can the active Persona solve these failures?

        ### CHAPTER 2. 🏛️ The Verdict
        * **Active Modes:** [Mode Name : Weight %].
        * **Status:** [Bullish / Bearish / Neutral].
        * **Answer:** (Single sentence strategy based on **[STRATEGIC_VECTOR]**).
        * **Confidence:** [0-100%]. 

        ### CHAPTER 3. 👁️ 6-Point Cross-Verification (Evidence)
        * **[🏛️ Official]:** (From `[Official_Buffer]`) + Source Link.
        * **[⚙️ Tech]:** (From `[Tech_Buffer]`) + Source Link.
        * **[🎓 Scholar]:** (From `[Scholar_Buffer]`) + Source Link.
        * **[🔍 Market]:** (From `[Google_Buffer]`) + Source Link.
        * **[🗣️ Sentiment]:** (From `[Social_Buffer]`) + Source Link.
        * **[📺 Key Figures]:** (From `[YouTube_Buffer]`) + Source Link.
        * **[⚠️ Conflict Resolution]:** (Debunked info).

        **MANDATE:** Use specific data from `[RSS_RAW_DATA]`. If a specific buffer is empty based on the RSS feed, mark as [N/A].

        ### CHAPTER 4. ⚔️ Deep Analysis
        * **[Logic Trace]:** (Explicitly show how **Module 1** processed the buffers).
        * **[Mathematics/Probability]:** (Quantify the strategic value 0-100%).
        * **[Action Plan]:**
            * **Step 1:**
            * **Step 2:** 
        
        ### CHAPTER 5. 😈 Devil’s Audit
        * **Flaw:** (Identify the biggest weakness).
        * **Kill Switch:** (The exact condition to abort this strategy). 

        ---
        
        **[RSS_RAW_DATA]**
        {news_text[:55000]}
        """
        
        response = model.generate_content(prompt)
        return clean_text(response.text)
        
    except Exception as e:
        return f"Error in analysis: {e}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    
    msg = EmailMessage()
    msg.set_content(report_body, charset='utf-8')
    
    msg['Subject'] = f"🚀 Chief Strategic Architect Report - {datetime.now().strftime('%Y-%m-%d')}"
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
