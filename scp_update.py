import csv
import argparse
from rich import print as rprint
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
from concurrent.futures import ThreadPoolExecutor

def configure_scp_server(hostname, device_type, username, password):
    if device_type != 'ios':
        rprint(f'[red]❌ SCP server configuration is not supported on {device_type} devices')
        return False
    try:
        device = {
            'device_type': 'cisco_ios',
            'ip': hostname,
            'username': username,
            'password': password,
        }
        with ConnectHandler(**device) as conn:
            conn.send_command('ip scp server enable')
        rprint(f'[green]✅ SCP server enabled on {hostname}')
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        rprint(f'[red]❌ Failed to configure SCP server on {hostname}: {e}')

if __name__ == '__main__':
    ##########################
    # Script Arguments
    ##########################
    parser = argparse.ArgumentParser(description="Credential to update ACL")
    parser.add_argument('-u', '--username', type=str, metavar='',\
        help='Username to access network device', required=True)
    parser.add_argument('-p', '--password', type=str, metavar='',\
        help='Password to access network device', required=True)
    args = parser.parse_args()
    username = args.username
    password = args.password
    with open('devices.csv', 'r') as file:
        reader = csv.DictReader(file)
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            for row in reader:
                hostname = row['IP Address']
                device_type = row['machine type'].lower()
                future = executor.submit(configure_scp_server, hostname, device_type, username=username, password=password)
                futures.append(future)
            for future in futures:
                future.result()
