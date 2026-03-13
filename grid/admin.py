from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, GridNode, GridEdge,
    PowerPlant, GridSubstation, DistributionSubstation,
    DistributionTransformer, House, Industry,
)


# ── Category ──────────────────────────────────────────────────────
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    ordering = ('id',)


# ── GridNode (base — all nodes visible here) ──────────────────────
@admin.register(GridNode)
class GridNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'input', 'output', 'demand')
    list_filter = ('category', 'status')
    search_fields = ('name',)


# ── GridEdge (connections / lines) ───────────────────────────────
@admin.register(GridEdge)
class GridEdgeAdmin(admin.ModelAdmin):
    list_display = ('source_name', 'arrow', 'target_name', 'type', 'capacity')
    list_filter = ('type',)
    search_fields = ('source__name', 'target__name')
    readonly_fields = ('source', 'target', 'type')

    @admin.display(description='From')
    def source_name(self, obj):
        return obj.source.name

    @admin.display(description='')
    def arrow(self, obj):
        return format_html('<strong>→</strong>')

    @admin.display(description='To')
    def target_name(self, obj):
        return obj.target.name


# ── Shared inline/admin config ────────────────────────────────────
class BaseNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'input', 'output', 'demand')
    list_filter = ('status',)
    search_fields = ('name',)
    readonly_fields = ('id', 'category')


# ── PowerPlant ────────────────────────────────────────────────────
class GridSubstationInline(admin.TabularInline):
    model = GridSubstation
    fk_name = 'power_plant'
    fields = ('name', 'status', 'input', 'output')
    extra = 0
    show_change_link = True

@admin.register(PowerPlant)
class PowerPlantAdmin(BaseNodeAdmin):
    inlines = [GridSubstationInline]


# ── GridSubstation ────────────────────────────────────────────────
class DistributionSubstationInline(admin.TabularInline):
    model = DistributionSubstation
    fk_name = 'grid_substation'
    fields = ('name', 'status', 'input', 'output')
    extra = 0
    show_change_link = True

@admin.register(GridSubstation)
class GridSubstationAdmin(BaseNodeAdmin):
    list_display = ('name', 'power_plant', 'status', 'input', 'output')
    list_select_related = ('power_plant',)
    inlines = [DistributionSubstationInline]


# ── DistributionSubstation ────────────────────────────────────────
class DistributionTransformerInline(admin.TabularInline):
    model = DistributionTransformer
    fk_name = 'distribution_substation'
    fields = ('name', 'status', 'input', 'output')
    extra = 0
    show_change_link = True

@admin.register(DistributionSubstation)
class DistributionSubstationAdmin(BaseNodeAdmin):
    list_display = ('name', 'grid_substation', 'status', 'input', 'output')
    list_select_related = ('grid_substation',)
    inlines = [DistributionTransformerInline]


# ── DistributionTransformer ───────────────────────────────────────
class HouseInline(admin.TabularInline):
    model = House
    fk_name = 'distribution_transformer'
    fields = ('name', 'status', 'output', 'demand')
    extra = 0
    show_change_link = True

class IndustryInline(admin.TabularInline):
    model = Industry
    fk_name = 'distribution_transformer'
    fields = ('name', 'status', 'output', 'demand')
    extra = 0
    show_change_link = True

@admin.register(DistributionTransformer)
class DistributionTransformerAdmin(BaseNodeAdmin):
    list_display = ('name', 'distribution_substation', 'status', 'input', 'output')
    list_select_related = ('distribution_substation',)
    inlines = [HouseInline, IndustryInline]


# ── Consumers ─────────────────────────────────────────────────────
@admin.register(House)
class HouseAdmin(BaseNodeAdmin):
    list_display = ('name', 'distribution_transformer', 'status', 'output', 'demand')
    list_select_related = ('distribution_transformer',)

@admin.register(Industry)
class IndustryAdmin(BaseNodeAdmin):
    list_display = ('name', 'distribution_transformer', 'status', 'output', 'demand')
    list_select_related = ('distribution_transformer',)
