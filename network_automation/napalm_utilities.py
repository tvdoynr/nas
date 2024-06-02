import datetime
import os
import re
import telnetlib
import time

from napalm import get_network_driver


def switch_get_info(ip, username, password, mode):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    result = {}

    # show ip interface brief
    if mode == "i":
        interfaces = device.get_interfaces_ip()
        result['interfaces'] = interfaces
        # print("IP Interfaces Brief:")
        # print(json.dumps(interfaces, indent=4))

    # show vlan brief
    if mode == "v":
        vlans = device.get_vlans()
        result['vlans'] = vlans
        # print("\nVLAN Brief:")
        # print(json.dumps(vlans, indent=4))

    # show ip route
    if mode == "r":
        output = device.cli(['show ip route'])
        routing_table = output['show ip route']
        # print("Routing Table:")
        # print(routing_table)

        routes = []
        for line in routing_table.split('\n'):
            if 'via' in line:
                route_parts = line.split()
                route = {}
                route['protocol'] = route_parts[0].strip('*')
                route['network'] = route_parts[1]
                route['distance'] = route_parts[2].strip('[]').split('/')[0]
                route['metric'] = route_parts[2].strip('[]').split('/')[1]
                route['next_hop'] = route_parts[4]
                if len(route_parts) > 5:
                    route['interface'] = route_parts[5]
                else:
                    route['interface'] = ''
                routes.append(route)

        result['routes'] = routes
    if mode == "f":
        device_facts = device.get_facts()
        result['facts'] = {
            'hostname': device_facts["hostname"],
            'model': device_facts["model"],
            'serial_number': device_facts["serial_number"],
            'uptime': device_facts["uptime"]
        }
        # print('Cihaz Bilgileri:')
        # print(f'  Hostname: {device_facts["hostname"]}')
        # print(f'  Model: {device_facts["model"]}')
        # print(f'  Serial Number: {device_facts["serial_number"]}')
        # print(f'  Uptime: {device_facts["uptime"]}')

    # Close the connection
    device.close()

    return result

def pc_telnet(ip, port, command):
    tn = telnetlib.Telnet(ip, port)

    time.sleep(1)

    tn.write(command.encode('ascii') + b"\n")
    time.sleep(1)  # Wait for the command to execute
    command_output = tn.read_very_eager().decode('ascii')

    # print(command_output)

    tn.close()

    return command_output


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


def create_vlan(ip, username, password, vlan_id, vlan_name):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    try:
        # Enter enable mode
        device.device.send_command_timing("enable")

        # Enter configuration mode
        device.device.send_command_timing("configure terminal")

        # Construct the configuration commands to create a VLAN
        config_commands = [
            f"vlan {vlan_id}",
            f"name {vlan_name}"
        ]

        # Execute each command using device.cli()
        for command in config_commands:
            device.device.send_command_timing(command)

        # Exit configuration mode
        device.device.send_command_timing("end")

        save_configuration(device)

        print(f"VLAN {vlan_id} ({vlan_name}) created successfully")

    except Exception as e:
        print(f"An error occurred while creating VLAN: {e}")

    finally:
        device.close()

def create_route(ip, username, password, destination_network, subnet_mask, next_hop):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    try:
        # Enter enable mode
        device.device.send_command_timing("enable")

        # Enter configuration mode
        device.device.send_command_timing("configure terminal")

        # Construct the configuration command to create a static route
        config_command = f"ip route {destination_network} {subnet_mask} {next_hop}"

        # Execute the command using device.cli()
        device.device.send_command_timing(config_command)

        # Exit configuration mode
        device.device.send_command_timing("end")

        # Save the configuration
        save_configuration(device)

        print(f"Static route to {destination_network} via {next_hop} created successfully")

    except Exception as e:
        print(f"An error occurred while creating the route: {e}")

    finally:
        device.close()


def create_vlan_interface(ip, username, password, vlan_id, vlan_ip, vlan_subnet_mask):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    try:
        # Enter enable mode
        print("Entering enable mode")
        output = device.device.send_command_timing("enable")
        print(output)

        # Enter configuration mode
        print("Entering configuration mode")
        output = device.device.send_command_timing("configure terminal")
        print(output)

        # Construct the configuration commands to create a VLAN and VLAN interface
        config_commands = [
            f"interface vlan {vlan_id}",
            f"ip address {vlan_ip} {vlan_subnet_mask}",
            "no shutdown"
        ]

        # Execute each command using device.cli()
        for command in config_commands:
            print(f"Executing command: {command}")
            output = device.device.send_command_timing(command)
            print(output)

        # Exit configuration mode
        print("Exiting configuration mode")
        output = device.device.send_command_timing("end")
        print(output)

        save_configuration(device)

        print(f"VLAN {vlan_id} with IP {vlan_ip}/{vlan_subnet_mask} created successfully")

    except Exception as e:
        print(f"An error occurred while creating VLAN interface: {e}")

    finally:
        device.close()
def save_configuration(device):
    try:
        # Save the configuration
        device.device.send_command_timing("write memory")

        # Wait for the command to complete
        time.sleep(10)

        print("Configuration saved successfully")
    except Exception as e:
        print(f"An error occurred while saving the configuration: {e}")