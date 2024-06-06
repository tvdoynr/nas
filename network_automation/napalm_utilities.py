import datetime
import json
import os
import re
import telnetlib
import time

from django.conf import settings
from napalm import get_network_driver

from network_automation.models import ConfigurationBackup, Interface, Vlan, Route


def switch_get_info(ip, username, password, mode):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    result = {}

    # show ip interface brief
    if mode == "i":
        interfaces = device.get_interfaces_ip()
        result['interfaces'] = interfaces

    # show vlan brief
    if mode == "v":
        vlans = device.get_vlans()
        result['vlans'] = vlans

    # show ip route
    if mode == "r":
        output = device.cli(['show ip route'])
        routing_table = output['show ip route']

        routes = []
        for line in routing_table.split('\n'):
            if any(proto in line for proto in ['via', 'is directly connected']):
                route_parts = line.split()
                route = {}
                route['protocol'] = route_parts[0].strip('*')
                route['network'] = route_parts[1]
                if 'via' in line:
                    route['distance'] = route_parts[2].strip('[]').split('/')[0]
                    route['metric'] = route_parts[2].strip('[]').split('/')[1]
                    route['next_hop'] = route_parts[4]
                    route['interface'] = route_parts[5] if len(route_parts) > 5 else ''
                else:
                    route['distance'] = '0'
                    route['metric'] = '0'
                    route['next_hop'] = route_parts[5]
                    route['interface'] = route_parts[3] if len(route_parts) > 3 else ''
                routes.append(route)

        result['routes'] = routes

    # show device info
    if mode == "f":
        device_facts = device.get_facts()
        result['facts'] = {
            'hostname': device_facts["hostname"],
            'model': device_facts["model"],
            'serial_number': device_facts["serial_number"],
            'uptime': device_facts["uptime"]
        }

    device.close()

    return result


def pc_telnet(ip, port, command):
    tn = telnetlib.Telnet(ip, port)

    time.sleep(1)

    tn.write(command.encode('ascii') + b"\n")
    time.sleep(1)  # Wait for the command to execute
    command_output = tn.read_very_eager().decode('ascii')

    tn.close()

    return command_output


def switch_get_backup(ip, username, password):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    config = device.get_config(retrieve='running')
    facts = device.get_facts()

    run_conf = config['running']
    run_config = re.sub(r'Building configuration.*|Current configuration.*|end', '', run_conf)

    date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    hostname = facts['hostname']

    backup_path = os.path.join(settings.STATICFILES_DIRS[0], 'backup_config')
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)

    file_path = os.path.join(backup_path, f"{hostname}_{date}_running-config")
    with open(file_path, 'w') as file:
        file.write(run_config)

    device.close()

    print(f"Configuration backed up to {file_path}")
    return file_path


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

    with open(backup_file, 'r') as file:
        backup_config = file.read()

    filtered_config = preprocess_config(backup_config)

    device.load_merge_candidate(config=filtered_config)
    diff = device.compare_config()

    if diff:
        device.commit_config()

    device.discard_config()
    device.close()


def create_vlan(ip, username, password, vlan_id, vlan_name):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    device.device.send_command_timing("enable")

    device.device.send_command_timing("configure terminal")

    config_commands = [
        f"vlan {vlan_id}",
        f"name {vlan_name}"
    ]

    for command in config_commands:
        device.device.send_command_timing(command)

    device.device.send_command_timing("end")

    save_configuration(device)

    device.close()

def create_route(ip, username, password, destination_network, subnet_mask, next_hop):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    device.device.send_command_timing("enable")

    device.device.send_command_timing("configure terminal")

    config_command = f"ip route {destination_network} {subnet_mask} {next_hop}"

    device.device.send_command_timing(config_command)

    device.device.send_command_timing("end")

    save_configuration(device)

    device.close()


def refresh_switch_info(switch):
    switch_info = switch_get_info(switch.ip_address, switch.ssh_username, switch.ssh_password, 'f')

    if 'facts' in switch_info:
        switch.hostname = switch_info['facts']['hostname']
        switch.uptime = switch_info['facts']['uptime']
        switch.model = switch_info['facts']['model']
        switch.serial_number = switch_info['facts']['serial_number']
        switch.save()

    # Delete existing interfaces, vlans, and routes
    Interface.objects.filter(switch=switch).delete()
    Vlan.objects.filter(switch=switch).delete()
    Route.objects.filter(switch=switch).delete()

    # Update interfaces
    interface_info = switch_get_info(switch.ip_address, switch.ssh_username, switch.ssh_password, 'i')
    if 'interfaces' in interface_info:
        for interface_name, interface_data in interface_info['interfaces'].items():
            if 'ipv4' in interface_data and interface_data['ipv4']:
                for ip_address, ip_info in interface_data['ipv4'].items():
                    prefix_length = ip_info.get('prefix_length', None)

                    Interface.objects.create(
                        switch=switch,
                        name=interface_name,
                        ip_address=ip_address,
                        mask=prefix_length,
                    )

    # Update vlans
    vlan_info = switch_get_info(switch.ip_address, switch.ssh_username, switch.ssh_password, 'v')
    if 'vlans' in vlan_info:
        for vlan_id, vlan_data in vlan_info['vlans'].items():
            if vlan_id in ["10", "20", "30", "40", "50", "150"]:
                Vlan.objects.create(
                    switch=switch,
                    vlan_id=vlan_id,
                    name=vlan_data['name'],
                    ports=', '.join(vlan_data['interfaces'])
                )

    # Update routes
    route_info = switch_get_info(switch.ip_address, switch.ssh_username, switch.ssh_password, 'r')
    if 'routes' in route_info:
        for route_data in route_info['routes']:
            Route.objects.create(
                switch=switch,
                protocol=route_data.get('protocol', ''),
                network=route_data.get('network', ''),
                distance=route_data.get('distance', ''),
                metric=route_data.get('metric', ''),
                next_hop=route_data.get('next_hop', ''),
            )


def create_vlan_interface(ip, username, password, vlan_id, vlan_ip, vlan_subnet_mask):
    driver = get_network_driver('ios')
    device = driver(ip, username, password)
    device.open()

    output = device.device.send_command_timing("enable")

    output = device.device.send_command_timing("configure terminal")

    config_commands = [
        f"interface vlan {vlan_id}",
        f"ip address {vlan_ip} {vlan_subnet_mask}",
        "no shutdown"
    ]

    for command in config_commands:
        output = device.device.send_command_timing(command)

    output = device.device.send_command_timing("end")

    save_configuration(device)

    device.close()


def save_configuration(device):
    device.device.send_command_timing("write memory")

    time.sleep(5)


def subnet_mask_to_prefix(subnet_mask):
    octets = subnet_mask.split('.')

    prefix_length = sum(bin(int(octet)).count('1') for octet in octets)

    return str(prefix_length)


def is_valid_ipv4(ip: str) -> bool:
    pattern = re.compile(r'^(([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])$')

    if pattern.match(ip):
        return True
    else:
        return False


def is_valid_subnet_mask(mask: str) -> bool:
    try:
        parts = list(map(int, mask.split('.')))
        if len(parts) != 4:
            return False

        binary_str = ''.join(f'{part:08b}' for part in parts)

        if '01' in binary_str:
            return False

        valid_masks = [
            "0.0.0.0", "128.0.0.0", "192.0.0.0", "224.0.0.0", "240.0.0.0",
            "248.0.0.0", "252.0.0.0", "254.0.0.0", "255.0.0.0", "255.128.0.0",
            "255.192.0.0", "255.224.0.0", "255.240.0.0", "255.248.0.0",
            "255.252.0.0", "255.254.0.0", "255.255.0.0", "255.255.128.0",
            "255.255.192.0", "255.255.224.0", "255.255.240.0", "255.255.248.0",
            "255.255.252.0", "255.255.254.0", "255.255.255.0", "255.255.255.128",
            "255.255.255.192", "255.255.255.224", "255.255.255.240",
            "255.255.255.248", "255.255.255.252", "255.255.255.254",
            "255.255.255.255"
        ]

        return mask in valid_masks
    except ValueError:
        return False
