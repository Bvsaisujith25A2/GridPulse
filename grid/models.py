from django.db import models
import uuid
import random

class Category(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class GridNode(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='nodes')
    name = models.CharField(max_length=100)
    
    STATUS_CHOICES = [
        ('Stable', 'Stable'),
        ('Warning', 'Warning'),
        ('Critical', 'Critical'),
        ('Offline', 'Offline'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Stable')
    
    demand = models.FloatField(default=0.0, help_text="Current demand/load")
    input = models.FloatField(default=0.0, help_text="Current input flow")
    output = models.FloatField(default=0.0, help_text="Current output flow")

    def __str__(self):
        return f"[{self.category_id}] {self.name} ({self.id})"

class GridEdge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(GridNode, on_delete=models.CASCADE, related_name='outgoing_edges', help_text="Connection Input (ci) node")
    target = models.ForeignKey(GridNode, on_delete=models.CASCADE, related_name='incoming_edges', help_text="Connection Output (co) node")
    
    TYPE_CHOICES = [
        ('TransmissionLine', 'TransmissionLine'),
        ('SubTransmissionLine', 'SubTransmissionLine'),
        ('Feeder11kV', 'Feeder11kV'),
        ('SecondaryDistributionLine', 'SecondaryDistributionLine'),
        ('ServiceLine', 'ServiceLine'),
    ]
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    capacity = models.FloatField(default=100.0, help_text="Maximum flow capacity")

    def __str__(self):
        return f"{self.source.name} -> {self.target.name} ({self.type})"


# The 6 Specific Node Types

class PowerPlant(GridNode):
    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-PP', defaults={'name': 'Power Plant'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        # 11-25 kV random generation
        self.output = random.uniform(11.0, 25.0)
        self.save()

class TransmissionLine(GridNode):
    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-TL', defaults={'name': 'Transmission Line'})
            self.category = cat
        super().save(*args, **kwargs)

class GridSubstation(GridNode):
    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-GS', defaults={'name': 'Grid Substation'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
         # Reducer voltage example
         # Depending on the incoming voltage, the output varies. For now using placeholder logic.
         if self.input > 0:
            self.output = self.input * random.uniform(0.8, 0.95)
         self.save()

class SubTransmissionLine(GridNode):
    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-STL', defaults={'name': 'Sub-Transmission Line'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        # 132 / 66 / 33 kV
        self.output = random.choice([132.0, 66.0, 33.0])
        self.save()



class Feeder11kV(GridNode):
    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-F11', defaults={'name': '11 kV Feeder'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        self.output = 11.0 + random.uniform(-0.1, 0.1)
        self.save()



class SecondaryDistributionLine(GridNode):
    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-SDL', defaults={'name': 'Secondary Distribution Line'})
            self.category = cat
        super().save(*args, **kwargs)

class ServiceLine(GridNode):
    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-SL', defaults={'name': 'Service Line'})
            self.category = cat
        super().save(*args, **kwargs)

class House(GridNode):
    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-HS', defaults={'name': 'House'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        # Houses generally have demand but may have solar output
        self.output = random.uniform(0.0, 5.0) # kW
        self.save()


class Industry(GridNode):
    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-ID', defaults={'name': 'Industry'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        # Industries have high demand
        self.output = random.uniform(0.0, 50.0) # kW
        self.save()
