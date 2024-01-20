import json
import re
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import openpyxl
import requests

class NetworkData:
    """ class for network data defined by chosen year """

    def __init__(self, year=2028, api_or_local="local"):
        self.GSP_Demand = None
        self.IC_Register = None
        self.TEC_Register = None
        self.all_trafo_w_changes = None
        self.all_circuits_w_changes = None
        self.all_substations = None
        self.bus_ids_df = None
        self.year = year
        self.api_or_local = api_or_local

    def network_data(self):
        # import network data and substation coordinates
        Sub_Coordinates = pd.read_csv('../data/CRM_Sub_Coordinates_WGS84.csv').dropna(inplace=True)

        etys_file_name = '../data/Appendix B 2022.xlsx'

        SHET_Substations = pd.read_excel(etys_file_name, sheet_name="B-1-1a", skiprows=[0])
        SHET_Substations['Region'] = "SHET"
        SPT_Substations = pd.read_excel(etys_file_name, sheet_name="B-1-1b", skiprows=[0])
        SPT_Substations['Region'] = "SPT"
        NGET_Substations = pd.read_excel(etys_file_name, sheet_name="B-1-1c", skiprows=[0])
        NGET_Substations['Region'] = "NGET"
        OFTO_Substations = pd.read_excel(etys_file_name, sheet_name="B-1-1d", skiprows=[0])
        OFTO_Substations['Region'] = "OFTO"

        self.all_substations = pd.concat([SHET_Substations, SPT_Substations, NGET_Substations, OFTO_Substations])

        SHET_Circuits = pd.read_excel(etys_file_name, sheet_name="B-2-1a", skiprows=[0])
        SHET_Circuit_Changes = pd.read_excel(etys_file_name, sheet_name="B-2-2a", skiprows=[0])
        SHET_Tx = pd.read_excel(etys_file_name, sheet_name="B-3-1a", skiprows=[0])
        SHET_Tx_Changes = pd.read_excel(etys_file_name, sheet_name="B-3-2a", skiprows=[0])

        SPT_Circuits = pd.read_excel(etys_file_name, sheet_name="B-2-1b", skiprows=[0])
        SPT_Circuit_Changes = pd.read_excel(etys_file_name, sheet_name="B-2-2b", skiprows=[0])
        SPT_Tx = pd.read_excel(etys_file_name, sheet_name="B-3-1b", skiprows=[0])
        SPT_Tx_Changes = pd.read_excel(etys_file_name, sheet_name="B-3-2b", skiprows=[0])

        NGET_Circuits = pd.read_excel(etys_file_name, sheet_name="B-2-1c", skiprows=[0])
        NGET_Circuit_Changes = pd.read_excel(etys_file_name, sheet_name="B-2-2c", skiprows=[0])
        NGET_Tx = pd.read_excel(etys_file_name, sheet_name="B-3-1c", skiprows=[0])
        NGET_Tx_Changes = pd.read_excel(etys_file_name, sheet_name="B-3-2c", skiprows=[0])

        OFTO_Circuits = (pd.read_excel(etys_file_name, sheet_name="B-2-1d", skiprows=[0])).ffill(axis=0)
        OFTO_Circuit_Changes = (pd.read_excel(etys_file_name, sheet_name="B-2-2d", skiprows=[0])).ffill(axis=0)
        OFTO_Tx = (pd.read_excel(etys_file_name, sheet_name="B-3-1d", skiprows=[0])).ffill(axis=0)
        OFTO_Tx_Changes = (pd.read_excel(etys_file_name, sheet_name="B-3-2d", skiprows=[0])).ffill(axis=0)

        # fix column headers for consistency across circuits and transformers
        df_list = [NGET_Circuits,
                   NGET_Circuit_Changes,
                   NGET_Tx,
                   NGET_Tx_Changes,
                   SHET_Circuits,
                   SHET_Circuit_Changes,
                   SHET_Tx,
                   SHET_Tx_Changes,
                   SPT_Circuits,
                   SPT_Circuit_Changes,
                   SPT_Tx,
                   SPT_Tx_Changes,
                   OFTO_Circuits,
                   OFTO_Circuit_Changes,
                   OFTO_Tx,
                   OFTO_Tx_Changes]

        for df in df_list:
            df.rename(columns={'Node1': 'Node 1',
                                         'Node2': 'Node 2',
                                         'R (% on 100 MVA)': 'R (% on 100MVA)',
                                         'X (% on 100 MVA)': 'X (% on 100MVA)',
                                         'B (% on 100 MVA)': 'B (% on 100MVA)'}, inplace=True)

        # append network data and future changes
        all_circuits = pd.concat([NGET_Circuits, SHET_Circuits, SPT_Circuits, OFTO_Circuits])
        all_circuits_changes = pd.concat([NGET_Circuit_Changes, SHET_Circuit_Changes, SPT_Circuit_Changes, OFTO_Circuit_Changes])
        all_trafo = pd.concat([NGET_Tx, SHET_Tx, SPT_Tx, OFTO_Tx])
        all_trafo_changes = pd.concat([NGET_Tx_Changes, SHET_Tx_Changes, SPT_Tx_Changes, OFTO_Tx_Changes])

        # clean data to remove rogue types
        # columns_to_cleanse = ['R (% on 100MVA)', 'X (% on 100MVA)', 'B (% on 100MVA)'] - not added due to error
        all_circuits= all_circuits[pd.to_numeric(all_circuits['X (% on 100MVA)'], errors='coerce').notnull()]
        all_circuits_changes= all_circuits_changes[pd.to_numeric(all_circuits_changes['X (% on 100MVA)'], errors='coerce').notnull()]
        all_trafo= all_trafo[pd.to_numeric(all_trafo['X (% on 100MVA)'], errors='coerce').notnull()]
        all_trafo_changes= all_trafo_changes[pd.to_numeric(all_trafo_changes['X (% on 100MVA)'], errors='coerce').notnull()]

        # create circuit dataframe for Great Britain including changes
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
                    print("Warning: Status of row" + str(
                        index) + "in Circuit Changes data needs checking. Ignored from for loop.")
            return all_circuits

        all_circuits_w_changes = apply_circuit_changes(all_circuits, all_circuits_changes)

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
                    print("Warning: Status of row" + str(
                        index) + "in Transformer Changes data needs checking. Ignored from for loop.")
            return all_trafo

        all_trafo_w_changes = apply_trafo_changes(all_trafo, all_trafo_changes)

        self.all_circuits_w_changes = all_circuits_w_changes
        self.all_trafo_w_changes = all_trafo_w_changes


        # create list of bus ids from NGET Circuit and Transformer data in ETYS
        bus_ids_cct = pd.unique(self.all_circuits_w_changes[['Node 1', 'Node 2']].values.ravel('K'))
        bus_ids_tx = pd.unique(self.all_trafo_w_changes[['Node 1', 'Node 2']].values.ravel('K'))
        bus_ids = list(set(list(bus_ids_cct) + list(bus_ids_tx)))


        # convert bus ids list into dataframe and add full name column and sort subs in alphabetical order.
        bus_ids_data = {"Name": bus_ids}
        bus_ids_df = pd.DataFrame(bus_ids_data)
        bus_ids_df = pd.merge(bus_ids_df, self.all_substations, how='left', left_on=bus_ids_df['Name'].str[:4], right_on=self.all_substations['Site Code'].str[:4])
        bus_ids_df['Full Name'] = bus_ids_df['Site Name'].astype(str) + ' ' + bus_ids_df['Voltage (kV)'].astype(str) + 'kV'
        bus_ids_df.sort_values(by=['Site Name'], inplace=True)
        bus_ids_df.reset_index(drop=True, inplace=True)
        # bus_ids_df["Index0"] = bus_ids_df.reset_index().index
        self.bus_ids_df = bus_ids_df


        # """add coordinates to bus_ids dataframe - decided not required and will continue to be handled by Homepage.py"""


    def network_data_initialise_gen_dem_data(self):
        try:
            if self.api_or_local == "api":
                proxies = {
                              "http"  : "http://proxy.invzb.uk.corporg.net:8083",
                              "https" : "http://proxy.invzb.uk.corporg.net:8083"
                            }

                url = "https://www.nationalgrideso.com/document/275586/download"
                response = requests.get(url, proxies = proxies)
                if response.status_code == 200:
                    NGET_Circuits = pd.read_excel(response.content, sheet_name="B-2-1c", skiprows=[0])
                    NGET_Circuit_Changes = pd.read_excel(response.content, sheet_name="B-2-2c", skiprows=[0])
                    NGET_Subs = pd.read_excel(response.content, sheet_name="B-1-1c", skiprows=[0])
                    NGET_Tx = pd.read_excel(response.content, sheet_name="B-3-1c", skiprows=[0])
                    NGET_Tx_Changes = pd.read_excel(response.content, sheet_name="B-3-2c", skiprows=[0])
                #     NGET_Reactive = pd.read_excel(response.content, sheet_name = "B-4-1c", skiprows=[0])
                #     NGET_Reactive_Changes = pd.read_excel(response.content, sheet_name = "B-4-2c", skiprows=[0])
                else:
                    print("Failed to download ETYS Appendix B file from https://www.nationalgrideso.com/document/275586/download")

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
                # GSP_Demand = pd.DataFrame.from_dict(all_data)
                # GSP_Demand = GSP_Demand.groupby('GSP').agg(
                #     {'DemandPk': 'sum', 'DemandAM': 'sum', 'DemandPM': 'sum'}).reset_index()

                url = "https://data.nationalgrideso.com/api/3/action/datastore_search"
                resource_ids = ["000d08b9-12d9-4396-95f8-6b3677664836", "17becbab-e3e8-473f-b303-3806f43a6a10",
                                "64f7908f-f787-4977-93e1-5342a5f1357f"]
                df_names = ["FES_2022_GSP_Info", "TEC_Register", "IC_Register"]
                dfs = {}
                for i, res_id in enumerate(resource_ids):
                    params = {
                        "resource_id": res_id,
                        "limit": 10000,
                        "offset": 0,
                    }
                    all_data = []
                    while True:
                        response = requests.get(url, params=params, proxies = proxies)
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
                TEC_Register = dfs["TEC_Register"]
                IC_Register = dfs["IC_Register"]


            elif self.api_or_local == "local":
                # import TEC, IC, GSP demand data from local path
                TEC_Register = pd.read_csv('../data/TEC_Reg.csv')
                IC_Register = pd.read_csv('../data/IC_Reg.csv')
                GSP_Demand = pd.read_csv('../data/ETYS23_Appendix G_Dem.csv')
                self.GSP_Demand = GSP_Demand[pd.to_numeric(GSP_Demand['24/25'], errors='coerce').notnull()]

            success=True

        except:
            print("Error occured - change selection to api or local")
            success=False
            sys.exit()


        if success:
            # clean TEC Register
            TEC_Register = TEC_Register[~TEC_Register["Project Name"].isin(["Drax (Coal)","Dungeness B","Hartlepool","Hinkley Point B","Uskmouth","Sutton Bridge","Ratcliffe on Soar","West Burton A"])]
            TEC_Register["Generator Name"] = TEC_Register["Project Name"] + " (" + TEC_Register["Customer Name"] + ")"
            TEC_Register['MW Effective From'] = pd.to_datetime(TEC_Register['MW Effective From'], dayfirst=True, errors='coerce')
            TEC_Register['MW Effective From'] = TEC_Register.apply(
                lambda row: datetime.today() if pd.isna(row['MW Effective From']) and row['Project Status'] == 'Built' else row[
                    'MW Effective From'], axis=1)
            TEC_Register.dropna(subset=['MW Effective From'], inplace=True)
            TEC_Register = TEC_Register[TEC_Register['MW Effective From'].dt.year <= int(self.year)]
            TEC_Register['MW Effective From'] = TEC_Register['MW Effective From'].dt.strftime('%d-%m-%Y')
            TEC_Register.reset_index(drop=True, inplace=True)
            self.TEC_Register = TEC_Register

            # clean IC Register
            IC_Register["Generator Name"] = IC_Register["Project Name"] + " (" + IC_Register["Connection Site"] + ")"
            IC_Register = IC_Register[IC_Register["HOST TO"] == "NGET"]
            IC_Register['MW Effective From'] = pd.to_datetime(IC_Register['MW Effective From'], dayfirst=True, errors='coerce')
            IC_Register['MW Effective From'] = IC_Register.apply(
                lambda row: datetime.today() if pd.isna(row['MW Effective From']) and row['Project Status'] == 'Built' else row[
                    'MW Effective From'], axis=1)
            IC_Register.dropna(subset=['MW Effective From'], inplace=True)
            IC_Register = IC_Register[IC_Register['MW Effective From'].dt.year <= int(self.year)]
            IC_Register['MW Effective From'] = IC_Register['MW Effective From'].dt.strftime('%d-%m-%Y')
            IC_Register.reset_index(drop=True, inplace=True)
            self.IC_Register = IC_Register

    def clean_gen_and_dem_data(self):
        # use loop statement to pick out known substations from Connection Site column and match
        # TEC Register first, Interconnector Register second
        self.TEC_Register['bus_name'] = ""
        for index1, row1 in self.TEC_Register.iterrows():
            conn_site = str(row1['Connection Site']).strip()
            subs_names = []
            if not (row1['Connection Site'] == "" or pd.isnull(row1['Connection Site'])):
                for index2, row2 in self.bus_ids_df.iterrows():
                    bus_site_name = (str(row2['Site Name']).strip()).upper()
                    if not (row2['Site Name'] == "" or pd.isnull(row2['Site Name'])):
                        if (bus_site_name.upper() in conn_site.upper()) or (bus_site_name.replace(" MAIN", "").replace("'", "").replace(" ", "").upper() in conn_site.replace(" ", "").replace("'", "").upper()):
                            if bus_site_name.upper() not in subs_names:
                                subs_names.append(bus_site_name.upper())
                    if len(subs_names)>1:
                        for each_subs_1 in subs_names:
                            for each_subs_2 in subs_names:
                                if each_subs_1 != each_subs_2 and each_subs_1.upper() in each_subs_2.upper():
                                    try:
                                        subs_names.remove(each_subs_1)
                                    except:
                                        pass
            subs_names.sort()
            x = ' or '.join(subs_names)
            self.TEC_Register.at[index1, 'bus_name'] = x

        # Interconnector Register
        self.IC_Register['bus_name'] = ""
        for index1, row1 in self.IC_Register.iterrows():
            conn_site = str(row1['Connection Site']).strip()
            subs_names = []
            if not (row1['Connection Site'] == "" or pd.isnull(row1['Connection Site'])):
                for index2, row2 in self.bus_ids_df.iterrows():
                    bus_site_name = (str(row2['Site Name']).strip()).upper()
                    if not (row2['Site Name'] == "" or pd.isnull(row2['Site Name'])):
                        if (bus_site_name.upper() in conn_site.upper()) or (bus_site_name.replace(" MAIN", "").replace("'", "").replace(" ", "").upper() in conn_site.replace(" ", "").replace("'", "").upper()):
                            if bus_site_name.upper() not in subs_names:
                                subs_names.append(bus_site_name.upper())
                    if len(subs_names)>1:
                        for each_subs_1 in subs_names:
                            for each_subs_2 in subs_names:
                                if each_subs_1 != each_subs_2 and each_subs_1.upper() in each_subs_2.upper():
                                    try:
                                        subs_names.remove(each_subs_1)
                                    except:
                                        pass
            subs_names.sort()
            x = ' or '.join(subs_names)
            self.IC_Register.at[index1, 'bus_name'] = x

        # define the Gen_Type for TEC Register based on Plant Type and Generator Name columns.
        # set all in IC Register to Gen_Type = Interconnector
        self.TEC_Register['Gen_Type'] = ""
        for index, row in self.TEC_Register.iterrows():
            if re.search('(?i).*nuclear.*', f"{row['Plant Type']} {row['Generator Name']}"):
                self.TEC_Register.at[index, 'Gen_Type'] = "Nuclear"
            elif re.search('(?i).*wind.*', f"{row['Plant Type']} {row['Generator Name']}"):
                self.TEC_Register.at[index, 'Gen_Type'] = "Wind"
            elif re.search('(?i).*pv|solar.*', f"{row['Plant Type']} {row['Generator Name']}"):
                self.TEC_Register.at[index, 'Gen_Type'] = "PV"
            elif re.search('(?i).*CCGT|CHP|Biomass|gas.*', f"{row['Plant Type']} {row['Generator Name']}"):
                self.TEC_Register.at[index, 'Gen_Type'] = "CCGT/CHP/Biomass"
            elif re.search('(?i).*pump|hydro|tidal.*', f"{row['Plant Type']} {row['Generator Name']}"):
                self.TEC_Register.at[index, 'Gen_Type'] = "Hydro/Pump/Tidal"
            elif re.search('(?i).*energy storage|battery|bess|grid park|energy park.*', f"{row['Plant Type']} {row['Generator Name']}"):
                self.TEC_Register.at[index, 'Gen_Type'] = "BESS / Energy Park"
            else:
                self.TEC_Register.at[index, 'Gen_Type'] = "Other"
        self.IC_Register['Gen_Type'] = "Interconnector"

        # cleanse demand data and add column with bus_id index number - TO BE DONE!
        bus_ids_df_copy = self.bus_ids_df[['Name', 'Full Name']]
        self.GSP_Demand = (pd.merge(self.GSP_Demand, bus_ids_df_copy, how='left', left_on=self.GSP_Demand['Node'].str[:6], right_on=bus_ids_df_copy['Name'].str[:6])).drop(columns=['key_0'])


call = NetworkData(2028, 'local')
call.network_data()
call.network_data_initialise_gen_dem_data()
call.clean_gen_and_dem_data()



