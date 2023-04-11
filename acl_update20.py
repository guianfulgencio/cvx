import csv
import argparse
from napalm import get_network_driver
from rich import print as rprint
from concurrent.futures import ThreadPoolExecutor
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException


class AccessListUpdater:
    def __init__(self, hostname, device_name, username, password, device_type='ios'):
        self.hostname = hostname
        self.device_name = device_name
        self.username = username
        self.password = password
        self.device_type = device_type
        self.driver = get_network_driver(device_type)
        self.device = None

    def connect(self):
        self.device = self.driver(hostname=self.hostname, username=self.username, password=self.password)
        print(f"Connecting to {self.hostname}...")
        self.device.open()

    def disconnect(self):
        self.device.close()
        self.device = None

    def update_access_list(self, acl_name, acl_commands):
        # Backup the current configuration
        # self.device.backup('pre-update-config')
        # Try to apply the access list configuration commands
        #global report_row
        try:
            self.device.load_merge_candidate(config='\n'.join(acl_commands))
            self.device.commit_config()
            rprint(f'✅ Access list updated successfully on {self.hostname}!')

            # Check if SSH port is accessible after the change
            if self.check_ssh_port():
                rprint(f'✅ SSH connection success for device {self.hostname} after change')   
                status = 'Success'             
            else:
                rprint(f'[red]❌ SSH connection failed for device {self.hostname} after change, rolling back config.')
                self.device.rollback()
                rprint(f'[red]❌ Update Failed. ACL rolled back for {self.hostname}')
                status = 'Failed'
                #return
            
        # Roll back to the previous configuration in case of failure
        except Exception as e:
            rprint(f'[red]: ' + str(e))
            self.device.rollback()
            rprint(f'[red]❌ ACL update rolled back for device {self.hostname}')
            status = 'Failed'
        report_row = {'Timestamp': datetime.now().strftime('%Y-%m-%d'),
                    'Device Name': self.device_name,
                    'IP address': self.hostname,
                    'Status': status}
        # Write the report to the CSV file
        report_name = f"ACL Report {datetime.now().strftime('%d-%b-%Y')}.csv"
        with open(report_name, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=report_row.keys())
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(report_row)
        
    def check_ssh_port(self):
        if self.device_type == 'ios':
            device_type = 'cisco_ios'
        elif self.device_type  == 'nxos_ssh':
            device_type = 'cisco_nxos'
        else:
            device_type = self.device_type
        device = {
            'device_type': device_type,
            'ip': self.hostname,
            'username': self.username,
            'password': self.password,
        }
        try:
            with ConnectHandler(**device) as conn:
                conn.find_prompt()
                return True
        except (NetmikoTimeoutException, NetmikoAuthenticationException):
            return False

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
            results = []
            for row in reader:
                if 'nexus' in row['machine type'].lower():
                    device_type = 'nxos_ssh'
                else:
                    device_type = 'ios'

                acl_updater = AccessListUpdater(hostname=row['IP Address'], device_name=row['Device Name'], username=username, password=password,
                                                device_type=device_type)
                acl_updater.connect()

                acl_name = '20'
                if device_type == 'ios':
                    acl_commands = [
                        'no ip access-list standard ' + acl_name,
                        'ip access-list standard ' + acl_name,
                        'permit 172.20.10.0 0.0.0.15',
                        'permit 139.65.136.0 0.0.3.255',
                        'permit 139.65.140.0 0.0.3.255',
                        'deny any log'
                    ]
                else:
                    acl_commands = [
                        'no ip access-list ' + acl_name,
                        'ip access-list ' + acl_name,
                        'permit ip 172.20.10.0/28 any',
                        'permit ip 139.65.136.0/22 any',
                        'permit ip 139.65.140.0/22 any',
                        'deny ip any any log'
                    ]

                # Schedule the update as a concurrent task
                future = executor.submit(acl_updater.update_access_list, acl_name, acl_commands)
                futures.append(future)

            # Wait for all the updates to complete
            for future in futures:
                future.result()
