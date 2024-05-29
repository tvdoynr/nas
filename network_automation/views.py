from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from napalm import get_network_driver
from .models import NetworkDevice

class DeviceListView(LoginRequiredMixin, View):
    def get(self, request):
        devices = NetworkDevice.objects.filter(user=request.user)
        nodes = []
        edges = []


        # BUNU SILMEYIN LUTFEN OLMASI GEREKN BU

        # for device in devices:
        #     node = {
        #         'id': device.id,
        #         'label': device.name,
        #         'title': f"{device.name}\nIP: {device.ip_address}\nSSH: {device.ssh_username}",
        #         'image': device.image.url if device.image else '',
        #         'shape': 'image',
        #         'size': 50,
        #     }
        #     nodes.append(node)
        #
        #     for connected_device in device.connected_devices.all():
        #         edge = {
        #             'from': device.id,
        #             'to': connected_device.id,
        #         }
        #         edges.append(edge)



        nodes = [
            {'id': 1, 'label': 'Backbone Switch', 'title': 'Backbone Switch\nIP: 10.0.0.1\nSSH: admin',
             'image': '/static/images/backbone.jpg', 'shape': 'image', 'size': 30},
            {'id': 2, 'label': 'Switch 1', 'title': 'Switch 1\nIP: 10.0.1.1\nSSH: admin',
             'image': '/static/images/Switch.png', 'shape': 'image', 'size': 50},
            {'id': 3, 'label': 'Switch 2', 'title': 'Switch 2\nIP: 10.0.2.1\nSSH: admin',
             'image': '/static/images/Switch.png', 'shape': 'image', 'size': 50},
            {'id': 4, 'label': 'Switch 3', 'title': 'Switch 3\nIP: 10.0.3.1\nSSH: admin',
             'image': '/static/images/Switch.png', 'shape': 'image', 'size': 50},
            {'id': 5, 'label': 'PC 1-1', 'title': 'PC 1-1\nIP: 10.0.1.2\nSSH: user', 'image': '/static/images/pc.jpg',
             'shape': 'image', 'size': 30},
            {'id': 6, 'label': 'PC 1-2', 'title': 'PC 1-2\nIP: 10.0.1.3\nSSH: user', 'image': '/static/images/pc.jpg',
             'shape': 'image', 'size': 30},
            {'id': 7, 'label': 'PC 1-3', 'title': 'PC 1-3\nIP: 10.0.1.4\nSSH: user', 'image': '/static/images/pc.jpg',
             'shape': 'image', 'size': 30},
            {'id': 8, 'label': 'PC 2-1', 'title': 'PC 2-1\nIP: 10.0.2.2\nSSH: user', 'image': '/static/images/pc.jpg',
             'shape': 'image', 'size': 30},
            {'id': 9, 'label': 'PC 2-2', 'title': 'PC 2-2\nIP: 10.0.2.3\nSSH: user', 'image': '/static/images/pc.jpg',
             'shape': 'image', 'size': 30},
            {'id': 10, 'label': 'PC 2-3', 'title': 'PC 2-3\nIP: 10.0.2.4\nSSH: user', 'image': '/static/images/pc.jpg',
             'shape': 'image', 'size': 30},
            {'id': 11, 'label': 'PC 3-1', 'title': 'PC 3-1\nIP: 10.0.3.2\nSSH: user', 'image': '/static/images/pc.jpg',
             'shape': 'image', 'size': 30},
            {'id': 12, 'label': 'PC 3-2', 'title': 'PC 3-2\nIP: 10.0.3.3\nSSH: user', 'image': '/static/images/pc.jpg',
             'shape': 'image', 'size': 30},
            {'id': 13, 'label': 'PC 3-3', 'title': 'PC 3-3\nIP: 10.0.3.4\nSSH: user', 'image': '/static/images/pc.jpg',
             'shape': 'image', 'size': 30}
        ]

        edges = [
            {'from': 1, 'to': 2},
            {'from': 1, 'to': 3},
            {'from': 1, 'to': 4},
            {'from': 2, 'to': 5},
            {'from': 2, 'to': 6},
            {'from': 2, 'to': 7},
            {'from': 3, 'to': 8},
            {'from': 3, 'to': 9},
            {'from': 3, 'to': 10},
            {'from': 4, 'to': 11},
            {'from': 4, 'to': 12},
            {'from': 4, 'to': 13}
        ]

        context = {
            'nodes': nodes,
            'edges': edges,
        }

        context = {
            'nodes': nodes,
            'edges': edges,
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
