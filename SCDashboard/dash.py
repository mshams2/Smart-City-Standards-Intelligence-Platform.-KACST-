from __future__ import annotations

from PIL import Image
import streamlit as st

from src.config import APP_TITLE, LOGO_FILE
from src.data_loader import load_all_data
from src.pages import (
    domain_maturity,
    evidence_repository,
    executive_overview,
    gap_analysis,
    project_checker,
    project_comparison,
    standards_library,
)
from src.ui import inject_global_css, render_sidebar


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=Image.open(LOGO_FILE),
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "Smart City Standards Intelligence Platform prototype - KACST / SCI.",
    },
)

inject_global_css()

try:
    dashboard_data = load_all_data()
except Exception as exc:
    st.error("The dashboard data could not be loaded. Check the files in the data folder.")
    st.exception(exc)
    st.stop()

pages = {
    "Executive Overview": executive_overview.render,
    "Standards Library": standards_library.render,
    "Domain Maturity View": domain_maturity.render,
    "Project Comparison": project_comparison.render,
    "Gap Analysis": gap_analysis.render,
    "Evidence Repository": evidence_repository.render,
    "Project Checker": project_checker.render,
}

pages[render_sidebar()](dashboard_data)
