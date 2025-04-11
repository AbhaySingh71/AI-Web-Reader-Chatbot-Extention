import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache
from langchain_community.document_loaders import WebBaseLoader, SeleniumURLLoader
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI  


load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['CACHE_TYPE'] = 'simple'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
cache = Cache(app)

logging.basicConfig(
    filename='app.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# Load key from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
USER_AGENT = os.getenv("USER_AGENT")

os.environ["USER_AGENT"] = USER_AGENT


llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash",
    temperature=0.5,
    max_output_tokens=512,
    google_api_key=GOOGLE_API_KEY 
)

# ---------------------
# Utility Functions
# ---------------------
def clean_html(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form", "iframe", "noscript"]):
            tag.decompose()
        main_content = soup.find("article") or soup.find("main") or soup.body or soup
        return main_content.get_text(separator="\n", strip=True)[:12000]
    except Exception as e:
        logging.error("Error cleaning HTML: %s", e)
        return ""

def scrape_website(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            text = clean_html(response.text)
            print("\n📝 Scraped Content from requests:\n", text[:1000], "\n... [truncated]\n")  # ✅ Print first 1000 chars
            return text
    except Exception as e:
        logging.error("Request failed for URL %s: %s", url, e)

    try:
        loader = WebBaseLoader(url)
        docs = loader.load()
        content = docs[0].page_content[:12000] if docs else "No content found."
        print("\n📝 Scraped Content from WebBaseLoader:\n", content[:1000], "\n... [truncated]\n")  # ✅
        return content
    except Exception as e:
        logging.error("WebBaseLoader failed: %s", e)

    try:
        loader = SeleniumURLLoader(url)
        docs = loader.load()
        content = docs[0].page_content[:12000] if docs else "No content found."
        print("\n📝 Scraped Content from SeleniumURLLoader:\n", content[:1000], "\n... [truncated]\n")  # ✅
        return content
    except Exception as e:
        logging.error("SeleniumURLLoader failed: %s", e)
        return "Error scraping webpage."


def generate_prompt(user_question, page_text):
    return (
        f"The following is content from a personal or product webpage:\n\n"
        f"{page_text}\n\n"
        f"Answer the following question based only on the above content:\n"
        f"{user_question}\n\n"
        f"If the answer is not available, say 'Information not available.'"
    )

# ---------------------
# Routes
# ---------------------
@app.route("/")
def home():
    return jsonify({"message": "Flask server (LangChain + Gemini Flash) is running!"})

@app.route("/answer", methods=["POST"])
def get_answer():
    data = request.get_json()
    if not data or "url" not in data or "question" not in data:
        return jsonify({"error": "Missing 'url' or 'question'"}), 400

    url = data["url"]
    user_question = data["question"]

    page_text = scrape_website(url)
    if not page_text.strip():
        return jsonify({"question": user_question, "answer": "Information not available."})

    prompt = generate_prompt(user_question, page_text)
    print("🔍 Prompt to Gemini Flash:\n", prompt[:500])

    try:
        response = llm.invoke(prompt)
        print("🤖 Gemini Response:", response)
        answer = response.content.strip() if hasattr(response, "content") else str(response).strip()
        if not answer:
            answer = "Information not available."
    except Exception as e:
        logging.error("Gemini LangChain error: %s", e)
        return jsonify({"question": user_question, "answer": f"❌ Gemini Error: {str(e)}"}), 500

    return jsonify({"question": user_question, "answer": answer})


if __name__ == "__main__":
    app.run(debug=True)
