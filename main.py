import streamlit as st
from interface.streamlit_app import LegalAnalysisInterface

if __name__ == "__main__":
    interface = LegalAnalysisInterface()
    interface.run()