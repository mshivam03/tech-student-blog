"""
automation.py — Programmatic SEO Content Engine
------------------------------------------------
Reads a pending keyword from Google Sheets, generates an SEO-optimised
tech article with Gemini, commits the Markdown file to GitHub Pages (_posts/),
and marks the row as Published — all without touching existing files.

Dependencies (pip install):
    gspread oauth2client google-genai PyGithub
"""

import os
import json
import base64
import logging
from datetime import datetime, timezone

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google import genai
from github import Github, GithubException

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


# ── Configuration (all values come from GitHub Actions Secrets / env vars) ───
GEMINI_API_KEY        = os.environ.get("AIzaSyB0xsh4ZKizWsg98w2D-RxW_gMghBPAFHs")
GITHUB_TOKEN          = "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"
GITHUB_REPO           = "shivamkumar/tech-student-blog"
GOOGLE_SHEET_NAME     = "TechBlogData"

# Directly injected service account JSON as a raw string
GCLOUD_SA_JSON = """{
  "type": "service_account",
  "project_id": "techautomation-497213",
  "private_key_id": "04df3d5ba7d71fbdc79ebd11ecfda68f4cb86fb3",
  "private_key": "-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDEAp04vuKNj1AV\\nJ8VaK/7yGfyKuUrvlpCOtQ7kA4xdlAxeIQU9Bi/xURZImbClMAhA36b7Nj2hD0CJ\\nbYxgbo++OuAeJ5/udFzB77isqG+3UVS7G/XkaBIlpFE9W0UQBdomAYYD5xZeUTJM\\njiI414ADcvwJ/6lYEpxJ32+AYbghTUBQeAa6D/Tt3Q7/kzNYMOTgAb3AFnp4+Zxl\\nhntHFUl+9AgpI9igpy6Vn6/cCOwHDEo8axhzmo3xdl9GMwpwq93x3IxWcI49P5vY\\nAAfK1SucZxesWOfksgQnHMcJ+uPogilzUfRrhn89dKWAlyb1jHAFNlr4Jb5JyeVc\\ne5pc28KfAgMBAAECggEABkEOsvxR1NiuFZBR/9LbWbs4vFTPZ/48X4+1/J8cwyTR\\nqwE2HkcMj/azFZ7w+XXv++Egl7xlbANFRZbjinVZcpiE644x6eH4AbVV7A01zCCB\\n6eepYvlrg5yO5DyXMAmXw9J7OOdBmfUD4oulQORzY7WVoCk/Rh2is5XrBCqNPWOG\\naNimFmpnlXqsoj18v+p8yvQqIeKm6HZwo8c1rT6rWje0LpkPfz2vEHqh5ksjx0dV\\nLkDRx3Z3bzDx55tYxW06afmw6oXdHUicEvD+251qWaiBTRE6NLS3rOI2anpldaf1\\nxJuhe/EibrDgdDzJtmm2y/L0e1p17gJoqFm+wWwErQKBgQDs680oJ0dL+3HqVGVn\\nHaB5z1oBO1aNbAUjp2SEyQ6BkMl6g+GYqjY7psEBve4STvZjb46N6WA09/wld6MB\\nd10JJWLc4VZ3Cr39NeNrDwo1FJhHEE4G4e8lSy3uWB+fOAWw78byuLxPcI0mMrtp\\nzVKLQvt5ozBnP/u+LdbPVDpwRQKBgQDTy2w1eVhcX3qEn1zJAjU/kBp5N1favxmT\\n9Is9jXI7hjjBJiEADq70s1XsYQqSUcM1myUu8d28BThscntGUtYd2TTu7q7qmtUw\\n8pvojJoPHctkWo38VOeTT7XiAAXBxoIAWMSxkDDLB8n2lGfrh/VJRePoHPTjm9b1\\nl+c4KohPkwKBgQDY1QaylSA/fiVH3W3g7dCNKySos/IHBLG/a9gnXwuTsTt0kXbL\\nDh0MgxVpzrYws2v0nYjOgKS4Va3DbLcXBHN1h23v0Zwc3wv6znMQ7HbfFbY4c8e1\\nrNn+O8wRsz1drxwmT4y5YDGYUt4b85pqvqupIOie7qfCF2EDMVjD78Z8MQKBgHJx\\niG44vLNlcFm7lzKSu9016+g2LIXqH1MgoCDJjsF1XLOZ+9kBFi7pvPM22LSJ89bC\\nl8wPK8bOd1e6YLx2RHbqiLzXQrNIqQyC/BYj65dhfScj+3cvFdc3CkwtwO6dal/v\\nl5FvHb6H3e0c8i6GT9ehKW6iPv3Cltwsked6rB97AoGBAJ0JQppzry8dZeX7uXZi\\nCJC6+aBsaXbWWLdx8Nd/wo16I12q8DdXu7EpNBvGWrL8+PXWu6n5hyrGNO65EAWH\\n8Sj0ZSgyD1bGxLKKgBk8nSWBkbn8oU74I3Fv+y1zhDziift+QV1b8iS3JWyZSqkE\\ncUYfpLE8FFcZp9Ql9qmwJQMQ\\n-----END PRIVATE KEY-----\\n\",
  "client_email": "sheets-bot@techautomation-497213.iam.gserviceaccount.com",
  "client_id": "106633983891945045840",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/sheets-bot%40techautomation-497213.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}"""


# ── Category → SEO prompt templates ──────────────────────────────────────────
CATEGORY_PROMPTS: dict[str, str] = {
    "Laptop": (
        "You are an expert tech journalist writing for engineering students in India. "
        "Write a comprehensive, SEO-optimised blog post about: '{keyword}'.\n\n"
        "Structure your article with the following sections:\n"
        "1. **Introduction** — why this laptop matters for students in 2026\n"
        "2. **Key Specifications** — processor, RAM options, GPU (integrated/discrete), "
        "   storage, display, and build quality\n"
        "3. **Performance Benchmarks** — real-world workloads (compiling code, "
        "   running simulations, CAD rendering)\n"
        "4. **Branch-wise Utility** — how CSE, ECE, Mechanical, Civil, and Data-Science "
        "   students will benefit specifically\n"
        "5. **Battery Life & Portability** — daily campus usage\n"
        "6. **Value for Money** — price tiers and best configurations\n"
        "7. **Pros & Cons**\n"
        "8. **Verdict & Recommendation**\n\n"
        "Use relevant LSI keywords naturally. Target length: 1200–1500 words. "
        "Use clear H2/H3 Markdown headings. Do NOT include the YAML front-matter — "
        "that will be added separately."
    ),

    "Mobile": (
        "You are an expert mobile technology reviewer writing for college students "
        "on a budget. Write a comprehensive, SEO-optimised blog post about: '{keyword}'.\n\n"
        "Structure your article with the following sections:\n"
        "1. **Introduction** — positioning in the student smartphone market\n"
        "2. **Performance & Processor** — chipset, AnTuTu/Geekbench scores, "
        "   multitasking, gaming frame-rates\n"
        "3. **Camera System** — photo and video quality, night mode, selfie camera "
        "   for online classes and vlogs\n"
        "4. **Battery Life** — screen-on time, fast charging, real campus-day usage\n"
        "5. **Display & Design** — refresh rate, brightness, build materials\n"
        "6. **Software & Features** — OS version, bloatware, update policy\n"
        "7. **Performance-to-Price Ratio** — how it stacks against competitors\n"
        "8. **Student Gaming Verdict** — can it handle BGMI, Free Fire, Call of Duty Mobile?\n"
        "9. **Pros & Cons**\n"
        "10. **Final Verdict**\n\n"
        "Use relevant LSI keywords naturally. Target length: 1200–1500 words. "
        "Use clear H2/H3 Markdown headings. Do NOT include the YAML front-matter."
    ),

    "AI Tool": (
        "You are an expert AI tools reviewer writing for students, freelancers, and "
        "early-career professionals. Write a comprehensive, SEO-optimised blog post "
        "about: '{keyword}'.\n\n"
        "Structure your article with the following sections:\n"
        "1. **Introduction** — what this AI tool does and who it is for\n"
        "2. **Core Features** — detailed breakdown of every major feature\n"
        "3. **Practical Use Cases** — at least 5 real-world scenarios with examples\n"
        "4. **Pricing & Plans** — Free tier, Pro, Team, and Enterprise pricing "
        "   (monthly & annual); what each unlocks\n"
        "5. **Pros & Cons** — honest evaluation\n"
        "6. **Top Alternatives** — 3–4 competitors with brief comparisons\n"
        "7. **How to Get Started** — step-by-step onboarding guide\n"
        "8. **Final Verdict** — is it worth it for students/professionals?\n\n"
        "Use relevant LSI keywords naturally. Target length: 1200–1500 words. "
        "Use clear H2/H3 Markdown headings. Do NOT include the YAML front-matter."
    ),
}


def get_sheet_client() -> gspread.Client:
    """Authenticate with Google Sheets using service-account credentials."""
    log.info("Authenticating with Google Sheets API ...")
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    sa_info = json.loads(GCLOUD_SA_JSON)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(sa_info, scope)
    client = gspread.authorize(creds)
    log.info("Google Sheets authentication successful.")
    return client


def fetch_pending_row(client: gspread.Client) -> tuple[gspread.Worksheet, int, str, str] | None:
    """
    Open the sheet, find the first row with Status == 'Pending'.
    Returns (worksheet, row_index, keyword, category) or None if nothing pending.
    Row index is 1-based (as used by gspread).
    """
    log.info("Opening Google Sheet: '%s' ...", GOOGLE_SHEET_NAME)
    spreadsheet = client.open(GOOGLE_SHEET_NAME)
    worksheet   = spreadsheet.sheet1

    records = worksheet.get_all_records()
    log.info("Total rows in sheet: %d", len(records))

    for idx, row in enumerate(records, start=2):
        status = str(row.get("Status", "")).strip()
        if status.lower() == "pending":
            keyword  = str(row.get("Keyword", "")).strip()
            category = str(row.get("Category", "")).strip()
            log.info("Found pending row %d — keyword='%s', category='%s'", idx, keyword, category)
            return worksheet, idx, keyword, category

    log.info("No pending rows found. Nothing to do.")
    return None


def build_prompt(keyword: str, category: str) -> str:
    """Select the category template and inject the keyword."""
    normalised = category.strip().title()
    if "ai" in category.lower():
        normalised = "AI Tool"

    template = CATEGORY_PROMPTS.get(normalised)
    if not template:
        raise ValueError(
            f"Unknown category '{category}'. "
            f"Supported categories: {list(CATEGORY_PROMPTS.keys())}"
        )
    return template.format(keyword=keyword)


def generate_article(keyword: str, category: str) -> str:
    """Call Gemini API and return the generated article body (Markdown, no front-matter)."""
    log.info("Initialising Gemini client ...")
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = build_prompt(keyword, category)
    log.info("Sending prompt to Gemini (model: gemini-2.5-flash) ...")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    article_body = response.text.strip()
    log.info("Article generated successfully (%d characters).", len(article_body))
    return article_body


def build_markdown_file(keyword: str, category: str, article_body: str) -> tuple[str, str]:
    """
    Wrap the article body in Jekyll-compatible YAML front-matter.
    Returns (filename, full_markdown_content).
    """
    today      = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug       = keyword.lower().replace(" ", "-")
    slug       = "".join(c if c.isalnum() or c == "-" else "" for c in slug)
    filename   = f"{today}-{slug}.md"

    safe_title = keyword.replace('"', '\\"')

    front_matter = (
        "---\n"
        f'title: "{safe_title}"\n'
        f"date: {today}\n"
        f"categories: [{category}]\n"
        f"tags: [tech, student, {category.lower()}]\n"
        f"layout: post\n"
        "---\n\n"
    )

    full_content = front_matter + article_body
    log.info("Markdown file prepared: '%s'", filename)
    return filename, full_content


def publish_to_github(filename: str, content: str) -> None:
    """
    Commit the Markdown file to the _posts/ directory of the GitHub Pages repo.
    Creates the file only — never overwrites existing posts.
    """
    log.info("Connecting to GitHub repository: '%s' ...", GITHUB_REPO)
    gh   = Github(GITHUB_TOKEN)
    repo = gh.get_repo(GITHUB_REPO)

    file_path = f"_posts/{filename}"
    log.info("Target path in repo: '%s'", file_path)

    try:
        repo.get_contents(file_path)
        raise FileExistsError(
            f"File '{file_path}' already exists in the repository. "
            "Skipping to prevent overwrite."
        )
    except GithubException as exc:
        if exc.status == 404:
            log.info("File does not exist yet — safe to create.")
        else:
            raise

    commit_message = f"feat(blog): auto-publish post — {filename}"
    repo.create_file(
        path=file_path,
        message=commit_message,
        content=content,
        branch="main",
    )
    log.info("Successfully committed '%s' to GitHub.", file_path)


def mark_as_published(worksheet: gspread.Worksheet, row_index: int) -> None:
    """Update the Status cell in the given row to 'Published'."""
    headers = worksheet.row_values(1)
    try:
        status_col = headers.index("Status") + 1
    except ValueError:
        raise ValueError("Column 'Status' not found in the sheet header row.")

    worksheet.update_cell(row_index, status_col, "Published")
    log.info("Row %d marked as 'Published' in Google Sheet.", row_index)


# ── Main orchestrator ─────────────────────────────────────────────────────────
def main() -> None:
    log.info("═" * 60)
    log.info("  SEO Content Engine — starting run")
    log.info("═" * 60)

    sheet_client = get_sheet_client()
    result = fetch_pending_row(sheet_client)

    if result is None:
        log.info("Nothing to publish today. Exiting cleanly.")
        return

    worksheet, row_index, keyword, category = result

    article_body = generate_article(keyword, category)
    filename, full_content = build_markdown_file(keyword, category, article_body)
    publish_to_github(filename, full_content)
    mark_as_published(worksheet, row_index)

    log.info("═" * 60)
    log.info("  Run complete. Post published: %s", filename)
    log.info("═" * 60)


if __name__ == "__main__":
    main()
