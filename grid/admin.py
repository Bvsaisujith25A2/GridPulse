from django.contrib import admin
from .models import (
    Category, GridNode, GridEdge, PowerPlant, TransmissionLine,
    GridSubstation, SubTransmissionLine, Feeder11kV,
    SecondaryDistributionLine, ServiceLine, House, Industry
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')

@admin.register(GridNode)
class GridNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'id', 'status', 'demand', 'input', 'output')
    list_filter = ('category', 'status')
    search_fields = ('name', 'id')

@admin.register(GridEdge)
class GridEdgeAdmin(admin.ModelAdmin):
    list_display = ('id', 'source', 'target', 'type', 'capacity')
    list_filter = ('type',)
    search_fields = ('source__name', 'target__name')

# Registering specific node types with the same base display
class SpecificNodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'status', 'input', 'output')
    list_filter = ('status',)
    search_fields = ('name',)

admin.site.register(PowerPlant, SpecificNodeAdmin)
admin.site.register(TransmissionLine, SpecificNodeAdmin)
admin.site.register(GridSubstation, SpecificNodeAdmin)
admin.site.register(SubTransmissionLine, SpecificNodeAdmin)
admin.site.register(Feeder11kV, SpecificNodeAdmin)
admin.site.register(SecondaryDistributionLine, SpecificNodeAdmin)
admin.site.register(ServiceLine, SpecificNodeAdmin)
admin.site.register(House, SpecificNodeAdmin)
admin.site.register(Industry, SpecificNodeAdmin)

