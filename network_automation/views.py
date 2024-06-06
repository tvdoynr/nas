import json

from django.contrib.auth import logout
from django.core.serializers import serialize
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from napalm import get_network_driver
from .napalm_utilities import switch_get_info, switch_get_backup, pc_telnet, create_vlan, subnet_mask_to_prefix, \
    create_route, create_vlan_interface, switch_restore_backup, refresh_switch_info, is_valid_ipv4, is_valid_subnet_mask
from .models import NetworkDevice, Switch, PC, Vlan, Interface, Route, ConfigurationBackup


class DeviceListView(LoginRequiredMixin, View):
    def get(self, request):
        switches = Switch.objects.all()
        pcs = PC.objects.all()
        devices = list(switches) + list(pcs)

        nodes = []
        edges = []

        vlan_datas = Vlan.objects.all()
        interface_datas = Interface.objects.all()
        route_datas = Route.objects.all()
        backups = ConfigurationBackup.objects.all()

        for switch in switches:
            node = {
                'id': switch.id,
                'label': switch.name,
                'title': f"{switch.name}\nHostname: {switch.hostname}\nModel: {switch.model}\nSerial Number: {switch.serial_number}\nUptime: {switch.uptime}",
                'shape': 'image',
                'size': 50,
                'image': switch.image,
                'type': 'switch',
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
                'title': f"{pc.name}\nIP: {pc.ip_address}\nSubnet Mask: {pc.mask}\nMac: {pc.mac_address}\nDefault Gateaway: {pc.default_gateway}",
                'shape': 'image',
                'size': 30,
                'image': pc.image,
                'type': 'pc',
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
            'vlan_datas': json.dumps(list(vlan_datas.values())),
            'interface_datas': json.dumps(list(interface_datas.values())),
            'route_datas': json.dumps(list(route_datas.values())),
            'backups': serialize('json', backups),
        }
        print(context)

        return render(request, 'device_list.html', context)

class PCSetIPView(LoginRequiredMixin, View):
    def post(self, request):
        pcs_port = {
            'StudentPC1[1]': '5004',
            'StudentPC2[1]': '5006',
            'StudentPC3[1]': '5008',
            'LabPC1[1]': '5014',
            'LabPC2[1]': '5010',
            'LabPC3[1]': '5012',
            'inspc1[1]': '5020',
            'inspc2[1]': '5018',
            'inspc3[1]': '5016',
        }
        pc_id = request.POST.get('pc_id')
        ip_address = request.POST.get('ip_address')
        default_gateway = request.POST.get('default_gateway')
        mask = request.POST.get('mask')

        # error handle
        if not is_valid_ipv4(ip_address) or not is_valid_ipv4(default_gateway) or not is_valid_subnet_mask(mask):
            return JsonResponse({'status': 'false'}, status=500)

        pc_object = PC.objects.filter(id=pc_id).first()
        pc_port = pcs_port.get(pc_object.name)
        try:
            ip_flag = pc_telnet("127.0.0.1", pc_port, f"ip {ip_address} {mask} {default_gateway if default_gateway else ''}")
            if not ip_flag:
                PC.objects.filter(id=pc_id).update(
                    ip_address=ip_address,
                    default_gateway=default_gateway if default_gateway else '',
                    mask=mask,
                )
            else:
                return JsonResponse({'status': 'false'}, status=500)
        except Exception as e:
            print(str(e))
            return JsonResponse({'status':'false','message':str(e)}, status=500)
        return JsonResponse({'status': 'success'})


class SwitchCreateVlanView(LoginRequiredMixin, View):
    def post(self, request):
        switch_id = request.POST.get('switch_id')
        vlan_id = request.POST.get('vlan_id')
        vlan_name = request.POST.get('vlan_name')
        switch_obj = Switch.objects.filter(id=switch_id).first()
        create_vlan(switch_obj.ip_address, switch_obj.ssh_username, switch_obj.ssh_password, vlan_id, vlan_name)
        Vlan.objects.create(
            vlan_id=vlan_id,
            name=vlan_name,
            switch_id=switch_id,
            ports="",
        )
        return JsonResponse({'status': 'success'})


class SwitchCreateRouteView(LoginRequiredMixin, View):
    def post(self, request):
        switch_id = request.POST.get('switch_id')
        network_ip = request.POST.get('network_ip')
        subnet_mask = request.POST.get('subnet_mask')

        # error handle
        if not is_valid_ipv4(network_ip) or not is_valid_subnet_mask(subnet_mask):
            return JsonResponse({'status': 'false'}, status=500)

        subnet_prefix = subnet_mask_to_prefix(subnet_mask)
        next_hop = request.POST.get('next_hop')
        network= network_ip + "/" + subnet_prefix
        switch_obj = get_object_or_404(Switch, id=switch_id)
        create_route(switch_obj.ip_address, switch_obj.ssh_username, switch_obj.ssh_password, network_ip, subnet_mask, next_hop)

        Route.objects.create(
            switch_id=switch_obj.id,
            protocol="S",
            network=network,
            distance=1,
            metric=0,
            next_hop=next_hop
        )

        return JsonResponse({'status': 'success'})


class SwitchCreateVlanInterfaceView(LoginRequiredMixin, View):
    def post(self, request):
        switch_id = request.POST.get('switch_id')
        interface_id = request.POST.get('interface_id')
        interface_ip = request.POST.get('interface_ip')
        interface_mask = request.POST.get('interface_mask')

        # error handle
        if not is_valid_ipv4(interface_ip) or not is_valid_subnet_mask(interface_mask):
            return JsonResponse({'status': 'false'}, status=500)

        subnet_prefix = subnet_mask_to_prefix(interface_mask)
        switch_obj = get_object_or_404(Switch, id=switch_id)

        create_vlan_interface(switch_obj.ip_address, switch_obj.ssh_username, switch_obj.ssh_password, interface_id, interface_ip, interface_mask)
        Interface.objects.create(
            switch_id=switch_id,
            name=f"Vlan{interface_id}",
            ip_address=interface_ip,
            mask=subnet_prefix,
        )
        return JsonResponse({'status': 'success'})


class GetBackupView(LoginRequiredMixin, View):
    def post(self, request):
        switch_id = request.POST.get('switch_id')
        switch_obj = get_object_or_404(Switch, id=switch_id)
        file_path = switch_get_backup(switch_obj.ip_address, switch_obj.ssh_username, switch_obj.ssh_password)

        ConfigurationBackup.objects.create(
            switch_id=switch_id,
            backup_file=file_path,
        ).save()
        return JsonResponse({'status': 'success'})


class RestoreBackupView(LoginRequiredMixin, View):
    def post(self, request):
        backup_id = request.POST.get('backup_id')
        backup_obj = get_object_or_404(ConfigurationBackup, id=backup_id)
        switch_restore_backup(backup_obj.switch.ip_address,
                              backup_obj.switch.ssh_username,
                              backup_obj.switch.ssh_password,
                              backup_obj.backup_file.path)

        refresh_switch_info(backup_obj.switch)

        return JsonResponse({'status': 'success'})


class LogoutView(LoginRequiredMixin, View):
    def get(self, request):
        logout(request)

        return redirect(reverse('login_page'))

