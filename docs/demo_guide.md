# Five-Minute Demonstration Package & Presentation Script
**TetraNoodle AI Hackathon 2026: AI Scholarship Finder**

---

## 1. Step-by-Step Demo Script (5-Minute Timing Breakdown)

### 0:00 - 0:45 | Introduction & Hackathon Problem Statement
- **Speaker:** "Hello everyone. Today, postgraduate applicants seeking scholarships abroad face a massive problem: generic chatbots hallucinate admission criteria, invent fake deadlines, and make false promises. We built the **AI Scholarship Finder**, an end-to-end multi-agent system powered by five cooperating agents that delivers verified, source-grounded research without hallucinations."
- **Screen:** Show the Streamlit application homepage at `http://localhost:8501`. Highlight the system status indicator and modern dashboard design.

### 0:45 - 1:45 | Reference Student Workflow (Rahul Sharma)
- **Speaker:** "Let's demonstrate with our reference student, Rahul Sharma: a BTech in Computer Science graduate from India with an 8.2 CGPA and AI/ML project experience, seeking Master's funding in Canada, Germany, and Singapore."
- **Actions on Screen:**
  1. Click **"Load Rahul (Reference)"** in the sidebar.
  2. Point out how the parameters (8.2 CGPA, 10.0 scale, IELTS 7.5, ML projects) populate the form.
  3. Click **"🚀 Start Multi-Agent Research"**.
  4. Expand the **Agent Collaboration Log** to watch real-time agent handoffs:
     - *Profile Analyst* normalizes academic facts.
     - *Discovery Agent* retrieves 10+ candidate opportunities.
     - *Eligibility Agent* audits citizenship and GPA requirements.
     - *Matching Agent* executes the 100-point transparent formula.

### 1:45 - 2:45 | Inspecting Top 5 Recommendations & Evidence Provenance
- **Speaker:** "Within seconds, the system ranks the top five defensible opportunities. Notice how each recommendation includes the exact official university link, verified funding details, and a clear breakdown of why it was chosen."
- **Actions on Screen:**
  1. Show **Rank #1: UBC Graduate Research Assistantship & International Tuition Award** (Score: ~92.5/100, Full Tuition + Living Stipend).
  2. Click **"🔍 Inspect Official Source Evidence"** to reveal the exact excerpt extracted from UBC's portal, retrieval timestamp, and official domain confidence policy.
  3. Show the interactive multi-attribute filter table below, with all 12 discovered candidates.

### 2:45 - 3:30 | Recoverable Failure & Error Handling Demonstration
- **Speaker:** "A critical requirement is resilience to real-world edge cases. Let's demonstrate how our system recovers from failures."
- **Actions on Screen:**
  1. Filter the candidates table by **"Eligibility: not_eligible"** or show an opportunity with citizenship restrictions.
  2. Explain: *"Notice how domestic-only programs or broken portals are never falsely recommended. When a source is inaccessible or conflicting, the system flags it as `insufficient_information` or `not_eligible` and excludes it from the top five rather than making up facts."*
  3. Point out that even if `GEMINI_API_KEY` is unset or an invalid GitHub username is provided, the system does not crash; it logs a warning and proceeds with validated local intelligence.

### 3:30 - 4:15 | Application Assistant & Zero-Hallucination SOP Drafting
- **Speaker:** "Next, Rahul wants to apply to the University of British Columbia. Our Application Drafting Agent synthesizes a personalized Statement of Purpose based strictly on verified facts."
- **Actions on Screen:**
  1. Under **Section 5: Application Drafting Assistant**, select *UBC Graduate Research Assistantship*.
  2. Click **"✍️ Generate / Refresh Application Draft"**.
  3. Scroll through the generated draft: point out how it weaves in Rahul's real undergraduate degree, 8.2 CGPA, and specific project names (*Plant Disease Detection*, *Traffic Signal Optimization*).
  4. Highlight the **Personalization Checklist** and the **Fact Audit** (0 hallucinations).
  5. Click **"📥 Download Draft as DOCX"** to show instant export functionality.

### 4:15 - 5:00 | Second Student Adaptability & Conclusion (Maria Santos)
- **Speaker:** "The true test of a general multi-agent architecture is adaptability to different student profiles without rewriting code. Let's switch to Maria Santos from Brazil, studying Computational Mathematics with a 3.85/4.0 GPA, targeting Germany and Canada."
- **Actions on Screen:**
  1. In the sidebar, click **"Load Maria (Profile 2)"**.
  2. Click **"🚀 Start Multi-Agent Research"**.
  3. Show how the rankings automatically re-prioritize: European and German fellowships (DAAD, TUM Informatics) rise to the top, reflecting Maria's Brazilian nationality, 4.0 GPA scale, and mathematical specialization.
  4. Conclude: *"In summary, the AI Scholarship Finder delivers multi-agent collaboration, source-grounded evidence, zero hallucinations, and full adaptability. Thank you!"*

---

## 2. Screen Action Checklist for Live Demo Recording

| Step | Action Item | Expected Result on Screen |
| :---: | :--- | :--- |
| **1** | Open browser to `http://localhost:8501` | Dashboard loads with clean dark header and sidebar status. |
| **2** | Click **"Load Rahul (Reference)"** | Input fields populate with Rahul's 8.2 CGPA and CS degree. |
| **3** | Click **"🚀 Start Multi-Agent Research"** | Status widget displays live agent event transitions. |
| **4** | Expand **"Agent Collaboration Log"** | Review chronological agent events with timestamps. |
| **5** | Inspect **Rank #1 Card** | Score badge (~92.5/100), full funding summary, and deadline status. |
| **6** | Open **"Inspect Official Source Evidence"** | View direct quoted excerpt and official domain verification badge. |
| **7** | Review **Application Drafting Assistant** | Real-time editable SOP with personalization checklist. |
| **8** | Click **"📥 Download Draft as DOCX"** | Downloads `.docx` file in browser. |
| **9** | Click **"Load Maria (Profile 2)"** | Profile shifts to Computational Math, 3.85 GPA, Brazil nationality. |
| **10** | Re-run research for Maria | German and math-aligned fellowships reprioritized to Rank #1. |

---

## 3. Statement of Purpose Preview (Sample Generated Output)

```text
STATEMENT OF PURPOSE

Applicant: Rahul Sharma
Target Program: Master of Science (MSc) in Computer Science / Machine Learning
Institution: University of British Columbia (UBC)
Funding / Fellowship: Graduate Research Assistantship & International Tuition Award (Full Tuition + Living Stipend)
Target Intake: Fall 2026

Dear Members of the Graduate Admissions and Scholarship Committee,

I am writing to formally submit my application for admission to the Master of Science (MSc) in Computer Science / Machine Learning at University of British Columbia (UBC), alongside consideration for the Graduate Research Assistantship & International Tuition Award. Having established a rigorous academic foundation through my BTech in Computer Science and Engineering in Computer Science, graduating with a cumulative grade point average of 8.2 on a 10.0 scale, I am eager to deepen my technical expertise and contribute actively to advanced graduate research.

ACADEMIC AND TECHNICAL FOUNDATION
Throughout my undergraduate training, I maintained a disciplined focus on computational fundamentals, algorithms, and practical software engineering. My core proficiencies encompass Python, Machine Learning, Deep Learning, PyTorch, SQL, Git, which I have applied systematically across both coursework and substantial practical implementations. My technical perspective has been shaped by direct engineering engagements, including:
  • Vision-based Plant Disease Detection using Deep Convolutional Networks
  • Multi-Agent Traffic Signal Optimization System with Deep Q-Networks
  • End-to-End Generative AI Research Paper Summarizer

These experiences exposed me to real-world challenges in data processing, model evaluation, and computational efficiency, underscoring the critical necessity of pursuing specialized postgraduate studies.

RESEARCH ALIGNMENT WITH UNIVERSITY OF BRITISH COLUMBIA (UBC)
The postgraduate program at University of British Columbia (UBC) stands out internationally for its distinguished faculty, cutting-edge facilities, and vibrant research culture in Computer Science / Machine Learning. I am particularly drawn to current departmental work focusing on [Insert Specific Research Group / Lab Focus]. In particular, I look forward to the prospect of contributing to research under the guidance of [Insert Professor / Faculty Advisor Name], whose ongoing contributions closely match my aspirations.

SCHOLARSHIP MOTIVATION AND VALUE CREATION
Receiving the Graduate Research Assistantship & International Tuition Award would be instrumental in allowing me to dedicate myself entirely to high-impact graduate research and academic excellence. By alleviating financial constraints through its Full Tuition + Living Stipend provision, this award will enable me to participate fully in lab seminars, collaborative projects, and the academic community at University of British Columbia (UBC).

With verified readiness (IELTS 7.5 (Academic)), academic dedication, and proven engineering discipline, I am prepared to meet the demanding standards of your program and represent University of British Columbia (UBC) with distinction.

Sincerely,
Rahul Sharma
```
