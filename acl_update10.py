import csv
import paramiko
from napalm import get_network_driver
from rich import print as rprint
from concurrent.futures import ThreadPoolExecutor
import smtplib
from email.mime.text import MIMEText
from datetime import datetime



class AccessListUpdater:
    def __init__(self, hostname, username, password, device_type='ios'):
        self.hostname = hostname
        self.username = username
        self.password = password
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
        '''try:
            self.device.load_merge_candidate(config='\n'.join(acl_commands))
            self.device.commit_config()
            rprint(f'✅ Access list updated successfully')'''
        try:
            if 'nxos' in self.device.platform:
                self.device.load_merge_candidate(config='\n'.join(acl_commands))
            else:
                self.device.load_merge_candidate(config='\n'.join(acl_commands))
            self.device.commit_config()
            rprint(f'✅ Access list updated successfully on {self.hostname}!')

            # Check if SSH port is accessible after the change
            if self.check_ssh_port():
                rprint(f'✅ SSH connection success for device {self.hostname} after change')
                
            else:
                rprint(f'[red]❌ SSH connection failed for device {self.hostname} after change!, rolling back config.')
                self.device.rollback()
                rprint(f'[red]❌ ACL update rolled back for {self.hostname}')
                status = 'Failed'
                return
            status = 'Success'
        # Roll back to the previous configuration in case of failure
        except Exception as e:
            rprint(f'[red]: ' + str(e))
            self.device.rollback()
            print(f'❌ Access list update rolled back')
            #status = 'Failed'
            report_row = {'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                      'Hostname': self.hostname,
                      'ACL Name': acl_name,
                      'Status': 'Failed'}
        # Write the report to the CSV file
            with open('report.csv', 'a', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=report_row.keys())
                if file.tell() == 0:
                    writer.writeheader()
                writer.writerow(report_row)
        
        report_row = {'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                      'Hostname': self.hostname,
                      'ACL Name': acl_name,
                      'Status': status}
        # Write the report to the CSV file
        with open('report.csv', 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=report_row.keys())
            if file.tell() == 0:
                writer.writeheader()
            writer.writerow(report_row)

    def check_ssh_port(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh.connect(self.hostname, username=self.username, password=self.password, timeout=5)
            transport = ssh.get_transport()
            transport.send_ignore()
            ssh.close()
            return True
        except:
            ssh.close()
            return False

    '''def send_email(body):
        msg = MIMEText(body)
        msg['Subject'] = 'ACL Update Report'
        msg['From'] = 'guian_fuglencio@yahoo.com'
        msg['To'] = 'guian_fuglencio@yahoo.com'
        s = smtplib.SMTP('smtp.example.com')
        s.send_message(msg)
        s.quit()'''


if __name__ == '__main__':
    with open('devices.csv', 'r') as file:
        reader = csv.DictReader(file)
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = []
            for row in reader:
                if 'nexus' in row['machine type'].lower():
                    device_type = 'nxos_ssh'
                else:
                    device_type = 'ios'

                acl_updater = AccessListUpdater(hostname=row['IP Address'], username='cisco', password='cisco',
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
                        #'permit ip 172.20.10.0/28 any',
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
