import os
import re
import json
import logging
import base64
from datetime import datetime
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from github import Github

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

GOOGLE_SHEET_NAME     = "TechBlogData"
GITHUB_REPO_PATH      = os.environ.get("GITHUB_REPOSITORY") 
GEMINI_API_KEY        = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN          = os.environ.get("GH_TOKEN")
GOOGLE_CREDENTIALS    = os.environ.get("GOOGLE_CREDENTIALS")

def get_google_sheets_client():
    """Decodes base64 string securely to avoid any string escape corruption"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    encoded_str = GOOGLE_CREDENTIALS.strip()
    # Decode base64 to clean original JSON string
    decoded_bytes = base64.b64decode(encoded_str)
    decoded_str = decoded_bytes.decode("utf-8")
    
    creds_info = json.loads(decoded_str)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    client = gspread.authorize(creds)
    return client

def generate_seo_content(keyword, category):
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"Write a professional SEO-friendly article in Markdown format for college students on the topic: '{keyword}' under the category: '{category}'. Keep it structured and around 1000 words."
    
    log.info("Sending prompt to Gemini (model: gemini-2.5-flash) ...")
    response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
    return response.text

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def main():
    log.info("════════════════════════════════════════════════════════════")
    log.info("  SEO Content Engine — starting run")
    log.info("════════════════════════════════════════════════════════════")
    
    try:
        log.info("Authenticating with Google Sheets API via Base64 Decode...")
        sheets_client = get_google_sheets_client()
        log.info(f"Opening Google Sheet: '{GOOGLE_SHEET_NAME}' ...")
        sheet = sheets_client.open(GOOGLE_SHEET_NAME).sheet1
        records = sheet.get_all_records()
    except Exception as e:
        log.error(f"❌ Google Sheets Connection Failed: {e}")
        return

    target_row_index = None
    keyword = None
    category = None
    
    for index, row in enumerate(records, start=2):
        if row.get("Status", "").strip().lower() == "pending":
            target_row_index = index
            keyword = row.get("Keyword")
            category = row.get("Category")
            break
            
    if not target_row_index:
        log.info("🎉 No pending keywords found!")
        return
        
    log.info(f"Found pending row {target_row_index} — '{keyword}'")

    try:
        blog_content = generate_seo_content(keyword, category)
    except Exception as e:
        log.error(f"❌ Gemini API Generation Failed: {e}")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    clean_title = keyword.replace('"', '\\"')
    
    front_matter = f"---\ntitle: \"{clean_title}\"\ndate: {today_str}\ncategory: {category}\nlayout: post\n---\n\n"
    final_markdown_data = front_matter + blog_content
    file_name = f"{today_str}-{slugify(keyword)}.md"
    file_path = f"_posts/{file_name}"

    try:
        log.info(f"Pushing '{file_name}' to GitHub main branch...")
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO_PATH)
        
        repo.create_file(
            path=file_path,
            message=f"Auto-published blog post: {keyword}",
            content=final_markdown_data,
            branch="main"
        )
        log.info("✅ File successfully uploaded to GitHub '_posts/' folder!")
    except Exception as e:
        log.error(f"❌ GitHub Push Failed: {e}")
        return

    try:
        sheet.update_cell(target_row_index, 3, "Published")
        log.info(f"🎯 Google Sheet updated successfully!")
    except Exception as e:
        log.warning(f"⚠️ Sheet update failed but file was pushed: {e}")

if __name__ == "__main__":
    main()
