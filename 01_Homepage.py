"""


"""

import pandas as pd
import streamlit as st
from PIL import Image
import streamlit.components.v1 as components
from rsaat_main import apply_data
import os


def set_page_config():
    st.set_page_config(
        page_title="Rapid System Access Analysis Tool",
        page_icon="⚡",
        layout="wide"
    )


@st.cache_data
def import_methods():
    initialise_apply_data = apply_data.DefineData()
    return initialise_apply_data

def initialise_session_states(initialise_apply_data):
    st.session_state.year = 2024
    st.session_state.circuit_outages = []
    st.session_state.trafo_outages = []
    st.session_state.ranking_order = initialise_apply_data.ranking_order
    st.session_state.scale_demand = 1.0

def create_homepage(initialise_apply_data):
    """ create homepage header """
    # project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # sub_coords = pd.read_csv(os.path.join(project_root, 'RSAAT/data', 'CRM_Sub_Coordinates_WGS84.csv'))
    # st.session_state.coord = sub_coords

    # add title logo
    with st.container():
        image_rsaat1 = Image.open('images/RSAAT_Logo.png')
        st.image(image_rsaat1, use_column_width="always")
    st.divider()

    tab_input, tab_back, tab_results = st.tabs(['Inputs', 'Background', 'Results'])
    with tab_back:
        with st.container():
            col1, col2 = st.columns([1, 1], gap="large")
            with col1:
                st.subheader("Generation Background", divider='red')
                tab1, tab2, tab3 = st.tabs(['Generators', 'Interconnectors', 'Generation Map'])
                with tab1:
                    tec_register = initialise_apply_data.tec_register[
                        initialise_apply_data.tec_register['HOST TO'] == 'NGET'][
                        ['Generator Name', 'Connection Site', 'bus_name', 'MW Effective', 'Plant Type',
                         'MW Effective From', 'Project Status', 'Agreement Type']]
                    tec_register_sorted = tec_register.sort_values(by='Generator Name')
                    st.dataframe(tec_register_sorted, height=500, hide_index=True,
                                 column_config={"bus_name": "ETYS Substation",
                                                "MW Effective From": st.column_config.DateColumn(format='DD-MM-YYYY')})
                with tab2:
                    ic_register = initialise_apply_data.ic_register[
                        initialise_apply_data.ic_register['HOST TO'] == 'NGET'][['Generator Name',
                                                                                 'Connection Site', 'bus_name',
                                                                                 'MW Effective - Import',
                                                                                 'MW Effective - Export',
                                                                                 'MW Effective From', 'Project Status']]
                    ic_register_sorted = ic_register.sort_values(by='Generator Name')
                    st.dataframe(ic_register_sorted, height=500, hide_index=True,
                                 column_config={"bus_name": "ETYS Substation", "Generator Name": "Interconnector Name",
                                                "MW Effective From": st.column_config.DateColumn(format='DD-MM-YYYY')})
                with tab3:
                    components.iframe("https://www.energydashboard.co.uk/map", height=500)

            with col2:
                st.subheader("Demand Background", divider='blue')
                tab1, tab2 = st.tabs(['GSP Demand', 'Total Demand'])
                with tab1:
                    gsp_demand = initialise_apply_data.gsp_demand[
                        initialise_apply_data.gsp_demand['region'] == 'nget']
                    gsp_demand = gsp_demand.drop(['region', 'bus_id'], axis=1)
                    gsp_demand_sorted = gsp_demand.sort_values(by='Node')
                    st.dataframe(gsp_demand_sorted, height=500, hide_index=True,
                                 column_config={"bus_name": "ETYS Substation"})
                with tab2:
                    columns_to_sum = gsp_demand_sorted.select_dtypes(include=[int, float]).columns
                    st.dataframe((gsp_demand_sorted[columns_to_sum].sum(axis=0)), height=500)

    with tab_input:
        with st.container():
            st.markdown('')
            co_1 = st.button(':red[Save Inputs]', type='secondary', use_container_width=True)
            st.markdown('')
            with st.container():
                st.subheader("Select Year of Study", divider='grey')
                years = list(range(2024, 2036))
                year_option = st.selectbox(
                    "Click dropdown to select year",
                    years)
                st.markdown('')
                st.markdown('')

            with st.container():
                with st.container():
                    col1, col2 = st.columns([1, 1], gap="large")
                    with col1:
                        st.subheader("Select Outages", divider='orange')
                    with col2:
                        st.subheader("Define Generation and Demand", divider='violet')
                with st.container():
                    col1, col2 = st.columns([1, 1], gap="large")
                    with col1:
                        tab1, tab2 = st.tabs(['Select Circuits', 'Select Transformers'])
                        with tab1:
                            initialise_apply_data.all_circuits.insert(0, 'Select', False)
                            all_circuits = st.data_editor(initialise_apply_data.all_circuits, height=450, column_config={
                                "Select": st.column_config.CheckboxColumn("Select", help="Select **outages**", default=False)},
                                                       hide_index=True)
                        with tab2:
                            initialise_apply_data.all_trafo.insert(0, 'Select', False)
                            all_trafo = st.data_editor(initialise_apply_data.all_trafo, height=450, column_config={
                                "Select": st.column_config.CheckboxColumn("Select", help="Select **outages**", default=False)},
                                                       hide_index=True)

                    with col2:
                        tab1, tab2 = st.tabs(['Scale Plant', 'Scale Demand'])
                        with tab1:
                            ranking_order = st.data_editor(initialise_apply_data.ranking_order, height=450)
                        with tab2:
                            # scale_demand_default = pd.DataFrame({'Demand': ['England & Wales', 'Scotland'], 'Scale Value': [1.0, 1.0]})
                            # scale_demand = st.data_editor(scale_demand_default, height=450)
                            scale_demand = st.number_input('**Scale England & Wales Demand**', min_value=0.3, max_value=2.0, value=1.0, step=0.1, label_visibility="visible")
                            st.write('You have selected: ', scale_demand)
                if co_1:
                    selected_co_1 = list(all_circuits[all_circuits['Select'] == True].index.values)
                    selected_to_1 = list(all_trafo[all_trafo['Select'] == True].index.values)
                    all_circuits_trafo = pd.merge(all_circuits[all_circuits['Select'] == True][['Node 1', 'Node 2']], all_trafo[all_trafo['Select'] == True][['Node 1', 'Node 2']], how="outer")
                    # all_circuits_trafo = "None" if all_circuits_trafo.empty else all_circuits_trafo
                    # ranking_order_changes = pd.concat([ranking_order, initialise_apply_data.ranking_order]).drop_duplicates(keep=False)
                    ranking_order_changes = ranking_order[~ranking_order.isin(initialise_apply_data.ranking_order).all(axis=1)].reset_index(drop=True)
                    # ranking_order_changes = "None" if ranking_order_changes.empty else ranking_order_changes
                    # demand_changes = pd.concat([scale_demand, scale_demand_default]).drop_duplicates(keep=False)
                    st.session_state.year = year_option
                    st.session_state.circuit_outages = selected_co_1
                    st.session_state.trafo_outages = selected_to_1
                    st.session_state.ranking_order = ranking_order
                    st.session_state.scale_demand = scale_demand

    with st.sidebar:
        # image1 = Image.open('images/National_Grid_Logo_White.png')
        # st.image(image1, use_column_width="always")
        st.write(':green[Study Type:]', '')
        study_type = st.selectbox(':blue[Study Type]', ['1st order contingency', '1st and 2nd order contingency', 'No contingency (base case)'], label_visibility='collapsed')
        st.write(':blue[Analysis Method:]', '')
        analysis_method = st.selectbox(':blue[Analysis Type]', ['AC', 'DC', 'DC with losses'],
                                       label_visibility='collapsed')

        st.write('**You have selected:**', ':green['+study_type+' study'+']'+' - '+':blue['+analysis_method+' analysis'+']'+':orange['+' - with the following background selected:]' + '\n')
        if co_1:
            st.markdown(':orange[*Year of Study:*]'+'\n')
            st.write(st.session_state.year)
            st.markdown(':orange[*Outages:*]'+'\n')
            st.dataframe(all_circuits_trafo, hide_index=True)
            st.markdown(':orange[*Demand Scaling:*]'+'\n')
            st.write(st.session_state.scale_demand)
            st.markdown(':orange[*Changes to default ranking order:*]'+'\n')
            st.dataframe(ranking_order_changes, hide_index=True)
        else:
            st.markdown(':orange[***Click Save Inputs to save and view selected Network Background***]')

        st.session_state.study_type = study_type
        st.session_state.analysis_method = analysis_method

        if st.button("⚡  **Run Power Flow Analysis**  ⚡"):
            with st.spinner(text=":orange[Contingencies running...]"):
                run_analysis(initialise_apply_data)
                net, line_tx_results_pre_int_sorted, overall_result_sorted, circuit_outages, trafo_outages, critical_lines, line_tx_results_pre_sorted = initialise_apply_data.run_analysis(st.session_state.circuit_outages, st.session_state.trafo_outages, st.session_state.study_type, st.session_state.analysis_method)

                st.session_state.line_tx_results_pre_int_sorted = line_tx_results_pre_int_sorted
                st.session_state.gen_info = net.sgen[["name", "type", "p_mw", "q_mvar", "in_service", "max_p_mw"]]
                st.session_state.load_info = net.load[["name", "p_mw", "q_mvar", "in_service"]]
                st.session_state.bus_info = net.bus[["name", "vn_kv", "in_service"]]
                st.session_state.line_info = net.line[["name", "length_km", "max_i_ka", "in_service"]]
                st.session_state.ext_grid_imb = round(float(net.res_ext_grid["p_mw"].sum()), 1)

                st.session_state.overall_result_sorted = overall_result_sorted
                st.session_state.critical_lines = critical_lines
                st.session_state.line_tx_results_pre_sorted = line_tx_results_pre_sorted

    # with tab_results:
    #     with st.container():
    #         st.title("View Results")
    #     st.text('\n')
    #
    #     # message if PFA has not been run yet
    #     if 'line_tx_results_pre_int_sorted' not in st.session_state:
    #         st.markdown("**:orange[Please come back to view results after running DC Power Flow Analysis.]**")
    #
    #     # if PFA has been run then show results
    #     else:
    #         tab1, tab2 = st.tabs(["Post-fault results", "Pre-fault results"])
    #         with tab1:
    #             col1, col2 = st.columns(2, gap="large")
    #             with col1:
    #                 with st.container():
    #                     list_outages = ""
    #                     for i in st.session_state.circuit_outages:
    #                         list_outages += "- " + f":blue[{i}]" + "\n"
    #                     for i in st.session_state.trafo_outages:
    #                         list_outages += "- " + f":blue[{i}]" + "\n"
    #                     list_critical = ""
    #                     for i in st.session_state.critical_lines:
    #                         list_critical += "- " + f":red[{i}]" + "\n"
    #                     st.subheader(":blue[Outages applied]")
    #                     if len(list_outages) < 2:
    #                         list_outages = 'None'
    #                     st.markdown(list_outages)
    #                     st.text('\n')
    #                     st.subheader(":blue[Post-fault loadings]")
    #                     st.markdown("★ _with outages applied_ ★")
    #                     st.dataframe(st.session_state.overall_result_sorted, use_container_width=True)
    #
    #                     st.text('\n')
    #                     st.subheader(":blue[Critical contingencies]")
    #                     st.markdown("★ _Contingencies resulting in an overload (>100%) of a circuit_ ★")
    #                     st.markdown(list_critical)
    #
    #             with col2:
    #                 with st.container():
    #                     st.subheader(":blue[Map of overloads]")
    #                     mask = st.session_state.overall_result_sorted['loading_percent'] > 100
    #                     point_names = "_".join(st.session_state.overall_result_sorted.loc[mask, 'name'].tolist())
    #                     map_center = [st.session_state.coord['latitude'].mean(),
    #                                   st.session_state.coord['longitude'].mean()]
    #                     m = folium.Map(location=map_center, zoom_start=10, tiles='cartodbpositron')
    #                     show_overload_markers_only = st.checkbox(":red[_Show only overloads_]")
    #
    #                     for index, row in st.session_state.coord.iterrows():
    #                         if row['Site Code'] in point_names:
    #                             color = 'red'
    #                         else:
    #                             color = 'blue'
    #                         if not show_overload_markers_only or color == 'red':
    #                             tooltip_content = f"{row['Site Name']}<br>Additional Info"
    #                             folium.CircleMarker(
    #                                 location=[row['latitude'], row['longitude']],
    #                                 radius=5,
    #                                 fill=True,
    #                                 fill_opacity=0.7,
    #                                 tooltip=tooltip_content,
    #                                 color=color
    #                             ).add_to(m)
    #
    #                     m.fit_bounds(m.get_bounds())
    #
    #                     # set map to be equal width of container
    #                     map_width_str = "100%"
    #                     map_height_str = "500px"
    #                     map_styling = f"width: {map_width_str}; height: {map_height_str}; margin: 0 auto;"
    #
    #                     map_html = f'<div style="{map_styling}">{m.get_root().render()}</div>'
    #                     st.components.v1.html(map_html, height=500)
    #
    #                     # if "set map to be equal width of container" not used then use folium_static(m) below
    #                     # folium_static(m)
    #
    #                     if show_overload_markers_only:
    #                         st.write(
    #                             ":red[**Only showing nodes connected to lines where loading > 100% pre / post-fault**]")
    #
    #         with tab2:
    #             col3, col4 = st.columns(2, gap="large")
    #             with col3:
    #                 st.subheader(":blue[Pre-fault intact line loadings]")
    #                 st.dataframe(st.session_state.line_tx_results_pre_int_sorted, use_container_width=True)
    #                 st.text('\n')
    #                 st.subheader(":blue[Pre-fault line loadings (outages applied)]")
    #                 st.dataframe(st.session_state.line_tx_results_pre_sorted, use_container_width=True)
    #                 st.text('\n')
    #                 st.subheader(":blue[Line ratings information]")
    #                 st.dataframe(st.session_state.line_info, use_container_width=True)
    #                 st.text('\n')
    #             with col4:
    #                 st.subheader(":blue[All generators]")
    #                 st.dataframe(st.session_state.gen_info, use_container_width=True)
    #                 st.text('\n')
    #                 st.subheader(":blue[All loads]")
    #                 st.dataframe(st.session_state.load_info, use_container_width=True)
    #                 st.text('\n')
    #                 st.subheader(":blue[All buses]")
    #                 st.dataframe(st.session_state.bus_info, use_container_width=True)
    #                 st.text('\n')
    #             with st.container():
    #                 col5, col6, col7 = st.columns(3)
    #                 with col5:
    #                     st.metric(":orange[Sum of generation]", f"{int((st.session_state.gen_info['p_mw']).sum())} MW")
    #                 with col6:
    #                     st.metric(":orange[Sum of loads]", f"{int((st.session_state.load_info['p_mw']).sum())} MW")
    #                 with col7:
    #                     st.metric(":orange[Number of buses (nodes)]", f"{st.session_state.bus_info.shape[0]}")

def run_analysis(initialise_apply_data):
    initialise_apply_data.filter_network_data(st.session_state.year)
    initialise_apply_data.filter_tec_ic_data()
    print(st.session_state.scale_demand)
    initialise_apply_data.filter_demand_data(st.session_state.scale_demand)
    initialise_apply_data.combine_tec_ic_registers()
    initialise_apply_data.determine_initial_dispatch_setting()
    initialise_apply_data.create_pandapower_system()

if __name__ == "__main__":
    set_page_config()
    initialise_apply_data = import_methods()
    initialise_session_states(initialise_apply_data)
    create_homepage(initialise_apply_data)


def old_code():
    # # ex-Configure page
    # # import and run functions from apply_data.py up to "filter_tec_ic_to_recognizables()"
    # from rsaat_main.apply_data import import_data, manipulate_static_data_sheets, create_static_network_elements, \
    #     filter_tec_ic_to_recognizables, create_load_gen, run_imbalance, delete_load_gen, run_and_critical
    #
    # TEC_Register, IC_Register, FES_2022_GSP_Dem, NGET_Circuits, NGET_Circuit_Changes, NGET_Subs, NGET_Tx, NGET_Tx_Changes, Sub_Coordinates = import_data()
    # bus_ids_df, TEC_Register, IC_Register = manipulate_static_data_sheets(TEC_Register, IC_Register, FES_2022_GSP_Dem,
    #                                                                       NGET_Circuits, NGET_Circuit_Changes,
    #                                                                       NGET_Subs, NGET_Tx, NGET_Tx_Changes,
    #                                                                       Sub_Coordinates)
    # net = create_static_network_elements(bus_ids_df, NGET_Circuits, NGET_Tx)
    # TEC_Register_With_Bus, IC_Register_With_Bus, FES_2022_GSP_Dem, tot_wind = filter_tec_ic_to_recognizables(net,
    #                                                                                                          NGET_Subs,
    #                                                                                                          TEC_Register,
    #                                                                                                          IC_Register,
    #                                                                                                          FES_2022_GSP_Dem)
    # st.session_state.coord = Sub_Coordinates
    # st.session_state.tot_wind = tot_wind
    # st.session_state.default_par = [1, 0, 0.51, 0, 0.95, 0.5, 0.42, 0.0, 0.0]
    # st.session_state.tot_values = [int(float(FES_2022_GSP_Dem['Demand_Summer_Peak'].sum())),
    #                                int(float(IC_Register_With_Bus['MW Import - Total'].sum())),
    #                                int(float(TEC_Register_With_Bus.loc[
    #                                              TEC_Register_With_Bus['Gen_Type'] == 'Wind', ['MW Connected',
    #                                                                                            'MW Increase / Decrease']].sum(
    #                                    axis=1).clip(lower=0).sum())),
    #                                int(float(TEC_Register_With_Bus.loc[
    #                                              TEC_Register_With_Bus['Gen_Type'] == 'PV', ['MW Connected',
    #                                                                                          'MW Increase / Decrease']].sum(
    #                                    axis=1).clip(lower=0).sum())),
    #                                int(float(TEC_Register_With_Bus.loc[
    #                                              TEC_Register_With_Bus['Gen_Type'] == 'Nuclear', ['MW Connected',
    #                                                                                               'MW Increase / Decrease']].sum(
    #                                    axis=1).clip(lower=0).sum())),
    #                                int(float(TEC_Register_With_Bus.loc[
    #                                              TEC_Register_With_Bus['Gen_Type'] == 'BESS', ['MW Connected',
    #                                                                                            'MW Increase / Decrease']].sum(
    #                                    axis=1).clip(lower=0).sum())),
    #                                int(float(TEC_Register_With_Bus.loc[
    #                                              TEC_Register_With_Bus['Gen_Type'] == 'CCGT/CHP/Biomass', [
    #                                                  'MW Connected', 'MW Increase / Decrease']].sum(axis=1).clip(
    #                                    lower=0).sum())),
    #                                int(float(TEC_Register_With_Bus.loc[
    #                                              TEC_Register_With_Bus['Gen_Type'] == 'Hydro/Pump', ['MW Connected',
    #                                                                                                  'MW Increase / Decrease']].sum(
    #                                    axis=1).clip(lower=0).sum())),
    #                                int(float(TEC_Register_With_Bus.loc[
    #                                              TEC_Register_With_Bus['Gen_Type'] == 'Other', ['MW Connected',
    #                                                                                             'MW Increase / Decrease']].sum(
    #                                    axis=1).clip(lower=0).sum()))]
    #
    # # FUTURE DEV: add SGT into column_data and ensure that trafo outages are translated into outage in run_and_critical
    # # in apply_data.py column_data = net.line["name"].tolist() + net.trafo["name"].tolist()
    # column_data = net.line["name"].tolist()
    # st.text('\n')
    #
    # # add container for setting network background
    # with st.container():
    #     st.title("Network Background")
    #     st.text('\n')
    #     col1, col2 = st.columns([3, 2], gap="large")
    #
    #     # setting the network background in column 1
    #     with col1:
    #         with st.container():
    #             st.subheader(":blue[Set network conditions]")
    #             st.text('\n')
    #             with st.expander("Outages"):
    #                 st.subheader("Outages")
    #                 outage_list = column_data
    #                 st.session_state.outages = st.multiselect(
    #                     "Select your outage(s)",
    #                     outage_list
    #                 )
    #
    #             expander_gen = st.expander("Set Generation and Demand")
    #             with expander_gen:
    #                 st.subheader("Define generation and demand scaling factors")
    #                 container_gen = st.container()
    #                 with container_gen:
    #                     st.text('\n')
    #                     check = st.checkbox(":blue[**Click to alter demand or generation background**]")
    #                     if check:
    #                         with st.container():
    #                             st.text('\n')
    #                             col3, col4 = st.columns([5, 4], gap="medium")
    #                             with col3:
    #                                 st.session_state.user_input_1 = st.number_input(
    #                                     "Type scaling factor for E&W FES LTW 2027 Demand (range 0.5 to 1)",
    #                                     min_value=0.5, max_value=1.0, value=float(st.session_state.default_par[0]),
    #                                     step=0.01)
    #                             with col4:
    #                                 st.metric(":blue[**Maximum Demand:**]", f"{st.session_state.tot_values[0]} MW")
    #                         with st.container():
    #                             col3, col4 = st.columns([5, 4], gap="medium")
    #                             with col3:
    #                                 st.session_state.user_input_2 = st.number_input(
    #                                     "Type scaling factor for E&W Interconnector (range -1 to 1)", min_value=-1.0,
    #                                     max_value=1.0, value=float(st.session_state.default_par[1]), step=0.01)
    #                             with col4:
    #                                 st.metric(":blue[**Total Interconnector Capacity:**]",
    #                                           f"{st.session_state.tot_values[1]} MW")
    #                         with st.container():
    #                             col3, col4 = st.columns([5, 4], gap="medium")
    #                             with col3:
    #                                 st.session_state.user_input_3 = st.number_input(
    #                                     "Type scaling factor for GB Wind (range 0 to 1)", min_value=0.0, max_value=1.0,
    #                                     value=float(st.session_state.default_par[2]), step=0.01)
    #                             with col4:
    #                                 st.metric(":blue[**Total Wind Capacity:**]", f"{st.session_state.tot_values[2]} MW")
    #                         with st.container():
    #                             col3, col4 = st.columns([5, 4], gap="medium")
    #                             with col3:
    #                                 st.session_state.user_input_4 = st.number_input(
    #                                     "Type scaling factor for E&W PV (range 0 to 1)", min_value=0.0, max_value=1.0,
    #                                     value=float(st.session_state.default_par[3]), step=0.01)
    #                             with col4:
    #                                 st.metric(":blue[**Total PV Capacity:**]", f"{st.session_state.tot_values[3]} MW")
    #                         with st.container():
    #                             col3, col4 = st.columns([5, 4], gap="medium")
    #                             with col3:
    #                                 st.session_state.user_input_5 = st.number_input(
    #                                     "Type scaling factor for E&W Nuclear (range 0 to 1)", min_value=0.0,
    #                                     max_value=1.0, value=float(st.session_state.default_par[4]), step=0.01)
    #                             with col4:
    #                                 st.metric(":blue[**Total Nuclear Capacity:**]",
    #                                           f"{st.session_state.tot_values[4]} MW")
    #                         with st.container():
    #                             col3, col4 = st.columns([5, 4], gap="medium")
    #                             with col3:
    #                                 st.session_state.user_input_6 = st.number_input(
    #                                     "Type scaling factor for E&W BESS (range 0 to 1)", min_value=0.0, max_value=1.0,
    #                                     value=float(st.session_state.default_par[5]), step=0.01)
    #                             with col4:
    #                                 st.metric(":blue[**Total BESS Capacity:**]", f"{st.session_state.tot_values[5]} MW")
    #                         with st.container():
    #                             col3, col4 = st.columns([5, 4], gap="medium")
    #                             with col3:
    #                                 st.session_state.user_input_7 = st.number_input(
    #                                     "Type scaling factor for E&W CCGT / Gas Reciprocating / CHP / Biomass (range 0 to 1)",
    #                                     min_value=0.0, max_value=1.0, value=float(st.session_state.default_par[6]),
    #                                     step=0.01)
    #                             with col4:
    #                                 st.metric(":blue[**Total CCGT/CHP/Biomass Capacity:**]",
    #                                           f"{st.session_state.tot_values[6]} MW")
    #                         with st.container():
    #                             col3, col4 = st.columns([5, 4], gap="medium")
    #                             with col3:
    #                                 st.session_state.user_input_8 = st.number_input(
    #                                     "Type scaling factor for E&W Hydro / Pump Storage (range 0 to 1)",
    #                                     min_value=0.0, max_value=1.0, value=float(st.session_state.default_par[7]),
    #                                     step=0.01)
    #                             with col4:
    #                                 st.metric(":blue[**Total Hydro/Pump Capacity:**]",
    #                                           f"{st.session_state.tot_values[7]} MW")
    #                         with st.container():
    #                             col3, col4 = st.columns([5, 4], gap="medium")
    #                             with col3:
    #                                 st.session_state.user_input_9 = st.number_input(
    #                                     "Type scaling factor for all other generation in E&W i.e. Coal, Tidal (range 0 to 1)",
    #                                     min_value=0.0, max_value=1.0, value=float(st.session_state.default_par[8]),
    #                                     step=0.01)
    #                             with col4:
    #                                 st.metric(":blue[**Total Other Capacity:**]",
    #                                           f"{st.session_state.tot_values[8]} MW")
    #                         st.session_state.b6_transfer_mw_0 = (-3.353e-6) * (
    #                                 st.session_state.user_input_3 * st.session_state.tot_wind) ** 2 + 0.3758 * st.session_state.user_input_3 * st.session_state.tot_wind - 61.84
    #                         st.session_state.b6_transfer_mw = st.session_state.b6_transfer_mw_0 if st.session_state.b6_transfer_mw_0 < 6001 else 6000
    #                         st.write("**B6 transfer (N->S) = {}**".format(
    #                             "" if st.session_state.user_input_3 == "" else "{}GW".format(
    #                                 round(float(st.session_state.b6_transfer_mw) / 1000, 2))))
    #                         st.session_state.text_inputs = [st.session_state.user_input_1,
    #                                                         st.session_state.user_input_2,
    #                                                         st.session_state.user_input_3,
    #                                                         st.session_state.user_input_4,
    #                                                         st.session_state.user_input_5,
    #                                                         st.session_state.user_input_6,
    #                                                         st.session_state.user_input_7,
    #                                                         st.session_state.user_input_8,
    #                                                         st.session_state.user_input_9]
    #                     else:
    #                         st.session_state.text_inputs = st.session_state.default_par
    #                     check_button = st.button("Check imbalance")
    #                     if check_button:
    #                         demand_scaling, scale_interconnector, scale_wind, scale_pv, scale_nuclear, scale_bess, scale_gas, scale_pump, scale_all_other = [
    #                             float(st.session_state.text_inputs[i]) for i in range(9)]
    #                         net = create_load_gen(demand_scaling, scale_interconnector, scale_wind, scale_pv,
    #                                               scale_nuclear, scale_bess, scale_gas, scale_pump, scale_all_other,
    #                                               net, FES_2022_GSP_Dem, TEC_Register_With_Bus, IC_Register_With_Bus)
    #                         net, line_tx_results_pre_int_sorted = run_imbalance(net)
    #                         st.session_state.ext_grid_imb = round(float(net.res_ext_grid["p_mw"].sum()), 1)
    #                         net = delete_load_gen(net)
    #                         if -500 < st.session_state.ext_grid_imb < 500:
    #                             st.session_state.succ1 = st.success("User input saved! Imbalance less than 500MW")
    #                             st.metric(":green[**Imbalance:**]", f"{st.session_state.ext_grid_imb} MW")
    #                         else:
    #                             st.session_state.err1 = st.error(
    #                                 "Please readjust scaling to reduce imbalance to less than 500MW. If you would like to apply the default values please clear your input(s).")
    #                             st.metric(":red[**Imbalance:**]", f"{st.session_state.ext_grid_imb} MW")
    #                             st.session_state.err2 = st.text("Note +ve imbalance indicates too little generation")
    #
    #             outages = st.session_state.outages
    #             list_o = ""
    #
    #             if not outages:
    #                 list_o = ":red[**None**]"
    #             else:
    #                 for i in outages:
    #                     list_o += "- " + f":red[**{i}**]" + "\n"
    #
    #             list_n = ""
    #             types_for_list_n = ["Demand:", "Interconnector:", "Wind:", "PV: ", "Nuclear:", "BESS:",
    #                                 "CCGT/CHP/Biomass:", "Pump/Hydro:", "All other generation:", "B6 transfer (N->S):"]
    #             for i, j in zip(st.session_state.text_inputs, types_for_list_n):
    #                 list_n += "- " + j + "  " + f":red[**{round(float(i), 2)}**]" + "\n"
    #
    #             st.text('\n')
    #         st.markdown("**:orange[Click _Run DC Power Flow Analysis_ in the sidebar to run all contingencies.]**")
    #
    #     # reflecting the network background in text in column 2
    #     with col2:
    #         with st.container():
    #             st.subheader(":blue[View network conditions]")
    #
    #         with st.container():
    #             st.write("**Year of Study:**")
    #             st.markdown(":red[2027]")
    #
    #         st.text('\n')
    #
    #         with st.container():
    #             st.write("**Outage Background:**")
    #             st.markdown(list_o)
    #
    #         st.text('\n')
    #
    #         with st.container():
    #             st.write("**Generation and Demand Background:**")
    #             st.markdown(list_n)
    #             st.text('\n')
    #
    #         st.text('\n')
    #
    # # add NG logo and Run button into sidebar
    # with st.sidebar:
    #     image1 = Image.open('images/National_Grid_Logo_White.png')
    #     st.image(image1, use_column_width="always")
    #     st.text('\n')
    #     if st.button("⚡  **Run DC Power Flow Analysis**  ⚡"):
    #         demand_scaling, scale_interconnector, scale_wind, scale_pv, scale_nuclear, scale_bess, scale_gas, scale_pump, scale_all_other = [
    #             float(st.session_state.text_inputs[i]) for i in range(9)]
    #         net = create_load_gen(demand_scaling, scale_interconnector, scale_wind, scale_pv, scale_nuclear, scale_bess,
    #                               scale_gas, scale_pump,
    #                               scale_all_other, net, FES_2022_GSP_Dem, TEC_Register_With_Bus, IC_Register_With_Bus)
    #         net, line_tx_results_pre_int_sorted = run_imbalance(net)
    #         st.session_state.line_tx_results_pre_int_sorted = line_tx_results_pre_int_sorted
    #         st.session_state.gen_info = net.sgen[["name", "type", "p_mw", "q_mvar", "in_service", "max_p_mw"]]
    #         st.session_state.load_info = net.load[["name", "p_mw", "q_mvar", "in_service"]]
    #         st.session_state.bus_info = net.bus[["name", "vn_kv", "in_service"]]
    #         st.session_state.line_info = net.line[["name", "length_km", "max_i_ka", "in_service"]]
    #         st.session_state.ext_grid_imb = round(float(net.res_ext_grid["p_mw"].sum()), 1)
    #         if -500 < st.session_state.ext_grid_imb < 500:
    #             st.markdown(f":green[Imbalance = **{st.session_state.ext_grid_imb} MW**]")
    #             with st.spinner(text=":orange[DC power flow contingencies running...]"):
    #                 overall_result_sorted, outage_line_name, critical_lines, line_tx_results_pre_sorted = run_and_critical(
    #                     outages, net)
    #                 st.session_state.overall_result_sorted = overall_result_sorted
    #                 st.session_state.outage_line_name = outage_line_name
    #                 st.session_state.critical_lines = critical_lines
    #                 st.session_state.line_tx_results_pre_sorted = line_tx_results_pre_sorted
    #             st.success("**Done! Please view the Results page.**")
    #         else:
    #             st.markdown(f":red[Imbalance = **{st.session_state.ext_grid_imb} MW**]")
    #             st.error("**There is an imbalance > 500MW, please review your scaling factors above.**")
    # st.divider()
    #
    # # ex-Results page
    # with st.container():
    #     st.title("View Results")
    # st.text('\n')
    #
    # # message if PFA has not been run yet
    # if 'line_tx_results_pre_int_sorted' not in st.session_state:
    #     st.markdown("**:orange[Please come back to view results after running DC Power Flow Analysis.]**")
    #
    # if PFA has been run then show results
    # else:
        tab1, tab2 = st.tabs(["Post-fault results", "Pre-fault results"])
        with tab1:
            col1, col2 = st.columns(2, gap="large")
            with col1:
                with st.container():
                    list_outages = ""
                    for i in st.session_state.outage_line_name:
                        list_outages += "- " + f":blue[{i}]" + "\n"
                    list_critical = ""
                    for i in st.session_state.critical_lines:
                        list_critical += "- " + f":red[{i}]" + "\n"
                    st.subheader(":blue[Outages applied]")
                    if len(list_outages) < 2:
                        list_outages = 'None'
                    st.markdown(list_outages)
                    st.text('\n')
                    st.subheader(":blue[Post-fault loadings]")
                    st.markdown("★ _with outages applied_ ★")
                    st.dataframe(st.session_state.overall_result_sorted, use_container_width=True)

                    st.text('\n')
                    st.subheader(":blue[Critical contingencies]")
                    st.markdown("★ _Contingencies resulting in an overload (>100%) of a circuit_ ★")
                    st.markdown(list_critical)

            with col2:
                with st.container():
                    st.subheader(":blue[Map of overloads]")
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
                        st.write(
                            ":red[**Only showing nodes connected to lines where loading > 100% pre / post-fault**]")

        with tab2:
            col3, col4 = st.columns(2, gap="large")
            with col3:
                st.subheader(":blue[Pre-fault intact line loadings]")
                st.dataframe(st.session_state.line_tx_results_pre_int_sorted, use_container_width=True)
                st.text('\n')
                st.subheader(":blue[Pre-fault line loadings (outages applied)]")
                st.dataframe(st.session_state.line_tx_results_pre_sorted, use_container_width=True)
                st.text('\n')
                st.subheader(":blue[Line ratings information]")
                st.dataframe(st.session_state.line_info, use_container_width=True)
                st.text('\n')
            with col4:
                st.subheader(":blue[All generators]")
                st.dataframe(st.session_state.gen_info, use_container_width=True)
                st.text('\n')
                st.subheader(":blue[All loads]")
                st.dataframe(st.session_state.load_info, use_container_width=True)
                st.text('\n')
                st.subheader(":blue[All buses]")
                st.dataframe(st.session_state.bus_info, use_container_width=True)
                st.text('\n')
            with st.container():
                col5, col6, col7 = st.columns(3)
                with col5:
                    st.metric(":orange[Sum of generation]", f"{int((st.session_state.gen_info['p_mw']).sum())} MW")
                with col6:
                    st.metric(":orange[Sum of loads]", f"{int((st.session_state.load_info['p_mw']).sum())} MW")
                with col7:
                    st.metric(":orange[Number of buses (nodes)]", f"{st.session_state.bus_info.shape[0]}")
