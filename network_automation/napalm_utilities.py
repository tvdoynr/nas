import datetime
import json
import os
import re
import telnetlib
import time

from napalm import get_network_driver


def switch_get_info(ip, username, password, mode):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    # show ip interface brief
    if mode == "i":
        interfaces = device.get_interfaces_ip()
        print("IP Interfaces Brief:")
        print(json.dumps(interfaces, indent=4))

    # show vlan brief
    if mode == "v":
        vlans = device.get_vlans()
        print("\nVLAN Brief:")
        print(json.dumps(vlans, indent=4))

    # show ip route
    if mode == "r":
        routes = device.get_route_to()
        print("\nIP Route:")
        print(json.dumps(routes, indent=4))

    if mode == "f":
        device_facts = device.get_facts()
        print('Cihaz Bilgileri:')
        print(f'  Hostname: {device_facts["hostname"]}')
        print(f'  Model: {device_facts["model"]}')
        print(f'  Serial Number: {device_facts["serial_number"]}')
        print(f'  Uptime: {device_facts["uptime"]}')

    # Close the connection
    device.close()

def pc_telnet(ip, port, command):
    tn = telnetlib.Telnet(ip, port)

    time.sleep(1)

    tn.write(command.encode('ascii') + b"\n")
    time.sleep(1)  # Wait for the command to execute
    command_output = tn.read_very_eager().decode('ascii')

    print(command_output)

    tn.close()


def switch_get_backup(ip, username, password, path):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    try:
        config = device.get_config(retrieve='running')
        facts = device.get_facts()

        run_conf = config['running']
        run_config = re.sub(r'Building configuration.*|Current configuration.*|end', '', run_conf)

        date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        hostname = facts['hostname']

        backup_path = os.path.join(path, 'backup_config')
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)

        file_path = os.path.join(backup_path, f"{hostname}_{date}_running-config")
        with open(file_path, 'w') as file:
            file.write(run_config)

        device.close()

        print(f"Configuration backed up to {file_path}")
        return file_path

    except Exception as e:
        print(f"An error occurred: {e}")
        device.close()


def preprocess_config(config):
    config_lines = config.splitlines()

    # Filters to exclude problematic lines
    exclude_patterns = [
        r'\bboot--marker\b',
        r'\bvlan internal allocation policy ascing\b'
    ]

    processed_lines = []
    for line in config_lines:
        if not any(re.search(pattern, line) for pattern in exclude_patterns):
            processed_lines.append(line)

    return "\n".join(processed_lines)


def switch_restore_backup(ip, username, password, backup_file):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    try:
        with open(backup_file, 'r') as file:
            backup_config = file.read()

        filtered_config = preprocess_config(backup_config)

        device.load_merge_candidate(config=filtered_config)
        diff = device.compare_config()

        if diff:
            print("Differences detected, applying changes:")
            print(diff)
            device.commit_config()
            print(f"Backup configuration from {backup_file} restored successfully")
        else:
            print("No changes required.")

    except Exception as e:
        print(f"An error occurred: {e}")
        try:
            device.discard_config()
        except Exception as discard_e:
            print(f"An error occurred while discarding config: {discard_e}")

    finally:
        device.close()