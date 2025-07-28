# filename: ad_scraper_log_classifier.py

import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="Google Ad Scraper Log Classifier", layout="wide")
st.title("📊 Google Ad Scraper Log Classifier")

st.markdown("""
Paste your domain list below and upload the scraper log file. This tool will classify each domain as:
- **Advertiser with No Active Ads**
- **Advertiser with Active Ads**
- **Non-Advertiser**

It will also count the number of unique creative IDs to verify total advertiser matches.
""")

# === Step 1: Domain input ===
domains_input = st.text_area("✏️ Paste your domain list (one per line):")

# === Step 2: Log upload ===
uploaded_log = st.file_uploader("📥 Upload log file (.txt or .log)", type=["txt", "log"])

if domains_input and uploaded_log:
    # === Parse domain list ===
    domain_lines = domains_input.strip().splitlines()
    domain_list = set(
        d.strip().lower()
        .replace("http://", "")
        .replace("https://", "")
        .replace("www.", "")
        .rstrip("/")
        for d in domain_lines if d.strip()
    )

    # === Read log content ===
    log_text = uploaded_log.read().decode("utf-8", errors="ignore")

    # === Step 3: Detect "No Active Ads" ===
    no_ads_pattern = r'Total results fetched for .*?([a-zA-Z0-9.-]+\.[a-zA-Z]+).*?: 0'
    no_ads_matches = re.findall(no_ads_pattern, log_text)
    no_ads_set = set(d.replace("www.", "").lower() for d in no_ads_matches)

    # === Step 4: Detect "Error Processing" ===
    error_pattern = r'Error processing "(?:http:\/\/)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]+)\/?"'
    error_matches = re.findall(error_pattern, log_text)
    error_set = set(d.replace("www.", "").lower() for d in error_matches)

    # === Step 5: Final classifications ===
    active_ads_set = error_set - no_ads_set
    non_advertisers_set = domain_list - no_ads_set - active_ads_set

    # === Step 6: Count unique creative IDs for verification ===
    creative_id_pattern = r'Successfully fetched creative ID (CR[0-9]+)'
    creative_ids = re.findall(creative_id_pattern, log_text)
    unique_creative_ids = set(creative_ids)
    advertiser_id_count = len(unique_creative_ids)

    # === Display Results ===
    st.success("✅ Classification Complete")

    def display_list(label, items):
        st.markdown(f"### {label} ({len(items)})")
        if items:
            st.code("\n".join(sorted(items)), language="text")
        else:
            st.text("None found.")

    display_list("Advertisers with No Active Ads", no_ads_set)
    display_list("Advertisers with Active Ads", active_ads_set)
    display_list("Non-Advertisers", non_advertisers_set)

    # === Step 7: Verification Section ===
    st.markdown("---")
    st.subheader("🧮 Advertiser Count Verification")
    st.markdown(f"**Total classified advertisers (No Ads + Active Ads):** {len(no_ads_set) + len(active_ads_set)}")
    st.markdown(f"**Total unique creative IDs (≈ advertisers):** {advertiser_id_count}")

    # === Step 8: CSV Download ===
    st.markdown("---")
    st.subheader("📤 Export Classified Results")
    combined = [(d, "Advertiser with No Active Ads") for d in no_ads_set] + \
               [(d, "Advertiser with Active Ads") for d in active_ads_set] + \
               [(d, "Non-Advertiser") for d in non_advertisers_set]

    df = pd.DataFrame(combined, columns=["Domain", "Classification"])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", data=csv, file_name="classified_domains.csv", mime="text/csv")
