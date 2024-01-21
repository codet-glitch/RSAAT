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

        self.ic_register_year_filtered = None
        self.tec_register_year_filtered = None
        self.all_trafo_year_filtered = None
        self.all_circuits_year_filtered = None
        self.year = year

    def filter_network_data(self):
        # apply year filter to GB data
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
                    print(
                        f"Warning: Status of row {index} in Circuit Changes data needs checking. Ignored from 'for' loop.")
            return self.all_circuits

        self.all_circuits_year_filtered = apply_circuit_changes()

        # create transformer dataframe for Great Britain including changes
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
                    print("Warning: Status of row " + str(
                        index) + " in Transformer Changes data needs checking. Ignored from for loop.")
            return self.all_trafo

        self.all_trafo_year_filtered = apply_trafo_changes()

    def filter_tec_ic_data(self):
        self.tec_register = self.tec_register[self.tec_register['bus_id'] != ""]
        self.ic_register = self.ic_register[self.ic_register['bus_id'] != ""]
        self.tec_register_year_filtered = self.tec_register[
            self.tec_register['MW Effective From'].apply(lambda x: x.year <= int(self.year))]
        self.ic_register_year_filtered = self.ic_register[
            self.ic_register['MW Effective From'].apply(lambda x: x.year <= int(self.year))]

    def filter_demand_data(self):
        self.gsp_demand_filtered = self.gsp_demand[self.gsp_demand['bus_id'] != ""]
        try:
            selected_column = [col for col in self.gsp_demand_filtered.columns if col.startswith(str(int(self.year))[-2:])]
            self.gsp_demand_filtered['demand'] = self.gsp_demand_filtered[selected_column[0]].copy()
        except:
            self.gsp_demand_filtered['demand'] = self.gsp_demand_filtered['26/27'].copy()
        self.gsp_demand_filtered.dropna(subset='demand', inplace=True)

    def create_pandapower_system(self):
        net = pp.create_empty_network()

        for index, row in self.bus_ids_df.iterrows():
            voltage_level = row["Voltage (kV)"]
            bus_name = row["Name"]
            index = row["index"]
            # geodata = row["geodata"]
            pp.create_bus(net, vn_kv=voltage_level, name=bus_name, index=index, type="b", zone=None,
                          in_service=True, max_vm_pu=1.05, min_vm_pu=0.95)

        for index, row in self.all_circuits_year_filtered.iterrows():
            pass
            pp.create_line_from_parameters(net, from_bus=, to_bus=, length_km=,
                                           r_ohm_per_km=, x_ohm_per_km=,
                                           c_nf_per_km=, max_i_ka=, name=)

        for index, row in self.all_circuits_year_filtered.iterrows():
            pass
            pp.create_impedance(net, from_bus=, to_bus=, rft_pu=, xft_pu=, rtf_pu=,
                                xtf_pu=, sn_mva=, name=, in_service=True)

        for index, row in self.all_trafo_year_filtered.iterrows():
            pass
            pp.create_transformer_from_parameters(net, hv_bus=, lv_bus=, sn_mva=,
                                                  vn_hv_kv=, vn_lv_kv=, vkr_percent=,
                                                  vk_percent=, pfe_kw=, i0_percent=, name=)

        for index, row in self.gsp_demand_filtered.iterrows():
            pass
            pp.create_load(net, bus=, p_mw=, q_mvar=, const_z_percent=0, const_i_percent=0, name=,
                           scaling=1, in_service=True)

        for index, row in self.tec_register_year_filtered.iterrows():
            pass
            pp.create_sgen(net, bus=, p_mw=, q_mvar=0, name=, type=, scaling=1,
                           in_service=True, max_p_mw=)

        for index, row in self.ic_register_year_filtered.iterrows():
            pass
            pp.create_load(net, bus=, p_mw=, q_mvar=, const_z_percent=0, const_i_percent=0, name=,
                           scaling=1, in_service=True)

        for index, row in self.ic_register_year_filtered.iterrows():
            pass
            pp.create_sgen(net, bus=, p_mw=, q_mvar=0, name=, type=, scaling=1,
                           in_service=True, max_p_mw=)

        pp.create_ext_grid(net, bus=, vm_pu=1, va_degree=0, name='Slack_Bus', in_service=True)

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


# if __name__ == "__main__":
call = DefineData(2028)
call.filter_network_data()
call.filter_tec_ic_data()
call.filter_demand_data()
call.create_pandapower_system()
call.get_imbalance()
call.run_analysis()
call.key_stats()