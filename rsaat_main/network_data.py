"""


"""

import re
import sys
from datetime import datetime
import pandas as pd
import requests
import os


class TransformData:
    def __init__(self, api_or_local='local', scotland_reduced=True, consider_ofto=False):
        self.gsp_demand = None
        self.ic_register = None
        self.tec_register = None
        self.ic_reg_sub_map = None
        self.tec_reg_sub_map = None
        self.ranking_order = None
        self.sub_coordinates = None
        self.intra_hvdc = None
        self.all_trafo_changes = None
        self.all_trafo = None
        self.all_circuits_changes = None
        self.all_circuits = None
        self.all_comp = None
        self.bus_ids_df = None
        self.network_df_dict_subs = None
        self.network_df_dict_comp = None

        self.api_or_local = api_or_local
        self.scotland_reduced = scotland_reduced
        self.consider_ofto = consider_ofto

    def import_network_data(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sub_coordinates = pd.read_csv(os.path.join(project_root, 'data', 'CRM_Sub_Coordinates_WGS84.csv')).dropna()
        intra_hvdc = pd.read_csv(os.path.join(project_root, 'data', 'intra_hvdc_etys_2022_curated.csv')).dropna()
        etys_file_path = os.path.join(project_root, 'data', 'Appendix B 2022.xlsx')

        self.sub_coordinates = sub_coordinates
        self.intra_hvdc = intra_hvdc

        shet_substations = pd.read_excel(etys_file_path, sheet_name="B-1-1a", skiprows=[0])
        spt_substations = pd.read_excel(etys_file_path, sheet_name="B-1-1b", skiprows=[0])
        nget_substations = pd.read_excel(etys_file_path, sheet_name="B-1-1c", skiprows=[0])
        ofto_substations = pd.read_excel(etys_file_path, sheet_name="B-1-1d", skiprows=[0])

        shet_circuits = pd.read_excel(etys_file_path, sheet_name="B-2-1a", skiprows=[0])
        shet_circuit_changes = pd.read_excel(etys_file_path, sheet_name="B-2-2a", skiprows=[0])
        shet_tx = pd.read_excel(etys_file_path, sheet_name="B-3-1a", skiprows=[0])
        shet_tx_changes = pd.read_excel(etys_file_path, sheet_name="B-3-2a", skiprows=[0])

        spt_circuits = pd.read_excel(etys_file_path, sheet_name="B-2-1b", skiprows=[0])
        spt_circuit_changes = pd.read_excel(etys_file_path, sheet_name="B-2-2b", skiprows=[0])
        spt_tx = pd.read_excel(etys_file_path, sheet_name="B-3-1b", skiprows=[0])
        spt_tx_changes = pd.read_excel(etys_file_path, sheet_name="B-3-2b", skiprows=[0])

        nget_circuits = pd.read_excel(etys_file_path, sheet_name="B-2-1c", skiprows=[0])
        nget_circuit_changes = pd.read_excel(etys_file_path, sheet_name="B-2-2c", skiprows=[0])
        nget_tx = pd.read_excel(etys_file_path, sheet_name="B-3-1c", skiprows=[0])
        nget_tx_changes = pd.read_excel(etys_file_path, sheet_name="B-3-2c", skiprows=[0])

        ofto_circuits = (pd.read_excel(etys_file_path, sheet_name="B-2-1d", skiprows=[0])).ffill(axis=0)
        ofto_circuit_changes = (pd.read_excel(etys_file_path, sheet_name="B-2-2d", skiprows=[0])).ffill(axis=0)
        ofto_tx = (pd.read_excel(etys_file_path, sheet_name="B-3-1d", skiprows=[0])).ffill(axis=0)
        ofto_tx_changes = (pd.read_excel(etys_file_path, sheet_name="B-3-2d", skiprows=[0])).ffill(axis=0)

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

        if not self.scotland_reduced:
            network_df_dict_comp.update({
                'shet_circuits': shet_circuits,
                'shet_circuit_changes': shet_circuit_changes,
                'shet_tx': shet_tx,
                'shet_tx_changes': shet_tx_changes,
                'spt_circuits': spt_circuits,
                'spt_circuit_changes': spt_circuit_changes,
                'spt_tx': spt_tx,
                'spt_tx_changes': spt_tx_changes
            })

        if self.consider_ofto:
            network_df_dict_comp.update({
                'ofto_circuits': ofto_circuits,
                'ofto_circuit_changes': ofto_circuit_changes,
                'ofto_tx': ofto_tx,
                'ofto_tx_changes': ofto_tx_changes
            })

        # pass the dictionary to subsequent functions.
        self.network_df_dict_comp = network_df_dict_comp
        self.network_df_dict_subs = network_df_dict_subs

    def import_tec_ic_demand_data(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tec_reg_sub_map = pd.read_csv(os.path.join(project_root, 'data', 'tec_reg_sub_map.csv'))
        ic_reg_sub_map = pd.read_csv(os.path.join(project_root, 'data', 'ic_reg_sub_map.csv'))
        ranking_order = pd.read_csv(os.path.join(project_root, 'data', 'Plant_Ranking_Order.csv'))
        self.tec_reg_sub_map = tec_reg_sub_map
        self.ic_reg_sub_map = ic_reg_sub_map
        self.ranking_order = ranking_order

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
                    NGET_Reactive = pd.read_excel(response.content, sheet_name="B-4-1c", skiprows=[0])
                    NGET_Reactive_Changes = pd.read_excel(response.content, sheet_name="B-4-2c", skiprows=[0])
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
                tec_register = pd.read_csv(os.path.join(project_root, 'data', 'tec-register-02-02-2024_curated.csv'), parse_dates=['MW Effective From'])
                ic_register = pd.read_csv(
                    os.path.join(project_root, 'data', 'interconnector-register-02-02-2024_curated.csv'), parse_dates=['MW Effective From'])
                self.tec_register = tec_register
                self.ic_register = ic_register
                success = True

            else:
                sys.exit()

            gsp_demand = pd.read_csv(os.path.join(project_root, 'data', 'ETYS23_Appendix G_Dem.csv'))
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

        all_subs['Voltage (kV)'] = pd.to_numeric(all_subs['Voltage (kV)'], errors='coerce').fillna(
            pd.NA).round().astype('Int64')
        bus_ids_df['voltage'] = pd.to_numeric(bus_ids_df['voltage'], errors='coerce').fillna(pd.NA).round().astype(
            'Int64')

        # merging on Name and Voltage to avoid merge resulting in duplicates. Only Monk Fryston & Monk Fryston New are_
        # the duplicates - can be fixed by changing MONF code to like MONN for one of the subs, however this will affect_
        # how circuits are mapped so that needs to be corrected too.
        # blank rows (based on Site Code) are removed - which is expected to include a couple of OFTO sites
        bus_ids_df = pd.merge(bus_ids_df, all_subs, how='left',
                              left_on=bus_ids_df['Name'].str[:4] + bus_ids_df['voltage'].astype(str),
                              right_on=all_subs['Site Code'].str[:4] + all_subs['Voltage (kV)'].astype(str))[
            lambda row: row['Site Code'].notna() & (row['Site Code'] != '')]

        bus_ids_df['Site Name'] = bus_ids_df['Site Name'].str.replace(r'\b\S*\d+\S*\b', "", regex=True).str.strip()

        try:
            bus_ids_df.drop(columns=['key_0'], inplace=True)
        except:
            pass

        bus_ids_df['Full Name'] = bus_ids_df.apply(lambda row: f"{str(row['Site Name'])} {str(row['Voltage (kV)'])}kV",
                                                   axis=1)
        bus_ids_df.sort_values(by=['Voltage (kV)'], ascending=False, inplace=True)
        bus_ids_df.drop_duplicates(subset='Name', keep='first', inplace=True)
        bus_ids_df.reset_index(inplace=True, drop=True)
        bus_ids_df.reset_index(inplace=True)

        self.bus_ids_df = bus_ids_df

        # """add coordinates to bus_ids dataframe - decided not required and will continue to be handled by 01_Homepage.py"""

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

        self.all_comp = all_comp
        self.all_circuits = all_circuits
        self.all_circuits_changes = all_circuits_changes
        self.all_trafo = all_trafo
        self.all_trafo_changes = all_trafo_changes

    def transform_tec_ic_data(self):

        # nominal_date = pd.Timestamp.today().normalize()
        nominal_date = datetime(2000, 1, 1)

        def format_tec_ic_registers(df, df_name, sub_map, bus_ids_df, ranking_order):
            def merge_sub_map_to_tec_ic(df, sub_map):
                # merge sub_map and tec/ic_reg
                sub_map = sub_map[['etys_sub_map', 'Project No']]
                df = pd.merge(df, sub_map, how='left', on='Project No')
                return df

            def merge_ranking_order_to_tec(df, df_name, ranking_order):
                # merge ranking_order and tec/ic_reg
                if 'Plant Type' in df.columns:
                    df = pd.merge(df, ranking_order, how='left', on='Plant Type')
                else:
                    if df_name == 'ic_register':
                        df['Plant Type'] = 'Interconnector'
                        df = pd.merge(df, ranking_order, how='left', on='Plant Type')
                    else:
                        print(f"Plant Type column not found in {str(df_name)}")
                return df

            def create_gen_name_col(df):
                df['Generator Name'] = df['Project Name'] + df['Stage'].fillna('').apply(
                    lambda x: f" *Stage: {x}*" if x else '') + ' (' + df['Customer Name'] + ')'
                return df

            def curate_mw_effective_from_date(df):
                df['MW Effective From'] = pd.to_datetime(df['MW Effective From'], errors='coerce', format='%d/%m/%Y')
                df.loc[(df['MW Effective From'].isna()) & (
                        df['Project Status'] == 'Built'), 'MW Effective From'] = nominal_date
                df['MW Effective From'] = df['MW Effective From'].dt.date
                return df

            def curate_mw_effective(df):
                condition = pd.isna(df['Stage']) | (df['Stage'] == 1)
                try:
                    df['MW Effective'] = df.where(condition, df['MW Increase / Decrease'], axis=0)[
                        'Cumulative Total Capacity (MW)']
                except:
                    df['MW Effective - Import'] = df.where(condition, df['MW Import - Increase / Decrease'], axis=0)[
                        'MW Import - Total']
                    df['MW Effective - Export'] = df.where(condition, df['MW Export - Increase / Decrease'], axis=0)[
                        'MW Export - Total']
                df.reset_index(drop=True, inplace=True)
                return df

            # pick out known substations from Connection Site column using bus_ids_df and populate bus_name_guess and
            # bus_name and bus_id_guess and bus_id for TEC and Interconnector Registers.
            def create_bus_name_bus_id_cols(df, bus_ids_df):
                df[['bus_name_guess', 'bus_id_guess', 'bus_name', 'bus_id']] = ""

                for index1, row1 in df.iterrows():
                    conn_site = str(row1['Connection Site']).strip()
                    conn_sub = str(row1['etys_sub_map']).strip()
                    subs_name_id_guess, subs_name_id, subs_name_id_backup, subs_name_id_backup_2 = [], [], [], []
                    if not (row1['Connection Site'] == "" or pd.isnull(row1['Connection Site'])):
                        # for bus_name_guess and bus_id_guess
                        for index2, row2 in bus_ids_df.iterrows():
                            bus_site_name = (str(row2['Site Name']).strip()).upper()
                            bus_site_code = (str(row2['Name']).strip()).upper()
                            bus_id = index2
                            if not (row2['Site Name'] == "" or pd.isnull(row2['Site Name'])):
                                if (bus_site_name.upper() in conn_site.upper()) or (
                                        bus_site_name.replace(" MAIN", "").replace("'", "").replace(" ",
                                                                                                    "").upper() in
                                        conn_site.replace(" ", "").replace("'", "").upper()):
                                    if tuple((bus_site_name.upper(), bus_id)) not in subs_name_id_guess:
                                        subs_name_id_guess.append(tuple((bus_site_name.upper(), bus_id)))
                            # for bus_name and bus_id
                            if conn_sub[:6].upper() in bus_site_code.upper():
                                if tuple((bus_site_name.upper(), bus_id)) not in subs_name_id:
                                    subs_name_id.append(tuple((bus_site_name.upper(), bus_id)))
                            elif conn_sub[:5].upper() in bus_site_code.upper():
                                if (bus_site_name.upper(), bus_id) not in subs_name_id and (
                                        bus_site_name.upper(), bus_id) not in subs_name_id_backup:
                                    subs_name_id_backup.append(tuple((bus_site_name.upper(), bus_id)))
                            elif conn_sub[:4].upper() in bus_site_code.upper():
                                if (bus_site_name.upper(), bus_id) not in subs_name_id and (
                                        bus_site_name.upper(), bus_id) not in subs_name_id_backup_2:
                                    subs_name_id_backup_2.append(tuple((bus_site_name.upper(), bus_id)))

                        if len(subs_name_id) == 0:
                            subs_name_id = subs_name_id_backup
                            if len(subs_name_id) == 0:
                                subs_name_id = subs_name_id_backup_2
                        else:
                            pass

                        if len(subs_name_id_guess) > 1:
                            for each_subs_1 in subs_name_id_guess:
                                for each_subs_2 in subs_name_id_guess:
                                    if (each_subs_1[0] != each_subs_2[0]) and (
                                            each_subs_1[0].upper() in each_subs_2[0].upper()):
                                        try:
                                            subs_name_id_guess.remove(each_subs_1)
                                        except:
                                            pass

                        if len(subs_name_id) > 1:
                            for each_subs_1 in subs_name_id:
                                for each_subs_2 in subs_name_id:
                                    if (each_subs_1[0] != each_subs_2[0]) and (
                                            each_subs_1[0].upper() in each_subs_2[0].upper()):
                                        try:
                                            subs_name_id_guess.remove(each_subs_1)
                                        except:
                                            pass

                    if len(subs_name_id_guess) != 0:
                        subs_names_unpacked, bus_id_unpacked = zip(*subs_name_id_guess)
                        subs_names_unpacked = list(set(list(subs_names_unpacked)))
                        subs_names_unpacked.sort()
                        x = ' or '.join(subs_names_unpacked)
                        df.at[index1, 'bus_name_guess'] = x
                        df.at[index1, 'bus_id_guess'] = list(bus_id_unpacked)

                    if len(subs_name_id) != 0:
                        subs_names_unpacked, bus_id_unpacked = zip(*subs_name_id)
                        subs_names_unpacked = list(set(list(subs_names_unpacked)))
                        subs_names_unpacked.sort()
                        x = ' or '.join(subs_names_unpacked)
                        df.at[index1, 'bus_name'] = x
                        df.at[index1, 'bus_id'] = list(bus_id_unpacked)

                return df

            df = merge_sub_map_to_tec_ic(df, sub_map)
            df = merge_ranking_order_to_tec(df, df_name, ranking_order)
            df = create_gen_name_col(df)
            df = curate_mw_effective_from_date(df)
            df = curate_mw_effective(df)
            df = create_bus_name_bus_id_cols(df, bus_ids_df)
            return df

        self.tec_register = format_tec_ic_registers(self.tec_register, 'tec_register', self.tec_reg_sub_map,
                                                    self.bus_ids_df, self.ranking_order)
        self.ic_register = format_tec_ic_registers(self.ic_register, 'ic_register', self.ic_reg_sub_map,
                                                   self.bus_ids_df, self.ranking_order)

        # account for where tec mw inc/dec is not 0 for Built units (ie Built unit is changing TEC in future year)
        new_rows = []
        def update_cumulative_capacity(row_tec):
            if row_tec['Project Status'] == 'Built' and row_tec['MW Increase / Decrease'] != 0:
                row_tec['MW Effective'] = row_tec['MW Connected']
                new_row = row_tec.copy()
                row_tec['MW Effective From'] = nominal_date
                new_row['Generator Name'] = f"{row_tec['Generator Name']}_2"
                new_row['MW Effective'] = row_tec['MW Increase / Decrease']
                new_rows.append(new_row)
            return row_tec

        self.tec_register = self.tec_register.apply(update_cumulative_capacity, axis=1)
        if new_rows:
            self.tec_register = pd.concat([self.tec_register, pd.DataFrame(new_rows)], ignore_index=True).reset_index(
                drop=True)

        self.tec_register['MW Effective From'] = pd.to_datetime(self.tec_register['MW Effective From'])
        self.tec_register['MW Effective From'] = self.tec_register['MW Effective From'].dt.date

        # DEPRECATED
        # define the Gen_Type for TEC Register based on Plant Type and Generator Name columns.
        # set all in IC Register to Gen_Type = Interconnector
        self.ic_register[['Gen_Type', 'Plant Type']] = "Interconnector"
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

    def transform_demand_data(self):
        # remove non-value rows by filtering the '24/25' column.
        # add substation full names and bus id as separate columns into the GSP demand table.
        self.gsp_demand = self.gsp_demand[pd.to_numeric(self.gsp_demand['24/25'], errors='coerce').notnull()]
        self.gsp_demand[['region', 'bus_name', 'bus_id']] = ""
        for index1, row1 in self.gsp_demand.iterrows():
            four_char_dem = str(row1['Node'][:4])
            six_char_dem = str(row1['Node'][:6])
            for index2, row2 in self.bus_ids_df.iterrows():
                four_char_bus = str(row2['Name'][:4])
                six_char_bus = str(row2['Name'][:6])
                if six_char_dem == six_char_bus:
                    self.gsp_demand.at[index1, 'bus_name'] = row2['Full Name']
                    self.gsp_demand.at[index1, 'bus_id'] = index2
                    self.gsp_demand.at[index1, 'region'] = row2['Region']
                    break
                elif four_char_dem == four_char_bus:
                    self.gsp_demand.at[index1, 'bus_name'] = row2['Full Name']
                    self.gsp_demand.at[index1, 'bus_id'] = index2
                    self.gsp_demand.at[index1, 'region'] = row2['Region']

    def transform_intrahvdc_data(self):
        self.intra_hvdc[['region', 'bus_name', 'bus_id']] = ""
        for index1, row1 in self.intra_hvdc.iterrows():
            four_char_dem = str(row1['NGET_Node'][:4])
            six_char_dem = str(row1['NGET_Node'][:6])
            for index2, row2 in self.bus_ids_df.iterrows():
                four_char_bus = str(row2['Name'][:4])
                six_char_bus = str(row2['Name'][:6])
                if six_char_dem == six_char_bus:
                    self.intra_hvdc.at[index1, 'bus_name'] = row2['Full Name']
                    self.intra_hvdc.at[index1, 'bus_id'] = index2
                    self.intra_hvdc.at[index1, 'region'] = row2['Region']
                    break
                elif four_char_dem == four_char_bus:
                    self.intra_hvdc.at[index1, 'bus_name'] = row2['Full Name']
                    self.intra_hvdc.at[index1, 'bus_id'] = index2
                    self.intra_hvdc.at[index1, 'region'] = row2['Region']

    def key_stats(self):
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.gsp_demand.to_csv(os.path.join(project_root, 'delete', 'gsp_demand.csv'))
        self.intra_hvdc.to_csv(os.path.join(project_root, 'delete', 'intra_hvdc.csv'))
        self.ic_register.to_csv(os.path.join(project_root, 'delete', 'ic_register.csv'))
        self.tec_register.to_csv(os.path.join(project_root, 'delete', 'tec_register.csv'))
        self.all_trafo_changes.to_csv(os.path.join(project_root, 'delete', 'all_trafo_changes.csv'))
        self.all_trafo.to_csv(os.path.join(project_root, 'delete', 'all_trafo.csv'))
        self.all_circuits_changes.to_csv(os.path.join(project_root, 'delete', 'all_circuits_changes.csv'))
        self.all_circuits.to_csv(os.path.join(project_root, 'delete', 'all_circuits.csv'))
        self.bus_ids_df.to_csv(os.path.join(project_root, 'delete', 'bus_ids_df.csv'))

        if __name__ == "__main__":
            print('If Scotland reduced: TEC Register has match on: ' + str(
                self.tec_register[self.tec_register['HOST TO'] == 'NGET']['bus_name_guess'].ne('').sum()) + '/' + str(
                self.tec_register[self.tec_register['HOST TO'] == 'NGET']['bus_name'].ne('').sum()) + ' out of ' + str(
                self.tec_register[self.tec_register['HOST TO'] == 'NGET'][
                    'Project Name'].notna().sum()) + ' generators.\nIf Scotland not reduced: TEC Register has match on: ' + str(
                self.tec_register['bus_name_guess'].ne('').sum()) + '/' + str(
                self.tec_register['bus_name'].ne('').sum()) + ' out of ' + str(
                self.tec_register['Project Name'].notna().sum()) + ' generators.\n')
            print('All components list has ' + str(
                (self.all_comp.shape[0])) + ' components. Individual lists have ' + str(
                (self.all_circuits.shape[0]) + (self.all_circuits_changes.shape[0]) + (self.all_trafo.shape[0]) + (
                    self.all_trafo_changes.shape[0])) + ' components')


if __name__ == "__main__":
    call = TransformData()
    call.import_network_data()
    call.import_tec_ic_demand_data()
    call.create_bus_id()
    call.transform_network_data()
    call.transform_tec_ic_data()
    call.transform_demand_data()
    call.transform_intrahvdc_data()
    call.key_stats()