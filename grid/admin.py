from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    Category, GridNode, GridEdge,
    PowerPlant, GridSubstation, DistributionSubstation,
    DistributionTransformer, House, Industry,
)


def power_badge(obj):
    """Show a green ✔ or red ✘ badge for power_active."""
    if obj.power_active:
        return mark_safe('<span style="color:#27ae60;font-weight:bold">⚡ Active</span>')
    return mark_safe('<span style="color:#e74c3c;font-weight:bold">✘ No Power</span>')
power_badge.short_description = 'Power'


# ── Category ──────────────────────────────────────────────────────
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    ordering = ('id',)


# ── GridNode (base view) ──────────────────────────────────────────
@admin.register(GridNode)
class GridNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'input', 'output', power_badge)
    list_filter  = ('category', 'status', 'power_active')
    search_fields = ('name',)


# ── GridEdge ──────────────────────────────────────────────────────
@admin.register(GridEdge)
class GridEdgeAdmin(admin.ModelAdmin):
    list_display  = ('source_name', 'arrow', 'target_name', 'type', 'capacity_display', 'edge_active')
    list_filter   = ('type', 'active')
    search_fields = ('source__name', 'target__name')
    readonly_fields = ('source', 'target', 'type', 'active')

    @admin.display(description='From')
    def source_name(self, obj):
        return obj.source.name

    @admin.display(description='')
    def arrow(self, obj):
        return mark_safe('<strong>→</strong>')

    @admin.display(description='To')
    def target_name(self, obj):
        return obj.target.name

    @admin.display(description='Capacity')
    def capacity_display(self, obj):
        c = obj.capacity
        if c >= 1_000_000:
            return f"{c/1_000_000:.0f} GW"
        if c >= 1_000:
            return f"{c/1_000:.0f} MW"
        return f"{c:.0f} kW"

    @admin.display(description='Line')
    def edge_active(self, obj):
        if obj.active:
            return mark_safe('<span style="color:#27ae60;">● Live</span>')
        return mark_safe('<span style="color:#e74c3c;">● Dead</span>')


# ── Shared base ───────────────────────────────────────────────────
class BaseNodeAdmin(admin.ModelAdmin):
    list_display  = ('name', 'category', 'status', 'input', 'output', power_badge)
    list_filter   = ('status', 'power_active')
    search_fields = ('name',)
    readonly_fields = ('id', 'category', 'power_active')


# ── PowerPlant ────────────────────────────────────────────────────
class GridSubstationInline(admin.TabularInline):
    model = GridSubstation
    fk_name = 'power_plant'
    fields  = ('name', 'status', 'power_active', 'input', 'output')
    readonly_fields = ('power_active',)
    extra = 0
    show_change_link = True

@admin.register(PowerPlant)
class PowerPlantAdmin(BaseNodeAdmin):
    inlines = [GridSubstationInline]


# ── GridSubstation ────────────────────────────────────────────────
class DistributionSubstationInline(admin.TabularInline):
    model = DistributionSubstation
    fk_name = 'grid_substation'
    fields  = ('name', 'status', 'power_active', 'input', 'output')
    readonly_fields = ('power_active',)
    extra = 0
    show_change_link = True

@admin.register(GridSubstation)
class GridSubstationAdmin(BaseNodeAdmin):
    list_display = ('name', 'power_plant', 'status', 'input', 'output', power_badge)
    list_select_related = ('power_plant',)
    inlines = [DistributionSubstationInline]


# ── DistributionSubstation ────────────────────────────────────────
class DistributionTransformerInline(admin.TabularInline):
    model = DistributionTransformer
    fk_name = 'distribution_substation'
    fields  = ('name', 'status', 'power_active', 'input', 'output')
    readonly_fields = ('power_active',)
    extra = 0
    show_change_link = True

@admin.register(DistributionSubstation)
class DistributionSubstationAdmin(BaseNodeAdmin):
    list_display = ('name', 'grid_substation', 'status', 'input', 'output', power_badge)
    list_select_related = ('grid_substation',)
    inlines = [DistributionTransformerInline]


# ── DistributionTransformer ───────────────────────────────────────
class HouseInline(admin.TabularInline):
    model = House
    fk_name = 'distribution_transformer'
    fields  = ('name', 'status', 'power_active', 'output')
    readonly_fields = ('power_active',)
    extra = 0
    show_change_link = True

class IndustryInline(admin.TabularInline):
    model = Industry
    fk_name = 'distribution_transformer'
    fields  = ('name', 'status', 'power_active', 'output')
    readonly_fields = ('power_active',)
    extra = 0
    show_change_link = True

@admin.register(DistributionTransformer)
class DistributionTransformerAdmin(BaseNodeAdmin):
    list_display = ('name', 'distribution_substation', 'status', 'input', 'output', power_badge)
    list_select_related = ('distribution_substation',)
    inlines = [HouseInline, IndustryInline]


# ── Consumers ─────────────────────────────────────────────────────
@admin.register(House)
class HouseAdmin(BaseNodeAdmin):
    list_display = ('name', 'distribution_transformer', 'status', 'output', power_badge)
    list_select_related = ('distribution_transformer',)

@admin.register(Industry)
class IndustryAdmin(BaseNodeAdmin):
    list_display = ('name', 'distribution_transformer', 'status', 'output', power_badge)
    list_select_related = ('distribution_transformer',)
