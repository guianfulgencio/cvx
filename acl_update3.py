from napalm import get_network_driver

class AccessListUpdater:
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.driver = get_network_driver('ios')
        self.device = None
        
    def connect(self):
        self.device = self.driver(hostname=self.hostname, username=self.username, password=self.password)
        self.device.open()
    
    def disconnect(self):
        self.device.close()
        self.device = None
        
    def update_access_list(self, acl_name, acl_commands):
        # Try to apply the access list configuration commands
        try:
            self.device.load_merge_candidate(config='\n'.join(acl_commands))
            self.device.commit_config()
            print('Access list updated successfully!')

            # Check if device is still accessible after the change
            ping_test = self.device.ping(destination='172.20.10.13')
            #self.device.open()
            #self.device.close()
            print('Device is accessible')
            if not ping_test['success']:
                raise Exception('Device is not accessible after change, rolling back config.')

        # Roll back to the previous configuration in case of failure
        except Exception as e:
            print('Failed to update access list: ' + str(e))
            self.device.discard_config()
        
if __name__ == '__main__':
    acl_updater = AccessListUpdater(hostname='172.20.10.5', username='cisco', password='cisco')
    acl_updater.connect()
    
    acl_name = '20'
    acl_commands = [
        'no ip access-list standard ' + acl_name,
        'ip access-list standard ' + acl_name,
        'permit 139.65.136.0 0.0.3.255',
        'permit 139.65.140.0 0.0.3.255',
        'deny   any log'
    ]
    
    acl_updater.update_access_list(acl_name, acl_commands)
    
    acl_updater.disconnect()
