from django.test import TestCase
from grid.models import (
    Category, GridNode, GridEdge, PowerPlant, TransmissionLine,
    GridSubstation, SubTransmissionLine, Feeder11kV,
    SecondaryDistributionLine, ServiceLine, House, Industry
)

class GridModelTests(TestCase):
    def test_category_creation(self):
        pp = PowerPlant.objects.create(name="Plant A")
        self.assertEqual(pp.category.id, 'CAT-PP')
        self.assertEqual(pp.category.name, 'Power Plant')

    def test_grid_node_uuid(self):
        h = House.objects.create(name="House A")
        self.assertIsNotNone(h.id)
        # Should be UUID type
        import uuid
        self.assertIsInstance(h.id, uuid.UUID)

    def test_output_generation(self):
        pp = PowerPlant.objects.create(name="Plant Gen")
        self.assertEqual(pp.output, 0.0) # default
        pp.generate_random_output()
        self.assertTrue(11.0 <= pp.output <= 25.0)

    def test_graph_connections(self):
        # Create a mini topology
        pp = PowerPlant.objects.create(name="Plant 1")
        tl = TransmissionLine.objects.create(name="Line 1")
        gs = GridSubstation.objects.create(name="Grid Substation 1")
        
        # Connect PP -> Line -> GS
        edge1 = GridEdge.objects.create(source=pp, target=tl, type='TransmissionLine')
        edge2 = GridEdge.objects.create(source=tl, target=gs, type='TransmissionLine')

        self.assertEqual(pp.outgoing_edges.count(), 1)
        self.assertEqual(tl.incoming_edges.count(), 1)
        self.assertEqual(tl.outgoing_edges.count(), 1)
        self.assertEqual(gs.incoming_edges.count(), 1)

        # Output flow relation validation
        self.assertEqual(pp.outgoing_edges.first().target.id, tl.id)
        self.assertEqual(tl.incoming_edges.first().source.id, pp.id)
