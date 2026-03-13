from django.test import TestCase
from grid.models import (
    Category, GridNode, GridEdge,
    PowerPlant, GridSubstation, DistributionSubstation,
    DistributionTransformer, House, Industry,
    LINE_CAPACITY_DEFAULTS,
)


class CategoryTests(TestCase):
    def test_six_categories_seeded(self):
        expected = {'CAT-PP', 'CAT-GS', 'CAT-DS', 'CAT-DT', 'CAT-HS', 'CAT-ID'}
        self.assertEqual(set(Category.objects.values_list('id', flat=True)), expected)


class AutoEdgeCreationTests(TestCase):
    def setUp(self):
        self.pp = PowerPlant.objects.create(name='PP')
        self.gs = GridSubstation.objects.create(name='GS', power_plant=self.pp)
        self.ds = DistributionSubstation.objects.create(name='DS', grid_substation=self.gs)
        self.dt = DistributionTransformer.objects.create(name='DT', distribution_substation=self.ds)
        self.h  = House.objects.create(name='H', distribution_transformer=self.dt)
        self.ind = Industry.objects.create(name='I', distribution_transformer=self.dt)

    def test_edges_created(self):
        self.assertTrue(GridEdge.objects.filter(source=self.pp, target=self.gs, type='TransmissionLine').exists())
        self.assertTrue(GridEdge.objects.filter(source=self.gs, target=self.ds, type='SubTransmissionLine').exists())
        self.assertTrue(GridEdge.objects.filter(source=self.ds, target=self.dt, type='Feeder11kV').exists())
        self.assertTrue(GridEdge.objects.filter(source=self.dt, target=self.h,  type='SecondaryDistributionLine').exists())
        self.assertTrue(GridEdge.objects.filter(source=self.dt, target=self.ind,type='SecondaryDistributionLine').exists())

    def test_edge_capacity_defaults(self):
        e = GridEdge.objects.get(source=self.pp, target=self.gs)
        self.assertEqual(e.capacity, LINE_CAPACITY_DEFAULTS['TransmissionLine'])

    def test_edge_removed_when_parent_cleared(self):
        self.gs.power_plant = None
        self.gs.save()
        self.assertFalse(GridEdge.objects.filter(target=self.gs).exists())


class PowerFlowPropagationTests(TestCase):
    def setUp(self):
        self.pp  = PowerPlant.objects.create(name='PP')
        self.gs  = GridSubstation.objects.create(name='GS', power_plant=self.pp)
        self.ds  = DistributionSubstation.objects.create(name='DS', grid_substation=self.gs)
        self.dt  = DistributionTransformer.objects.create(name='DT', distribution_substation=self.ds)
        self.h   = House.objects.create(name='H', distribution_transformer=self.dt)
        self.ind = Industry.objects.create(name='I', distribution_transformer=self.dt)

    def _refresh(self):
        for attr in ('gs', 'ds', 'dt', 'h', 'ind'):
            setattr(self, attr, getattr(self, attr).__class__.objects.get(pk=getattr(self, attr).pk))

    def test_all_active_by_default(self):
        self._refresh()
        for node in (self.gs, self.ds, self.dt, self.h, self.ind):
            self.assertTrue(node.power_active, f"{node.name} should be power_active")

    def test_powerplant_offline_cascades(self):
        self.pp.status = 'Offline'
        self.pp.save()
        self._refresh()
        self.assertFalse(self.pp.power_active)
        for node in (self.gs, self.ds, self.dt, self.h, self.ind):
            self.assertFalse(node.power_active, f"{node.name} should lose power")

    def test_powerplant_back_online_restores(self):
        self.pp.status = 'Offline'
        self.pp.save()
        self.pp.status = 'Stable'
        self.pp.save()
        self._refresh()
        for node in (self.gs, self.ds, self.dt, self.h, self.ind):
            self.assertTrue(node.power_active, f"{node.name} should regain power")

    def test_intermediate_node_offline_cascades(self):
        """DistributionSubstation offline → DT, H, I lose power; GS stays active."""
        self.ds.status = 'Offline'
        self.ds.save()
        self._refresh()
        self.assertTrue(self.gs.power_active)    # upstream unaffected
        self.assertFalse(self.ds.power_active)
        self.assertFalse(self.dt.power_active)
        self.assertFalse(self.h.power_active)
        self.assertFalse(self.ind.power_active)

    def test_consumer_own_offline_does_not_affect_others(self):
        """A House going Offline only affects itself, not siblings."""
        self.h.status = 'Offline'
        self.h.save()
        self.h.refresh_from_db()
        self.ind.refresh_from_db()
        self.assertFalse(self.h.power_active)
        self.assertTrue(self.ind.power_active)   # sibling unaffected

    def test_edge_active_mirrors_node_power_active(self):
        self.ds.status = 'Offline'
        self.ds.save()
        edge_ds = GridEdge.objects.get(target=self.ds)
        edge_dt = GridEdge.objects.get(target=self.dt)
        self.assertFalse(edge_ds.active)   # upstream edge to DS goes dead
        self.assertFalse(edge_dt.active)   # downstream edge follows
