from django.test import TestCase
from grid.models import (
    Category, GridNode, GridEdge,
    PowerPlant, GridSubstation, DistributionSubstation,
    DistributionTransformer, House, Industry
)


class CategoryTests(TestCase):
    def test_six_categories_seeded(self):
        """All 6 required categories should be present via data migration."""
        expected = {'CAT-PP', 'CAT-GS', 'CAT-DS', 'CAT-DT', 'CAT-HS', 'CAT-ID'}
        actual = set(Category.objects.values_list('id', flat=True))
        self.assertEqual(actual, expected)

    def test_category_ids_auto_assigned(self):
        pp = PowerPlant.objects.create(name="Plant A")
        self.assertEqual(pp.category.id, 'CAT-PP')
        gs = GridSubstation.objects.create(name="GS A")
        self.assertEqual(gs.category.id, 'CAT-GS')
        ds = DistributionSubstation.objects.create(name="DS A")
        self.assertEqual(ds.category.id, 'CAT-DS')
        dt = DistributionTransformer.objects.create(name="DT A")
        self.assertEqual(dt.category.id, 'CAT-DT')
        h = House.objects.create(name="House A")
        self.assertEqual(h.category.id, 'CAT-HS')
        i = Industry.objects.create(name="Industry A")
        self.assertEqual(i.category.id, 'CAT-ID')


class GridNodeUUIDTests(TestCase):
    def test_uuid_generated(self):
        import uuid
        node = House.objects.create(name="UUID Test")
        self.assertIsInstance(node.id, uuid.UUID)


class OutputIntervalTests(TestCase):
    def test_power_plant_output_interval(self):
        pp = PowerPlant.objects.create(name="PP")
        pp.generate_random_output()
        self.assertTrue(11.0 <= pp.output <= 25.0)

    def test_distribution_substation_output_interval(self):
        ds = DistributionSubstation.objects.create(name="DS")
        ds.generate_random_output()
        self.assertTrue(10.5 <= ds.output <= 11.5)

    def test_distribution_transformer_output_interval(self):
        dt = DistributionTransformer.objects.create(name="DT")
        dt.generate_random_output()
        self.assertTrue(0.21 <= dt.output <= 0.25)


class GridEdgeTests(TestCase):
    def test_edge_connects_nodes(self):
        pp = PowerPlant.objects.create(name="Plant 1")
        gs = GridSubstation.objects.create(name="GS 1")
        edge = GridEdge.objects.create(source=pp, target=gs, type='TransmissionLine')

        self.assertEqual(pp.outgoing_edges.count(), 1)
        self.assertEqual(gs.incoming_edges.count(), 1)
        self.assertEqual(edge.source.id, pp.id)
        self.assertEqual(edge.target.id, gs.id)
