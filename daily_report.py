import os
import smtplib
import feedparser
import google.generativeai as genai
from datetime import datetime
import time
import re
import unicodedata
import traceback

# --- [설정] Gmail 서버 ---
SMTP_SERVER = "smtp.gmail.com"

# --- [0단계] 무균실 세탁 함수 ---
def forensic_clean(text, var_name):
    if text is None: return ""
    text = str(text)
    text = unicodedata.normalize('NFKC', text)
    text = text.replace('\xa0', '').replace('\u200b', '')
    try:
        text = text.encode('ascii', 'ignore').decode('ascii')
    except Exception:
        pass
    text = text.strip()
    if "PASSWORD" in var_name:
        print(f"✅ Cleaned {var_name}: (Hidden) [Length: {len(text)}]")
    else:
        print(f"✅ Cleaned {var_name}: '{text}' (Len: {len(text)})")
    return text

# RSS 데이터는 깔끔하게 태그 제거
def clean_rss_text(text):
    if text is None: return ""
    text = str(text)
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'<[^>]+>', '', text) 
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# [중요] AI 결과는 HTML 태그를 살려둬야 디자인이 나옴
def clean_report_body(text):
    if text is None: return ""
    text = str(text)
    text = unicodedata.normalize('NFKC', text)
    text = text.replace('\xa0', ' ') 
    return text.strip()

# --- [1단계] 환경변수 로드 ---
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
EMAIL_USER = forensic_clean(os.environ.get("EMAIL_USER", ""), "EMAIL_USER")
EMAIL_PASSWORD = forensic_clean(os.environ.get("EMAIL_PASSWORD", ""), "EMAIL_PASSWORD") 
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
                title = clean_rss_text(getattr(entry, 'title', 'No Title'))
                link = clean_rss_text(getattr(entry, 'link', 'No Link'))
                pubDate = clean_rss_text(getattr(entry, 'published', 'No Date'))
                content = ""
                if hasattr(entry, 'content'): content = entry.content[0].value
                elif hasattr(entry, 'summary_detail'): content = entry.summary_detail.value
                elif hasattr(entry, 'summary'): content = entry.summary
                clean_content = clean_rss_text(content)[:10000]
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
        
        # [HTML 디자인 + 닥터 둠 풀버전 프롬프트]
        # 여기에 색상(color)과 스타일(style) 지시가 포함되어야 예쁘게 나옵니다.
        prompt = f"""
        # 🌌 STRATEGIC COUNCIL: THE AVENGERS PROTOCOL

        **ROLE:** You are the **'Chief Architect'**.
        **GOAL:** Create a highly readable, visual **HTML Email Report**.
        **LANGUAGE:** Korean (한국어).

        **🎨 DESIGN INSTRUCTIONS (HTML & Inline CSS):**
        * Use a modern, clean design.
        * **Dr. Doom (Risk):** MUST speak in <span style='color: #D32F2F; font-weight:bold;'>Red tones</span>.
        * **The Visionary (Growth):** MUST speak in <span style='color: #1976D2; font-weight:bold;'>Blue tones</span>.
        * **The Hawk (Macro):** MUST speak in <span style='color: #388E3C; font-weight:bold;'>Green tones</span>.
        * **The Fox (Contrarian):** MUST speak in <span style='color: #FBC02D; font-weight:bold; background-color: #333; padding: 2px;'>Yellow on Dark</span>.
        * Use `<h3>` for Chapter titles.
        * Use `<ul>` and `<li>` for lists.
        * Use `<b>` for emphasis (No Markdown `**`).
        
        **👥 THE COUNCIL MEMBERS (Full Persona):**
        1.  **🐻 Dr. Doom (Risk):** Pessimistic. Focuses on flaws, bubbles, debt, and regulatory threats.
        2.  **🐂 The Visionary (Growth):** Optimistic. Focuses on innovation, adoption, and 10x opportunities.
        3.  **🦅 The Hawk (Macro):** Realist. Focuses on Fed rates, Oil, Wars, and Liquidity.
        4.  **🦊 The Fox (Contrarian):** Skeptic of the crowd. Looks for information asymmetry.

        ## 📝 REPORT STRUCTURE

        <h3>👑 CHAPTER 1. The Architect's Verdict</h3>
        <div style="border: 1px solid #ccc; padding: 15px; background-color: #f9f9f9; border-radius: 5px;">
          <p><b>Strategic Vector:</b> (The single most important trend)</p>
          <p><b>Market Stance:</b> [Aggressive Buy / Cautious Buy / Neutral / Sell / Short]</p>
          <p><b>Confidence Score:</b> [0-100%]</p>
          <p><b>The Bottom Line:</b> (Synthesize the directive)</p>
        </div>

        <h3>🗣️ CHAPTER 2. The Council's Debate</h3>
        <p><i>Simulate a short, intense debate.</i></p>
        <ul>
          <li><span style='color: #D32F2F;'><b>🐻 Dr. Doom:</b></span> "Wait, look at the risks in..."</li>
          <li><span style='color: #1976D2;'><b>🐂 The Visionary:</b></span> "But you are missing the growth signal in..."</li>
          <li><span style='color: #388E3C;'><b>🦅 The Hawk:</b></span> "Actually, the macro environment suggests..."</li>
          <li><span style='color: #FBC02D; background-color:#333; padding:2px;'><b>🦊 The Fox:</b></span> "The crowd is wrong because..."</li>
        </ul>

        <h3>👁️ CHAPTER 3. Evidence & Triangulation</h3>
        <ul>
          <li><b>[Macro/Energy]:</b> ...</li>
          <li><b>[Tech/VC]:</b> ...</li>
          <li><b>[Market/Money]:</b> ...</li>
          <li><b>[Conflict]:</b> ...</li>
        </ul>

        <h3>⚔️ CHAPTER 4. Action Plan</h3>
        <table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse; width: 100%;">
          <tr style="background-color: #eee;"><th>Step</th><th>Action</th></tr>
          <tr><td><b>🛡️ Defense</b></td><td>(How to not lose money)</td></tr>
          <tr><td><b>⚔️ Offense</b></td><td>(Where to attack for profit)</td></tr>
          <tr><td><b>🚨 Kill Switch</b></td><td>(Condition to exit immediately)</td></tr>
        </table>

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
        return clean_report_body(response.text)
    except Exception as e:
        return f"Error in analysis: {e}\n{traceback.format_exc()}"

def send_email(report_body):
    print(f"Preparing email via {SMTP_SERVER}...")
    
    safe_date = datetime.now().strftime('%Y-%m-%d')
    subject = f"Strategic_Council_Report_{safe_date}"
    
    # [핵심] Content-Type을 'text/html'로 설정해야 예쁘게 보입니다.
    email_content = f"""From: {EMAIL_USER}
To: {EMAIL_RECEIVER}
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/html; charset="utf-8"
Content-Transfer-Encoding: 8bit

<html>
<head>
    <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h3 {{ border-bottom: 2px solid #333; padding-bottom: 5px; margin-top: 30px; }}
        li {{ margin-bottom: 10px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
{report_body}
<br><br>
<hr>
<p style="font-size: 12px; color: #999; text-align: center;">Generated by AI News Analyst (The Avengers Protocol)</p>
</body>
</html>
"""
    
    print("--- PRE-FLIGHT CHECK ---")
    if not EMAIL_PASSWORD.isascii():
        print("❌ CRITICAL: Password contains non-ASCII characters!")
        return

    print("Connecting to Gmail Server...")

    try:
        server = smtplib.SMTP(SMTP_SERVER, 587, local_hostname='localhost')
        server.set_debuglevel(1) 
        
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_USER, EMAIL_RECEIVER, email_content.encode('utf-8'))
        
        server.quit()
        print("✅ Email sent successfully!")
        
    except Exception:
        print("\n❌ FATAL ERROR in send_email:")
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
