# models.py
from django.contrib.auth.models import User
from django.db import models

class NetworkDevice(models.Model):
    name = models.CharField(max_length=100)
    ip_address = models.CharField(max_length=20)
    ssh_username = models.CharField(max_length=50)
    ssh_password = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
class Switch(models.Model):
    hostname = models.CharField(max_length=100)
    uptime = models.CharField(max_length=100)
    modal = models.CharField(max_length=100)
    serial_number = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class PC(models.Model):
    hostname = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField(protocol='IPv4')
    mask = models.GenericIPAddressField(protocol='IPv4')
    default_gateway = models.GenericIPAddressField(protocol='IPv4')
    mac_address = models.GenericIPAddressField(protocol='IPv6')
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Interface(models.Model):
    switch = models.ForeignKey(Switch, related_name='interfaces', on_delete=models.CASCADE)
    name = models.CharField(max_length=50)  # e.g., GigabitEthernet0/0
    ip_address = models.GenericIPAddressField(protocol='IPv4', null=True, blank=True)
    status = models.CharField(max_length=10)  # e.g., up, down
    protocol_status = models.CharField(max_length=10)  # e.g., up, down

    def __str__(self):
        return f'{self.name} on {self.switch.name}'

class Vlan(models.Model):
    switch = models.ForeignKey(Switch, related_name='vlans', on_delete=models.CASCADE)
    vlan_id = models.PositiveIntegerField()
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20)  # e.g., active, act/unsup
    ports = models.CharField(max_length=255, blank=True, null=True)  # e.g., Gi1/0, Gi1/1, ...

    def __str__(self):
        return f'VLAN {self.vlan_id} ({self.name}) on {self.switch.name}'

class Route(models.Model):
    switch = models.ForeignKey(Switch, related_name='routes', on_delete=models.CASCADE)
    network = models.CharField(max_length=50)  # e.g., 192.168.50.0/24
    subnet_mask = models.CharField(max_length=50, blank=True, null=True)  # e.g., 255.255.255.0
    gateway = models.CharField(max_length=50, blank=True, null=True)  # e.g., 192.168.1.1
    interface = models.CharField(max_length=50, blank=True, null=True)  # e.g., Vlan50
    route_type = models.CharField(max_length=50)  # e.g., connected, local

    def __str__(self):
        return f'Route to {self.network} via {self.interface} on {self.switch.name}'
