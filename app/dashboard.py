import requests
import pandas as pd
import streamlit as st


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

API_URL = "http://127.0.0.1:8000"


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="YottaFlex Fraud Investigation",
    page_icon="🔎",
    layout="wide",
)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def get_api(endpoint):
    """Call the FastAPI backend."""

    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.RequestException as exc:
        st.error(
            "Could not connect to the FastAPI backend.\n\n"
            f"Make sure the API is running at {API_URL}\n\n"
            f"Error: {exc}"
        )
        return None


def risk_badge(level):
    """Display a simple risk indicator."""

    if level == "CRITICAL":
        return "🔴 CRITICAL"

    if level == "HIGH":
        return "🟠 HIGH"

    if level == "MEDIUM":
        return "🟡 MEDIUM"

    return "🟢 LOW"


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.title("🔎 YottaFlex Fraud Network Investigation")

st.caption(
    "AI-assisted insurance claim investigation using "
    "risk indicators, relationship networks and evidence."
)


# ---------------------------------------------------------
# API health check
# ---------------------------------------------------------

health = get_api("/health")

if health is None:
    st.stop()

if health.get("status") == "healthy":
    st.success("API connected • Generated data available")
else:
    st.warning("API connected, but some generated data is unavailable.")


# ---------------------------------------------------------
# Summary
# ---------------------------------------------------------

summary = get_api("/summary")

if summary is None:
    st.stop()


st.header("Investigation Overview")


risk_levels = summary.get("risk_levels", {})
priority_levels = summary.get("investigation_priorities", {})


col1, col2, col3, col4 = st.columns(4)


with col1:
    st.metric(
        "Scored Claims",
        summary.get("total_scored_claims", 0),
    )


with col2:
    st.metric(
        "Fraud Indicators",
        summary.get("total_indicators", 0),
    )


with col3:
    st.metric(
        "Investigation Candidates",
        summary.get("investigation_candidates", 0),
    )


with col4:
    critical_count = risk_levels.get("CRITICAL", 0)

    st.metric(
        "Critical Claims",
        critical_count,
    )


# ---------------------------------------------------------
# Risk distribution
# ---------------------------------------------------------

st.subheader("Risk Distribution")


risk_df = pd.DataFrame(
    list(risk_levels.items()),
    columns=["Risk Level", "Claims"],
)


if not risk_df.empty:
    st.bar_chart(
        risk_df.set_index("Risk Level")
    )


# ---------------------------------------------------------
# Investigation queue
# ---------------------------------------------------------

st.header("Investigation Queue")


investigation_data = get_api(
    "/investigations?limit=200"
)

if investigation_data is None:
    st.stop()


investigations = investigation_data.get(
    "results",
    [],
)


if not investigations:

    st.info(
        "No investigation cases are currently available."
    )

else:

    investigation_df = pd.DataFrame(
        investigations
    )

    # Search
    search_text = st.text_input(
        "Search Claim ID",
        placeholder="Example: CLM-2026-000001",
    )

    if search_text:

        investigation_df = investigation_df[
            investigation_df["claim_id"]
            .astype(str)
            .str.contains(
                search_text,
                case=False,
                na=False,
            )
        ]


    # Priority filter
    priority_options = [
        "ALL"
    ] + sorted(
        investigation_df["priority"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_priority = st.selectbox(
        "Priority",
        priority_options,
    )


    if selected_priority != "ALL":

        investigation_df = investigation_df[
            investigation_df["priority"]
            == selected_priority
        ]


    # Risk filter
    risk_options = [
        "ALL"
    ] + sorted(
        investigation_df["risk_level"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    selected_risk = st.selectbox(
        "Risk Level",
        risk_options,
    )


    if selected_risk != "ALL":

        investigation_df = investigation_df[
            investigation_df["risk_level"]
            == selected_risk
        ]


    # Display columns
    display_columns = [
        "investigation_id",
        "claim_id",
        "priority",
        "risk_level",
        "claim_risk_score",
        "network_score",
        "combined_network_score",
        "status",
    ]

    available_columns = [
        column
        for column in display_columns
        if column in investigation_df.columns
    ]


    st.dataframe(
        investigation_df[
            available_columns
        ],
        width='stretch',
        hide_index=True,
    )


# ---------------------------------------------------------
# Claim investigation
# ---------------------------------------------------------

st.header("Claim Investigation")


claim_id = st.text_input(
    "Enter Claim ID",
    placeholder="Example: CLM-2026-000001",
)


if st.button(
    "Investigate Claim",
    type="primary",
):

    if not claim_id.strip():

        st.warning(
            "Please enter a claim ID."
        )

    else:

        claim_id = claim_id.strip()

        claim_data = get_api(
            f"/claims/{claim_id}"
        )


        if claim_data is None:
            st.stop()


        # -------------------------------------------------
        # Risk information
        # -------------------------------------------------

        st.subheader(
            f"Claim: {claim_id}"
        )


        risk = claim_data.get(
            "risk",
            {},
        )


        risk_col1, risk_col2, risk_col3, risk_col4 = (
            st.columns(4)
        )


        with risk_col1:
            st.metric(
                "Risk Score",
                risk.get(
                    "risk_score",
                    0,
                ),
            )


        with risk_col2:
            st.metric(
                "Risk Level",
                risk.get(
                    "risk_level",
                    "UNKNOWN",
                ),
            )


        with risk_col3:
            st.metric(
                "Priority",
                risk.get(
                    "investigation_priority",
                    "UNKNOWN",
                ),
            )


        with risk_col4:
            st.metric(
                "Indicators",
                risk.get(
                    "indicator_count",
                    0,
                ),
            )


        # -------------------------------------------------
        # Explanation
        # -------------------------------------------------

        st.subheader(
            "Why is this claim suspicious?"
        )


        explanation = risk.get(
            "explanation",
            "No explanation available.",
        )


        st.info(explanation)


        # -------------------------------------------------
        # Fraud indicators
        # -------------------------------------------------

        st.subheader(
            "Fraud Indicators"
        )


        indicators = claim_data.get(
            "indicators",
            [],
        )


        if indicators:

            indicator_df = pd.DataFrame(
                indicators
            )


            indicator_columns = [
                "indicator_type",
                "severity",
                "score",
                "evidence",
            ]


            available_indicator_columns = [
                column
                for column in indicator_columns
                if column in indicator_df.columns
            ]


            st.dataframe(
                indicator_df[
                    available_indicator_columns
                ],
                width='stretch',
                hide_index=True,
            )

        else:

            st.info(
                "No fraud indicators found."
            )


        # -------------------------------------------------
        # Network evidence
        # -------------------------------------------------

        st.subheader(
            "Network Evidence"
        )


        network = claim_data.get(
            "network",
            {},
        )


        if network:

            network_col1, network_col2, network_col3 = (
                st.columns(3)
            )


            with network_col1:

                st.metric(
                    "Network Score",
                    network.get(
                        "network_score",
                        0,
                    ),
                )


            with network_col2:

                st.metric(
                    "Combined Score",
                    network.get(
                        "combined_network_score",
                        0,
                    ),
                )


            with network_col3:

                st.metric(
                    "Provider Connections",
                    network.get(
                        "provider_connections",
                        0,
                    ),
                )


            st.write(
                "**Network explanation:**",
                network.get(
                    "network_explanation",
                    "No explanation available.",
                ),
            )


            network_details = {
                "Claimant ID": network.get(
                    "claimant_id",
                    "",
                ),
                "Provider ID": network.get(
                    "provider_id",
                    "",
                ),
                "Claimant Claim Count": network.get(
                    "claimant_claim_count",
                    0,
                ),
                "Provider Claim Count": network.get(
                    "provider_claim_count",
                    0,
                ),
                "Claim Connections": network.get(
                    "claim_connections",
                    0,
                ),
                "Temporal Cluster Claims": network.get(
                    "temporal_cluster_claim_count",
                    0,
                ),
                "Temporal Cluster Claimants": network.get(
                    "temporal_cluster_claimant_count",
                    0,
                ),
            }


            st.json(network_details)


        else:

            st.info(
                "No network evidence available."
            )


        # -------------------------------------------------
        # Investigation record
        # -------------------------------------------------

        st.subheader(
            "Investigation Record"
        )


        investigations_for_claim = claim_data.get(
            "investigations",
            [],
        )


        if investigations_for_claim:

            investigation_df = pd.DataFrame(
                investigations_for_claim
            )


            st.dataframe(
                investigation_df,
                width='stretch',
                hide_index=True,
            )

        else:

            st.info(
                "No investigation record found."
            )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.divider()

st.caption(
    "YottaFlex Fraud Network Investigation System "
    "• Synthetic data • Fixed seed • Ground truth "
    "kept separate from detection features"
)
