from django.db import models
import uuid
import random


class Category(models.Model):
    """
    Unique category for each of the 6 canvas node types.
    Category IDs: CAT-PP, CAT-GS, CAT-DS, CAT-DT, CAT-HS, CAT-ID
    """
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.id}: {self.name}"


class GridNode(models.Model):
    """
    Base model for all grid entities.
    Each resource gets a globally unique UUID.
    'demand', 'input', 'output' represent current electrical flow values.
    """
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
    input = models.FloatField(default=0.0, help_text="Current input flow (kV or kW)")
    output = models.FloatField(default=0.0, help_text="Current output flow (kV or kW)")

    def __str__(self):
        return f"[{self.category_id}] {self.name}"


class GridEdge(models.Model):
    """
    Represents lines/connections between nodes on the React Flow canvas.
    Lines are NOT categories — they are edges connecting GridNode instances.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(
        GridNode, on_delete=models.CASCADE,
        related_name='outgoing_edges',
        help_text="Connection Input (ci): upstream node"
    )
    target = models.ForeignKey(
        GridNode, on_delete=models.CASCADE,
        related_name='incoming_edges',
        help_text="Connection Output (co): downstream node"
    )

    LINE_TYPE_CHOICES = [
        ('TransmissionLine', 'Transmission Line'),
        ('SubTransmissionLine', 'Sub-Transmission Line'),
        ('Feeder11kV', '11 kV Feeder'),
        ('SecondaryDistributionLine', 'Secondary Distribution Line'),
        ('ServiceLine', 'Service Line'),
    ]
    type = models.CharField(max_length=50, choices=LINE_TYPE_CHOICES)
    capacity = models.FloatField(default=100.0, help_text="Max flow capacity (kW)")

    def __str__(self):
        return f"{self.source.name} → {self.target.name} [{self.type}]"


# ──────────────────────────────────────────────
# The 6 Canvas Node Models (Category: CAT-XX)
# ──────────────────────────────────────────────

class PowerPlant(GridNode):
    """Category: CAT-PP | Output interval: 11–25 kV"""

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-PP', defaults={'name': 'Power Plant'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        """Generates a random output in the 11–25 kV range."""
        self.output = random.uniform(11.0, 25.0)
        self.save()


class GridSubstation(GridNode):
    """Category: CAT-GS | Reduces incoming HV to sub-transmission voltage."""

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-GS', defaults={'name': 'Grid Substation'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        if self.input > 0:
            self.output = self.input * random.uniform(0.8, 0.95)
        self.save()


class DistributionSubstation(GridNode):
    """Category: CAT-DS | Reduces 33 kV → 11 kV."""

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-DS', defaults={'name': 'Distribution Substation'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        """Output interval: ~11 kV (±0.5 kV)"""
        self.output = 11.0 + random.uniform(-0.5, 0.5)
        self.save()


class DistributionTransformer(GridNode):
    """Category: CAT-DT | Steps down 11 kV → 415/230 V."""

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-DT', defaults={'name': 'Distribution Transformer'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        """Output: 0.23 kV (230 V) ± noise"""
        self.output = 0.23 + random.uniform(-0.01, 0.01)
        self.save()


class House(GridNode):
    """Category: CAT-HS | Residential consumer / prosumer node."""

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-HS', defaults={'name': 'House'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        """Output: 0–5 kW (solar generation potential)"""
        self.output = random.uniform(0.0, 5.0)
        self.save()


class Industry(GridNode):
    """Category: CAT-ID | Industrial consumer node."""

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-ID', defaults={'name': 'Industry'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        """Output: 0–50 kW"""
        self.output = random.uniform(0.0, 50.0)
        self.save()
