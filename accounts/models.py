from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from .managers import UserManager

# Create your models here.
class Admins(AbstractBaseUser):  # username & password fields are imported from AbstractBaseUser
    username = models.CharField(unique=True, max_length=20)

    objects = UserManager()
    USERNAME_FIELD = "username"  # for authenticating
    REQUIRED_FIELDS = []

    def __str__(self):
        return f"{self.username}"

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_lable):
        return True

    def is_staff(self):
        return True

