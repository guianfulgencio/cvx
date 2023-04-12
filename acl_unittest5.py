import csv
import unittest
from concurrent.futures import ThreadPoolExecutor
from netmiko import ConnectHandler


class TestCiscoPasswords(unittest.TestCase):

    def send_command_to_device(self, device_type, ip, username, password, command):
        device = {
            "device_type": device_type,
            "ip": ip,
            "username": username,
            "password": password,
        }

        try:
            with ConnectHandler(**device) as ssh:
                output = ssh.send_command(command)
            return output

        except Exception as e:
            print(f"Error connecting to device {ip}: {str(e)}")
            return None

    def test_cisco_ios_passwords(self, ip, username, password):
        ios_device = {
            "device_type": "cisco_ios",
            "ip": ip,
            "username": username,
            "password": password,
        }

        output = self.send_command_to_device(**ios_device, command="show running-config | include secret|username")
        print(output)
        self.assertIn("enable secret 9 $9$Tr.fJkiWqTDLNE$uZnlmaQm7TjDezx3X59P.rZBh3diBR6z41Op8/igj5g", output)
        self.assertIn("username admin secret 9 $9$.E8i4elg0kVv5U$mhwRPfT6.rIGwYtLKaL2PLkajzxH2s7rBcSPDPiureM", output)
        #self.assertIn("password 7 032E0B12035A31020F0700044932", output)

    def test_cisco_nxos_passwords(self, ip, username, password):
        nxos_device = {
            "device_type": "cisco_nxos",
            "ip": ip,
            "username": username,
            "password": password,
        }

        output = self.send_command_to_device(**nxos_device, command="show running-config | include secret|username|password")
        self.assertIn("admin password 5 $1$032E0B12035A31020F0700044932", output)

if __name__ == '__main__':
    with open('devices.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)

        with ThreadPoolExecutor(max_workers=100) as executor:
            results = []

            for row in csv_reader:
                if row['machine type'] == 'ios':
                    results.append(executor.submit(TestCiscoPasswords().test_cisco_ios_passwords, row['IP Address'], 'cisco', 'cisco'))
                elif row['machine type'] == 'Nexus':
                    results.append(executor.submit(TestCiscoPasswords().test_cisco_nxos_passwords, row['IP Address'], 'cisco', 'cisco'))
                else:
                    print(f"Unsupported device type for IP address {row['ip']}: {row['machine type']}")

            for result in results:
                result.result()
