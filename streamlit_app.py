from __future__ import annotations

from datetime import date
from io import StringIO
from pathlib import Path

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Energy Site Weekly Review", layout="wide")

REQUIRED_COLUMNS = {
    "site_id",
    "site_name",
    "region",
    "issue_type",
    "status",
    "estimated_cost_impact",
    "opened_date",
    "last_update_date",
    "notes_history",
}


def read_master_file(uploaded_file) -> pd.DataFrame:
    suffix = Path(uploaded_file.name).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(uploaded_file)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(uploaded_file)
    raise ValueError("Unsupported file type. Use CSV or Excel.")


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {', '.join(sorted(missing))}")

    output = df.copy()
    output["estimated_cost_impact"] = pd.to_numeric(
        output["estimated_cost_impact"], errors="coerce"
    ).fillna(0)
    output["opened_date"] = pd.to_datetime(output["opened_date"], errors="coerce")
    output["last_update_date"] = pd.to_datetime(output["last_update_date"], errors="coerce")

    today = pd.Timestamp(date.today())
    output["unresolved_age_days"] = (today - output["opened_date"]).dt.days
    output["days_since_update"] = (today - output["last_update_date"]).dt.days

    def stale_flag(days: float) -> str:
        if pd.isna(days):
            return "Unknown"
        if days >= 14:
            return "14+ days"
        if days >= 7:
            return "7+ days"
        return "Fresh"

    output["stale_bucket"] = output["days_since_update"].apply(stale_flag)
    return output


def format_money(value: float) -> str:
    return f"${value:,.0f}"


def build_briefing(top10: pd.DataFrame) -> str:
    lines = [
        "# Weekly Top 10 Problem Sites Briefing",
        "",
        f"Date: {date.today().isoformat()}",
        "",
        "## Priority Sites",
    ]

    for idx, row in top10.reset_index(drop=True).iterrows():
        lines.extend(
            [
                f"### {idx + 1}. {row['site_name']} ({row['site_id']})",
                f"- Region: {row['region']}",
                f"- Issue: {row['issue_type']}",
                f"- Status: {row['status']}",
                f"- Estimated cost impact: {format_money(row['estimated_cost_impact'])}",
                f"- Unresolved age: {int(row['unresolved_age_days']) if pd.notna(row['unresolved_age_days']) else 'N/A'} days",
                f"- Days since update: {int(row['days_since_update']) if pd.notna(row['days_since_update']) else 'N/A'} ({row['stale_bucket']})",
                f"- Notes: {row['notes_history']}",
                "",
            ]
        )

    return "\n".join(lines)


st.title("⚡ Energy Site Weekly Review")
st.caption("Simple weekly triage for top-priority sites by cost impact.")

sample_path = Path("data/sample_sites.csv")

with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Upload master file (CSV or Excel)", type=["csv", "xlsx", "xls"])

    use_sample = st.toggle("Use sample data", value=uploaded is None)
    if use_sample and sample_path.exists():
        raw_df = pd.read_csv(sample_path)
        st.success("Loaded sample data")
    elif uploaded is not None:
        raw_df = read_master_file(uploaded)
        st.success(f"Loaded {uploaded.name}")
    else:
        st.info("Upload a file or enable sample data to start.")
        st.stop()

try:
    df = prepare_data(raw_df)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

with st.sidebar:
    st.header("Filters")
    selected_regions = st.multiselect(
        "Region", sorted(df["region"].dropna().unique()), default=sorted(df["region"].dropna().unique())
    )
    selected_issues = st.multiselect(
        "Issue type",
        sorted(df["issue_type"].dropna().unique()),
        default=sorted(df["issue_type"].dropna().unique()),
    )
    selected_status = st.multiselect(
        "Status", sorted(df["status"].dropna().unique()), default=sorted(df["status"].dropna().unique())
    )

filtered = df[
    df["region"].isin(selected_regions)
    & df["issue_type"].isin(selected_issues)
    & df["status"].isin(selected_status)
].copy()

if filtered.empty:
    st.warning("No sites match the selected filters.")
    st.stop()

top10 = filtered.sort_values("estimated_cost_impact", ascending=False).head(10)

col1, col2, col3 = st.columns(3)
col1.metric("Filtered sites", len(filtered))
col2.metric("Top 10 cost impact", format_money(top10["estimated_cost_impact"].sum()))
col3.metric("Stale (7+ days)", int((top10["days_since_update"] >= 7).sum()))


def stale_style(row: pd.Series) -> list[str]:
    days = row["days_since_update"]
    styles = [""] * len(row)
    if pd.notna(days) and days >= 14:
        return ["background-color: #ffe3e3; color: #6f1d1b;"] * len(row)
    if pd.notna(days) and days >= 7:
        return ["background-color: #fff3cd; color: #5c3d00;"] * len(row)
    return styles


st.subheader("Top 10 by estimated cost impact")
display_cols = [
    "site_id",
    "site_name",
    "region",
    "issue_type",
    "status",
    "estimated_cost_impact",
    "unresolved_age_days",
    "days_since_update",
    "stale_bucket",
]

styled = (
    top10[display_cols]
    .style.format({"estimated_cost_impact": "${:,.0f}"})
    .apply(stale_style, axis=1)
)
st.dataframe(styled, use_container_width=True, hide_index=True)

st.caption("Stale highlight: yellow = 7+ days without update, red = 14+ days.")

st.subheader("Notes history per site")
site_choice = st.selectbox(
    "Choose a site", options=top10["site_id"].tolist(), format_func=lambda sid: f"{sid} — {top10.loc[top10['site_id'] == sid, 'site_name'].iloc[0]}"
)
site_row = top10[top10["site_id"] == site_choice].iloc[0]

left, right = st.columns([1, 2])
with left:
    st.markdown(f"**Status:** {site_row['status']}")
    st.markdown(f"**Impact:** {format_money(site_row['estimated_cost_impact'])}")
    unresolved = int(site_row["unresolved_age_days"]) if pd.notna(site_row["unresolved_age_days"]) else "N/A"
    days_update = int(site_row["days_since_update"]) if pd.notna(site_row["days_since_update"]) else "N/A"
    st.markdown(f"**Unresolved age:** {unresolved} days")
    st.markdown(f"**Days since update:** {days_update} ({site_row['stale_bucket']})")
with right:
    notes = str(site_row.get("notes_history", "")).replace("|", "\n- ")
    st.markdown("**Notes history**")
    st.markdown(f"- {notes}" if notes else "_No notes available._")

briefing_md = build_briefing(top10)
summary_table = top10[
    [
        "site_id",
        "site_name",
        "region",
        "issue_type",
        "status",
        "estimated_cost_impact",
        "days_since_update",
        "stale_bucket",
    ]
].copy()
summary_table["estimated_cost_impact"] = summary_table["estimated_cost_impact"].map(format_money)

st.subheader("Export briefing")
st.download_button(
    "Download markdown briefing",
    data=briefing_md,
    file_name=f"weekly_top10_briefing_{date.today().isoformat()}.md",
    mime="text/markdown",
)

ppt_text = StringIO()
ppt_text.write("Top 10 Priority Sites (copy into PowerPoint)\n\n")
for idx, row in summary_table.reset_index(drop=True).iterrows():
    ppt_text.write(
        f"{idx + 1}. {row['site_name']} ({row['site_id']}) | {row['region']} | {row['issue_type']} | {row['status']} | "
        f"{row['estimated_cost_impact']} | {int(row['days_since_update']) if pd.notna(row['days_since_update']) else 'N/A'} days since update ({row['stale_bucket']})\n"
    )

st.download_button(
    "Download PowerPoint-friendly summary (.txt)",
    data=ppt_text.getvalue(),
    file_name=f"weekly_top10_summary_{date.today().isoformat()}.txt",
    mime="text/plain",
)
