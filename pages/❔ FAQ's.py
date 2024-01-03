import streamlit as st
from PIL import Image

with st.sidebar:
    image1 = Image.open('National_Grid_Logo_White.png')
    st.image(image1, use_column_width="always")

with st.container():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("Frequently Asked Questions")
    with col2:
        image_rsaat2 = Image.open('RSAAT_Logo2.png')
        st.image(image_rsaat2, use_column_width="always")

st.text('\n')

if "button" not in st.session_state:
    st.session_state.button = False
def toggle():
    if st.session_state.button:
        st.session_state.button = False
    else:
        st.session_state.button = True
st.button("⏬  Expand All", on_click=toggle, type = "primary")

with st.expander("How do I use RSAAT?", expanded=st.session_state.button):
    st.text('\n')
    st.markdown(
        "RSAAT has been designed to enable you to run DC Power Flow Analysis and review the results to establish the viability of any network background you have defined.")
    st.markdown(
        "This app has been created by the System Access Team and pulls data from the latest **_TEC Register_**, latest **_Interconnector Register_**, **_FES 2022_** and **_ETYS 2022 (Appendix B)_**, and has been set up for **2027**, however further developments are expected in future which will enable users to specify a year.")
    st.markdown("A diagram has been included below illustrating the mix of tools and services that make RSAAT.")
    with st.container():
        col3, col4 = st.columns([3, 2])
        with col3:
            image2 = Image.open('Process inputs for power flow app.png')
            st.image(image2, use_column_width="always")
with st.expander("How was the default Demand and Generation Background determined?", expanded=st.session_state.button):
    st.text('\n')
    st.markdown("The B6 transfer (power flowing across the Scotland-England border) has been set as a function of the "
                "National wind output. This has been implemented to simplify the calculation of B6 transfer and has "
                "undergone verification to establish the appropriate relationship between wind and B6 transfer; the "
                "process is explained further below:")
    st.markdown("-	Data for B6 transfer collated from operational metering data (Data Historian) for power flow on "
                "circuits across the B6 boundary between 2019-2022.")
    st.markdown("- Data for wind collated from ESO published operational metering data for the same time period, "
                "2019-2022.")
    st.markdown("- Histogram of B6 Transfer, Scotland Wind and National Wind are shown below to illustrate the "
                "range of power levels and the frequency of occurences for each block.")
    image_corr1 = Image.open('Distribution_B6_Wind.png')
    st.image(image_corr1, width=500)
    st.caption('*_the frequency axis returns a probability density, where the cumulative area of each category '
               'summates to 1_')
    st.markdown("- Correlation between Scotland wind and B6 transfer calculated to be **0.90** (Pearson’s Correlation "
                "Coefficient) which is a very strong positive correlation, and correction between National wind and "
                "B6 transfer calculated to be **0.73** (Pearson’s Correlation Coefficient which is a strong positive "
                "correlation.")
    image_corr2 = Image.open('Correlation_Matrix.png')
    st.image(image_corr2, width=500)
    st.markdown("- The relationship between National wind and B6 transfer can be broadly calculated (to a covariance of 0.73) using a polynomial equation as displayed below:")
    image_corr3 = Image.open('Relationship_B6_Wind.png')
    st.image(image_corr3, width=500)
    st.markdown("- Sharing of power transfer on the AC network was found to be distributed 56:44 between the BLYT/ECCL/STEW and HARK/GRNA/MOFF route respectively.")
    st.markdown("- Where total B6 transfer is >4GW then Western Link is set to operate at its maximum power transfer (2.2GW). For B6 transfer <4GW then Western Link takes a 1/3 share of the total B6 transfer.")
    st.markdown('''
    <style>
    [data-testid="stMarkdownContainer"] ul{
        list-style-position: inside;
    }
    </style>
    ''', unsafe_allow_html=True)
with st.expander("How was the Network Topology determined?", expanded=st.session_state.button):
    st.text('\n')
    st.markdown('The parameters and connections of nodes and lines that make up the GB transmission network are shared by the respective Transmission Owners to National Grid ESO and are subsequently published by in the ESO Data Portal. This data is updated on an annual basis and has been compiled into a functioning network using Python library pandapower to enable Load Flow analysis.')
    st.markdown('Please note that **Supergrid Transformers** that connect **demand** are not modelled; therefore demand security studies cannot be undertaken in this _App_.')
with st.expander("What is Contingency Analysis?", expanded=st.session_state.button):
    st.text('\n')
    st.markdown('Contingency Analysis involves simulating faults on the network to determine which faults result in a constraint.')
    st.markdown('The _App_ currently only runs single circuit contingency analysis, however this is expected to be expanded to include double circuits in the near future.')
with st.expander("How do I interpret the results?", expanded=st.session_state.button):
    st.text('\n')
    st.markdown('The following guidance has been produced to ensure the appropriate course of action is followed when reviewing your _Results_:')
    st.markdown("- if there are any pre-fault circuit loadings >70% then :red[contact the System Access team]")
    st.markdown("- if there are any post-fault circuit loadings >90% then :red[contact the System Access team]")
    st.markdown("- if there are >1 outage at the same substation then :red[contact the System Access team]")
    st.markdown("- if there are none of the above then your outage is deemed likely to be acceptable :green[please submit an SRD into OPPM]")
    st.markdown('''
    <style>
    [data-testid="stMarkdownContainer"] ul{
        list-style-position: inside;
    }
    </style>
    ''', unsafe_allow_html=True)
with st.expander("How were the results validated?", expanded=st.session_state.button):
    st.text('\n')
    st.markdown('_Further info to follow._')
with st.expander("What is in the pipeline for future developments?", expanded=st.session_state.button):
    st.text('\n')
    st.markdown('_Further info to follow._')
with st.expander("Who do I contact for more information or to report an issue?", expanded=st.session_state.button):
    st.text('\n')
    st.markdown('Please contact <a href="nathanael.sims@nationalgrid.com"> Nathanael Sims</a> within System Access if you experience any issues / have any queries or suggestions.', unsafe_allow_html=True)
