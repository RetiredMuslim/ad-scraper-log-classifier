import streamlit as st
import re
import pandas as pd

st.set_page_config(page_title="Google Ad Scraper Log Classifier", layout="wide")
st.title("📊 Google Ad Scraper Log Classifier")

st.markdown("""
Paste your domain list below and upload the log file. The tool will:
- Classify domains using strict 3-rule logic
- Only classify domains from your input
- Ignore unrelated log noise
""")

# === Input: Pasted domain list ===
domains_input = st.text_area("✏️ Paste your domain list (one per line):")

# === Input: Log file upload ===
uploaded_log = st.file_uploader("📥 Upload log file (.txt or .log)", type=["txt", "log", "pdf"])

if domains_input and uploaded_log:
    # Step 1: Normalize and clean input domains
    domain_lines = domains_input.strip().splitlines()
    domain_list = {
        d.strip().lower()
        .replace("http://", "")
        .replace("https://", "")
        .replace("www.", "")
        .rstrip("/")
        for d in domain_lines if d.strip()
    }

    # Step 2: Read the log file
    log_text = uploaded_log.read().decode("utf-8", errors="ignore").lower()

    # Step 3: Match logic per domain
    advertisers_with_no_ads = set()
    advertisers_with_active_ads = set()
    all_logged_domains = set()

    for domain in domain_list:
        # Build variants to match common patterns
        domain_variants = [
            domain,
            f"http://www.{domain}/",
            f"www.{domain}",
            f"http://{domain}/"
        ]

        matched = False

        for variant in domain_variants:
            if f'total results fetched for {variant}: 0' in log_text:
                advertisers_with_no_ads.add(domain)
                matched = True
                break

        if not matched:
            for variant in domain_variants:
                if f'error processing "{variant}"' in log_text:
                    advertisers_with_active_ads.add(domain)
                    matched = True
                    break

        if matched:
            all_logged_domains.add(domain)

    # Step 4: The rest are Non-Advertisers
    non_advertisers = domain_list - all_logged_domains

    # === Display results
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

    # === Export CSV
    st.markdown("---")
    st.subheader("📤 Download Results as CSV")
    all_rows = [(d, "Advertiser with No Active Ads") for d in advertisers_with_no_ads] + \
               [(d, "Advertiser with Active Ads") for d in advertisers_with_active_ads] + \
               [(d, "Non-Advertiser") for d in non_advertisers]

    df = pd.DataFrame(all_rows, columns=["Domain", "Classification"])
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Download CSV", data=csv, file_name="classified_domains.csv", mime="text/csv")
