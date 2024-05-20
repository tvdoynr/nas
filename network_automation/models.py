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
