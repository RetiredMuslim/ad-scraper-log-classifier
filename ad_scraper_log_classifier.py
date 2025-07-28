# filename: ad_scraper_log_classifier.py

import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="Google Ad Scraper Log Classifier", layout="wide")
st.title("📊 Google Ad Scraper Log Classifier")
st.markdown("""
Paste your domain list below and upload the log file. This tool:
- Classifies only the domains you provide
- Follows strict 3-step logic
- Ignores log noise from unrelated domains
""")

# === Input: Pasted domain list ===
domains_input = st.text_area("✏️ Paste your domain list (one per line):")

# === Input: Log file upload ===
uploaded_log = st.file_uploader("📥 Upload log file (.txt or .log)", type=["txt", "log"])

if domains_input and uploaded_log:
    # Step 1: Normalize domain input
    domain_lines = domains_input.strip().splitlines()
    domain_list = set(
        d.strip().lower()
        .replace("http://", "")
        .replace("https://", "")
        .replace("www.", "")
        .rstrip("/")
        for d in domain_lines if d.strip()
    )

    # Step 2: Read log
    log_text = uploaded_log.read().decode("utf-8", errors="ignore")

    # Step 3: Detect domains with "No Active Ads"
    no_ads_pattern = r'Total results fetched for .*?([a-zA-Z0-9.-]+\.[a-zA-Z]+).*?: 0'
    no_ads_matches = re.findall(no_ads_pattern, log_text)
    no_ads_set = {d.strip().lower().replace("www.", "") for d in no_ads_matches}
    no_ads_set = no_ads_set & domain_list  # only keep from input list

    # Step 4: Detect domains with "Error processing"
    error_pattern = r'Error processing "(?:http:\/\/)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]+)\/?"'
    error_matches = re.findall(error_pattern, log_text)
    error_set = {d.strip().lower().replace("www.", "") for d in error_matches}
    error_set = error_set & domain_list  # only keep from input list

    # Step 5: Apply logic
    advertisers_with_no_ads = no_ads_set
    advertisers_with_active_ads = error_set - no_ads_set
    non_advertisers = domain_list - advertisers_with_no_ads - advertisers_with_active_ads

    # Display results
    st.success("✅ Classification Complete")

    def show(label, items):
        st.markdown(f"### {label} ({len(items)})")
        if items:
            st.code("\n".join(sorted(items)))
        else:
            st.text("None")

    show("Advertisers with No Active Ads", advertisers_with_no_ads)
    show("Advertisers with Active Ads", advertisers_with_active_ads)
    show("Non-Advertisers", non_advertisers)

    # Export CSV
    st.markdown("---")
    st.subheader("📤 Download Results as CSV")
    all_rows = [(d, "Advertiser with No Active Ads") for d in advertisers_with_no_ads] + \
               [(d, "Advertiser with Active Ads") for d in advertisers_with_active_ads] + \
               [(d, "Non-Advertiser") for d in non_advertisers]

    df = pd.DataFrame(all_rows, columns=["Domain", "Classification"])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", data=csv, file_name="classified_domains.csv", mime="text/csv")
