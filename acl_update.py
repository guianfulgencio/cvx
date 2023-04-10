from napalm import get_network_driver

##########################
# Global Variables
##########################
#username = args.username
username = 'cisco'
#password = args.password
password = 'cisco'
#hostname = '172.20.10.5'

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
        # Backup the current configuration
        #self.device.backup('pre-update-config')

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
        
if __name__ == '__main__':
    acl_updater = AccessListUpdater(hostname='172.20.10.5', username='cisco', password='cisco')
    acl_updater.connect()
    
    acl_name = 'standard 20'
    acl_commands = [
        'no ip access-list ' + acl_name,
        'ip access-list ' + acl_name,
        'permit 139.65.136.0 0.0.3.255',
        'permit 139.65.140.0 0.0.3.255',
        'deny   any log'
    ]
    
    acl_updater.update_access_list(acl_name, acl_commands)
    
    acl_updater.disconnect()