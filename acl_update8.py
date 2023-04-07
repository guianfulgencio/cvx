import csv
import paramiko
from napalm import get_network_driver
from rich import print as rprint

class AccessListUpdater:
    def __init__(self, hostname, username, password, device_type='ios'):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.driver = get_network_driver(device_type)
        self.device = None

    def connect(self):
        self.device = self.driver(hostname=self.hostname, username=self.username, password=self.password)
        self.device.open()

    def disconnect(self):
        self.device.close()
        self.device = None

    def update_access_list(self, acl_name, acl_commands):
        # Backup the current configuration
        # self.device.backup('pre-update-config')

        # Try to apply the access list configuration commands
        try:
            self.device.load_merge_candidate(config='\n'.join(acl_commands))
            self.device.commit_config()
            rprint(f'✅ Access list updated successfully!')

            # Check if SSH port is accessible after the change
            if not self.check_ssh_port():
                raise Exception('SSH port is not accessible after change, rolling back config.')

        # Roll back to the previous configuration in case of failure
        except Exception as e:
            rprint(f'[red]: ' + str(e))
            self.device.rollback()
            print('Access list update rolled back successfully!')

    def check_ssh_port(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.hostname, username=self.username, password=self.password, timeout=5)
        try:
            transport = ssh.get_transport()
            transport.send_ignore()
            ssh.close()
            return True
        except:
            ssh.close()
            return False


if __name__ == '__main__':
    with open('devices.csv', 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if 'nexus' in row['machine type'].lower():
                device_type = 'nxos_ssh'
            else:
                device_type = 'ios'

            acl_updater = AccessListUpdater(hostname=row['IP Address'], username='cisco', password='cisco',
                                            device_type=device_type)
            acl_updater.connect()

            acl_name = 'standard 20'
            if device_type == 'ios':
                acl_commands = [
                    'no ip access-list ' + acl_name,
                    'ip access-list ' + acl_name,
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

            acl_updater.update_access_list(acl_name, acl_commands)

            acl_updater.disconnect()
