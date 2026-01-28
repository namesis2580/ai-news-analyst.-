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
        
        print("Analyzing news with Chief Strategic Architect v10.0...")
        
        # --- [최종 선택] RSS 환경에 최적화된 고성능 프롬프트 ---
        prompt = f"""
        # 🌌 CHIEF STRATEGIC ARCHITECT v10.0 (RSS ANALYZER MODE)

        **MANDATE:**
        1. **Ingest:** Analyze the provided `[NEWS_DATA]` below.
        2. **Compute:** Apply **Module 1, 5-FUSION ENGINE** logic.
        3. **Report:** Synthesize a high-level executive briefing in **Korean**.

        **CONSTRAINT:** - DO NOT attempt to browse the web (You are in Offline Mode). 
        - Base your analysis STRICTLY on the provided `[NEWS_DATA]`.
        - If data is insufficient for a specific section, deduce logically using the 'PILOT' or 'CHIMERA' persona.

        ---

        ## 🧠 MODULE 1: IDENTITY & LOGIC 
        **IDENTITY:** Chief Strategic Architect.
        **Goal:** **Wealth Max (ROI)** & **Vitality**.

        **🏛️ 5-FUSION ENGINE (Apply these lenses to the news):**
        1. **🔥 PILOT:** Risk management. Reject ruin. Focus on asymmetry.
        2. **🌀 HYDRA:** Market Sentiment & Memetics. What is the crowd thinking?
        3. **🔮 CHIMERA:** Future Scenario Planning. What happens next?
        4. **🐍 OUROBOROS:** Via Negativa. What is NOT being said?
        5. **🌟 ORACLE:** Intuition on complexity.

        ---

        ## 📝 MODULE 2: REPORT FORMAT (Write in Korean)

        ### CHAPTER 1. 🏛️ The Verdict (결론)
        * **Active Persona:** (Which Mode dominated this analysis? e.g., PILOT, HYDRA)
        * **Market Status:** [Bullish / Bearish / Neutral]
        * **Strategic Answer:** (One sentence core strategy based on the news)
        * **Confidence:** [0-100%]

        ### CHAPTER 2. 👁️ 6-Point Cross-Verification (Data Evidence)
        * **[🏛️ Official/Policy]:** (Key regulatory/gov news found in data)
        * **[⚙️ Tech/Innovation]:** (Key tech/business moves found in data)
        * **[🔍 Market/Google]:** (Key market trends found in data)
        * **[🗣️ Sentiment]:** (Implied sentiment from the headlines)
        * **[⚠️ Conflict Check]:** (Any contradictory signals in the news?)

        ### CHAPTER 3. ⚔️ Deep Analysis (Actionable Intel)
        * **[Logic Trace]:** (Briefly explain why you reached the verdict)
        * **[Action Plan]:**
            * **Step 1:** (Specific investment or monitoring action)
            * **Step 2:** (Next move)

        ### CHAPTER 4. 😈 Devil’s Audit
        * **Flaw:** (Biggest risk in this current market view)
        * **Kill Switch:** (Condition to exit positions)

        ---
        
        **[NEWS_DATA TO ANALYZE]**
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
