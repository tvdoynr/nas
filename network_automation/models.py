# models.py
import os

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Switch(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.CharField(max_length=20, null=True, blank=True)
    ssh_username = models.CharField(max_length=50, null=True, blank=True)
    ssh_password = models.CharField(max_length=50, null=True, blank=True)
    image = models.CharField(max_length=100, null=True, blank=True)
    hostname = models.CharField(max_length=100, null=True, blank=True)
    uptime = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    serial_number = models.CharField(max_length=100, null=True, blank=True)
    backbone_switch = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class PC(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True, unique=True)
    ip_address = models.CharField(max_length=20, null=True, blank=True)
    image = models.CharField(max_length=100, null=True, blank=True)
    mask = models.CharField(max_length=20, null=True, blank=True)
    default_gateway = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    mac_address = models.CharField(unique=True, max_length=20, null=True, blank=True)
    lport = models.CharField(max_length=10, null=True, blank=True)
    rhost_port = models.CharField(max_length=20, null=True, blank=True)
    mtu = models.CharField(max_length=10, null=True, blank=True)
    switch = models.ForeignKey(Switch, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class Interface(models.Model):
    switch = models.ForeignKey(Switch, related_name='interfaces', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    ip_address = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    mask = models.CharField(max_length=20, null=True, blank=True)
    def __str__(self):
        return f'{self.name} on {self.switch.name}'


class Vlan(models.Model):
    switch = models.ForeignKey(Switch, related_name='vlans', on_delete=models.CASCADE, null=True, blank=True)
    vlan_id = models.PositiveIntegerField(null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    ports = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f'VLAN {self.vlan_id} ({self.name}) on {self.switch.name}'


class Route(models.Model):
    switch = models.ForeignKey(Switch, related_name='routes', on_delete=models.CASCADE, null=True, blank=True)
    protocol = models.CharField(max_length=50, null=True, blank=True)
    network = models.CharField(max_length=50, null=True, blank=True)
    distance = models.CharField(max_length=50, null=True, blank=True)
    metric = models.CharField(max_length=50, null=True, blank=True)
    next_hop = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'Route to {self.network} via {self.next_hop} on {self.switch.name}'


class ConfigurationBackup(models.Model):
    def backup_file_name(instance, filename):
        return '/'.join([str(instance.backup_date.year), str(instance.backup_date.month),
                         str(instance.backup_date.day), os.path.basename(filename)])

    switch = models.ForeignKey(Switch, related_name='backups', on_delete=models.CASCADE, null=True, blank=True)
    backup_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    backup_file = models.FileField(max_length=500, null=True, blank=True, upload_to=backup_file_name)


class DeviceLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='device_logs')
    switch = models.ForeignKey(Switch, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    pc = models.ForeignKey(PC, on_delete=models.CASCADE, null=True, blank=True, related_name='logs')
    action = models.CharField(max_length=50)
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.TextField()

    def __str__(self):
        device = self.switch if self.switch else self.pc
        return f'{device} - {self.action} by {self.user.username if self.user else "System"}'
