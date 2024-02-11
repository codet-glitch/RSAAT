import pandapower as pp
import pandas as pd
import numpy as np
import streamlit as st
import re
from datetime import datetime
import network_data_test


# import openpyxl
# import requests
# import json
# from PIL import Image

class DefineData(network_data_test.TransformData):
    def __init__(self, year: int):
        super().__init__()

        self.import_network_data()
        self.import_tec_ic_demand_data()
        self.create_bus_id()
        self.transform_network_data()
        self.transform_tec_ic_data()
        self.transform_demand_data()

        self.year = year

        self.ic_register_year_filtered = None
        self.tec_register_year_filtered = None
        self.all_trafo_year_filtered = None
        self.all_circuits_year_filtered = None
        self.gsp_demand_filtered = None
        self.net = None

    # apply year filter to GB data
    def filter_network_data(self):
        # filter circuit data by self.year
        def apply_circuit_changes():
            self.all_circuits_changes = self.all_circuits_changes[
                pd.to_numeric(self.all_circuits_changes['Year'], errors='coerce') <= self.year]
            for index, row in self.all_circuits_changes.iterrows():
                status = row['Status']
                if 'addition' in status.lower():
                    # Convert row to DataFrame before concatenating
                    row_df = pd.DataFrame([row])
                    self.all_circuits = pd.concat([self.all_circuits, row_df], ignore_index=True)
                elif 'remove' in status.lower():
                    for index1, row1 in self.all_circuits.iterrows():
                        if (row1['Node 1'] == row['Node 1']) & (row1['Node 2'] == row['Node 2']):
                            self.all_circuits.drop(index1, inplace=True)
                            break
                elif 'change' in status.lower():
                    for index2, row2 in self.all_circuits.iterrows():
                        if (row2['Node 1'] == row['Node 1']) & (row2['Node 2'] == row['Node 2']):
                            self.all_circuits.drop(index2, inplace=True)
                            # Convert row to DataFrame before concatenating
                            row_df = pd.DataFrame([row])
                            self.all_circuits = pd.concat([self.all_circuits, row_df], ignore_index=True)
                            break
                else:
                    print(f"Warning: Status of row {index} "
                          f"in Circuit Changes data needs checking. Ignored from 'for' loop.")
            return self.all_circuits

        self.all_circuits_year_filtered = apply_circuit_changes()

        # filter transformer data by self.year
        def apply_trafo_changes():
            self.all_trafo_changes = self.all_trafo_changes[
                pd.to_numeric(self.all_trafo_changes['Year'], errors='coerce') <= self.year]
            for index, row in self.all_trafo_changes.iterrows():
                status = row['Status']
                if 'addition' in status.lower():
                    row_df = pd.DataFrame([row])
                    self.all_trafo = pd.concat([self.all_trafo, row_df], ignore_index=True)
                elif 'remove' in status.lower():
                    for index1, row1 in self.all_trafo.iterrows():
                        if (row1['Node 1'] == row['Node 1']) & (row1['Node 2'] == row['Node 2']):
                            self.all_trafo.drop(index1, inplace=True)
                            break
                elif 'change' in status.lower():
                    for index2, row2 in self.all_trafo.iterrows():
                        if (row2['Node 1'] == row['Node 1']) & (row2['Node 2'] == row['Node 2']):
                            self.all_trafo.drop(index2, inplace=True)
                            row_df = pd.DataFrame([row])
                            self.all_trafo = pd.concat([self.all_trafo, row_df], ignore_index=True)
                            break
                else:
                    print(f"Warning: Status of row {index} "
                          f"in Transformer Changes data needs checking. Ignored from 'for' loop.")
            return self.all_trafo

        self.all_trafo_year_filtered = apply_trafo_changes()

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
        self.gsp_demand_filtered.dropna(subset='demand', inplace=True)

    # code to determine initial dispatch setting for tec and ic
    def determine_initial_dispatch_setting(self):
        def calculate_demand_target():
            if self.scotland_reduced:
                pass
            else:
                pass

        def define_b6_transfer():
            if self.scotland_reduced:
                def find_boundary_nodes():
                    pass

                def add_boundary_nodes():
                    pass
            else:
                pass

        def set_mw_dispatch():
            pass

    # code to make any adjustments to mw_setpoint of tec or reduce demand ahead of creating pandapower model
    def balance_demand_generation(self):
        total_generation = self.tec_register_year_filtered['mw_setpoint'].sum() + self.ic_register_year_filtered['mw_setpoint'].sum()
        total_demand = self.gsp_demand_filtered['demand'].sum()
        b6_limit = None
        if abs(total_generation-total_demand) > 500:
            if total_generation > total_demand:
                x = total_generation - total_demand
                x1 = x / self.tec_register_year_filtered['mw_setpoint'].sum()
                self.tec_register_year_filtered['mw_setpoint'] += self.tec_register_year_filtered['mw_setpoint'] * x1
            else:
                x = total_demand - total_generation
                x1 = x / self.gsp_demand_filtered['demand'].sum()
                self.gsp_demand_filtered['demand'] += self.gsp_demand_filtered['demand'] * x1

    def create_pandapower_system(self):
        net = pp.create_empty_network()

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
            pp.create_bus(net, vn_kv=voltage_level, name=bus_name, index=index, geodata=geodata, type=type_of_bus,
                          zone=zone,
                          in_service=in_service, min_vm_pu=min_bus_v, max_vm_pu=max_bus_v)

        # create circuits, impedances and TCSC's for net
        for index, row in self.all_circuits_year_filtered.iterrows():
            name = f"{row['Node 1']}-{row['Node 2']} ({row['Circuit Type']})"
            from_bus = row['Node 1 bus_id']
            to_bus = row['Node 2 bus_id']
            length_km = row['OHL Length (km)'] + row['Cable Length (km)'] if row['OHL Length (km)'] + row['Cable Length (km)'] > 0 else 1
            base_voltage = row['Voltage (kV) Node 1']
            base_impedance = (base_voltage ** 2) / 100.0
            max_i_ka = row['Summer Rating (MVA)'] / ((3 ** 0.5) * base_voltage)
            if not any(type in row['Circuit Type'] for type in ['SSSC', 'Series Capacitor', 'Series Reactor', 'Zero Length']):
                r_ohm_per_km = length_km and (row['R (% on 100MVA)'] * base_impedance / (
                            100 * length_km)) or 0.0001  # divide by 100 to convert % value to per unit value
                x_ohm_per_km = length_km and (row['X (% on 100MVA)'] * base_impedance / (
                            100 * length_km)) or 0.0001  # divide by 100 to convert % value to per unit value
                c_nf_per_km = length_km and ((
                            row['B (% on 100MVA)'] / ((base_voltage ** 2) * 2 * 3.14159265359 * 50 * length_km)) * 10 ** 9) or 10
                pp.create_line_from_parameters(net, from_bus=from_bus, to_bus=to_bus, length_km=length_km,
                                               r_ohm_per_km=r_ohm_per_km, x_ohm_per_km=x_ohm_per_km,
                                               c_nf_per_km=c_nf_per_km, max_i_ka=max_i_ka, name=name)
            elif any(type in row['Circuit Type'] for type in ['Series Reactor', 'Zero Length']):
                r_pu = row['R (% on 100MVA)'] and row['R (% on 100MVA)'] * 100 or 0.0001
                x_pu = row['X (% on 100MVA)'] and row['X (% on 100MVA)'] * 100 or 0.0001
                sn_mva = row['Summer Rating (MVA)']
                pp.create_impedance(net, from_bus=from_bus, to_bus=to_bus, rft_pu=r_pu, xft_pu=x_pu,
                                    sn_mva=sn_mva, rtf_pu=r_pu, xtf_pu=x_pu, name=name)

            elif any(type in row['Circuit Type'] for type in ['Series Capacitor', 'SSSC']):
                x_l_ohm = 0
                x_cvar_ohm = (row['X (% on 100MVA)'] * base_impedance /
                            100) or 0.0001  # divide by 100 to convert % value to per unit value
                set_p_to_mw = row['Summer Rating (MVA)'] * 0.839
                thyristor_firing_angle_degree = 55 # 55 degrees (capacitive mode) used as placeholder
                pp.create.create_tcsc(net, from_bus=from_bus, to_bus=to_bus, x_l_ohm=x_l_ohm, x_cvar_ohm=x_cvar_ohm,
                                      set_p_to_mw=set_p_to_mw, thyristor_firing_angle_degree=thyristor_firing_angle_degree,
                                      name=name, controllable=False)

        # create transformers for net
        for index, row in self.all_trafo_year_filtered.iterrows():
            name = f"{row['Node 1']}-{row['Node 2']} (Transformer)"
            hv_bus = row['Node 1 bus_id']
            lv_bus = row['Node 2 bus_id']
            sn_mva = row['Winter Rating (MVA)']
            vn_hv_kv = row['Voltage (kV) Node 1']
            vn_lv_kv = row['Voltage (kV) Node 2']
            vkr_percent = row['R (% on 100MVA)']
            vk_percent = max(5, min(35, row['X (% on 100MVA)']))
            pfe_kw = 0
            i0_percent = 0
            pp.create_transformer_from_parameters(net, hv_bus=hv_bus, lv_bus=lv_bus, sn_mva=sn_mva,
                                                  vn_hv_kv=vn_hv_kv, vn_lv_kv=vn_lv_kv, vkr_percent=vkr_percent,
                                                  vk_percent=vk_percent, pfe_kw=pfe_kw, i0_percent=i0_percent, name=name)

        # create generation from tec reg for net
        # NEED TO ENSURE BUS ID IS SORTED IN ORDER OF VOLTAGE OR CORRECT BUS ID IS DEFINED IN BUS_ID COLUMN
        for index, row in self.tec_register_year_filtered.iterrows():
            name = f"{row['Generator Name']} (Gen)"
            bus = row['bus_id'][0]
            type = row['Gen_Type']
            max_p_mw = row['MW Effective']
            scaling = 1
            p_mw = abs(row['mw_setpoint'])
            pp.create_sgen(net, bus=bus, p_mw=p_mw, q_mvar=0, name=name, type=type, scaling=scaling,
                           in_service=True, max_p_mw=max_p_mw)

        # create generation from ic reg for net
        for index, row in self.ic_register_year_filtered.iterrows():
            name = f"{row['Generator Name']} (IC)"
            bus = row['bus_id'][0]
            type = row['Gen_Type']
            scaling = 1
            p_mw = abs(row['mw_setpoint'])
            if row['mw_setpoint'] >= 0:
                max_p_mw = row['MW Import - Total']
                pp.create_sgen(net, bus=bus, p_mw=p_mw, q_mvar=0, name=name, type=type, scaling=scaling,
                               in_service=True, max_p_mw=max_p_mw)
            else:
                max_d_mw = row['MW Export - Total']
                pp.create_load(net, bus=bus, p_mw=p_mw, q_mvar=0, const_z_percent=0, const_i_percent=0, name=name,
                           scaling=1)

        # create demand for net
        for index, row in self.gsp_demand_filtered.iterrows():
            name = f"{row['Node']} (Demand)"
            bus = row['bus_id']
            p_mw = row['demand']
            q_mvar = p_mw * -0.1 # 10% mvar spill applied based on average winter P/Q ratio
            pp.create_load(net, bus=bus, p_mw=p_mw, q_mvar=q_mvar, const_z_percent=0, const_i_percent=0, name=name,
                           scaling=1)

        # create external grid to serve if scotland reduced
        pp.create_ext_grid(net, bus=309, vm_pu=1, va_degree=0, name='Slack_Bus') # HEYS41 bus selected for slack

        self.net = net

    def get_imbalance(self):
        pass

    def run_analysis(self):
        pass

    def key_stats(self):
        delete = '../delete/'
        self.ic_register_year_filtered.to_csv(delete + 'ic_register_year_filtered.csv')
        self.tec_register_year_filtered.to_csv(delete + 'tec_register_year_filtered.csv')
        self.all_trafo_year_filtered.to_csv(delete + 'all_trafo_year_filtered.csv')
        self.all_circuits_year_filtered.to_csv(delete + 'all_circuits_year_filtered.csv')
        self.gsp_demand_filtered.to_csv(delete + 'gsp_demand_filtered.csv')
        pp.to_excel(self.net, delete + 'net_pp.xlsx')


if __name__ == "__main__":
    call = DefineData(2028)
    call.filter_network_data()
    call.filter_tec_ic_data()
    call.filter_demand_data()
    call.determine_initial_dispatch_setting()
    call.balance_demand_generation()
    call.create_pandapower_system()
    call.get_imbalance()
    call.run_analysis()
    call.key_stats()
