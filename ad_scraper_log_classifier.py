import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="Google Ad Scraper Log Classifier", layout="wide")
st.title("📊 Google Ad Scraper Log Classifier")

st.markdown("""
Paste your domain list below and upload the `.log` file. The tool will:
- Classify based only on your input list
- Apply exact 3-rule logic:
  - "Total results fetched" → No Active Ads
  - "Error processing" → Active Ads
  - Neither → Non-Advertiser
""")

# Input domain list
domains_input = st.text_area("✏️ Paste your domain list (one per line):")

# Upload raw log file (.log or .txt)
uploaded_log = st.file_uploader("📥 Upload the original .log file", type=["log", "txt"])

if domains_input and uploaded_log:
    # Normalize input domains
    raw_domains = domains_input.strip().splitlines()
    normalized_domains = {
        d.strip().lower()
        .replace("http://", "")
        .replace("https://", "")
        .replace("www.", "")
        .rstrip("/")
        for d in raw_domains if d.strip()
    }

    # Read log content
    log_text = uploaded_log.read().decode("utf-8", errors="ignore").lower()

    # Sets for classification
    no_ads = set()
    active_ads = set()
    non_advertisers = set()

    # Exact matching, domain by domain
    for domain in normalized_domains:
        found = False
        variants = [
            f'total results fetched for {domain}: 0',
            f'total results fetched for www.{domain}: 0',
            f'total results fetched for http://www.{domain}/: 0',
        ]
        for variant in variants:
            if variant in log_text:
                no_ads.add(domain)
                found = True
                break

        if not found:
            error_variants = [
                f'error processing "{domain}/"',
                f'error processing "www.{domain}/"',
                f'error processing "http://www.{domain}/"',
            ]
            for variant in error_variants:
                if variant in log_text:
                    active_ads.add(domain)
                    found = True
                    break

        if not found:
            non_advertisers.add(domain)

    # Output
    st.success("✅ Classification Complete")

    def show(label, items):
        st.markdown(f"### {label} ({len(items)})")
        st.code("\n".join(sorted(items)) if items else "None")

    show("Advertisers with No Active Ads", no_ads)
    show("Advertisers with Active Ads", active_ads)
    show("Non-Advertisers", non_advertisers)

    # Export CSV
    st.markdown("---")
    st.subheader("📤 Export CSV")
    rows = [(d, "Advertiser with No Active Ads") for d in no_ads] + \
           [(d, "Advertiser with Active Ads") for d in active_ads] + \
           [(d, "Non-Advertiser") for d in non_advertisers]
    df = pd.DataFrame(rows, columns=["Domain", "Classification"])
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download CSV", csv, "classified_domains.csv", "text/csv")
