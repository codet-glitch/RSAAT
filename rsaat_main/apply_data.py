"""


"""

import pandapower as pp
import pandas as pd
import numpy as np
from rsaat_main.network_data import TransformData
import os
import copy
import re
from datetime import datetime
import sys
import requests


# import openpyxl
# import json
# from PIL import Image

class DefineData:  # (network_data.TransformData)
    def __init__(self):
        instance_transform_data = TransformData()
        instance_transform_data.import_network_data()
        instance_transform_data.import_tec_ic_demand_data()
        instance_transform_data.create_bus_id()
        instance_transform_data.transform_network_data()
        instance_transform_data.transform_tec_ic_data()
        instance_transform_data.transform_demand_data()
        instance_transform_data.transform_intrahvdc_data()
        self.__dict__.update(instance_transform_data.__dict__)

        self.year = None

        self.ic_register_year_filtered = None
        self.tec_register_year_filtered = None
        self.all_gen_register = None
        self.all_trafo_year_filtered = None
        self.all_circuits_year_filtered = None
        self.gsp_demand_filtered = None
        self.net = None

    # apply year filter to GB data
    def filter_network_data(self, year: int):
        # filter circuit and transformer data by self.year
        self.year = year
        def filter_circuit_trafo_data(data, changes):
            changes = changes[pd.to_numeric(changes['Year'], errors='coerce') <= self.year]
            for index, row in changes.iterrows():
                status = row['Status']
                if 'addition' in status.lower():
                    row_df = pd.DataFrame([row])
                    data = pd.concat([data, row_df], ignore_index=True)
                elif 'remove' in status.lower():
                    for index1, row1 in data.iterrows():
                        if (row1['Node 1'] == row['Node 1']) & (row1['Node 2'] == row['Node 2']):
                            data.drop(index1, inplace=True)
                            break
                elif 'change' in status.lower():
                    for index2, row2 in data.iterrows():
                        if (row2['Node 1'] == row['Node 1']) & (row2['Node 2'] == row['Node 2']):
                            data.drop(index2, inplace=True)
                            row_df = pd.DataFrame([row])
                            data = pd.concat([data, row_df], ignore_index=True)
                            break
                else:
                    print(f"Warning: Status of row {index} needs checking. Ignored from 'for' loop.")
            return data

        self.all_circuits_year_filtered = filter_circuit_trafo_data(self.all_circuits, self.all_circuits_changes)
        self.all_trafo_year_filtered = filter_circuit_trafo_data(self.all_trafo, self.all_trafo_changes)

    # filter tec & ic data by self.year
    def filter_tec_ic_data(self):
        self.tec_register = self.tec_register[self.tec_register['bus_id'] != ""]
        self.ic_register = self.ic_register[self.ic_register['bus_id'] != ""]
        self.tec_register_year_filtered = self.tec_register[
            self.tec_register['MW Effective From'].apply(lambda x: x.year <= int(self.year))]
        self.ic_register_year_filtered = self.ic_register[
            self.ic_register['MW Effective From'].apply(lambda x: x.year <= int(self.year))]

    # filter demand data by self.year
    def filter_demand_data(self):
        self.gsp_demand_filtered = self.gsp_demand[self.gsp_demand['bus_id'] != ""]
        try:
            selected_column = [col for col in self.gsp_demand_filtered.columns if
                               col.startswith(str(int(self.year))[-2:])]
            self.gsp_demand_filtered['demand'] = self.gsp_demand_filtered[selected_column[0]].copy()
        except:
            self.gsp_demand_filtered['demand'] = self.gsp_demand_filtered['26/27'].copy()
        finally:
            self.gsp_demand_filtered.dropna(subset='demand').reset_index(inplace=True)

    def combine_tec_ic_registers(self):
        tec_register_year_filtered_ = self.tec_register_year_filtered.rename(
            columns={'MW Effective': 'MW Effective - Import'})
        tec_register_year_filtered_['MW Effective - Export'] = 0
        all_gen_register = pd.concat([tec_register_year_filtered_, self.ic_register_year_filtered], ignore_index=True)
        all_gen_register['Force MW Dispatch'] = 0
        all_gen_register = all_gen_register[
            ['Generator Name', 'HOST TO', 'Plant Type', 'Gen_Type', 'Ranking', 'Apportion', 'bus_id',
             'MW Effective - Import', 'MW Effective - Export', 'Force MW Dispatch']]
        all_gen_register.sort_values(by='Ranking', inplace=True)
        all_gen_register.reset_index(drop=True, inplace=True)

        self.all_gen_register = all_gen_register

    # code to determine initial dispatch setting for tec and ic
    def determine_initial_dispatch_setting(self):
        def calculate_demand_target():
            demand_total = self.gsp_demand_filtered['demand'].sum()
            return demand_total

        def calculate_b6_transfer_max():
            b6_transfer_max = self.intra_hvdc.loc[self.intra_hvdc['MW Effective From'] <= self.year, 'B6_Limit'].max()
            return b6_transfer_max

        # NEED TO ADD CODE TO ACCOUNT FOR FORCE MW DISPATCH
        def set_gen_mw_dispatch():
            def create_max_dispatchable_col(row):
                # split the apportionment into each component separated by semicolon.
                # Each row may have a different number of apportionments - NEED REVIEWING.
                # multiply apportionment by MW Effective - Import or Export if apportionment <0
                values = map(float, row['Apportion'].split(';'))  # Split and convert to float
                multiplied_values = [
                    value * (row['MW Effective - Import'] if value >= 0 else row['MW Effective - Export']) for value in
                    values]
                return multiplied_values

            self.all_gen_register['Max Dispatchable'] = self.all_gen_register.apply(create_max_dispatchable_col, axis=1)

            number_scenarios = len(self.all_gen_register['Apportion'].iloc[0].split(';'))
            self.all_gen_register['MW Dispatch'] = [[0] * number_scenarios for _ in range(len(self.all_gen_register))]

            b6_transfer_max = calculate_b6_transfer_max()

            b6_effective_values = []

            for num in range(number_scenarios):
                demand_total = calculate_demand_target()
                remaining_demand = demand_total
                b6_effective_value_total = 0
                b6_effective_value_total_clipped = np.clip(b6_effective_value_total, 0, b6_transfer_max)
                for rank in sorted(self.all_gen_register['Ranking'].unique()):
                    rank_df = self.all_gen_register[self.all_gen_register['Ranking'] == rank]
                    try:
                        b6_effective_capacity = rank_df[rank_df['Gen_Type'] == "Wind"]['Max Dispatchable'].apply(
                            lambda x: x[num]).sum()
                    except ValueError:
                        b6_effective_capacity = 0
                    b6_effective_value = 0.3758 * b6_effective_capacity
                    value = (b6_transfer_max - b6_effective_value_total_clipped) if (
                                                                                                b6_effective_value_total_clipped + b6_effective_value) > b6_transfer_max else b6_effective_value
                    total_effective_for_scenario = rank_df['Max Dispatchable'].apply(lambda x: x[num]).sum() + (
                        value if self.scotland_reduced else 0)
                    if remaining_demand >= total_effective_for_scenario:
                        b6_effective_value_total += b6_effective_value
                        for index, row in rank_df.iterrows():
                            self.all_gen_register.at[index, 'MW Dispatch'][num] = row['Max Dispatchable'][num]
                        remaining_demand -= total_effective_for_scenario
                    else:
                        proportion = remaining_demand / total_effective_for_scenario
                        b6_effective_value_total += (b6_effective_value * proportion)
                        for index, row in rank_df.iterrows():
                            dispatch_value = round(row['Max Dispatchable'][num] * proportion, 1)
                            self.all_gen_register.at[index, 'MW Dispatch'][num] = dispatch_value
                        break  # stop processing as demand has been met.
                b6_effective_values.append(np.clip(b6_effective_value_total, 0, b6_transfer_max))
            return b6_effective_values

        def set_b6_transfer():
            b6_effective_values = set_gen_mw_dispatch()
            self.intra_hvdc['MW Dispatch'] = [[0, 0, 0] for _ in range(len(self.intra_hvdc))]

            # create gens at HARK and STEW border nodes and append to gen_register
            hark_border_nodes_bus_id = []
            stew_border_nodes_bus_id = []
            for bus_name in self.bus_ids_df['Name']:
                selected_rows = self.bus_ids_df[self.bus_ids_df['Name'] == bus_name]
                if not selected_rows.empty:
                    if bus_name in ['HAKB4-', 'HAKB4B']:
                        bus_id = selected_rows['index'].values[0]
                        hark_border_nodes_bus_id.append(bus_id)
                    elif bus_name in ['STWB4Q', 'STWB4R']:
                        bus_id = selected_rows['index'].values[0]
                        stew_border_nodes_bus_id.append(bus_id)

            b6_remaining = []

            for value in range(len(b6_effective_values)):
                b6_total = b6_effective_values[value]
                b6_left = b6_total
                for index, row in self.intra_hvdc.iterrows():
                    if row['MW Effective From'] <= self.year:
                        dispatch = np.clip(b6_total * 0.3, 0, min(row['Summer Rating (MVA)'], b6_left))
                        self.intra_hvdc.at[index, 'MW Dispatch'][value] = int(dispatch)
                        b6_left -= dispatch
                b6_remaining.append(b6_left)

            for index, row in self.intra_hvdc.iterrows():
                if row['MW Effective From'] <= self.year:
                    self.all_gen_register = pd.concat([self.all_gen_register, pd.DataFrame([{
                        'Generator Name': f"{str(row['Interconnector Name'])}",
                        'HOST TO': 'NGET',
                        'Plant Type': 'B6_Transfer_DC',
                        'Gen_Type': 'B6_Transfer_DC',
                        'bus_id': [row['bus_id']],
                        'MW Dispatch': row['MW Dispatch']}])], ignore_index=True)

            for bus_id in hark_border_nodes_bus_id:
                b6_effective_values_hark = [int(item * (0.44 / len(hark_border_nodes_bus_id))) for item in
                                            b6_remaining]
                self.all_gen_register = pd.concat([self.all_gen_register, pd.DataFrame([{
                    'Generator Name': f"HARK Border Node {str(hark_border_nodes_bus_id.index(bus_id))}",
                    'HOST TO': 'NGET',
                    'Plant Type': 'B6_Transfer_AC',
                    'Gen_Type': 'B6_Transfer_AC',
                    'bus_id': [bus_id],
                    'MW Dispatch': b6_effective_values_hark}])], ignore_index=True)

            for bus_id in stew_border_nodes_bus_id:
                b6_effective_values_stew = [int(item * (0.56 / len(hark_border_nodes_bus_id))) for item in
                                            b6_remaining]
                self.all_gen_register = pd.concat([self.all_gen_register, pd.DataFrame([{
                    'Generator Name': f"STEW Border Node {str(stew_border_nodes_bus_id.index(bus_id))}",
                    'HOST TO': 'NGET',
                    'Plant Type': 'B6_Transfer_AC',
                    'Gen_Type': 'B6_Transfer_AC',
                    'bus_id': [bus_id],
                    'MW Dispatch': b6_effective_values_stew}])], ignore_index=True)

            print('x[0]', self.all_gen_register['MW Dispatch'].apply(lambda x: x[0]).sum())
            print('x[1]', self.all_gen_register['MW Dispatch'].apply(lambda x: x[1]).sum())
            print('x[2]', self.all_gen_register['MW Dispatch'].apply(lambda x: x[2]).sum())
            return self.all_gen_register

        set_b6_transfer() if self.scotland_reduced else None

    def create_pandapower_system(self):
        # PERHAPS CREATE CLASS HERE AND PASS SELF.NET
        def create_net():
            net = pp.create_empty_network()
            self.net = net
            # return net

        # net = create_net()
        # self.net = net

        def create_bus():
            # create bus nodes for net
            # nice to have - add zone information
            for index, row in self.bus_ids_df.iterrows():
                voltage_level = row['Voltage (kV)']
                bus_name = row['Name']
                index = row['index']
                type_of_bus = 'b'  # “n” - node; “b” - busbar; “m” - muff
                in_service = True
                min_bus_v = 0.95
                max_bus_v = 1.05
                geodata = None
                zone = None
                pp.create_bus(self.net, vn_kv=voltage_level, name=bus_name, index=index, geodata=geodata,
                              type=type_of_bus,
                              zone=zone,
                              in_service=in_service, min_vm_pu=min_bus_v, max_vm_pu=max_bus_v)

        def create_lines():
            # create circuits, impedances and TCSC's for net
            for index, row in self.all_circuits_year_filtered.iterrows():
                name = f"{row['Node 1']}-{row['Node 2']} ({row['Circuit Type']})"
                from_bus = row['Node 1 bus_id']
                to_bus = row['Node 2 bus_id']
                length_km = row['OHL Length (km)'] + row['Cable Length (km)'] if row['OHL Length (km)'] + row[
                    'Cable Length (km)'] > 0 else 1
                base_voltage = row['Voltage (kV) Node 1']
                base_impedance = (base_voltage ** 2) / 100.0
                max_i_ka = row['Summer Rating (MVA)'] / ((3 ** 0.5) * base_voltage)
                if not any(type in row['Circuit Type'] for type in
                           ['SSSC', 'Series Capacitor', 'Series Reactor', 'Zero Length']):
                    r_ohm_per_km = length_km and (row['R (% on 100MVA)'] * base_impedance / (
                            100 * length_km)) or 0.0001  # divide by 100 to convert % value to per unit value
                    x_ohm_per_km = length_km and (row['X (% on 100MVA)'] * base_impedance / (
                            100 * length_km)) or 0.0001  # divide by 100 to convert % value to per unit value
                    c_nf_per_km = length_km and ((
                                                         row['B (% on 100MVA)'] / ((
                                                                                           base_voltage ** 2) * 2 * 3.14159265359 * 50 * length_km)) * 10 ** 9) or 10
                    pp.create_line_from_parameters(self.net, from_bus=from_bus, to_bus=to_bus, length_km=length_km,
                                                   r_ohm_per_km=r_ohm_per_km, x_ohm_per_km=x_ohm_per_km,
                                                   c_nf_per_km=c_nf_per_km, max_i_ka=max_i_ka, name=name)
                elif any(type in row['Circuit Type'] for type in ['Series Reactor', 'Zero Length']):
                    r_pu = row['R (% on 100MVA)'] and row['R (% on 100MVA)'] * 100 or 0.0001
                    x_pu = row['X (% on 100MVA)'] and row['X (% on 100MVA)'] * 100 or 0.0001
                    sn_mva = row['Summer Rating (MVA)']
                    pp.create_impedance(self.net, from_bus=from_bus, to_bus=to_bus, rft_pu=r_pu, xft_pu=x_pu,
                                        sn_mva=sn_mva, rtf_pu=r_pu, xtf_pu=x_pu, name=name)

                elif any(type in row['Circuit Type'] for type in ['Series Capacitor', 'SSSC']):
                    # IF AC POWER FLOW USE BELOW:
                    # x_l_ohm = 0
                    # x_cvar_ohm = (row['X (% on 100MVA)'] * base_impedance /
                    #             100) or 0.0001  # divide by 100 to convert % value to per unit value
                    # set_p_to_mw = row['Summer Rating (MVA)'] * 0.839
                    # thyristor_firing_angle_degree = 55 # 55 degrees (capacitive mode) used as placeholder
                    # pp.create.create_tcsc(self.net, from_bus=from_bus, to_bus=to_bus, x_l_ohm=x_l_ohm, x_cvar_ohm=x_cvar_ohm,
                    #                       set_p_to_mw=set_p_to_mw, thyristor_firing_angle_degree=thyristor_firing_angle_degree,
                    #                       name=name, controllable=False)
                    pp.create_impedance(self.net, from_bus=from_bus, to_bus=to_bus, rft_pu=0.0001, xft_pu=0.0001,
                                        sn_mva=99999, rtf_pu=0.0001, xtf_pu=0.0001, name=name)

        def create_transformers():
            # create transformers for net
            for index, row in self.all_trafo_year_filtered.iterrows():
                name = f"{row['Node 1']}-{row['Node 2']} (Transformer)"
                hv_bus = row['Node 1 bus_id']
                lv_bus = row['Node 2 bus_id']
                sn_mva = row['Winter Rating (MVA)']
                vn_hv_kv = row['Voltage (kV) Node 1']
                vn_lv_kv = row['Voltage (kV) Node 2']
                vkr_percent = row['R (% on 100MVA)']
                vk_percent = max(5, min(35, row['X (% on 100MVA)']))  # set bounds of 5-35% on X.
                pfe_kw = 0
                i0_percent = 0
                pp.create_transformer_from_parameters(self.net, hv_bus=hv_bus, lv_bus=lv_bus, sn_mva=sn_mva,
                                                      vn_hv_kv=vn_hv_kv, vn_lv_kv=vn_lv_kv, vkr_percent=vkr_percent,
                                                      vk_percent=vk_percent, pfe_kw=pfe_kw, i0_percent=i0_percent,
                                                      name=name)

        def create_demand():
            # create demand for net
            for index, row in self.gsp_demand_filtered.iterrows():
                name = f"{row['Node']} (Demand)"
                bus = row['bus_id']
                p_mw = row['demand']
                q_mvar = p_mw * -0.1  # 10% mvar injection applied based on average winter P/Q ratio
                pp.create_load(self.net, bus=bus, p_mw=p_mw, q_mvar=q_mvar, const_z_percent=0, const_i_percent=0,
                               name=name,
                               scaling=1)

        def create_gen():
            # NEED TO ENSURE BUS ID IS SORTED IN ORDER OF VOLTAGE OR CORRECT BUS ID IS DEFINED IN BUS_ID COLUMN
            scaling = self.gsp_demand_filtered['demand'].sum() / self.all_gen_register['MW Dispatch'].apply(
                lambda x: x[0]).sum()
            for index, row in self.all_gen_register.iterrows():
                name = f"{row['Generator Name']}"
                bus = row['bus_id'][0]  # referring only to the first value in bus_id column in gen register.
                type = row['Gen_Type']
                p_mw = row['MW Dispatch'][0]  # referring only to the first value in bus_id column in gen register.
                if p_mw >= 0:
                    max_p_mw = row['MW Effective - Import'] if isinstance(row['MW Effective - Import'],
                                                                          (int, float)) else 9999
                    pp.create_sgen(self.net, bus=bus, p_mw=p_mw, q_mvar=0, name=name, type=type, scaling=scaling,
                                   in_service=True, max_p_mw=max_p_mw)
                else:
                    pp.create_load(self.net, bus=bus, p_mw=p_mw, q_mvar=0, const_z_percent=0, const_i_percent=0,
                                   name=name,
                                   scaling=scaling)

        def create_slack_gen():
            # create external grid to serve if scotland reduced
            for bus_name in self.bus_ids_df['Name']:
                if bus_name == 'HEYS41':
                    bus_id = self.bus_ids_df[self.bus_ids_df['Name'] == bus_name]['index'].values[0]
                    pp.create_ext_grid(self.net, bus=bus_id, vm_pu=1, va_degree=0,
                                       name='Slack_Bus')  # HEYS41 index 309 bus selected for slack

        def create_full_network():
            create_net()
            create_bus()
            create_lines()
            create_transformers()
            create_demand()
            create_gen()
            create_slack_gen()
            return self.net

        self.net = create_full_network()

    def get_imbalance(self):
        pp.rundcpp(self.net, numba=False)
        slack_gen = self.net['res_ext_grid']['p_mw']
        print(slack_gen)

        # net1 = copy.deepcopy(self.net)
        # pp.rundcpp(net1, numba=False)
        # slack_gen1 = net1['res_ext_grid']['p_mw']
        # print(slack_gen1)

    def run_analysis(self):
        def check_convergence():
            pass

    def key_stats(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ic_register_year_filtered.to_csv(os.path.join(project_root, 'delete', 'ic_register_year_filtered.csv'))
        self.tec_register_year_filtered.to_csv(os.path.join(project_root, 'delete', 'tec_register_year_filtered.csv'))
        self.all_trafo_year_filtered.to_csv(os.path.join(project_root, 'delete', 'all_trafo_year_filtered.csv'))
        self.all_circuits_year_filtered.to_csv(os.path.join(project_root, 'delete', 'all_circuits_year_filtered.csv'))
        self.gsp_demand_filtered.to_csv(os.path.join(project_root, 'delete', 'gsp_demand_filtered.csv'))
        self.all_gen_register.to_csv(os.path.join(project_root, 'delete', 'all_gen_register.csv'))
        pp.to_excel(self.net, os.path.join(project_root, 'delete', 'net_pp.xlsx'))


if __name__ == "__main__":
    call = DefineData()
    call.filter_network_data(2028)
    call.filter_tec_ic_data()
    call.filter_demand_data()
    call.combine_tec_ic_registers()
    call.determine_initial_dispatch_setting()
    call.create_pandapower_system()
    call.get_imbalance()
    call.run_analysis()
    call.key_stats()