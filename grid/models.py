from django.db import models
import uuid
import random


class Category(models.Model):
    """
    Unique identifier for each of the 6 node types in the canvas.
    IDs: CAT-PP, CAT-GS, CAT-DS, CAT-DT, CAT-HS, CAT-ID
    """
    id = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['id']

    def __str__(self):
        return f"{self.id}: {self.name}"


class GridNode(models.Model):
    """
    Base class for all grid entities.
    Each resource gets a globally unique UUID.
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

    demand = models.FloatField(default=0.0, help_text="Current demand/load (kW)")
    input  = models.FloatField(default=0.0, help_text="Current input flow (kV or kW)")
    output = models.FloatField(default=0.0, help_text="Current output flow (kV or kW)")

    def __str__(self):
        return f"[{self.category_id}] {self.name}"


class GridEdge(models.Model):
    """
    Represents a physical electrical line between two nodes.
    Line type is auto-determined by the hierarchy:
      PowerPlant → GridSubstation        : TransmissionLine     (400–765 kV)
      GridSubstation → DistSubstation    : SubTransmissionLine  (132/66/33 kV)
      DistSubstation → DistTransformer   : Feeder11kV           (11 kV)
      DistTransformer → Consumer         : SecondaryDistribution (415/230 V)
    """
    LINE_TYPE_CHOICES = [
        ('TransmissionLine',         'Transmission Line (400–765 kV)'),
        ('SubTransmissionLine',      'Sub-Transmission Line (132/66/33 kV)'),
        ('Feeder11kV',               '11 kV Feeder'),
        ('SecondaryDistributionLine','Secondary Distribution Line (415/230 V)'),
        ('ServiceLine',              'Service Line'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(
        GridNode, on_delete=models.CASCADE,
        related_name='outgoing_edges',
        help_text="Upstream node (Connection Input)"
    )
    target = models.ForeignKey(
        GridNode, on_delete=models.CASCADE,
        related_name='incoming_edges',
        help_text="Downstream node (Connection Output)"
    )
    type = models.CharField(max_length=50, choices=LINE_TYPE_CHOICES)
    capacity = models.FloatField(default=100.0, help_text="Max flow capacity (kW)")

    class Meta:
        unique_together = ('source', 'target')

    def __str__(self):
        return f"{self.source.name} → {self.target.name} [{self.get_type_display()}]"


# ─────────────────────────────────────────────────────────────────────────────
# Helper: ensure a GridEdge exists between two nodes with the correct line type
# ─────────────────────────────────────────────────────────────────────────────

def _sync_edge(source_node: GridNode, target_node: GridNode, line_type: str):
    """Create or update the GridEdge between source and target."""
    GridEdge.objects.update_or_create(
        source=source_node,
        target=target_node,
        defaults={'type': line_type},
    )


def _remove_edge(target_node: GridNode):
    """Remove any incoming edge for target_node (when its parent is cleared)."""
    GridEdge.objects.filter(target=target_node).delete()


# ─────────────────────────────────────────────────────────────────────────────
# Node Models  (One-to-Many hierarchy via ForeignKey)
# ─────────────────────────────────────────────────────────────────────────────

class PowerPlant(GridNode):
    """
    Top of the hierarchy. Category: CAT-PP
    Output: 11–25 kV (random per generate_random_output)
    One PowerPlant → many GridSubstations.
    """

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-PP', defaults={'name': 'Power Plant'})
            self.category = cat
        super().save(*args, **kwargs)

    def generate_random_output(self):
        self.output = random.uniform(11.0, 25.0)
        self.save()


class GridSubstation(GridNode):
    """
    Category: CAT-GS | Reduces transmission voltage.
    Connected to one PowerPlant; can feed many DistributionSubstations.
    Edge auto-created: PowerPlant → GridSubstation = TransmissionLine
    """
    power_plant = models.ForeignKey(
        PowerPlant,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='grid_substations',
        help_text="Parent Power Plant"
    )

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-GS', defaults={'name': 'Grid Substation'})
            self.category = cat
        super().save(*args, **kwargs)
        # Auto-create / update connecting edge
        if self.power_plant_id:
            _sync_edge(self.power_plant, self, 'TransmissionLine')
        else:
            _remove_edge(self)

    def generate_random_output(self):
        if self.input > 0:
            self.output = self.input * random.uniform(0.8, 0.95)
        self.save()


class DistributionSubstation(GridNode):
    """
    Category: CAT-DS | 33 → 11 kV.
    Connected to one GridSubstation; can feed many DistributionTransformers.
    Edge auto-created: GridSubstation → DistributionSubstation = SubTransmissionLine
    """
    grid_substation = models.ForeignKey(
        GridSubstation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='distribution_substations',
        help_text="Parent Grid Substation"
    )

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-DS', defaults={'name': 'Distribution Substation'})
            self.category = cat
        super().save(*args, **kwargs)
        if self.grid_substation_id:
            _sync_edge(self.grid_substation, self, 'SubTransmissionLine')
        else:
            _remove_edge(self)

    def generate_random_output(self):
        """Output: ~11 kV"""
        self.output = 11.0 + random.uniform(-0.5, 0.5)
        self.save()


class DistributionTransformer(GridNode):
    """
    Category: CAT-DT | 11 kV → 415/230 V.
    Connected to one DistributionSubstation; can supply many Consumers.
    Edge auto-created: DistributionSubstation → DistributionTransformer = Feeder11kV
    """
    distribution_substation = models.ForeignKey(
        DistributionSubstation,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='distribution_transformers',
        help_text="Parent Distribution Substation"
    )

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-DT', defaults={'name': 'Distribution Transformer'})
            self.category = cat
        super().save(*args, **kwargs)
        if self.distribution_substation_id:
            _sync_edge(self.distribution_substation, self, 'Feeder11kV')
        else:
            _remove_edge(self)

    def generate_random_output(self):
        """Output: ~0.23 kV (230 V)"""
        self.output = 0.23 + random.uniform(-0.01, 0.01)
        self.save()


class House(GridNode):
    """
    Category: CAT-HS | Residential consumer.
    Connected to one DistributionTransformer.
    Edge auto-created: DistributionTransformer → House = SecondaryDistributionLine
    """
    distribution_transformer = models.ForeignKey(
        DistributionTransformer,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='houses',
        help_text="Parent Distribution Transformer"
    )

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-HS', defaults={'name': 'House'})
            self.category = cat
        super().save(*args, **kwargs)
        if self.distribution_transformer_id:
            _sync_edge(self.distribution_transformer, self, 'SecondaryDistributionLine')
        else:
            _remove_edge(self)

    def generate_random_output(self):
        """Solar output potential: 0–5 kW"""
        self.output = random.uniform(0.0, 5.0)
        self.save()


class Industry(GridNode):
    """
    Category: CAT-ID | Industrial consumer.
    Connected to one DistributionTransformer.
    Edge auto-created: DistributionTransformer → Industry = SecondaryDistributionLine
    """
    distribution_transformer = models.ForeignKey(
        DistributionTransformer,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='industries',
        help_text="Parent Distribution Transformer"
    )

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-ID', defaults={'name': 'Industry'})
            self.category = cat
        super().save(*args, **kwargs)
        if self.distribution_transformer_id:
            _sync_edge(self.distribution_transformer, self, 'SecondaryDistributionLine')
        else:
            _remove_edge(self)

    def generate_random_output(self):
        """Industrial load: 0–50 kW"""
        self.output = random.uniform(0.0, 50.0)
        self.save()
