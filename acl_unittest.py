from napalm import get_network_driver
import unittest

##########################
# Global Variables
##########################
#username = args.username
username = 'cisco'
#password = args.password
password = 'cisco'


class AccessListUpdater:
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.driver = get_network_driver('ios')
        self.device = None

    def update_access_list(self, acl_name, acl_commands):
        # Connect to the device
        self.connect()

        # Backup the current configuration
        self.device.backup('pre-update-config')

        # Try to apply the access list configuration commands
        try:
            self.device.load_merge_candidate(config='\n'.join(acl_commands))
            self.device.commit_config()
            print('Access list updated successfully!')

            # Check if device is still accessible after the change
            ping_test = self.device.ping(destination='8.8.8.8')
            if not ping_test['success']:
                raise Exception('Device is not accessible after change, rolling back config.')

        # Roll back to the previous configuration in case of failure
        except Exception as e:
            print('Failed to update access list: ' + str(e))
            self.device.rollback()
            print('Access list update rolled back successfully!')

        # Disconnect from the device
        self.disconnect()

    def has_config_line(self, config_line):
        # Connect to the device
        self.connect()

        show_command = 'show running-config | include ' + config_line
        output = self.device.cli([show_command])
        has_line = len(output[show_command]) > 0

        # Disconnect from the device
        self.disconnect()

        return has_line

    def connect(self):
        self.device = self.driver(hostname=self.hostname, username=self.username, password=self.password)
        self.device.open()

    def disconnect(self):
        if self.device:
            self.device.close()
            self.device = None

class TestAccessListUpdater(unittest.TestCase):
    def setUp(self):
        self.acl_updater = AccessListUpdater(hostname='192.168.1.1', username='admin', password='password')

    def test_has_password_of_last_resort(self):
        has_password_of_last_resort = self.acl_updater.has_config_line('password 7 ')
        self.assertTrue(has_password_of_last_resort, 'Device does not have password of last resort')

if __name__ == '__main__':
    unittest.main()
