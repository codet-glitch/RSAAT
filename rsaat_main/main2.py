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

class DefineData:
    def __init__(self, year):
        self.year = year

    def filter_network_data(self):
        # apply year filter to GB data
        def apply_circuit_changes(all_circuits, all_circuits_changes):
            for index, row in all_circuits_changes.iterrows():
                status = row['Status']
                all_circuits_changes = all_circuits_changes[all_circuits_changes['Year'] <= self.year]
                if 'addition' in status.lower():
                    all_circuits = pd.concat([all_circuits, row], ignore_index=True)
                elif 'remove' in status.lower():
                    for index1, row1 in all_circuits.iterrows():
                        if (row1['Node 1'] == row['Node 1']) & (row1['Node 2'] == row['Node 2']):
                            all_circuits.drop(index1, inplace=True)
                            break
                elif 'change' in status.lower():
                    for index2, row2 in all_circuits.iterrows():
                        if (row2['Node 1'] == row['Node 1']) & (row2['Node 2'] == row['Node 2']):
                            all_circuits.drop(index2, inplace=True)
                            all_circuits = pd.concat([all_circuits, row], ignore_index=True)
                            break
                else:
                    print("Warning: Status of row " + str(
                        index) + " in Circuit Changes data needs checking. Ignored from for loop.")
            return all_circuits

        all_circuits_year_filtered = apply_circuit_changes(all_circuits, all_circuits_changes)

        # create transformer dataframe for Great Britain including changes
        def apply_trafo_changes(all_trafo, all_trafo_changes):
            for index, row in all_trafo_changes.iterrows():
                status = row['Status']
                all_trafo_changes = all_trafo_changes[all_trafo_changes['Year'] <= self.year]
                if 'addition' in status.lower():
                    all_trafo = pd.concat([all_trafo, row], ignore_index=True)
                elif 'remove' in status.lower():
                    for index1, row1 in all_trafo.iterrows():
                        if (row1['Node 1'] == row['Node 1']) & (row1['Node 2'] == row['Node 2']):
                            all_trafo.drop(index1, inplace=True)
                            break
                elif 'change' in status.lower():
                    for index2, row2 in all_trafo.iterrows():
                        if (row2['Node 1'] == row['Node 1']) & (row2['Node 2'] == row['Node 2']):
                            all_trafo.drop(index2, inplace=True)
                            all_trafo = pd.concat([all_trafo, row], ignore_index=True)
                            break
                else:
                    print("Warning: Status of row " + str(
                        index) + " in Transformer Changes data needs checking. Ignored from for loop.")
            return all_trafo

        all_trafo_year_filtered = apply_trafo_changes(all_trafo, all_trafo_changes)


    def filter_tec_ic_data(self):
        tec_register_year_filtered = tec_register[tec_register['MW Effective From'].dt.year <= int(self.year)]
        ic_register_year_filtered = ic_register[ic_register['MW Effective From'].dt.year <= int(self.year)]

    def filter_demand_data(self):
        pass

    def create_pandapower_system(self):
        pass

    def get_imbalance(self):
        pass

    def delete_gen_demand(self):
        pass

    def run_analysis(self):
        pass

