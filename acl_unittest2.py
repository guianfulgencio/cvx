import unittest
from netmiko import ConnectHandler


class TestCiscoPasswords(unittest.TestCase):

    def send_command_to_device(self, ip, username, password, command):
        device = {
            "device_type": "cisco_ios",
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

    def test_admin_password(self):
        # replace 172.20.10.12 with the IP address of the device being tested
        output = self.send_command_to_device("172.20.10.12", "cisco", "cisco", "show running-config | include username cisco")
        self.assertTrue("cisco1" in output, "Admin password is not compliant.")

    #def test_enable_password(self):
        # replace 172.20.10.12 with the IP address of the device being tested
        #output = self.send_command_to_device("172.20.10.12", "cisco", "cisco", "show running-config | include enable password")
        #self.assertTrue("P@ssw0rd" in output, "Enable password is not compliant.")

    #def test_console_password(self):
        # replace 172.20.10.12 with the IP address of the device being tested
        #output = self.send_command_to_device("172.20.10.12", "cisco", "cisco", "show running-config | include line console 0 password")
        #self.assertTrue("cisco" in output, "POLR is not compliant.")

if __name__ == '__main__':
    unittest.main()
