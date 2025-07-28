import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Google Ad Scraper Log Classifier", layout="wide")
st.title("📊 Google Ad Scraper Log Classifier (Strict Line-by-Line Match)")

st.markdown("""
Upload a `.log` file and paste your domain list. This tool applies **only** your three classification rules:
- `"Total results fetched for …: 0"` → **No Active Ads**
- `"Error processing \"…\""` → **Active Ads**
- Domain not found at all → **Non-Advertiser**

No global matching, no overreach. Just facts.
""")

# === Step 1: Domain Input ===
domains_input = st.text_area("✏️ Paste your domain list (one per line):")

# === Step 2: Log Upload ===
uploaded_log = st.file_uploader("📥 Upload log file (.log or .txt)", type=["log", "txt"])

if domains_input and uploaded_log:
    raw_domains = domains_input.strip().splitlines()
    normalized_domains = set()
    domain_lookup_map = {}

    # Normalize domains
    for raw in raw_domains:
        clean = raw.strip().lower()
        clean = clean.replace("http://", "").replace("https://", "").replace("www.", "").rstrip("/")
        normalized_domains.add(clean)
        domain_lookup_map[clean] = raw.strip()  # For original formatting later

    # Step 3: Read log lines
    log_lines = uploaded_log.read().decode("utf-8", errors="ignore").splitlines()

    # Step 4: Classify each domain
    no_ads = set()
    active_ads = set()
    found_domains = set()

    for line in log_lines:
        line = line.strip().lower()

        # Match "no active ads" lines
        match_no_ads = re.match(r"total results fetched for (.+?): 0", line)
        if match_no_ads:
            domain = match_no_ads.group(1)
            domain = domain.replace("http://", "").replace("https://", "").replace("www.", "").rstrip("/")
            if domain in normalized_domains:
                no_ads.add(domain)
                found_domains.add(domain)

        # Match "error processing" lines
        match_error = re.match(r'error processing "http:\/\/www\.([a-z0-9.-]+)\/"', line)
        if match_error:
            domain = match_error.group(1).strip()
            domain = domain.replace("www.", "").rstrip("/")
            if domain in normalized_domains:
                active_ads.add(domain)
                found_domains.add(domain)

    # Step 5: The rest are non-advertisers
    non_advertisers = normalized_domains - found_domains

    # Step 6: Display Results
    st.success("✅ Classification Complete")

    def show(label, items):
        st.markdown(f"### {label} ({len(items)})")
        if items:
            original = [domain_lookup_map[d] for d in sorted(items)]
            st.code("\n".join(original))
        else:
            st.text("None")

    show("Advertisers with No Active Ads", no_ads)
    show("Advertisers with Active Ads", active_ads)
    show("Non-Advertisers", non_advertisers)

    # Step 7: Export to CSV
    all_rows = [(domain_lookup_map[d], "Advertiser with No Active Ads") for d in no_ads] + \
               [(domain_lookup_map[d], "Advertiser with Active Ads") for d in active_ads] + \
               [(domain_lookup_map[d], "Non-Advertiser") for d in non_advertisers]

    df = pd.DataFrame(all_rows, columns=["Domain", "Classification"])
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "classified_domains.csv", "text/csv")
