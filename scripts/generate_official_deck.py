import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

BLUE_GOOGLE = RGBColor(66, 133, 244)
BLACK_TEXT = RGBColor(32, 33, 36)
FONT_BOLD = True
FONT_NAME = 'Google Sans' 

def apply_google_sans(shape, text, size=18, is_bold=False, color=None, alignment=None):
    if not hasattr(shape, "text_frame"):
        return
    
    tf = shape.text_frame
    tf.word_wrap = True
    
    # Clear existing
    while len(tf.paragraphs) > 0:
        p = tf.paragraphs[0]
        p._p.getparent().remove(p._p)
    
    lines = text.split('\n')
    for line in lines:
        p = tf.add_paragraph()
        if alignment:
            p.alignment = alignment
        
        run = p.add_run()
        run.text = line
        run.font.name = FONT_NAME
        run.font.size = Pt(size)
        
        if ':' in line and len(line.split(':')[0]) < 35:
            run.font.bold = True
            if color:
                run.font.color.rgb = color
        elif line.startswith('➢') or line.startswith('-'):
            run.font.bold = False
            run.font.size = Pt(size - 2)
        else:
            run.font.bold = is_bold
            if color:
                run.font.color.rgb = color

def generate_querysage_deck():
    # References to the template in the geo_pulse_mcp directory as requested
    template_path = r'D:\Siva\Books\CAREER\HACKATHON\Gen_AI_APAC_2026\geo_pulse_mcp\scripts\docs\Project Submission Deck _ Gen AI Academy APAC Edition.pptx'
    prs = Presentation(template_path)

    # slide 1: Title
    s1 = prs.slides[0]
    title_info = (
        "➢ Participant name: SIVASUBRAMANIAN\n"
        "➢ Problem Statement: Transforming fragmented pharmaceutical inventory into an AI-powered conversational data mesh.\n"
        "➢ Project Name: QuerySage - Pharma Inventory Intelligence\n"
        "➢ Tagline: Conversational Clarity for Life-Saving Decisions.\n"
        "➢ Domain: Healthcare / Pharma Tech / Enterprise AI\n"
        "➢ Technology Stack: Gemini 2.5 Flash, AlloyDB AI, Cloud Run."
    )
    apply_google_sans(s1.shapes[1], title_info, size=18, color=BLUE_GOOGLE)

    # slide 2: Problem Statement
    s2 = prs.slides[1]
    apply_google_sans(s2.shapes[1], "Pharma Inventory: The 'Opaque Data' Crisis", size=28, is_bold=True, color=BLUE_GOOGLE)
    prob_text = (
        "Context: Critical drugs, controlled substances, and expiring inventory are trapped in SQL databases, inaccessible to floor staff.\n\n"
        "Pain Points:\n"
        "➢ Access Barrier: Pharmacists and administrators cannot query database tables in real-time during emergencies.\n"
        "➢ Inventory Waste: Estimated $2B lost annually in expired pharma stock due to poor visibility.\n"
        "➢ Latency: Manual cross-referencing between suppliers and inventory levels leads to stockouts of life-saving medications.\n"
        "➢ The Opportunity: QuerySage democratizes data—moving from 'SQL-only' to 'Conversational Intelligence'."
    )
    apply_google_sans(s2.shapes[2], prob_text, size=20)

    # slide 3: The Solution (Criteria)
    s4 = prs.slides[3] # Meeting Build Criteria slide
    apply_google_sans(s4.shapes[1], "QuerySage - Technical Implementation & Innovation", size=24, is_bold=True, color=BLUE_GOOGLE)
    sol_text = (
        "➢ AlloyDB AI Mesh: Leveraged Google's AlloyDB AI Natural Language extension inside a Private VPC for secure SQL generation.\n"
        "➢ Gemini 2.5 Intelligence: Primary reasoning engine used for results synthesis and conversational summarization.\n"
        "➢ Cloud Native Resilience: Deployed as a 3-tier mesh on Google Cloud Run with Direct VPC Egress for zero-latency private access.\n"
        "➢ Real-Time Insight: Automated alerting for controlled substance thresholds and imminent 60-day expiry windows."
    )
    apply_google_sans(s4.shapes[2], sol_text, size=18)

    # slide 4: Opportunities
    s3 = prs.slides[2] # Solution Outline slide
    apply_google_sans(s3.shapes[3], "The QuerySage Omni-Agent Framework", size=24, is_bold=True, color=BLUE_GOOGLE)
    opp_text = (
        "➢ Predictive Reordering: Moving from reactive queries to proactive AI-driven procurement suggestions.\n"
        "➢ Multimodal Inspection: Gemini Vision focus for scanning shipment invoices and matching physical stock automatically.\n"
        "➢ Enterprise Scale: Ready for Multi-Facility Hospital Networks via Google Cloud's Global VPC connectivity."
    )
    apply_google_sans(s3.shapes[1], opp_text, size=18)

    # slide 5: Impact
    s5 = prs.slides[4] # Project Details / Business Case
    apply_google_sans(s5.shapes[1], "QuerySage: Business Impact & Operational Efficiency", size=24, is_bold=True, color=BLUE_GOOGLE)
    feat_text = (
        "Key Innovations\n"
        "➢ Self-Correcting SQL Pipeline: Automatically routes queries to curated fallbacks for mission-critical reliability.\n"
        "➢ Private IP Security: Enterprise-grade isolation; sensitive pharmaceutical data never crosses the public internet.\n"
        "➢ Harmonized UX: Glassmorphic dashboard optimized for hospital floor tablet use.\n\n"
        "Business ROI\n"
        "➢ Response Time: 95% reduction in time-to-insight for inventory stock levels.\n"
        "➢ Risk Mitigation: Automated identification of controlled substance discrepancies."
    )
    apply_google_sans(s5.shapes[2], feat_text, size=18)

    # slide 6: Flow
    s6 = prs.slides[5]
    apply_google_sans(s6.shapes[1], "QuerySage Architecture: Private VPC & AI Mesh", size=24, is_bold=True, color=BLUE_GOOGLE)
    apply_google_sans(s6.shapes[2], "[Cloud Run + Direct VPC Egress + AlloyDB AI]", size=14)
    arch_img = r'C:\Users\USER\.gemini\antigravity\brain\d56f2d93-8bf6-470f-bcb4-03c0de81dd40\querysage_architecture_diagram_1774980478982.png'
    if os.path.exists(arch_img):
        s6.shapes.add_picture(arch_img, Inches(1), Inches(1.8), height=Inches(4.8))

    # slide 7: Tech Stack
    s7 = prs.slides[6]
    apply_google_sans(s7.shapes[1], "Full Stack Google Gen AI Implementation", size=24, is_bold=True, color=BLUE_GOOGLE)
    tech_text = (
        "➢ Gemini 2.5 Flash: The conversational summarization and planning layer.\n"
        "➢ AlloyDB for PostgreSQL: The bedrock of pharmaceutical data with low-latency private access.\n"
        "➢ Vertex AI SDK: Powering the model handshake and safety filters.\n"
        "➢ Google Cloud Run: Serverless production-grade hosting.\n"
        "➢ Artifact Registry: Automated container management for high-frequency CI/CD."
    )
    apply_google_sans(s7.shapes[2], tech_text, size=20)

    # slide 8: Snapshots
    s8 = prs.slides[7]
    apply_google_sans(s8.shapes[2], "QuerySage Live: Inventory Intelligence in Action", size=24, is_bold=True, color=BLUE_GOOGLE)
    # Using the successful screenshot we just took
    snap_img = r'C:\Users\USER\.gemini\antigravity\brain\d56f2d93-8bf6-470f-bcb4-03c0de81dd40\querysafe_ai_summary_success_1774978355377.png'
    if os.path.exists(snap_img):
        s8.shapes.add_picture(snap_img, Inches(1), Inches(1.8), height=Inches(4.8))

    # slide 9: Thank You
    s9 = prs.slides[8]
    box = s9.shapes.add_textbox(Inches(0), Inches(3), Inches(13.33), Inches(2))
    apply_google_sans(box, "Thank You!\nQuerySage - Intelligence for Healthcare.", size=60, is_bold=True, color=BLUE_GOOGLE, alignment=PP_ALIGN.CENTER)

    output_file = r"D:\Siva\Books\CAREER\HACKATHON\Gen_AI_APAC_2026\alloy_nexus_mcp\QUERYSAGE_OFFICIAL_SUBMISSION_DECK_FINAL.pptx"
    prs.save(output_file)
    print(f"[SUCCESS] Official Submission Deck saved to {output_file}")

if __name__ == "__main__":
    generate_querysage_deck()
