# filename: ad_scraper_log_classifier.py

import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="Google Ad Scraper Log Classifier", layout="wide")
st.title("📊 Google Ad Scraper Log Classifier")
st.markdown("Upload your domain list and log file to classify advertisers and count unique advertiser IDs.")

# === File Uploads ===
uploaded_domains = st.file_uploader("📥 Upload domain list (.txt)", type=["txt"])
uploaded_log = st.file_uploader("📥 Upload log file (.txt or .pdf)", type=["txt", "log", "pdf"])

if uploaded_domains and uploaded_log:
    # === Read and normalize domains ===
    domain_lines = uploaded_domains.read().decode("utf-8").splitlines()
    domain_list = set(
        d.strip().lower().replace("http://", "")
        .replace("https://", "").replace("www.", "").rstrip("/")
        for d in domain_lines if d.strip()
    )

    # === Read log ===
    log_text = uploaded_log.read().decode("utf-8", errors="ignore")

    # === Step 1: Advertisers with No Active Ads ===
    no_ads_pattern = r'Total results fetched for .*?([a-zA-Z0-9.-]+\.[a-zA-Z]+).*?: 0'
    no_ads_matches = re.findall(no_ads_pattern, log_text)
    no_ads_set = set(d.replace("www.", "").lower() for d in no_ads_matches)

    # === Step 2: Advertisers with Errors ===
    error_pattern = r'Error processing "(?:http:\/\/)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]+)\/?"'
    error_matches = re.findall(error_pattern, log_text)
    error_set = set(d.replace("www.", "").lower() for d in error_matches)

    # === Step 3: Advertisers with Clean Success (via creative IDs) ===
    creative_pattern = r'Successfully fetched creative ID CR[0-9]+'
    domain_block_pattern = r'(?:http:\/\/)?(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]+)'
    creative_blocks = re.findall(r'(Successfully fetched creative ID CR[0-9]+.*?)(?:\n|$)', log_text)
    creative_domains = set()

    for match in creative_blocks:
        context_lines = match.splitlines()
        for line in context_lines:
            found = re.search(domain_block_pattern, line)
            if found:
                domain = found.group(1).replace("www.", "").lower()
                creative_domains.add(domain)

    # Remove any domains already classified as no-ads
    clean_success_set = creative_domains - no_ads_set

    # === Final Advertiser with Active Ads Set ===
    active_ads_set = (error_set | clean_success_set) - no_ads_set

    # === Non-Advertisers ===
    non_advertisers_set = domain_list - no_ads_set - active_ads_set

    # === Count Unique Advertiser IDs (Creative Groups) ===
    creative_id_pattern = r'Successfully fetched creative ID (CR[0-9]+)'
    creative_ids = re.findall(creative_id_pattern, log_text)
    unique_creatives = set(creative_ids)
    advertiser_id_count = len(unique_creatives)

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

    st.markdown("---")
    st.subheader("🧮 Advertiser Count Verification")
    st.markdown(f"**Total Confirmed Advertisers (No Ads + Active Ads):** {len(no_ads_set) + len(active_ads_set)}")
    st.markdown(f"**Total Unique Creative IDs (≈ Advertiser Count):** {advertiser_id_count}")

    # === CSV Export ===
    st.markdown("---")
    st.subheader("📤 Export Classified Data")
    combined = [(d, "Advertiser with No Active Ads") for d in no_ads_set] + \
               [(d, "Advertiser with Active Ads") for d in active_ads_set] + \
               [(d, "Non-Advertiser") for d in non_advertisers_set]

    df = pd.DataFrame(combined, columns=["Domain", "Classification"])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", data=csv, file_name="classified_domains.csv", mime="text/csv")
