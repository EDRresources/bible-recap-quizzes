import json
import os
import re
import subprocess
import sys

quiz_file = os.environ.get("QUIZ_FILE", "").strip()
print(f"QUIZ_FILE env var: '{quiz_file}'")

if not quiz_file:
    print("No quiz file passed — skipping.")
    sys.exit(0)

basename = os.path.splitext(quiz_file)[0]
m = re.match(r"biblerecap_quiz_day(\d+)_(\d{4})", basename)
if not m:
    print(f"Could not parse filename: {quiz_file}")
    sys.exit(1)

day = m.group(1)
mmdd = m.group(2)
month_num = int(mmdd[:2])
day_num = int(mmdd[2:])
month_names = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]
month_name = month_names[month_num]
date_str = f"{month_name} {day_num}"

print(f"Day {day}, {date_str}")

pages_url = f"https://edrresources.github.io/bible-recap-quizzes/{quiz_file}"

meta_file = basename + ".json"
passages_html = ""
summary_html = ""
psalm_html = ""

if os.path.exists(meta_file):
    with open(meta_file) as f:
        meta = json.load(f)
    date_str = meta.get("date", date_str)
    passages = meta.get("passages", [])
    if passages:
        passages_html = " &middot; ".join(passages)
    summary_html = meta.get("summary", "")
    psalm_html = meta.get("psalm_rows_html", "")

passages_section = (
    '<p style="font-family:Georgia,serif;font-size:15px;color:#2c1a00;margin-top:8px;">'
    f'<strong>Passages:</strong> {passages_html}</p>'
) if passages_html else ""

summary_section = (
    '<p style="font-family:Georgia,serif;font-size:15px;color:#2c1a00;margin-top:12px;">'
    f'{summary_html}</p>'
) if summary_html else ""

psalm_section = (
    '<hr style="border:none;border-top:1px solid #c9a84c;margin:16px 0;">'
    '<p style="font-family:Georgia,serif;font-size:13px;color:#6b4f1a;margin-bottom:8px;">'
    '<strong>Psalm Reference</strong></p>'
    + psalm_html
) if psalm_html else ""

html_body = (
    '<div style="font-family:Georgia,serif;max-width:600px;margin:0 auto;color:#2c1a00;">'
    f'<p style="font-size:16px;margin:0 0 8px 0;"><strong>Day {day} &mdash; {date_str}</strong></p>'
    + passages_section + summary_section + psalm_section
    + f'<p style="margin-top:24px;"><a href="{pages_url}" style="font-family:Georgia,serif;font-size:16px;color:#7a4a00;font-weight:bold;text-decoration:none;">&#9670; Open Today&rsquo;s Quiz &rarr;</a></p>'
    + '<hr style="border:none;border-top:1px solid #c9a84c;margin:20px 0 12px;">'
    + f'<p style="font-size:12px;color:#6b4f1a;margin:0;">The Bible Recap &middot; Daily Quiz &middot; Day {day} &middot; 10 challenging questions</p>'
    + '</div>'
)

api_key = os.environ.get("RESEND_API_KEY", "")
print(f"RESEND_API_KEY present: {bool(api_key)} (length {len(api_key)})")

payload = {
    "from": "onboarding@resend.dev",
    "to": ["erik.d.roberson@gmail.com", "eden.roberson@gmail.com"],
    "subject": f"Bible Recap Quiz \u2014 Day {day} \u2014 {date_str}",
    "html": html_body
}

payload_file = "/tmp/resend_payload.json"
with open(payload_file, "w") as f:
    json.dump(payload, f)

print("Calling Resend API via curl...")
result = subprocess.run([
    "curl", "-s", "-w", "\nHTTP_STATUS:%{http_code}",
    "-X", "POST", "https://api.resend.com/emails",
    "-H", f"Authorization: Bearer {api_key}",
    "-H", "Content-Type: application/json",
    "-d", f"@{payload_file}"
], capture_output=True, text=True)

output = result.stdout
print(f"curl stdout: {output}")
if result.stderr:
    print(f"curl stderr: {result.stderr}")

if "HTTP_STATUS:2" in output:
    print("Email sent successfully\!")
else:
    print("Email send failed.")
    sys.exit(1)
