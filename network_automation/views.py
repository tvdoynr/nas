from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from napalm import get_network_driver
from .napalm_utilities import switch_get_info, switch_get_backup, pc_telnet
from .models import NetworkDevice, Switch, PC


class DeviceListView(LoginRequiredMixin, View):
    def get(self, request):
        switches = Switch.objects.all()
        pcs = PC.objects.all()
        devices = list(switches) + list(pcs)

        nodes = []
        edges = []

        for switch in switches:
            node = {
                'id': switch.id,
                'label': switch.name,
                'title': f"{switch.name}\nIP: {switch.ip_address}\nSSH: {switch.ssh_username}",
                'shape': 'image',
                'size': 50,
                'image': switch.image,
            }
            nodes.append(node)

            if switch.backbone_switch:
                edge = {
                    'from': switch.backbone_switch.id,
                    'to': switch.id,
                }
                edges.append(edge)

        for pc in pcs:
            node = {
                'id': pc.id,
                'label': pc.name,
                'title': f"{pc.name}\nIP: {pc.ip_address}\nSSH: user",
                'shape': 'image',
                'size': 30,
                'image': pc.image,
            }
            nodes.append(node)

            if pc.switch:
                edge = {
                    'from': pc.switch.id,
                    'to': pc.id,
                }
                edges.append(edge)

        context = {
            'nodes': nodes,
            'edges': edges,
            'devices': devices,
        }

        return render(request, 'device_list.html', context)


class DeviceBackupView(LoginRequiredMixin, View):
    def post(self, request, device_id):
        device = NetworkDevice.objects.get(id=device_id, user=request.user)
        driver = get_network_driver('ios')
        try:
            with driver(device.ip_address, device.ssh_username, device.ssh_password) as device_conn:
                backup_config = device_conn.get_config()
                # Save the backup configuration to a file or database
                # ...
            return redirect('device_list')
        except Exception as e:
            # Handle any exceptions that occur during SSH connection
            print(f"Error backing up device {device.name}: {str(e)}")
            return redirect('device_list')

class DeviceFirmwareUpdateView(LoginRequiredMixin, View):
    def post(self, request, device_id):
        device = NetworkDevice.objects.get(id=device_id, user=request.user)
        driver = get_network_driver('ios')
        try:
            with driver(device.ip_address, device.ssh_username, device.ssh_password) as device_conn:
                print("za")
                # Perform firmware update logic here
                #
            return redirect('device_list')
        except Exception as e:
            # Handle any exceptions that occur during SSH connection
            print(f"Error updating firmware for device {device.name}: {str(e)}")
            return redirect('device_list')

class DeviceInfoView(LoginRequiredMixin, View):
    def get(self, request, device_id):
        device = NetworkDevice.objects.get(id=device_id, user=request.user)
        driver = get_network_driver('ios')
        try:
            with driver(device.ip_address, device.ssh_username, device.ssh_password) as device_conn:
                facts = device_conn.get_facts()
                interfaces = device_conn.get_interfaces()
                # Retrieve other relevant information
                # ...
            return render(request, 'device_info.html', {'device': device, 'facts': facts, 'interfaces': interfaces})
        except Exception as e:
            # Handle any exceptions that occur during SSH connection
            print(f"Error retrieving information for device {device.name}: {str(e)}")
            return redirect('device_list')

class DeviceSetIPView(LoginRequiredMixin, View):
    def post(self, request, device_id):
        device = NetworkDevice.objects.get(id=device_id, user=request.user)
        driver = get_network_driver('ios')
        try:
            with driver(device.ip_address, device.ssh_username, device.ssh_password) as device_conn:
                print("zaa")
                # Perform IP address configuration logic here
                #
            return redirect('device_list')
        except Exception as e:
            # Handle any exceptions that occur during SSH connection
            print(f"Error setting IP for device {device.name}: {str(e)}")
            return redirect('device_list')
