from django.db import models

class Visitor(models.Model):
    name = models.CharField(max_length=100)
    visitor_type = models.CharField(max_length=50, choices=[('Guest', 'Guest'), ('Delivery', 'Delivery')], default='Guest')
    unit = models.CharField(max_length=20)
    
    # New fields for Watchman
    visitor_photo = models.ImageField(upload_to='visitors/photos/', blank=True, null=True)
    vehicle_photo = models.ImageField(upload_to='visitors/vehicles/', blank=True, null=True)
    vehicle_number = models.CharField(max_length=50, blank=True, null=True)
    recorded_by = models.CharField(max_length=100, blank=True, null=True) # Watchman Name
    
    time_in = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Inside')

    def __str__(self):
        return f"{self.name} - {self.unit}"
