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

    def test_device_passwords(self, device_type, ip, username, password, expected_output):
        output = self.send_command_to_device(device_type, ip, username, password, command="show running-config | include secret")
        self.assertIn(expected_output, output)

    def test_cisco_ios_passwords(self):
        ios_device = {
            "device_type": "cisco_ios",
            "ip": "172.20.10.12",
            "username": "cisco",
            "password": "cisco",
        }
        expected_output = "enable secret 9 $9$Tr.fJkiWqTDLNE$uZnlmaQm7TjDezx3X59P.rZBh3diBR6z41Op8/igj5g\nusername cisco privilege 15 password 0 cisco\nusername admin secret 9 $9$.E8i4elg0kVv5U$mhwRPfT6.rIGwYtLKaL2PLkajzxH2s7rBcSPDPiureM"
        self.test_device_passwords(**ios_device, expected_output=expected_output)

    def test_cisco_nxos_passwords(self):
        nxos_device = {
            "device_type": "cisco_nxos",
            "ip": "192.168.1.2",
            "username": "admin",
            "password": "password123",
        }
        expected_output = "admin password 5 $1$032E0B12035A31020F0700044932"
        self.test_device_passwords(**nxos_device, expected_output=expected_output)


if __name__ == '__main__':
    with open('devices.csv', 'r') as f:
        reader = csv.DictReader(f)
        with ThreadPoolExecutor(max_workers=100) as executor:
            results = []
            for row in reader:
                if row['machine type'] == 'ios':
                    results.append(executor.submit(TestCiscoPasswords().test_cisco_ios_passwords))
                elif row['machine type'] == 'Nexus':
                    results.append(executor.submit(TestCiscoPasswords().test_cisco_nxos_passwords))

            for result in results:
                try:
                    result.result()
                    print('Test passed.')
                except AssertionError:
                    print('Test failed.')
