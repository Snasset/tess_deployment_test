import streamlit as st

main_page = st.Page(
    page="views/text_extraction.py",
    title="Ekstraksi Infromasi Nilai Gizi",
    default=True
)

info_page = st.Page(
    page="views/information.py",
    title="Informasi"
)


pg = st.navigation(pages=[main_page, info_page])
st.logo("assets/title_logo.png")
st.sidebar.text("Made by Snasset (Github)")

pg.run()

