import csv
import concurrent.futures
from netmiko import ConnectHandler

def get_device_credentials(device_csv):
    """
    Read the device IP, username, and password from the csv file.
    """
    with open(device_csv, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row["IP Address"]

def check_cisco_passwords(ip, username, password):
    """
    Test if a given device is using compliant Cisco passwords.
    """
    device = {
        "device_type": "cisco_ios",
        "ip": ip,
        "username": 'cisco',
        "password": 'cisco',
    }

    output = ""
    try:
        with ConnectHandler(**device) as ssh:
            output = ssh.send_command("show running-config | include secret|username|password")
    except Exception as e:
        print(f"Error connecting to device {ip}: {str(e)}")
        return f"{ip}: {str(e)}"

    errors = []
    if "enable secret" in output:
        errors.append(f"{ip}: Enable secret is not compliant.")
    if "username" in output and "secret" in output:
        errors.append(f"{ip}: Username secret is not compliant.")
    if "password" in output and "7 " in output:
        errors.append(f"{ip}: Password encryption is not compliant.")
    
    if not errors:
        print(f"{ip}: Compliant")
    else:
        for error in errors:
            print(error)

if __name__ == "__main__":
    device_csv = "devices.csv"

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        device_credentials = get_device_credentials(device_csv)
        for ip in device_credentials:
            executor.submit(check_cisco_passwords, ip, 'cisco', 'cisco')
