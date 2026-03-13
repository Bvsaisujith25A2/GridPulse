from django.contrib import admin
from .models import (
    Category, GridNode, GridEdge,
    PowerPlant, GridSubstation, DistributionSubstation,
    DistributionTransformer, House, Industry
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    ordering = ('id',)


@admin.register(GridNode)
class GridNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'id', 'status', 'demand', 'input', 'output')
    list_filter = ('category', 'status')
    search_fields = ('name',)


@admin.register(GridEdge)
class GridEdgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'source', 'target', 'type', 'capacity')
    list_filter = ('type',)
    search_fields = ('source__name', 'target__name')


# ── The 6 Canvas Node Types ──────────────────────────────────────

class NodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'input', 'output', 'demand')
    list_filter = ('status',)
    search_fields = ('name',)
    readonly_fields = ('id', 'category')


admin.site.register(PowerPlant, NodeAdmin)
admin.site.register(GridSubstation, NodeAdmin)
admin.site.register(DistributionSubstation, NodeAdmin)
admin.site.register(DistributionTransformer, NodeAdmin)
admin.site.register(House, NodeAdmin)
admin.site.register(Industry, NodeAdmin)
