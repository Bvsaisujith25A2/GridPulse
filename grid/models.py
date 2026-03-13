from django.db import models, transaction
import uuid
import random

from .arduino import sync_house_output


class Category(models.Model):
    id   = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['id']

    def __str__(self):
        return f"{self.id}: {self.name}"


class GridNode(models.Model):
    """
    Base class for all grid entities.
    power_active reflects whether this node is actually receiving power,
    taking its own status AND its parent's power_active into account.
    """
    id       = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='nodes')
    name     = models.CharField(max_length=100)

    STATUS_CHOICES = [
        ('Stable',   'Stable'),
        ('Warning',  'Warning'),
        ('Critical', 'Critical'),
        ('Offline',  'Offline'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Stable')

    input  = models.FloatField(default=0.0, help_text="Current input flow (kV or kW)")
    output = models.FloatField(default=0.0, help_text="Current output flow (kV or kW)")

    # ── Power-Flow State ──────────────────────────────────────────
    power_active = models.BooleanField(
        default=True,
        help_text=(
            "True only if this node is NOT Offline AND its parent is also power_active. "
            "Automatically propagated through the hierarchy."
        )
    )

    def __str__(self):
        return f"[{self.category_id}] {self.name}"


# ─────────────────────────────────────────────────────────────────────────────
# GridEdge – physical electrical lines between nodes
# ─────────────────────────────────────────────────────────────────────────────

# Realistic rated capacity (kW) per line type
LINE_CAPACITY_DEFAULTS = {
    'TransmissionLine':          500_000,   # 500 MW
    'SubTransmissionLine':        50_000,   #  50 MW
    'Feeder11kV':                 10_000,   #  10 MW
    'SecondaryDistributionLine':     100,   # 100 kW
    'ServiceLine':                    10,   #  10 kW
}


class GridEdge(models.Model):
    LINE_TYPE_CHOICES = [
        ('TransmissionLine',          'Transmission Line (400–765 kV)'),
        ('SubTransmissionLine',       'Sub-Transmission Line (132/66/33 kV)'),
        ('Feeder11kV',                '11 kV Feeder'),
        ('SecondaryDistributionLine', 'Secondary Distribution Line (415/230 V)'),
        ('ServiceLine',               'Service Line'),
    ]

    id     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(GridNode, on_delete=models.CASCADE, related_name='outgoing_edges')
    target = models.ForeignKey(GridNode, on_delete=models.CASCADE, related_name='incoming_edges')
    type   = models.CharField(max_length=50, choices=LINE_TYPE_CHOICES)
    # Rated capacity in kW – defaults are set per line type automatically
    capacity = models.FloatField(help_text="Rated capacity in kW", default=0.0)
    active   = models.BooleanField(default=True, help_text="Mirrors target node power_active")

    class Meta:
        unique_together = ('source', 'target')

    def save(self, *args, **kwargs):
        # Auto-set capacity to the realistic default if not overridden
        if self.capacity == 0.0 and self.type:
            self.capacity = LINE_CAPACITY_DEFAULTS.get(self.type, 100.0)
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.source.name} → {self.target.name} "
            f"[{self.get_type_display()}] "
            f"{'✓' if self.active else '✗'}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sync_edge(source_node: GridNode, target_node: GridNode, line_type: str):
    """Create or update the GridEdge; mirror power state on the edge."""
    edge, _ = GridEdge.objects.update_or_create(
        source=source_node,
        target=target_node,
        defaults={'type': line_type},
    )
    # Sync edge.active with the target's power_active
    if edge.active != target_node.power_active:
        edge.active = target_node.power_active
        edge.save(update_fields=['active'])


def _remove_edge(target_node: GridNode):
    GridEdge.objects.filter(target=target_node).delete()


def _set_power_active(node: GridNode, active: bool):
    """Persist power_active on a node if it changed; also update its incoming edge."""
    if node.power_active != active:
        node.power_active = active
        node.save(update_fields=['power_active'])
    # Keep the incoming edge in sync
    GridEdge.objects.filter(target=node).update(active=active)


# ─────────────────────────────────────────────────────────────────────────────
# Node Models
# ─────────────────────────────────────────────────────────────────────────────

class PowerPlant(GridNode):
    """
    Top of the hierarchy. Category: CAT-PP
    power_active = (status != 'Offline')
    """

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-PP', defaults={'name': 'Power Plant'})
            self.category = cat
        # Recompute own power_active before saving
        self.power_active = (self.status != 'Offline')
        super().save(*args, **kwargs)
        # Cascade to children
        self._propagate_to_children(self.power_active)

    def _propagate_to_children(self, parent_active: bool):
        for gs in self.grid_substations.all():
            new_active = (gs.status != 'Offline') and parent_active
            _set_power_active(gs, new_active)
            gs._propagate_to_children(new_active)

    def generate_random_output(self):
        self.output = random.uniform(11.0, 25.0)
        self.save()


class GridSubstation(GridNode):
    """
    Category: CAT-GS
    power_active = (status != 'Offline') AND power_plant.power_active
    Edge: PowerPlant → GridSubstation = TransmissionLine
    """
    power_plant = models.ForeignKey(
        PowerPlant, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='grid_substations',
    )

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-GS', defaults={'name': 'Grid Substation'})
            self.category = cat
        # Recompute power_active
        parent_active = self.power_plant.power_active if self.power_plant_id else True
        self.power_active = (self.status != 'Offline') and parent_active
        super().save(*args, **kwargs)
        # Edge management
        if self.power_plant_id:
            _sync_edge(self.power_plant, self, 'TransmissionLine')
        else:
            _remove_edge(self)
        self._propagate_to_children(self.power_active)

    def _propagate_to_children(self, parent_active: bool):
        for ds in self.distribution_substations.all():
            new_active = (ds.status != 'Offline') and parent_active
            _set_power_active(ds, new_active)
            ds._propagate_to_children(new_active)

    def generate_random_output(self):
        if self.input > 0:
            self.output = self.input * random.uniform(0.8, 0.95)
        self.save()


class DistributionSubstation(GridNode):
    """
    Category: CAT-DS | 33 → 11 kV
    Edge: GridSubstation → DistributionSubstation = SubTransmissionLine
    """
    grid_substation = models.ForeignKey(
        GridSubstation, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='distribution_substations',
    )

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-DS', defaults={'name': 'Distribution Substation'})
            self.category = cat
        parent_active = self.grid_substation.power_active if self.grid_substation_id else True
        self.power_active = (self.status != 'Offline') and parent_active
        super().save(*args, **kwargs)
        if self.grid_substation_id:
            _sync_edge(self.grid_substation, self, 'SubTransmissionLine')
        else:
            _remove_edge(self)
        self._propagate_to_children(self.power_active)

    def _propagate_to_children(self, parent_active: bool):
        for dt in self.distribution_transformers.all():
            new_active = (dt.status != 'Offline') and parent_active
            _set_power_active(dt, new_active)
            dt._propagate_to_children(new_active)

    def generate_random_output(self):
        self.output = 11.0 + random.uniform(-0.5, 0.5)
        self.save()


class DistributionTransformer(GridNode):
    """
    Category: CAT-DT | 11 kV → 415/230 V
    Edge: DistributionSubstation → DistributionTransformer = Feeder11kV
    """
    distribution_substation = models.ForeignKey(
        DistributionSubstation, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='distribution_transformers',
    )

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-DT', defaults={'name': 'Distribution Transformer'})
            self.category = cat
        parent_active = self.distribution_substation.power_active if self.distribution_substation_id else True
        self.power_active = (self.status != 'Offline') and parent_active
        super().save(*args, **kwargs)
        if self.distribution_substation_id:
            _sync_edge(self.distribution_substation, self, 'Feeder11kV')
        else:
            _remove_edge(self)
        self._propagate_to_children(self.power_active)

    def _propagate_to_children(self, parent_active: bool):
        for consumer in list(self.houses.all()) + list(self.industries.all()):
            new_active = (consumer.status != 'Offline') and parent_active
            _set_power_active(consumer, new_active)

    def generate_random_output(self):
        self.output = 0.23 + random.uniform(-0.01, 0.01)
        self.save()


class House(GridNode):
    """
    Category: CAT-HS | Residential consumer
    Edge: DistributionTransformer → House = SecondaryDistributionLine
    """
    distribution_transformer = models.ForeignKey(
        DistributionTransformer, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='houses',
    )
    hardware_enabled = models.BooleanField(default=False)
    arduino_pin = models.PositiveSmallIntegerField(default=13)

    def save(self, *args, **kwargs):
        previous_state = None
        if self.pk:
            previous_state = House.objects.filter(pk=self.pk).values(
                'status',
                'power_active',
                'hardware_enabled',
                'arduino_pin',
            ).first()
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-HS', defaults={'name': 'House'})
            self.category = cat
        parent_active = self.distribution_transformer.power_active if self.distribution_transformer_id else True
        self.power_active = (self.status != 'Offline') and parent_active
        with transaction.atomic():
            super().save(*args, **kwargs)
            self._ensure_exclusive_hardware_binding()
            if self.distribution_transformer_id:
                _sync_edge(self.distribution_transformer, self, 'SecondaryDistributionLine')
            else:
                _remove_edge(self)
        self._sync_hardware(previous_state)

    def _ensure_exclusive_hardware_binding(self):
        if not self.hardware_enabled:
            return

        for other_house in House.objects.filter(hardware_enabled=True).exclude(pk=self.pk):
            other_house.hardware_enabled = False
            other_house.save(update_fields=['hardware_enabled'])

    def _sync_hardware(self, previous_state):
        current_output_active = self.hardware_enabled and self.power_active and self.status != 'Offline'
        previous_output_active = False
        previous_pin = self.arduino_pin
        previous_hardware_enabled = False

        if previous_state is not None:
            previous_output_active = (
                previous_state['hardware_enabled']
                and previous_state['power_active']
                and previous_state['status'] != 'Offline'
            )
            previous_pin = previous_state['arduino_pin']
            previous_hardware_enabled = previous_state['hardware_enabled']

        should_sync = (
            previous_state is None
            or previous_output_active != current_output_active
            or previous_pin != self.arduino_pin
            or previous_hardware_enabled != self.hardware_enabled
        )

        if not should_sync:
            return

        sync_house_output(
            pin=self.arduino_pin,
            is_on=current_output_active,
            flash_before_off=previous_output_active and not current_output_active,
        )

    def generate_random_output(self):
        self.output = random.uniform(0.0, 5.0)
        self.save()


class Industry(GridNode):
    """
    Category: CAT-ID | Industrial consumer
    Edge: DistributionTransformer → Industry = SecondaryDistributionLine
    """
    distribution_transformer = models.ForeignKey(
        DistributionTransformer, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='industries',
    )

    def save(self, *args, **kwargs):
        if not self.category_id:
            cat, _ = Category.objects.get_or_create(id='CAT-ID', defaults={'name': 'Industry'})
            self.category = cat
        parent_active = self.distribution_transformer.power_active if self.distribution_transformer_id else True
        self.power_active = (self.status != 'Offline') and parent_active
        super().save(*args, **kwargs)
        if self.distribution_transformer_id:
            _sync_edge(self.distribution_transformer, self, 'SecondaryDistributionLine')
        else:
            _remove_edge(self)

    def generate_random_output(self):
        self.output = random.uniform(0.0, 50.0)
        self.save()
