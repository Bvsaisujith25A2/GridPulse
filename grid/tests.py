from django.test import TestCase
from grid.models import (
    Category, GridNode, GridEdge,
    PowerPlant, GridSubstation, DistributionSubstation,
    DistributionTransformer, House, Industry,
)


class CategorySeedTests(TestCase):
    def test_six_categories_seeded(self):
        """Data migration must seed exactly the 6 required categories."""
        expected = {'CAT-PP', 'CAT-GS', 'CAT-DS', 'CAT-DT', 'CAT-HS', 'CAT-ID'}
        actual = set(Category.objects.values_list('id', flat=True))
        self.assertEqual(actual, expected)

    def test_category_auto_assigned_on_save(self):
        self.assertEqual(PowerPlant.objects.create(name='PP').category_id, 'CAT-PP')
        self.assertEqual(GridSubstation.objects.create(name='GS').category_id, 'CAT-GS')
        self.assertEqual(DistributionSubstation.objects.create(name='DS').category_id, 'CAT-DS')
        self.assertEqual(DistributionTransformer.objects.create(name='DT').category_id, 'CAT-DT')
        self.assertEqual(House.objects.create(name='H').category_id, 'CAT-HS')
        self.assertEqual(Industry.objects.create(name='I').category_id, 'CAT-ID')


class UUIDTests(TestCase):
    def test_each_node_gets_unique_uuid(self):
        import uuid
        pp = PowerPlant.objects.create(name='PP1')
        gs = GridSubstation.objects.create(name='GS1')
        self.assertIsInstance(pp.id, uuid.UUID)
        self.assertIsInstance(gs.id, uuid.UUID)
        self.assertNotEqual(pp.id, gs.id)


class HierarchyAndAutoEdgeTests(TestCase):
    def setUp(self):
        self.pp = PowerPlant.objects.create(name='Plant 1')
        self.gs = GridSubstation.objects.create(name='GS 1', power_plant=self.pp)
        self.ds = DistributionSubstation.objects.create(name='DS 1', grid_substation=self.gs)
        self.dt = DistributionTransformer.objects.create(name='DT 1', distribution_substation=self.ds)
        self.house = House.objects.create(name='House 1', distribution_transformer=self.dt)
        self.industry = Industry.objects.create(name='Industry 1', distribution_transformer=self.dt)

    def test_fk_relationships(self):
        self.assertEqual(self.gs.power_plant, self.pp)
        self.assertEqual(self.ds.grid_substation, self.gs)
        self.assertEqual(self.dt.distribution_substation, self.ds)
        self.assertEqual(self.house.distribution_transformer, self.dt)
        self.assertEqual(self.industry.distribution_transformer, self.dt)

    def test_reverse_relations(self):
        self.assertIn(self.gs, self.pp.grid_substations.all())
        self.assertIn(self.ds, self.gs.distribution_substations.all())
        self.assertIn(self.dt, self.ds.distribution_transformers.all())
        self.assertIn(self.house, self.dt.houses.all())
        self.assertIn(self.industry, self.dt.industries.all())

    def test_edges_auto_created(self):
        # Each connection must auto-create a GridEdge with the correct type
        self.assertTrue(GridEdge.objects.filter(source=self.pp, target=self.gs, type='TransmissionLine').exists())
        self.assertTrue(GridEdge.objects.filter(source=self.gs, target=self.ds, type='SubTransmissionLine').exists())
        self.assertTrue(GridEdge.objects.filter(source=self.ds, target=self.dt, type='Feeder11kV').exists())
        self.assertTrue(GridEdge.objects.filter(source=self.dt, target=self.house, type='SecondaryDistributionLine').exists())
        self.assertTrue(GridEdge.objects.filter(source=self.dt, target=self.industry, type='SecondaryDistributionLine').exists())

    def test_edge_removed_when_parent_cleared(self):
        self.gs.power_plant = None
        self.gs.save()
        self.assertFalse(GridEdge.objects.filter(target=self.gs).exists())

    def test_multiple_consumers_per_transformer(self):
        house2 = House.objects.create(name='House 2', distribution_transformer=self.dt)
        house3 = House.objects.create(name='House 3', distribution_transformer=self.dt)
        self.assertEqual(self.dt.houses.count(), 3)  # house + house2 + house3
        # All have edges
        self.assertTrue(GridEdge.objects.filter(source=self.dt, target=house2).exists())
        self.assertTrue(GridEdge.objects.filter(source=self.dt, target=house3).exists())


class OutputIntervalTests(TestCase):
    def test_power_plant_output(self):
        pp = PowerPlant.objects.create(name='PP')
        pp.generate_random_output()
        self.assertTrue(11.0 <= pp.output <= 25.0)

    def test_distribution_substation_output(self):
        ds = DistributionSubstation.objects.create(name='DS')
        ds.generate_random_output()
        self.assertTrue(10.5 <= ds.output <= 11.5)

    def test_distribution_transformer_output(self):
        dt = DistributionTransformer.objects.create(name='DT')
        dt.generate_random_output()
        self.assertTrue(0.21 <= dt.output <= 0.25)

    def test_house_output(self):
        h = House.objects.create(name='H')
        h.generate_random_output()
        self.assertTrue(0.0 <= h.output <= 5.0)

    def test_industry_output(self):
        i = Industry.objects.create(name='I')
        i.generate_random_output()
        self.assertTrue(0.0 <= i.output <= 50.0)
