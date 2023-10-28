import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import folium
from PIL import Image

with st.container():
    col1, col2 = st.columns([5,1], gap="large")

    with col2:
        image1 = Image.open('National_Grid_Logo_White.png')
        st.image(image1, use_column_width="always")

    with col1:
        with st.container():
            st.title("View the Results")
st.text('\n')

if 'line_tx_results_pre_int_sorted' not in st.session_state:
    st.subheader("**:red[Please come back to view results after hitting _Run DC Power Flow Analysis_ on the _Configure_ page]**")

else:
    tab1, tab2 = st.tabs(["Post-fault results", "Pre-fault results"])
    with tab1:
        col1, col2 = st.columns(2,gap="large")
        with col1:
            with st.container():
                list_outages = ""
                for i in st.session_state.outage_line_name:
                    list_outages += "- " + f":blue[{i}]" + "\n"
                list_critical = ""
                for i in st.session_state.critical_lines:
                    list_critical += "- " + f":red[{i}]" + "\n"
                st.subheader("Selected outages:")
                st.markdown(list_outages)
                st.text('\n')
                st.subheader("Post-fault line loadings (outages applied):")
                st.dataframe(st.session_state.overall_result_sorted,use_container_width=True)

                st.text('\n')
                st.subheader("Critical contingencies:")
                st.markdown("_Contingencies resulting in an overload (>100%) of a line._")
                st.markdown(list_critical)


        with col2:
            with st.container():
                st.subheader("Map of overloads:")
                mask = st.session_state.overall_result_sorted['loading_percent'] > 100
                point_names = "_".join(st.session_state.overall_result_sorted.loc[mask, 'name'].tolist())
                map_center = [st.session_state.coord['latitude'].mean(), st.session_state.coord['longitude'].mean()]
                m = folium.Map(location=map_center, zoom_start=10, tiles='cartodbpositron')
                show_overload_markers_only = st.checkbox(":red[_Show only overloads_]")

                for index, row in st.session_state.coord.iterrows():
                    if row['Site Code'] in point_names:
                        color = 'red'
                    else:
                        color = 'blue'
                    if not show_overload_markers_only or color == 'red':
                        tooltip_content = f"{row['Site Name']}<br>Additional Info"
                        folium.CircleMarker(
                            location=[row['latitude'], row['longitude']],
                            radius=5,
                            fill=True,
                            fill_opacity=0.7,
                            tooltip=tooltip_content,
                            color=color
                        ).add_to(m)

                m.fit_bounds(m.get_bounds())

                # set map to be equal width of container
                map_width_str = "100%"
                map_height_str = "500px"
                map_styling = f"width: {map_width_str}; height: {map_height_str}; margin: 0 auto;"

                map_html = f'<div style="{map_styling}">{m.get_root().render()}</div>'
                st.components.v1.html(map_html, height=500)

                # if "set map to be equal width of container" not used then use folium_static(m) below
                # folium_static(m)

                if show_overload_markers_only:
                    st.write(":red[**Only showing nodes connected to lines where loading > 100% pre / post-fault**]")

    with tab2:
        col3, col4 = st.columns(2, gap="large")
        with col3:
            st.subheader("Pre-fault intact line loadings:")
            st.dataframe(st.session_state.line_tx_results_pre_int_sorted, use_container_width=True)
            st.text('\n')
            st.subheader("Pre-fault line loadings (outages applied):")
            st.dataframe(st.session_state.line_tx_results_pre_sorted, use_container_width=True)
            st.text('\n')
            st.subheader("Line ratings information: ")
            st.dataframe(st.session_state.line_info, use_container_width=True)
            st.text('\n')
        with col4:
            st.subheader("All generators:")
            st.dataframe(st.session_state.gen_info, use_container_width=True)
            st.text('\n')
            st.subheader("All loads:")
            st.dataframe(st.session_state.load_info, use_container_width=True)
            st.text('\n')
            st.subheader("All buses:")
            st.dataframe(st.session_state.bus_info, use_container_width=True)
            st.text('\n')
            with st.container():
                col5, col6, col7 = st.columns(3)
                with col5:
                    st.metric(":orange[Sum of generation]", f"{round((st.session_state.gen_info['p_mw']).sum(),1)}MW")
                with col6:
                    st.metric(":orange[Sum of loads]", f"{round((st.session_state.load_info['p_mw']).sum(),1)}MW")
                with col7:
                    st.metric(":orange[Number of buses (nodes)]", f"{st.session_state.bus_info.shape[0]}")