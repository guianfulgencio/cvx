"""
Script to fetch and pull device list from Solarwinds
This script will generate a csv file named "device_list.csv" containing the devices
that has been queried from Solarwinds.
"""
import csv
import argparse
import urllib3
from orionsdk import SwisClient
from rich import print as rprint


##########################
# Script Argument
##########################
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
parser = argparse.ArgumentParser(description="Fetch and pull devices list from all regions")
parser.add_argument('-u', '--username', type=str, metavar='',\
    help='SolarWinds username', required=True)
parser.add_argument('-p', '--password', type=str, metavar='',\
    help='SolarWinds password', required=True)
parser.add_argument('-us', '--us_npm_server', type=str, metavar='',\
    help='SolarWinds NPM US server', required=True)
parser.add_argument('-emea', '--emea_npm_server', type=str, metavar='',\
    help='SolarWinds NPM EMEA server', required=True)
parser.add_argument('-apac', '--apac_npm_server', type=str, metavar='',\
    help='SolarWinds NPM APAC server', required=True)
args = parser.parse_args()

npm_server_us = args.us_npm_server
npm_server_emea = args.emea_npm_server
npm_server_apac = args.apac_npm_server
sw_username = args.username
sw_password = args.password


##########################
# Solarwinds Query function
##########################
def solarwinds_query(server, username, password, region):
    '''
    Get all device list from Solarwinds using defined Query
        - server => solarwinds npm server ip address
        - username => solarwinds username
        - password => solarwinds password
        - region => solarwinds region
    '''
    rprint(f"[#FFF833]Querying {region} devices from Orion NPM server {server}... [/#FFF833]")
    swis = SwisClient(server, username, password)
    # import ipdb; ipdb.set_trace()
    results = swis.query("SELECT DisplayName, IP_address, MachineType, IOSversion,\
        Vendor FROM Orion.Nodes where DisplayName like '%PHRCSL34F13%' or DisplayName like '%BIR240SL1%'or DisplayName like '%ALMRA01%' order by DisplayName asc")
    output = []
    for row in results['results']:
        device_name = "{DisplayName}".format(**row).split('.')[0]
        ip_address = "{IP_address}".format(**row)
        machine_type = "{MachineType}".format(**row)
        ios_version = "{IOSversion}".format(**row)
        if not ios_version:
            ios_version = "None"

        device_info = {
                "Device Name": device_name,
                "IP Address": ip_address,
                "Machine Type": machine_type,
                "IOS Version": ios_version,
                "Region": region
            }
        output.append(device_info)

        rprint(f"[#43FF33]✅ Successfully fetched and copied Hostname: {device_name} |"
            f" IP Address: {ip_address} | Machine Type: {machine_type} | IOS Version: {ios_version}"
            f" | Region: {region} [/#43FF33]")

    rprint(f"[cyan]{region} device count: {len(output)}[/cyan]")
    return output


##########################
# Main Script
##########################
def main():
    '''
    Main Script
    '''
    servers = [npm_server_us, npm_server_emea, npm_server_apac]
    regions = ['US', 'EMEA', 'APAC']
    results = []
    for server, region in zip(servers, regions):
        region_device_list = solarwinds_query(server, sw_username, sw_password, region)
        results += region_device_list

    with open('device_list.csv', 'w', newline='') as us_csv_file:
        fieldnames  = ['Device Name', 'IP Address', 'Machine Type', 'IOS Version', 'Region']
        writer = csv.DictWriter(us_csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(result)


##########################
# Run Script
##########################
if __name__ == "__main__":
    main()
