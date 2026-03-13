"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from grid import views as grid_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('grid/topology/', grid_views.grid_topology, name='grid-topology'),
    path('grid/nodes/create/', grid_views.grid_node_create, name='grid-node-create'),
    path('grid/nodes/<uuid:node_id>/arduino/', grid_views.grid_house_arduino_binding, name='grid-house-arduino-binding'),
    path('grid/nodes/<uuid:node_id>/power/', grid_views.grid_node_power, name='grid-node-power'),
    path('grid/snapshot/', grid_views.grid_status_snapshot, name='grid-status-snapshot'),
    path('grid/stream/', grid_views.grid_status_stream, name='grid-status-stream'),
]
