from napalm import get_network_driver

# Define the device connection details
driver = get_network_driver('ios')
device = driver(hostname='172.20.10.5', username='cisco', password='cisco')
device.open()

# Define the access list configuration commands
acl_name = 'my_access_list'
acl_commands = [
    'no access-list ' + acl_name,
    'access-list ' + acl_name + ' permit ip any any'
]

# Backup the current configuration
device.backup('pre-update-config')

# Try to apply the access list configuration commands
try:
    device.load_merge_candidate(config='\n'.join(acl_commands))
    device.commit_config()
    print('Access list updated successfully!')

    # Check if device is still accessible after the change
    ping_test = device.ping(destination='8.8.8.8')
    if not ping_test['success']:
        raise Exception('Device is not accessible after change, rolling back config.')

# Roll back to the previous configuration in case of failure
except Exception as e:
    print('Failed to update access list: ' + str(e))
    device.rollback()
    print('Access list update rolled back successfully!')

# Close the device connection
device.close()
