from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from napalm import get_network_driver
from .models import NetworkDevice

class DeviceListView(LoginRequiredMixin, View):
    def get(self, request):
        devices = NetworkDevice.objects.filter(user=request.user)
        return render(request, 'device_list.html', {'devices': devices})

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
