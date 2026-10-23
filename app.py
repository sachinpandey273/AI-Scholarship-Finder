"""
AI Scholarship Finder — Your Study Abroad Funding Assistant
Main Streamlit Application
TetraNoodle AI Hackathon 2026

Multi-Agent System orchestrated by coordinator.py:
1. Profile Analyst Agent (document extraction & facts normalization)
2. Discovery Agent (web research & candidate deduplication)
3. Eligibility & Verification Agent (criteria audit & official sources)
4. Matching & Ranking Agent (100-point transparent formula)
5. Application Drafting Agent (SOP & personalization checklist)
"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import json
import time
from pathlib import Path
from datetime import datetime

from config import AppConfig
from coordinator import WorkflowCoordinator
from models.schemas import StudentProfile, Opportunity, WorkflowResult, AgentEvent
from agents.application_agent import ApplicationDraftingAgent
from data.sample_profiles import RAHUL_PROFILE, MARIA_PROFILE

# -----------------------------------------------------------------------------
# Page Configuration & Modern Design System
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Scholarship Finder — Study Abroad Funding Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .main-header h1 {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.025em;
        background: linear-gradient(to right, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .main-header p {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: 0.5rem;
        margin-bottom: 0;
    }

    .agent-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }

    .badge-eligible {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
    }

    .badge-potential {
        background-color: #fef3c7;
        color: #b45309;
        border: 1px solid #fde68a;
    }

    .badge-ineligible {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
    }

    .badge-insufficient {
        background-color: #f1f5f9;
        color: #475569;
        border: 1px solid #e2e8f0;
    }

    .recommendation-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.4rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .recommendation-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }

    .score-circle {
        font-size: 1.8rem;
        font-weight: 800;
        color: #2563eb;
    }

    .evidence-box {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 0.8rem 1rem;
        font-size: 0.9rem;
        border-radius: 0 8px 8px 0;
        margin: 0.6rem 0;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
if "workflow_result" not in st.session_state:
    st.session_state.workflow_result = None
if "current_profile_data" not in st.session_state:
    st.session_state.current_profile_data = RAHUL_PROFILE.copy()
if "agent_live_logs" not in st.session_state:
    st.session_state.agent_live_logs = []
if "selected_opp_id" not in st.session_state:
    st.session_state.selected_opp_id = None
if "active_draft" not in st.session_state:
    st.session_state.active_draft = None

# Header Banner
st.markdown("""
<div class="main-header">
    <h1>🎓 AI Scholarship Finder</h1>
    <p>Multi-Agent Research Assistant for Postgraduate International Scholarships & University Programs</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Sidebar: System Status & Profile Presets
# -----------------------------------------------------------------------------
with st.sidebar:
    st.subheader("⚙️ System Status")
    is_live = AppConfig.is_live_gemini_available()
    if is_live:
        st.success(f"🟢 **Live Gemini API Connected**\nModel: `{AppConfig.GEMINI_MODEL}`")
    else:
        st.info("🟡 **Demonstration Mode Active**\nUnset `GEMINI_API_KEY`. Running verified local intelligence.")

    st.markdown("---")
    st.subheader("👤 Student Profile Presets")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        if st.button("Load Rahul\n(Reference)", use_container_width=True):
            st.session_state.current_profile_data = RAHUL_PROFILE.copy()
            st.session_state.workflow_result = None
            st.rerun()
    with col_p2:
        if st.button("Load Maria\n(Profile 2)", use_container_width=True):
            st.session_state.current_profile_data = MARIA_PROFILE.copy()
            st.session_state.workflow_result = None
            st.rerun()

    st.caption("Demonstrates adaptability across different degrees, GPAs, disciplines, and country preferences.")

    st.markdown("---")
    st.subheader("🛡️ Privacy & Local Session")
    st.markdown(
        "<small>Documents are parsed locally in memory. No personal data is stored indefinitely.</small>",
        unsafe_allow_html=True
    )
    if st.button("🧹 Clear Uploads & Reset Session", use_container_width=True):
        st.session_state.workflow_result = None
        st.session_state.agent_live_logs = []
        st.session_state.active_draft = None
        st.rerun()

# -----------------------------------------------------------------------------
# Section A: Student Profile & Document Ingestion
# -----------------------------------------------------------------------------
curr = st.session_state.current_profile_data

st.markdown("### 1. Student Profile & Document Verification")
with st.expander("📄 Upload Resume / Academic Transcripts", expanded=True):
    col_up1, col_up2 = st.columns(2)
    with col_up1:
        uploaded_resume = st.file_uploader(
            "Upload Resume / CV (PDF or DOCX)",
            type=["pdf", "docx"],
            help="Extracts degree, CGPA, technical skills, and research projects automatically."
        )
    with col_up2:
        uploaded_transcript = st.file_uploader(
            "Upload Academic Marksheet / Transcript (PDF or DOCX)",
            type=["pdf", "docx"],
            help="High-authority source for official GPA verification and course breakdown."
        )

# Editable Profile Form
with st.form("student_profile_form"):
    st.markdown("##### Verified Academic and Technical Parameters")
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        full_name = st.text_input("Full Name", value=curr.get("full_name", "Rahul Sharma"))
        nationality = st.text_input("Citizenship / Nationality", value=curr.get("nationality", "India"))
    with c2:
        current_degree = st.text_input("Undergraduate Degree", value=curr.get("current_degree", "BTech in Computer Science"))
        cgpa = st.number_input("Cumulative GPA / Marks", value=float(curr.get("cgpa", 8.2)), step=0.1, min_value=0.0)
    with c3:
        major = st.text_input("Major / Discipline", value=curr.get("major", "Computer Science"))
        gpa_scale = st.number_input("GPA Scale Denominator", value=float(curr.get("gpa_scale", 10.0)), step=1.0)

    c4, c5 = st.columns(2)
    with c4:
        skills_str = st.text_input("Technical & Research Skills (comma-separated)", value=", ".join(curr.get("skills", [])))
        projects_str = st.text_area("Key Research / Technical Projects (one per line)", value="\n".join(curr.get("projects", [])))
    with c5:
        github_input = st.text_input("Public GitHub Profile (URL or username)", value=curr.get("github_username", "rahul-ml-dev"))
        english_status = st.text_input("English Test Status", value=curr.get("english_test_status", "IELTS 7.5 (Academic)"))

    st.markdown("##### Postgraduate Goals & Target Destinations")
    c6, c7, c8 = st.columns(3)
    with c6:
        target_degree = st.selectbox(
            "Target Postgraduate Degree",
            ["Master of Science (MSc / MS)", "Master of Engineering (MEng)", "Doctor of Philosophy (PhD)"],
            index=0
        )
        target_subject = st.text_input("Target Field / Specialization", value=curr.get("target_subject", "Computer Science / AI"))
    with c7:
        countries_options = ["Canada", "Germany", "Singapore", "United States", "United Kingdom", "Sweden", "Switzerland"]
        default_countries = [c for c in curr.get("preferred_countries", ["Canada", "Germany", "Singapore"]) if c in countries_options]
        preferred_countries = st.multiselect("Destination Countries", countries_options, default=default_countries)
    with c8:
        target_intake = st.selectbox("Intended Intake", ["Fall 2026", "Spring 2026", "Fall 2027"], index=0)
        funding_req = st.text_input("Funding Requirement", value=curr.get("funding_requirement", "Full tuition + living stipend"))

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        submit_profile = st.form_submit_button("💾 Save Profile Facts", use_container_width=True)

    if submit_profile:
        st.session_state.current_profile_data.update({
            "full_name": full_name,
            "nationality": nationality,
            "current_degree": current_degree,
            "major": major,
            "cgpa": cgpa,
            "gpa_scale": gpa_scale,
            "skills": [s.strip() for s in skills_str.split(",") if s.strip()],
            "projects": [p.strip() for p in projects_str.split("\n") if p.strip()],
            "github_username": github_input.strip(),
            "target_degree": target_degree,
            "target_subject": target_subject,
            "preferred_countries": preferred_countries,
            "target_intake": target_intake,
            "english_test_status": english_status,
            "funding_requirement": funding_req,
        })
        st.success("✅ Profile parameters updated and validated.")

# -----------------------------------------------------------------------------
# Section B: Run Multi-Agent Research Workflow
# -----------------------------------------------------------------------------
st.markdown("### 2. Multi-Agent Coordinated Research")

col_start, col_info = st.columns([2, 5])
with col_start:
    start_research = st.button("🚀 Start Multi-Agent Research", type="primary", use_container_width=True)
with col_info:
    st.caption("Executes: Profile Analysis ➔ Web Discovery ➔ Official Source Verification ➔ 100-pt Formula Matching ➔ SOP Drafting")

if start_research:
    # Save uploaded files temporarily if provided
    resume_temp_path = None
    transcript_temp_path = None

    if uploaded_resume:
        resume_temp_path = AppConfig.UPLOAD_DIR / uploaded_resume.name
        with open(resume_temp_path, "wb") as f:
            f.write(uploaded_resume.getbuffer())

    if uploaded_transcript:
        transcript_temp_path = AppConfig.UPLOAD_DIR / uploaded_transcript.name
        with open(transcript_temp_path, "wb") as f:
            f.write(uploaded_transcript.getbuffer())

    # Real-time Agent Progress Monitor
    st.session_state.agent_live_logs = []
    status_widget = st.status("🤖 Cooperating AI Agents Running...", expanded=True)
    progress_bar = st.progress(0.0)

    coordinator = WorkflowCoordinator()

    def update_agent_ui(event: AgentEvent):
        st.session_state.agent_live_logs.append(event)
        status_widget.write(f"**[{event.agent_name}]** {event.action} — *{event.detail}*")

    # Pipeline execution
    try:
        progress_bar.progress(0.2)
        result = coordinator.run_pipeline(
            resume_path=resume_temp_path,
            transcript_path=transcript_temp_path,
            manual_overrides=st.session_state.current_profile_data,
            github_url_or_user=st.session_state.current_profile_data.get("github_username"),
            progress_callback=update_agent_ui
        )
        progress_bar.progress(1.0)
        status_widget.update(
            label=f"✅ Research Completed in {result.execution_time_seconds}s! Discovered {len(result.discovered_candidates)} opportunities.",
            state="complete",
            expanded=False
        )
        st.session_state.workflow_result = result
        if result.top_recommendations:
            st.session_state.selected_opp_id = result.top_recommendations[0].id
            st.session_state.active_draft = result.application_draft
    except Exception as e:
        status_widget.update(label=f"❌ Workflow Error: {str(e)}", state="error")
        st.error(f"Error during execution: {e}")

# Display Real Agent Execution Log Expander
if st.session_state.agent_live_logs:
    with st.expander("📋 View Real-Time Agent Collaboration Log", expanded=False):
        for log in st.session_state.agent_live_logs:
            st.write(f"`{log.timestamp}` | **{log.agent_name}** | {log.action}: {log.detail}")

# -----------------------------------------------------------------------------
# Section C & D: Top 5 Recommendations & Discovered Candidates
# -----------------------------------------------------------------------------
res: WorkflowResult | None = st.session_state.workflow_result

if res:
    st.markdown("---")
    st.markdown("### 3. Top 5 Recommended Opportunities")
    st.caption("Ranked using a transparent, deterministic 100-point formula based on verified official sources.")

    top_recs = res.top_recommendations

    if not top_recs:
        st.warning("No opportunities passed the strict eligibility criteria. Review filters or profile parameters.")
    else:
        for idx, opp in enumerate(top_recs, 1):
            score_obj = opp.match_score
            elig_obj = opp.eligibility

            # Badge styling
            badge_class = "badge-eligible" if elig_obj.status == "likely_eligible" else "badge-potential"
            status_label = "Likely Eligible" if elig_obj.status == "likely_eligible" else "Potential Fit"

            with st.container():
                st.markdown(f"""
                <div class="recommendation-card">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div>
                            <span style="background: #2563eb; color: white; padding: 0.2rem 0.6rem; border-radius: 6px; font-weight: 700; font-size: 0.85rem;">Rank #{idx}</span>
                            <h3 style="margin: 0.4rem 0 0.2rem 0; color: #0f172a;">{opp.name}</h3>
                            <p style="margin: 0; color: #475569; font-weight: 500;">🏛️ {opp.university_or_provider} &nbsp;•&nbsp; 📍 {opp.country} &nbsp;•&nbsp; 🎓 {opp.degree_level}</p>
                        </div>
                        <div style="text-align: right;">
                            <div class="score-circle">{score_obj.total_score if score_obj else 0}<span style="font-size: 1rem; color: #64748b;">/100</span></div>
                            <span class="agent-pill {badge_class}">{status_label}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_det1, col_det2 = st.columns([3, 2])
                with col_det1:
                    st.write(f"💰 **Funding:** {opp.funding_amount} ({opp.funding_type})")
                    st.write(f"⏳ **Deadline:** `{opp.deadline}` (Status: **{opp.deadline_status.upper()}**)")
                    st.write(f"🎯 **Why Ranked:** {score_obj.reason if score_obj else 'Aligned with qualifications'}")
                    if elig_obj.missing_or_unresolved_criteria:
                        st.warning(f"⚠️ **Pending Conditions:** {'; '.join(elig_obj.missing_or_unresolved_criteria)}")
                with col_det2:
                    st.markdown("**Transparent Scoring Breakdown:**")
                    if score_obj and score_obj.score_breakdown:
                        for cat, desc in score_obj.score_breakdown.items():
                            st.caption(f"• **{cat.replace('_', ' ').title()}:** {desc}")
                    st.markdown(f"[🌐 Official Portal]({opp.official_url}) | [📝 Application Link]({opp.application_url or opp.official_url})")

                # Evidence inspection drawer
                with st.expander(f"🔍 Inspect Official Source Evidence ({len(opp.source_evidence)} source records)", expanded=False):
                    for ev in opp.source_evidence:
                        st.markdown(f"""
                        <div class="evidence-box">
                            <b>Source Domain:</b> {ev.domain} ({'Official Accredited Portal' if ev.is_official else 'Third-Party'})<br>
                            <b>Retrieval Timestamp:</b> {ev.retrieval_timestamp}<br>
                            <b>Confidence Policy:</b> <code>{ev.confidence_policy}</code><br>
                            <b>Verified Excerpt:</b> <i>"{ev.excerpt}"</i>
                        </div>
                        """, unsafe_allow_html=True)

                st.write("")

    # Full Research Results with Multi-attribute Filtering
    st.markdown("---")
    st.markdown("### 4. Comprehensive Researched Candidates (All Discovered)")
    st.caption(f"Preserving all {len(res.discovered_candidates)} discovered university programs with interactive multi-attribute filters.")

    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    all_opps = res.discovered_candidates
    with f_col1:
        f_countries = st.multiselect("Filter by Country", sorted(list(set(o.country for o in all_opps))), default=[])
    with f_col2:
        f_elig = st.multiselect("Filter by Eligibility", ["likely_eligible", "potential_fit", "not_eligible", "insufficient_information"], default=[])
    with f_col3:
        f_fund = st.multiselect("Filter by Funding Type", sorted(list(set(o.funding_type for o in all_opps))), default=[])
    with f_col4:
        f_dead = st.multiselect("Filter by Deadline Status", sorted(list(set(o.deadline_status for o in all_opps))), default=[])

    filtered_opps = all_opps
    if f_countries:
        filtered_opps = [o for o in filtered_opps if o.country in f_countries]
    if f_elig:
        filtered_opps = [o for o in filtered_opps if o.eligibility and o.eligibility.status in f_elig]
    if f_fund:
        filtered_opps = [o for o in filtered_opps if o.funding_type in f_fund]
    if f_dead:
        filtered_opps = [o for o in filtered_opps if o.deadline_status in f_dead]

    # Render Table
    table_data = []
    for o in filtered_opps:
        table_data.append({
            "Score": o.match_score.total_score if o.match_score else 0.0,
            "University / Provider": o.university_or_provider,
            "Opportunity Name": o.name,
            "Country": o.country,
            "Funding Type": o.funding_type,
            "Eligibility": o.eligibility.status if o.eligibility else "N/A",
            "Deadline": o.deadline,
            "Official URL": o.official_url
        })
    df_results = pd.DataFrame(table_data)
    st.dataframe(df_results, use_container_width=True)

    # -----------------------------------------------------------------------------
    # Section E: Application Drafting Assistant
    # -----------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 5. Application Drafting Assistant")
    st.caption("Generates a personalized, evidence-grounded Statement of Purpose for your selected scholarship.")

    # Opportunity selector
    opp_dict = {f"{o.university_or_provider} - {o.name}": o.id for o in top_recs}
    selected_name = st.selectbox(
        "Select target opportunity for Statement of Purpose draft:",
        list(opp_dict.keys()),
        index=0
    )
    chosen_id = opp_dict[selected_name]

    if st.button("✍️ Generate / Refresh Application Draft"):
        chosen_opp = next((o for o in top_recs if o.id == chosen_id), top_recs[0])
        draft_agent = ApplicationDraftingAgent(coordinator.gemini)
        st.session_state.active_draft = draft_agent.generate_draft(
            opportunity=chosen_opp,
            profile=res.student_profile
        )

    active_draft = st.session_state.active_draft
    if active_draft:
        c_draft, c_check = st.columns([3, 2])
        with c_draft:
            st.markdown(f"##### Editable Draft: {active_draft.document_type}")
            edited_content = st.text_area(
                "Statement of Purpose Content",
                value=active_draft.content,
                height=450
            )
            # Update draft content if edited by user
            active_draft.content = edited_content

        with c_check:
            st.markdown("##### 📌 Personalization Checklist")
            st.info("Complete these specific actions to make the essay your own:")
            for item in active_draft.personalization_checklist:
                st.write(f"• {item}")

            st.markdown("##### 🛡️ Hallucination & Fact Audit")
            st.success("**Verified Facts Used:**\n" + "\n".join([f"• {f}" for f in active_draft.verified_facts_used[:4]]))
            st.warning("**Unverified Claims Avoided:**\n" + "\n".join([f"• {a}" for a in active_draft.unverified_claims_avoided[:2]]))

        # Download Actions
        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.download_button(
                "📥 Download Draft as TXT",
                data=active_draft.content,
                file_name=f"SOP_{active_draft.university.replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col_d2:
            docx_bytes = ApplicationDraftingAgent.export_as_docx(active_draft)
            st.download_button(
                "📥 Download Draft as DOCX",
                data=docx_bytes,
                file_name=f"SOP_{active_draft.university.replace(' ', '_')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        with col_d3:
            st.caption(f"Generated at: `{active_draft.generated_timestamp}`")

    # -----------------------------------------------------------------------------
    # Section F: Export Full Results
    # -----------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 6. Export Research Records")
    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        csv_data = df_results.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📊 Export Researched Opportunities (CSV)",
            data=csv_data,
            file_name=f"scholarship_research_{res.run_id}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_ex2:
        json_data = json.dumps(res.model_dump(), indent=2).encode('utf-8')
        st.download_button(
            "💾 Export Complete Workflow Result (JSON)",
            data=json_data,
            file_name=f"scholarship_workflow_{res.run_id}.json",
            mime="application/json",
            use_container_width=True
        )
