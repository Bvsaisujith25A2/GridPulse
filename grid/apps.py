from django.apps import AppConfig


class GridConfig(AppConfig):
    name = 'grid'

    def ready(self):
        from .telemetry import register_shutdown_hooks

        register_shutdown_hooks()
