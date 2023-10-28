import streamlit as st
from PIL import Image


from main import import_data, manipulate_static_data_sheets, create_static_network_elements, \
    filter_tec_ic_to_recognizables, create_load_gen, run_imbalance, delete_load_gen, run_and_critical

TEC_Register, IC_Register, FES_2022_GSP_Dem, NGET_Circuits, NGET_Circuit_Changes, NGET_Subs, NGET_Tx, NGET_Tx_Changes, Sub_Coordinates = import_data()
bus_ids_df, TEC_Register, IC_Register = manipulate_static_data_sheets(TEC_Register,IC_Register,FES_2022_GSP_Dem,NGET_Circuits,NGET_Circuit_Changes,NGET_Subs,NGET_Tx,NGET_Tx_Changes,Sub_Coordinates)
net = create_static_network_elements(bus_ids_df,NGET_Circuits,NGET_Tx)
TEC_Register_With_Bus, IC_Register_With_Bus, FES_2022_GSP_Dem, tot_wind = filter_tec_ic_to_recognizables(net,NGET_Subs,TEC_Register,IC_Register,FES_2022_GSP_Dem)
st.session_state.coord = Sub_Coordinates
st.session_state.tot_wind = tot_wind
st.session_state.default_par = [1, 0, 0.51, 0, 0.95, 0.5, 0.42, 0.0, 0.0]
st.session_state.tot_values = [int(float(FES_2022_GSP_Dem['Demand_Summer_Peak'].sum())),
                               int(float(IC_Register_With_Bus['MW Import - Total'].sum())),
                               int(float(TEC_Register_With_Bus.loc[TEC_Register_With_Bus['Gen_Type'] == 'Wind', ['MW Connected', 'MW Increase / Decrease']].sum(axis=1).clip(lower=0).sum())),
                               int(float(TEC_Register_With_Bus.loc[TEC_Register_With_Bus['Gen_Type'] == 'PV', ['MW Connected', 'MW Increase / Decrease']].sum(axis=1).clip(lower=0).sum())),
                               int(float(TEC_Register_With_Bus.loc[TEC_Register_With_Bus['Gen_Type'] == 'Nuclear', ['MW Connected', 'MW Increase / Decrease']].sum(axis=1).clip(lower=0).sum())),
                               int(float(TEC_Register_With_Bus.loc[TEC_Register_With_Bus['Gen_Type'] == 'BESS', ['MW Connected', 'MW Increase / Decrease']].sum(axis=1).clip(lower=0).sum())),
                               int(float(TEC_Register_With_Bus.loc[TEC_Register_With_Bus['Gen_Type'] == 'CCGT/CHP/Biomass', ['MW Connected', 'MW Increase / Decrease']].sum(axis=1).clip(lower=0).sum())),
                               int(float(TEC_Register_With_Bus.loc[TEC_Register_With_Bus['Gen_Type'] == 'Hydro/Pump', ['MW Connected', 'MW Increase / Decrease']].sum(axis=1).clip(lower=0).sum())),
                               int(float(TEC_Register_With_Bus.loc[TEC_Register_With_Bus['Gen_Type'] == 'Other', ['MW Connected', 'MW Increase / Decrease']].sum(axis=1).clip(lower=0).sum()))]

# future dev is to add SGT into column_data and ensure that trafo outages are translated into outage in run_and_critical in main.py
# column_data = net.line["name"].tolist() + net.trafo["name"].tolist()
column_data = net.line["name"].tolist()

with st.container():
    col1, col2 = st.columns([5,1], gap="large")

    with col2:
        image1 = Image.open('National_Grid_Logo_White.png')
        st.image(image1, use_column_width="always")

    with col1:
        with st.container():
            st.title("Set Network Background")
st.text('\n')
st.subheader(":blue[Define your network background below (if different to default):]")
st.text('\n')
with st.expander("Outages"):
    st.title("Select Outage(s)")
    outage_list = column_data
    st.session_state.outages = st.multiselect(
        "Select your outage(s)",
        outage_list
    )

# gen_dem_expander = st.expander("Generation and Demand Background")
expander_gen = st.expander("Scale Generation and Demand")
with expander_gen:
    st.title("Define generation and demand scaling factors")
    container_gen = st.container()
    with container_gen:
        check = st.checkbox(":blue[**Click here to define your own load and generation background.**]")
        if check:
            with st.container():
                col1, col2 = st.columns([3,2], gap="large")
                with col1:
                    st.session_state.user_input_1 = st.number_input("Type scaling factor for E&W FES LTW 2027 Demand (range 0.5 to 1)", min_value=0.5, max_value=1.0, value=float(st.session_state.default_par[0]), step=0.01)
                with col2:
                    st.metric(":blue[**Maximum Demand:**]", f"{st.session_state.tot_values[0]} MW")
            with st.container():
                col1, col2 = st.columns([3,2], gap="large")
                with col1:
                    st.session_state.user_input_2 = st.number_input("Type scaling factor for E&W Interconnector (range -1 to 1)", min_value=-1.0, max_value=1.0, value=float(st.session_state.default_par[1]), step=0.01)
                with col2:
                    st.metric(":blue[**Total Interconnector Capacity:**]", f"{st.session_state.tot_values[1]} MW")
            with st.container():
                col1, col2 = st.columns([3,2], gap="large")
                with col1:
                    st.session_state.user_input_3 = st.number_input("Type scaling factor for GB Wind (range 0 to 1)", min_value=0.0, max_value=1.0, value=float(st.session_state.default_par[2]), step=0.01)
                with col2:
                    st.metric(":blue[**Total Wind Capacity:**]", f"{st.session_state.tot_values[2]} MW")
            with st.container():
                col1, col2 = st.columns([3,2], gap="large")
                with col1:
                    st.session_state.user_input_4 = st.number_input("Type scaling factor for E&W PV (range 0 to 1)", min_value=0.0, max_value=1.0, value=float(st.session_state.default_par[3]), step=0.01)
                with col2:
                    st.metric(":blue[**Total PV Capacity:**]", f"{st.session_state.tot_values[3]} MW")
            with st.container():
                col1, col2 = st.columns([3,2], gap="large")
                with col1:
                    st.session_state.user_input_5 = st.number_input("Type scaling factor for E&W Nuclear (range 0 to 1)", min_value=0.0, max_value=1.0, value=float(st.session_state.default_par[4]), step=0.01)
                with col2:
                    st.metric(":blue[**Total Nuclear Capacity:**]", f"{st.session_state.tot_values[4]} MW")
            with st.container():
                col1, col2 = st.columns([3,2], gap="large")
                with col1:
                    st.session_state.user_input_6 = st.number_input("Type scaling factor for E&W BESS (range 0 to 1)", min_value=0.0, max_value=1.0, value=float(st.session_state.default_par[5]), step=0.01)
                with col2:
                    st.metric(":blue[**Total BESS Capacity:**]", f"{st.session_state.tot_values[5]} MW")
            with st.container():
                col1, col2 = st.columns([3,2], gap="large")
                with col1:
                    st.session_state.user_input_7 = st.number_input("Type scaling factor for E&W CCGT / Gas Reciprocating / CHP / Biomass (range 0 to 1)", min_value=0.0, max_value=1.0, value=float(st.session_state.default_par[6]), step=0.01)
                with col2:
                    st.metric(":blue[**Total CCGT/CHP/Biomass Capacity:**]", f"{st.session_state.tot_values[6]} MW")
            with st.container():
                col1, col2 = st.columns([3,2], gap="large")
                with col1:
                    st.session_state.user_input_8 = st.number_input("Type scaling factor for E&W Hydro / Pump Storage (range 0 to 1)", min_value=0.0, max_value=1.0, value=float(st.session_state.default_par[7]), step=0.01)
                with col2:
                    st.metric(":blue[**Total Hydro/Pump Capacity:**]", f"{st.session_state.tot_values[7]} MW")
            with st.container():
                col1, col2 = st.columns([3,2], gap="large")
                with col1:
                    st.session_state.user_input_9 = st.number_input("Type scaling factor for all other generation in E&W i.e. Coal, Tidal (range 0 to 1)", min_value=0.0, max_value=1.0, value=float(st.session_state.default_par[8]), step=0.01)
                with col2:
                    st.metric(":blue[**Total Other Capacity:**]", f"{st.session_state.tot_values[8]} MW")
            st.session_state.b6_transfer_mw_0 = (-3.353e-6) * (
                    st.session_state.user_input_3 * st.session_state.tot_wind) ** 2 + 0.3758 * st.session_state.user_input_3 * st.session_state.tot_wind - 61.84
            st.session_state.b6_transfer_mw = st.session_state.b6_transfer_mw_0 if st.session_state.b6_transfer_mw_0 < 6001 else 6000
            st.write("**B6 transfer (N->S) = {}**".format("" if st.session_state.user_input_3 == "" else "{}GW".format(round(float(st.session_state.b6_transfer_mw) / 1000, 2))))

            st.session_state.text_inputs = [st.session_state.user_input_1,
                                            st.session_state.user_input_2,
                                            st.session_state.user_input_3,
                                            st.session_state.user_input_4,
                                            st.session_state.user_input_5,
                                            st.session_state.user_input_6,
                                            st.session_state.user_input_7,
                                            st.session_state.user_input_8,
                                            st.session_state.user_input_9]
        else:
            st.session_state.text_inputs = st.session_state.default_par
        check_button = st.button("Check imbalance")
        if check_button:
            demand_scaling, scale_interconnector, scale_wind, scale_pv, scale_nuclear, scale_bess, scale_gas, scale_pump, scale_all_other = [float(st.session_state.text_inputs[i]) for i in range(9)]
            net = create_load_gen(demand_scaling, scale_interconnector, scale_wind, scale_pv, scale_nuclear, scale_bess, scale_gas, scale_pump, scale_all_other, net, FES_2022_GSP_Dem, TEC_Register_With_Bus, IC_Register_With_Bus)
            net, line_tx_results_pre_int_sorted = run_imbalance(net)
            st.session_state.ext_grid_imb = round(float(net.res_ext_grid["p_mw"].sum()), 1)
            net = delete_load_gen(net)
            if -500 < st.session_state.ext_grid_imb < 500:
                st.session_state.succ1 = st.success("User input saved! Imbalance less than 500MW")
                st.metric(":green[**Imbalance:**]", f"{st.session_state.ext_grid_imb} MW")
            else:
                st.session_state.err1 = st.error("Please readjust scaling to reduce imbalance to less than 500MW. If you would like to apply the default values please clear your input(s).")
                st.metric(":red[**Imbalance:**]", f"{st.session_state.ext_grid_imb} MW")
                st.session_state.err2 = st.text("Note +ve imbalance indicates too little generation")

outages = st.session_state.outages
list_o = ""

if not outages:
    list_o = ":blue[**None**]"
else:
    for i in outages:
        list_o += "- " + f":blue[**{i}**]" + "\n"

list_n = ""
types_for_list_n = ["Demand:","Interconnector:","Wind:","PV: ","Nuclear:","BESS:","CCGT/CHP/Biomass:", "Pump/Hydro:", "All other generation:", "B6 transfer (N->S):"]
for i, j in zip(st.session_state.text_inputs, types_for_list_n):
    list_n += "- " + j + "  " + f":blue[**{round(float(i),2)}**]" + "\n"

st.text('\n')

st.divider()

st.subheader(":blue[The following Network Background is being applied:]")

with st.container():
    st.write("**Year of Study:**")
    st.markdown(":blue[2027]")

st.text('\n')

with st.container():
    st.write("**Outage Background:**")
    st.markdown(list_o)

st.text('\n')

with st.container():
    st.write("**Generation and Demand Background:**")
    st.markdown(list_n)
    st.text('\n')

st.text('\n')

st.subheader("**:orange[Click _'Run DC Power Flow Analysis'_ in the sidebar to run all contingencies]**")

with st.sidebar:
    st.text('\n')
    if st.button("⚡  **Run DC Power Flow Analysis**  ⚡"):
        demand_scaling, scale_interconnector, scale_wind, scale_pv, scale_nuclear, scale_bess, scale_gas, scale_pump, scale_all_other = [
            float(st.session_state.text_inputs[i]) for i in range(9)]
        net = create_load_gen(demand_scaling, scale_interconnector, scale_wind, scale_pv, scale_nuclear, scale_bess, scale_gas, scale_pump,
                              scale_all_other, net, FES_2022_GSP_Dem, TEC_Register_With_Bus, IC_Register_With_Bus)
        net, line_tx_results_pre_int_sorted = run_imbalance(net)
        st.session_state.line_tx_results_pre_int_sorted = line_tx_results_pre_int_sorted
        st.session_state.gen_info = net.sgen[["name","type","p_mw","q_mvar","in_service","max_p_mw"]]
        st.session_state.load_info = net.load[["name","p_mw","q_mvar","in_service"]]
        st.session_state.bus_info = net.bus[["name", "vn_kv", "in_service"]]
        st.session_state.line_info = net.line[["name", "length_km", "max_i_ka", "in_service"]]
        st.session_state.ext_grid_imb = round(float(net.res_ext_grid["p_mw"].sum()),1)
        if -500 < st.session_state.ext_grid_imb < 500:
            st.markdown(f":green[Imbalance = **{st.session_state.ext_grid_imb} MW**]")
            with st.spinner(text=":orange[DC power flow contingencies running...]"):
                overall_result_sorted, outage_line_name, critical_lines, line_tx_results_pre_sorted = run_and_critical(outages, net)
                st.session_state.overall_result_sorted = overall_result_sorted
                st.session_state.outage_line_name = outage_line_name
                st.session_state.critical_lines = critical_lines
                st.session_state.line_tx_results_pre_sorted = line_tx_results_pre_sorted
            st.success("**Done! Please view the Results page.**")
        else:
            st.markdown(f":red[Imbalance = **{st.session_state.ext_grid_imb} MW**]")
            st.error("**There is an imbalance > 500MW, please review your scaling factors above.**")
