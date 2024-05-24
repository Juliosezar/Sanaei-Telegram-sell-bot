from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    def create_user(self, username, password):
        if not username:
            raise ValidationError("!! enter username !!")

        user = self.model(username=username,)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        user = self.create_user(username, password)
        user.save(using=self._db)
        return user

    def create_seller(self, username, password):
        user = self.create_user(username, password)
        user.save(using=self._db)
        return user
