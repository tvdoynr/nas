from django.urls import path
from .views import DeviceListView, DeviceBackupView, DeviceFirmwareUpdateView, DeviceInfoView, PCSetIPView, \
    SwitchCreateVlanView, SwitchCreateRouteView, SwitchCreateVlanInterfaceView, GetBackupView, RestoreBackupView

urlpatterns = [
    path('devices/', DeviceListView.as_view(), name='device_list'),
    path('devices/<int:device_id>/backup/', DeviceBackupView.as_view(), name='device_backup'),
    path('devices/<int:device_id>/firmware-update/', DeviceFirmwareUpdateView.as_view(), name='device_firmware_update'),
    path('devices/<int:device_id>/info/', DeviceInfoView.as_view(), name='device_info'),
    path('devices/set-ip/', PCSetIPView.as_view(), name='pc_set_ip'),
    path('devices/create-vlan/', SwitchCreateVlanView.as_view(), name='create_vlan'),
    path('devices/create-route/', SwitchCreateRouteView.as_view(), name='create_route'),
    path('devices/create-vlan-interface/', SwitchCreateVlanInterfaceView.as_view(), name='create_vlan_interface'),
    path('devices/get_backup', GetBackupView.as_view(), name='get_backup'),
    path('devices/restore_backup/', RestoreBackupView.as_view(), name="restore_backup"),
]
