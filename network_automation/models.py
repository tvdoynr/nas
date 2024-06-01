# models.py
from django.contrib.auth.models import User
from django.db import models

class NetworkDevice(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.CharField(max_length=20, null=True, blank=True)
    ssh_username = models.CharField(max_length=50, null=True, blank=True)
    ssh_password = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    image = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        abstract = True

class Switch(NetworkDevice):
    hostname = models.CharField(max_length=100, null=True, blank=True)
    uptime = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    serial_number = models.CharField(max_length=100, null=True, blank=True)
    backbone_switch = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

class PC(NetworkDevice):
    mask = models.CharField(max_length=20, null=True, blank=True)
    default_gateway = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    mac_address = models.CharField(max_length=20, null=True, blank=True)
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
    status = models.CharField(max_length=10, null=True, blank=True)
    protocol_status = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f'{self.name} on {self.switch.name}'

class Vlan(models.Model):
    switch = models.ForeignKey(Switch, related_name='vlans', on_delete=models.CASCADE, null=True, blank=True)
    vlan_id = models.PositiveIntegerField(null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
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
    interface = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f'Route to {self.network} via {self.interface} on {self.switch.name}'
