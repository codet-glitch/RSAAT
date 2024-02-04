import json
import re
import sys
import pandas as pd
from datetime import datetime
import openpyxl
import requests


class TransformData:
    def __init__(self, api_or_local='local'):
        self.gsp_demand = None
        self.ic_register = None
        self.tec_register = None
        self.all_trafo_changes = None
        self.all_trafo = None
        self.all_circuits_changes = None
        self.all_circuits = None
        self.bus_ids_df = None
        self.network_df_dict_subs = None
        self.network_df_dict_comp = None

        self.api_or_local = api_or_local

    def import_network_data(self, scotland_reduced):
        sub_coordinates = pd.read_csv('../data/CRM_Sub_Coordinates_WGS84.csv').dropna(inplace=True)

        etys_file_name = '../data/Appendix B 2022.xlsx'

        shet_substations = pd.read_excel(etys_file_name, sheet_name="B-1-1a", skiprows=[0])
        spt_substations = pd.read_excel(etys_file_name, sheet_name="B-1-1b", skiprows=[0])
        nget_substations = pd.read_excel(etys_file_name, sheet_name="B-1-1c", skiprows=[0])
        ofto_substations = pd.read_excel(etys_file_name, sheet_name="B-1-1d", skiprows=[0])

        shet_circuits = pd.read_excel(etys_file_name, sheet_name="B-2-1a", skiprows=[0])
        shet_circuit_changes = pd.read_excel(etys_file_name, sheet_name="B-2-2a", skiprows=[0])
        shet_tx = pd.read_excel(etys_file_name, sheet_name="B-3-1a", skiprows=[0])
        shet_tx_changes = pd.read_excel(etys_file_name, sheet_name="B-3-2a", skiprows=[0])

        spt_circuits = pd.read_excel(etys_file_name, sheet_name="B-2-1b", skiprows=[0])
        spt_circuit_changes = pd.read_excel(etys_file_name, sheet_name="B-2-2b", skiprows=[0])
        spt_tx = pd.read_excel(etys_file_name, sheet_name="B-3-1b", skiprows=[0])
        spt_tx_changes = pd.read_excel(etys_file_name, sheet_name="B-3-2b", skiprows=[0])

        nget_circuits = pd.read_excel(etys_file_name, sheet_name="B-2-1c", skiprows=[0])
        nget_circuit_changes = pd.read_excel(etys_file_name, sheet_name="B-2-2c", skiprows=[0])
        nget_tx = pd.read_excel(etys_file_name, sheet_name="B-3-1c", skiprows=[0])
        nget_tx_changes = pd.read_excel(etys_file_name, sheet_name="B-3-2c", skiprows=[0])

        ofto_circuits = (pd.read_excel(etys_file_name, sheet_name="B-2-1d", skiprows=[0])).ffill(axis=0)
        ofto_circuit_changes = (pd.read_excel(etys_file_name, sheet_name="B-2-2d", skiprows=[0])).ffill(axis=0)
        ofto_tx = (pd.read_excel(etys_file_name, sheet_name="B-3-1d", skiprows=[0])).ffill(axis=0)
        ofto_tx_changes = (pd.read_excel(etys_file_name, sheet_name="B-3-2d", skiprows=[0])).ffill(axis=0)

        # TO BE ADDED EVENTUALLY #
        intra_hvdc = None
        intra_hvdc_changes = None

        def define_network_df_dict(scotland_reduced):
            if not scotland_reduced:
                network_df_dict_comp = {
                    'shet_circuits': shet_circuits,
                    'shet_circuit_changes': shet_circuit_changes,
                    'shet_tx': shet_tx,
                    'shet_tx_changes': shet_tx_changes,
                    'spt_circuits': spt_circuits,
                    'spt_circuit_changes': spt_circuit_changes,
                    'spt_tx': spt_tx,
                    'spt_tx_changes': spt_tx_changes,
                    'nget_circuits': nget_circuits,
                    'nget_circuit_changes': nget_circuit_changes,
                    'nget_tx': nget_tx,
                    'nget_tx_changes': nget_tx_changes,
                    # 'ofto_circuits': ofto_circuits,
                    # 'ofto_circuit_changes': ofto_circuit_changes,
                    # 'ofto_tx': ofto_tx,
                    # 'ofto_tx_changes': ofto_tx_changes
                }

                network_df_dict_subs = {
                    'shet_substations': shet_substations,
                    'spt_substations': spt_substations,
                    'nget_substations': nget_substations,
                    'ofto_substations': ofto_substations,
                }
            else:
                network_df_dict_comp = {
                    'nget_circuits': nget_circuits,
                    'nget_circuit_changes': nget_circuit_changes,
                    'nget_tx': nget_tx,
                    'nget_tx_changes': nget_tx_changes
                }

                network_df_dict_subs = {
                    'shet_substations': shet_substations,
                    'spt_substations': spt_substations,
                    'nget_substations': nget_substations,
                    'ofto_substations': ofto_substations,
                }

            return network_df_dict_comp, network_df_dict_subs

        network_df_dict_comp, network_df_dict_subs = define_network_df_dict(scotland_reduced)

        # pass the dictionary to subsequent functions
        self.network_df_dict_comp = network_df_dict_comp
        self.network_df_dict_subs = network_df_dict_subs

    def import_tec_ic_demand_data(self):
        try:
            if self.api_or_local == "api":
                proxies = {
                    "http": "http://proxy.invzb.uk.corporg.net:8083",
                    "https": "http://proxy.invzb.uk.corporg.net:8083"
                }

                url = "https://www.nationalgrideso.com/document/275586/download"
                response = requests.get(url, proxies=proxies)
                if response.status_code == 200:
                    NGET_Circuits = pd.read_excel(response.content, sheet_name="B-2-1c", skiprows=[0])
                    NGET_Circuit_Changes = pd.read_excel(response.content, sheet_name="B-2-2c", skiprows=[0])
                    NGET_Subs = pd.read_excel(response.content, sheet_name="B-1-1c", skiprows=[0])
                    NGET_Tx = pd.read_excel(response.content, sheet_name="B-3-1c", skiprows=[0])
                    NGET_Tx_Changes = pd.read_excel(response.content, sheet_name="B-3-2c", skiprows=[0])
                #     NGET_Reactive = pd.read_excel(response.content, sheet_name = "B-4-1c", skiprows=[0])
                #     NGET_Reactive_Changes = pd.read_excel(response.content, sheet_name = "B-4-2c", skiprows=[0])
                else:
                    print(
                        "Failed to download ETYS Appendix B file from https://www.nationalgrideso.com/document/275586/download")

                # """comment out FES Demand Data API as ETYS App-G data preferable due to better match with ETYS Node names"""

                # url = "https://data.nationalgrideso.com/api/3/action/datastore_search"
                # params = {
                #     "resource_id": "6a1d99c2-a3c5-4ae0-b66a-21e4c15a9ae6",
                #     "limit": 10000,
                #     "offset": 0,
                #     "filters": json.dumps({
                #         "scenario": "LW",
                #         "year": "27"
                #     })
                # }
                # all_data = []
                # while True:
                #     response = requests.get(url, params=params, proxies = proxies)
                #     if response.status_code == 200:
                #         data_dict = response.json()["result"]["records"]
                #         all_data.extend(data_dict)
                #         if len(data_dict) < 10000:
                #             break
                #         params["offset"] += 10000
                #     else:
                #         print(f"Error: {response.status_code} - {response.reason}")
                #         break
                # gsp_demand = pd.DataFrame.from_dict(all_data)
                # gsp_demand = gsp_demand.groupby('GSP').agg(
                #     {'DemandPk': 'sum', 'DemandAM': 'sum', 'DemandPM': 'sum'}).reset_index()

                url = "https://data.nationalgrideso.com/api/3/action/datastore_search"
                resource_ids = ["000d08b9-12d9-4396-95f8-6b3677664836", "17becbab-e3e8-473f-b303-3806f43a6a10",
                                "64f7908f-f787-4977-93e1-5342a5f1357f"]
                df_names = ["fes_2022_gsp_info", "tec_register", "ic_register"]
                dfs = {}
                for i, res_id in enumerate(resource_ids):
                    params = {
                        "resource_id": res_id,
                        "limit": 10000,
                        "offset": 0,
                    }
                    all_data = []
                    while True:
                        response = requests.get(url, params=params, proxies=proxies)
                        if response.status_code == 200:
                            data_dict = response.json()["result"]["records"]
                            all_data.extend(data_dict)
                            if len(data_dict) < 10000:
                                break
                            params["offset"] += 10000
                        else:
                            print(f"Error: {response.status_code} - {response.reason}")
                            break
                    dfs[df_names[i]] = pd.DataFrame.from_dict(all_data)
                tec_register = dfs["tec_register"]
                ic_register = dfs["ic_register"]
                self.tec_register = tec_register
                self.ic_register = ic_register
                success = True

            elif self.api_or_local == "local":
                # import TEC and IC data from local path
                tec_register = pd.read_csv('../data/TEC_Reg.csv')
                ic_register = pd.read_csv('../data/IC_Reg.csv')
                self.tec_register = tec_register
                self.ic_register = ic_register
                success = True

            else:
                sys.exit()

            gsp_demand = pd.read_csv('../data/ETYS23_Appendix G_Dem.csv')
            self.gsp_demand = gsp_demand

        except:
            print("Error occured - change selection to api or local")
            success = False
            sys.exit()

    def create_bus_id(self):
        # fix column headers for consistency across circuits and transformers
        for df_name, df in self.network_df_dict_comp.items():
            df.columns = df.columns.str.strip()
            df.rename(columns={'Node1': 'Node 1',
                               'Node2': 'Node 2',
                               'OHL Length(km)': 'OHL Length (km)',
                               'Cable Length(km)': 'Cable Length (km)',
                               'Rating (MVA)': 'Winter Rating (MVA)',
                               'R (% on 100 MVA)': 'R (% on 100MVA)',
                               'X (% on 100 MVA)': 'X (% on 100MVA)',
                               'B (% on 100 MVA)': 'B (% on 100MVA)'}, inplace=True)

        unique_values_node1 = set()
        unique_values_node2 = set()
        for df_name, df in self.network_df_dict_comp.items():
            unique_values_node1.update((df.loc[:, 'Node 1']).unique())
            unique_values_node2.update((df.loc[:, 'Node 2']).unique())
        bus_ids = list(unique_values_node1.union(unique_values_node2))

        for df_name, df in self.network_df_dict_subs.items():
            df['Region'] = str(df_name[:4])

        all_subs = pd.concat(self.network_df_dict_subs.values(), ignore_index=True)

        # convert bus ids list into dataframe and add full name column and sort subs in alphabetical order.
        bus_ids_data = {'Name': bus_ids}
        bus_ids_df = pd.DataFrame(bus_ids_data)

        dict_voltage = {'1': '132', '2': '275', '3': '33', '4': '400', '5': '11', '6': '66', '7': '25', '8': '22'}
        bus_ids_df['voltage'] = bus_ids_df['Name'].str[4].map(dict_voltage)

        def set_voltage_col_to_int(site_df, col_name):
            site_df[col_name] = pd.to_numeric(site_df[col_name], errors='coerce').fillna(pd.NA).round().astype('Int64')
        set_voltage_col_to_int(all_subs, 'Voltage (kV)')
        set_voltage_col_to_int(bus_ids_df, 'voltage')

        # merging on Name and Voltage to avoid merge resulting in duplicates. Only Monk Fryston & Monk Fryston New are_
        # the duplicates - can be fixed by changing MONF code to like MONN for one of the subs, however this will affect_
        # how circuits are mapped so that needs to be corrected too.
        # blank rows (based on Site Code) are removed - which is expected to include a couple of OFTO sites
        bus_ids_df = pd.merge(bus_ids_df, all_subs, how='left',
                              left_on=bus_ids_df['Name'].str[:4] + bus_ids_df['voltage'].astype(str),
                              right_on=all_subs['Site Code'].str[:4] + all_subs['Voltage (kV)'].astype(str))[lambda row: row['Site Code'].notna() & (row['Site Code'] != '')]

        bus_ids_df['Site Name'] = bus_ids_df['Site Name'].str.replace(r'\b\S*\d+\S*\b', "", regex=True).str.strip()

        try:
            bus_ids_df.drop(columns=['key_0'], inplace=True)
        except:
            pass

        bus_ids_df['Full Name'] = bus_ids_df.apply(lambda row: f"{str(row['Site Name'])} {str(row['Voltage (kV)'])}kV", axis=1)
        bus_ids_df.sort_values(by=['Site Name'], inplace=True)
        bus_ids_df.drop_duplicates(subset='Name', keep='first', inplace=True)
        bus_ids_df.reset_index(inplace=True, drop=True)
        bus_ids_df.reset_index(inplace=True)

        self.bus_ids_df = bus_ids_df

        # """add coordinates to bus_ids dataframe - decided not required and will continue to be handled by Homepage.py"""

    def transform_network_data(self):
        for df_name, df in self.network_df_dict_comp.items():
            df['Dataframe'] = str(df_name)

        # append network data and future changes
        all_comp = pd.concat(self.network_df_dict_comp.values(), ignore_index=True)

        # clean data to remove rogue types and ensure all components are between known substations found in bus_ids_df
        all_comp = all_comp[pd.to_numeric(all_comp['X (% on 100MVA)'], errors='coerce').notnull()]
        all_comp = all_comp[
            all_comp['Node 1'].isin(self.bus_ids_df['Name']) & all_comp['Node 2'].isin(self.bus_ids_df['Name'])]
        all_comp.sort_values(by=['Node 1']).reset_index(inplace=True, drop=True)

        # create a mapping from Node name to index and map indices to Node 1 and Node 2 in bus_ids_df; this will add_
        # bus_id into the all components (i.e. circuit, trafo) lists.
        node_name_to_index = pd.Series(self.bus_ids_df.index, index=self.bus_ids_df['Name'])
        node_voltage_to_voltage = pd.Series(self.bus_ids_df['Voltage (kV)'], index=self.bus_ids_df['index'])
        all_comp['Node 1 bus_id'] = all_comp['Node 1'].map(node_name_to_index)
        all_comp['Node 2 bus_id'] = all_comp['Node 2'].map(node_name_to_index)
        all_comp['Voltage (kV) Node 1'] = all_comp['Node 1 bus_id'].map(node_voltage_to_voltage)
        all_comp['Voltage (kV) Node 2'] = all_comp['Node 2 bus_id'].map(node_voltage_to_voltage)

        all_circuits = all_comp[
            all_comp['Dataframe'].isin(['nget_circuits', 'shet_circuits', 'spt_circuits', 'ofto_circuits'])].dropna(
            how='all', axis=1).reset_index(drop=True)
        all_circuits_changes = all_comp[all_comp['Dataframe'].isin(
            ['nget_circuit_changes', 'shet_circuit_changes', 'spt_circuit_changes', 'ofto_circuit_changes'])].dropna(
            how='all', axis=1).reset_index(drop=True)
        all_trafo = all_comp[all_comp['Dataframe'].isin(['nget_tx', 'shet_tx', 'spt_tx', 'ofto_tx'])].dropna(how='all',
                                                                                                             axis=1).reset_index(
            drop=True)
        all_trafo_changes = all_comp[all_comp['Dataframe'].isin(
            ['nget_tx_changes', 'shet_tx_changes', 'spt_tx_changes', 'ofto_tx_changes'])].dropna(how='all',
                                                                                                 axis=1).reset_index(
            drop=True)
        # print('All components list has :' + str((all_comp.shape[0])) + ' components.\n Individual lists have ' + str(
        #     (all_circuits.shape[0]) + (all_circuits_changes.shape[0]) + (all_trafo.shape[0]) + (
        #     all_trafo_changes.shape[0])) + ' components')

        self.all_circuits = all_circuits
        self.all_circuits_changes = all_circuits_changes
        self.all_trafo = all_trafo
        self.all_trafo_changes = all_trafo_changes

    def transform_tec_ic_data(self):
        # clean TEC Register
        self.tec_register = self.tec_register[~self.tec_register["Project Name"].isin(
            ["Drax (Coal)", "Dungeness B", "Hartlepool", "Hinkley Point B", "Uskmouth", "Sutton Bridge",
             "Ratcliffe on Soar", "West Burton A"])]
        self.tec_register['Generator Name'] = self.tec_register.apply(
            lambda row: str(row['Project Name']) + ' (' + str(row['Customer Name']) + ')' if pd.isna(
                row['Stage']) else str(row['Project Name']) + ' *Stage: ' + str(row['Stage']) + '*' + ' (' + str(
                row['Customer Name']) + ')', axis=1)
        self.tec_register['MW Effective From'] = pd.to_datetime(self.tec_register['MW Effective From'],
                                                                format='%d/%m/%Y', errors='coerce')
        self.tec_register['MW Effective From'] = self.tec_register.apply(
            lambda row: datetime.today() if pd.isna(row['MW Effective From']) and row['Project Status'] == 'Built' else
            row[
                'MW Effective From'], axis=1)
        self.tec_register.dropna(subset=['MW Effective From'], inplace=True)
        self.tec_register['MW Effective From'] = self.tec_register['MW Effective From'].dt.date
        self.tec_register['MW Effective'] = self.tec_register.apply(
            lambda row: row['Cumulative Total Capacity (MW)'] if pd.isna(row['Stage']) or row['Stage'] == 1 else row[
                'MW Increase / Decrease'], axis=1)
        self.tec_register.reset_index(drop=True, inplace=True)

        # clean IC Register
        self.ic_register['Generator Name'] = self.ic_register.apply(lambda row: f"{str(row['Project Name'])} ({str(row['Connection Site'])})", axis=1)
        self.ic_register['MW Effective From'] = pd.to_datetime(self.ic_register['MW Effective From'], format='%d/%m/%Y',
                                                               errors='coerce')
        self.ic_register['MW Effective From'] = self.ic_register.apply(
            lambda row: datetime.today() if pd.isna(row['MW Effective From']) and row['Project Status'] == 'Built' else
            row[
                'MW Effective From'], axis=1)
        self.ic_register.dropna(subset=['MW Effective From'], inplace=True)
        self.ic_register['MW Effective From'] = self.ic_register['MW Effective From'].dt.date
        # self.ic_register['MW Effective From'] = self.ic_register['MW Effective From'].dt.strftime('%d-%m-%Y')
        self.ic_register.reset_index(drop=True, inplace=True)

        # use loop statement to pick out known substations from Connection Site column using bus_ids_df and populate bus_name and bus_id for TEC and Interconnector units.
        # TEC Register first, Interconnector Register second
        def add_bus_details(df, bus_ids_df, register_type):
            df[['bus_name', 'bus_id']] = ""
            for index1, row1 in df.iterrows():
                conn_site = str(row1['Connection Site']).strip()
                subs_names_id = []
                if not (row1['Connection Site'] == "" or pd.isnull(row1['Connection Site'])):
                    for index2, row2 in bus_ids_df.iterrows():
                        bus_site_name = (str(row2['Site Name']).strip()).upper()
                        bus_id = index2
                        if not (row2['Site Name'] == "" or pd.isnull(row2['Site Name'])):
                            if (bus_site_name.upper() in conn_site.upper()) or (bus_site_name.replace(" MAIN", "").replace("'", "").replace(" ", "").upper() in conn_site.replace(" ", "").replace("'", "").upper()):
                                if tuple((bus_site_name.upper(), bus_id)) not in subs_names_id:
                                    subs_names_id.append(tuple((bus_site_name.upper(), bus_id)))
                        if len(subs_names_id) > 1:
                            for each_subs_1 in subs_names_id:
                                for each_subs_2 in subs_names_id:
                                    if (each_subs_1[0] != each_subs_2[0]) and (
                                            each_subs_1[0].upper() in each_subs_2[0].upper()):
                                        try:
                                            subs_names_id.remove(each_subs_1)
                                        except:
                                            pass
                if len(subs_names_id) != 0:
                    subs_names_unpacked, bus_id_unpacked = zip(*subs_names_id)
                    subs_names_unpacked = list(set(list(subs_names_unpacked)))
                    subs_names_unpacked.sort()
                    x = ' or '.join(subs_names_unpacked)
                    df.at[index1, 'bus_name'] = x
                    df.at[index1, 'bus_id'] = list(bus_id_unpacked)

        add_bus_details(self.tec_register, self.bus_ids_df, 'tec_register')
        add_bus_details(self.ic_register, self.bus_ids_df, 'ic_register')

        # define the Gen_Type for TEC Register based on Plant Type and Generator Name columns.
        # set all in IC Register to Gen_Type = Interconnector
        self.tec_register['Gen_Type'] = ""
        for index, row in self.tec_register.iterrows():
            if re.search('(?i).*nuclear.*', f"{row['Plant Type']} {row['Generator Name']}"):
                self.tec_register.at[index, 'Gen_Type'] = "Nuclear"
            elif re.search('(?i).*wind.*', f"{row['Plant Type']} {row['Generator Name']}"):
                self.tec_register.at[index, 'Gen_Type'] = "Wind"
            elif re.search('(?i).*pv|solar.*', f"{row['Plant Type']} {row['Generator Name']}"):
                self.tec_register.at[index, 'Gen_Type'] = "PV"
            elif re.search('(?i).*CCGT|CHP|Biomass|gas.*', f"{row['Plant Type']} {row['Generator Name']}"):
                self.tec_register.at[index, 'Gen_Type'] = "CCGT/CHP/Biomass"
            elif re.search('(?i).*pump|hydro|tidal.*', f"{row['Plant Type']} {row['Generator Name']}"):
                self.tec_register.at[index, 'Gen_Type'] = "Hydro/Pump/Tidal"
            elif re.search('(?i).*energy storage|battery|bess|grid park|energy park.*',
                           f"{row['Plant Type']} {row['Generator Name']}"):
                self.tec_register.at[index, 'Gen_Type'] = "BESS / Energy Park"
            else:
                self.tec_register.at[index, 'Gen_Type'] = "Other"
        self.ic_register['Gen_Type'] = "Interconnector"

        print('If Scotland reduced:\nTEC Register has match on: ' + str(
            self.tec_register[self.tec_register['HOST TO'] == 'NGET']['bus_name'].ne('').sum()) + ' out of ' + str(
            self.tec_register[self.tec_register['HOST TO'] == 'NGET']['Project Name'].notna().sum()) + ' generators.')
        print('If Scotland not reduced:\nTEC Register has match on: ' + str(self.tec_register['bus_name'].ne('').sum())
              + ' out of ' + str(self.tec_register['Project Name'].notna().sum()) + ' generators.')

    def transform_demand_data(self):
        # remove non-value rows by filtering the '24/25' column.
        # add substation full names and bus id as separate columns into the GSP demand table.
        self.gsp_demand = self.gsp_demand[pd.to_numeric(self.gsp_demand['24/25'], errors='coerce').notnull()]
        self.gsp_demand[['bus_name', 'bus_id']] = ""
        for index1, row1 in self.gsp_demand.iterrows():
            four_char_dem = str(row1['Node'][:4])
            six_char_dem = str(row1['Node'][:6])
            for index2, row2 in self.bus_ids_df.iterrows():
                four_char_bus = str(row2['Name'][:4])
                six_char_bus = str(row2['Name'][:6])
                if six_char_dem == six_char_bus:
                    self.gsp_demand.at[index1, 'bus_name'] = row2['Full Name']
                    self.gsp_demand.at[index1, 'bus_id'] = index2
                    break
                elif four_char_dem == four_char_bus:
                    self.gsp_demand.at[index1, 'bus_name'] = row2['Full Name']
                    self.gsp_demand.at[index1, 'bus_id'] = index2

    def key_stats(self):
        delete = '../delete/'
        self.gsp_demand.to_csv(delete + 'gsp_demand.csv')
        self.ic_register.to_csv(delete + 'ic_register.csv')
        self.tec_register.to_csv(delete + 'tec_register.csv')
        self.all_trafo_changes.to_csv(delete + 'all_trafo_changes.csv')
        self.all_trafo.to_csv(delete + 'all_trafo.csv')
        self.all_circuits_changes.to_csv(delete + 'all_circuits_changes.csv')
        self.all_circuits.to_csv(delete + 'all_circuits.csv')
        self.bus_ids_df.to_csv(delete + 'bus_ids_df.csv')


if __name__ == "__main__":
    call = TransformData()
    call.import_network_data(True)
    call.import_tec_ic_demand_data()
    call.create_bus_id()
    call.transform_network_data()
    call.transform_tec_ic_data()
    call.transform_demand_data()
    call.key_stats()
