from django.urls import path
from .views import DeviceListView, DeviceBackupView, DeviceFirmwareUpdateView, DeviceInfoView, DeviceSetIPView

urlpatterns = [
    path('devices/', DeviceListView.as_view(), name='device_list'),
    path('devices/<int:device_id>/backup/', DeviceBackupView.as_view(), name='device_backup'),
    path('devices/<int:device_id>/firmware-update/', DeviceFirmwareUpdateView.as_view(), name='device_firmware_update'),
    path('devices/<int:device_id>/info/', DeviceInfoView.as_view(), name='device_info'),
    path('devices/<int:device_id>/set-ip/', DeviceSetIPView.as_view(), name='device_set_ip'),
]
