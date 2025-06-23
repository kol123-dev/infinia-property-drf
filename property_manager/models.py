from django.db import models
from accounts.models import User

class PropertyManager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='property_manager_profile', limit_choices_to={'role': 'property_manager'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.name if hasattr(self.user, 'name') else self.user.email
