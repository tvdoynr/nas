# management/commands/gather_topology.py
import re

from django.core.management.base import BaseCommand
from network_automation.napalm_utilities import switch_get_info, pc_telnet
from network_automation.models import Switch, PC, Interface, Vlan, Route

class Command(BaseCommand):
    help = 'Gathers topology information from switches and populates the database'

    def handle(self, *args, **options):
        switches = {
            'BACKBONE': '192.168.50.1',
            'studentsw': '192.168.50.10',
            'instructorsw': '192.168.50.12',
            'labsw': '192.168.50.11',
        }

        pcs_port = {
            'studentpc1': '5004',
            'studentpc2': '5006',
            'studentpc3': '5008',
            'labpc1': '5014',
            'labpc2': '5010',
            'labpc3': '5012',
            'instructorpc1': '5020',
            'instructorpc2': '5018',
            'instructorpc3': '5016',
        }

        for switch_name, switch_ip in switches.items():
            switch_info = switch_get_info(switch_ip, 'admin', 'admin123', 'f')

            if 'facts' not in switch_info:
                self.stdout.write(self.style.WARNING(f'Failed to retrieve information for switch {switch_name}'))
                continue

            switch, created = Switch.objects.get_or_create(
                name=switch_name,
                ip_address=switch_ip,
                ssh_username='admin',
                ssh_password='admin123'
            )
            switch.hostname = switch_info['facts']['hostname']
            switch.uptime = switch_info['facts']['uptime']
            switch.model = switch_info['facts']['model']
            switch.serial_number = switch_info['facts']['serial_number']

            if 'backbone' in switch_name.lower():
                switch.image = '/static/images/backbone.jpg'
            else:
                switch.image = '/static/images/Switch.png'

            switch.save()

            interface_info = switch_get_info(switch_ip, 'admin', 'admin123', 'i')
            if 'interfaces' in interface_info:
                for interface_name, interface_data in interface_info['interfaces'].items():
                    if 'ipv4' in interface_data and interface_data['ipv4']:
                        for ip_address, ip_info in interface_data['ipv4'].items():
                            prefix_length = ip_info.get('prefix_length', None)

                            interface, created = Interface.objects.get_or_create(switch=switch, name=interface_name)
                            interface.ip_address = ip_address
                            interface.mask = prefix_length
                            interface.save()

            vlan_info = switch_get_info(switch_ip, 'admin', 'admin123', 'v')
            if 'vlans' in vlan_info:
                for vlan_id, vlan_data in vlan_info['vlans'].items():
                    if vlan_id in ["10", "20", "30", "40", "50", "150"]:
                        vlan, created = Vlan.objects.get_or_create(switch=switch, vlan_id=vlan_id)
                        vlan.name = vlan_data['name']
                        vlan.ports = ', '.join(vlan_data['interfaces'])
                        vlan.save()

            route_info = switch_get_info(switch_ip, 'admin', 'admin123', 'r')
            if 'routes' in route_info:
                for route_data in route_info['routes']:
                    route, created = Route.objects.get_or_create(
                        switch=switch,
                        protocol=route_data.get('protocol', ''),
                        network=route_data.get('network', ''),
                        distance=route_data.get('distance', ''),
                        metric=route_data.get('metric', ''),
                        next_hop=route_data.get('next_hop', ''),
                    )

        for pc_name, pc_port in pcs_port.items():
            pc_info = pc_telnet('127.0.0.1', pc_port, 'show ip')
            if pc_info:
                name = re.search(r'NAME\s+:\s+(\S+)', pc_info).group(1)
                ip_mask = re.search(r'IP/MASK\s+:\s+(\S+)', pc_info).group(1)
                ip_address, mask = ip_mask.split('/')
                default_gateway = re.search(r'GATEWAY\s+:\s+(\S+)', pc_info).group(1)
                mac_address = re.search(r'MAC\s+:\s+(\S+)', pc_info).group(1)
                lport = re.search(r'LPORT\s+:\s+(\S+)', pc_info).group(1)
                rhost_port = re.search(r'RHOST:PORT\s+:\s+(\S+)', pc_info).group(1)
                mtu = re.search(r'MTU:\s+:\s+(\S+)', pc_info).group(1)

                pc, created = PC.objects.get_or_create(
                    name=name,
                    ip_address=ip_address,
                    mask=mask,
                    default_gateway=default_gateway,
                    mac_address=mac_address,
                    lport=lport,
                    rhost_port=rhost_port,
                    mtu=mtu
                )
                pc.image = '/static/images/pc.jpg'
                if 'studentpc' in pc_name.lower():
                    switch = Switch.objects.filter(name__icontains='studentsw').first()
                    if switch:
                        pc.switch = switch
                elif 'labpc' in pc_name.lower():
                    switch = Switch.objects.filter(name__icontains='labsw').first()
                    if switch:
                        pc.switch = switch
                elif 'instructorpc' in pc_name.lower():
                    switch = Switch.objects.filter(name__icontains='instructorsw').first()
                    if switch:
                        pc.switch = switch

                pc.save()

        backbone_switch = Switch.objects.filter(name__icontains='backbone').first()
        if backbone_switch:
            for switch in Switch.objects.exclude(name__icontains='backbone'):
                switch.backbone_switch = backbone_switch
                switch.save()

        self.stdout.write(self.style.SUCCESS('Topology information gathered and stored in the database.'))
