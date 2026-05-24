import os
import re
import json
import logging
from datetime import datetime
from google import genai
from google.genai import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from github import Github

# Logging setup for GitHub Actions Console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ==============================================================================
# ── Configuration (SAFE WAY: All values come securely from GitHub Secrets) ───
# ==============================================================================
GOOGLE_SHEET_NAME     = "TechBlogData"
GITHUB_REPO_PATH      = os.environ.get("GITHUB_REPOSITORY") 

# Direct environment variable mappings from GitHub Actions secrets
GEMINI_API_KEY        = os.environ.get("GEMINI_API_KEY")
GITHUB_TOKEN          = os.environ.get("GITHUB_TOKEN")
GOOGLE_CREDENTIALS    = os.environ.get("GOOGLE_CREDENTIALS")

def get_google_sheets_client():
    """Google Sheets API authentication function using robust raw credentials parsing"""
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # GitHub Secrets ke backslash strings ko escape-safe banane ke liye filter
        safe_credentials = GOOGLE_CREDENTIALS.replace('\n', '\\n')
        creds_info = json.loads(safe_credentials, strict=False)
    except Exception as e:
        # Fallback agar text mein double slashes pehle se lag gaye hon
        creds_info = json.loads(GOOGLE_CREDENTIALS, strict=False)
        
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    client = gspread.authorize(creds)
    return client

def generate_seo_content(keyword, category):
    """Gemini API Content Generation based on category"""
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    if category.lower() == "laptop":
        prompt = f"""
        Tum ek tech hardware expert aur senior tech blogger ho. Keywords: '{keyword}'.
        Engineering students ke liye ek detailed, SEO-friendly laptop review/buying guide likho Markdown format mein.
        Sections required: Introduction, Technical Specifications, Performance Benchmarks, Branch Utility, Pros/Cons Table, Student Verdict.
        Length: ~1200 words. Natural human tone.
        """
    elif category.lower() == "mobile":
        prompt = f"""
        Tum ek smartphone geek aur top tech reviewer ho. Keywords: '{keyword}'.
        Students ke liye ek practical Mobile Phone review/roundup likho Markdown format mein.
        Sections required: High-catching Introduction, Performance-to-Price Ratio, Processor & Gaming, Battery Life, Camera, Pros/Cons Table, Final Verdict.
        Length: ~1000 words.
        """
    else:
        prompt = f"""
        Tum ek AI researcher aur SaaS product reviewer ho. Keywords: '{keyword}'.
        Ek in-depth AI Tool review aur hands-on analysis likho Markdown format mein.
        Sections required: Introduction, Core Features, Pricing Packages (Free tier?), Pros/Cons Table, Top 3 Alternatives, Final Verdict.
        Length: ~1000 words.
        """

    log.info(f"Sending prompt to Gemini (model: gemini-2.5-flash) ...")
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
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
    
    if not GEMINI_API_KEY or not GITHUB_TOKEN or not GOOGLE_CREDENTIALS:
        log.error("❌ Critical Secrets are missing in GitHub Actions environment variables!")
        return

    try:
        log.info("Authenticating with Google Sheets API ...")
        # Yahan humne perfect matching function call set kar diya hai
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
        log.info("🎉 No pending keywords found! Everything is published.")
        return
        
    log.info(f"Found pending row {target_row_index} — keyword='{keyword}', category='{category}'")

    try:
        blog_content = generate_seo_content(keyword, category)
    except Exception as e:
        log.error(f"❌ Gemini API Generation Failed: {e}")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    clean_title = keyword.replace('"', '\\"')
    
    front_matter = f"""---
title: "{clean_title}"
date: {today_str}
category: {category}
layout: post
---

"""
    final_markdown_data = front_matter + blog_content
    file_name = f"{today_str}-{slugify(keyword)}.md"
    file_path = f"_posts/{file_name}"

    try:
        log.info(f"Pushing '{file_name}' to GitHub Repository via PyGithub...")
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
        log.info(f"🎯 Google Sheet updated! Row {target_row_index} status is now 'Published'.")
    except Exception as e:
        log.warning(f"⚠️ Sheet update failed but file was pushed: {e}")

if __name__ == "__main__":
    main()
