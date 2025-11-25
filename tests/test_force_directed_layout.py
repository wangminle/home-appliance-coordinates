import unittest
import sys
import os
import math
import numpy as np

# Add dev/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dev', 'src'))

from utils.fast_layout import FastLayoutManager, LayoutElement, ElementType, BoundingBox

class TestForceDirectedLayout(unittest.TestCase):
    def setUp(self):
        self.bounds = (-10, -10, 10, 10)
        self.manager = FastLayoutManager(self.bounds)

    def test_overlap_resolution(self):
        """Test that overlapping elements are pushed apart"""
        # Create two overlapping elements at (0,0)
        bbox1 = BoundingBox(-1, -0.5, 1, 0.5) # 2x1 box
        elem1 = LayoutElement(ElementType.DEVICE_INFO, bbox1, (0, 0), element_id="1")
        
        bbox2 = BoundingBox(-1, -0.5, 1, 0.5) # 2x1 box
        elem2 = LayoutElement(ElementType.DEVICE_INFO, bbox2, (0, 0), element_id="2")
        
        self.manager.add_element(elem1)
        self.manager.add_element(elem2)
        
        # Initial position check
        self.assertEqual(elem1.current_x, 0)
        self.assertEqual(elem2.current_x, 0)
        
        # Run layout
        self.manager.compute_layout(iterations=50)
        
        # Check that they moved apart
        dist = math.sqrt((elem1.current_x - elem2.current_x)**2 + 
                         (elem1.current_y - elem2.current_y)**2)
        
        print(f"Distance after layout: {dist}")
        self.assertGreater(dist, 1.0, "Elements should be pushed apart")

    def test_boundary_constraint(self):
        """Test that elements stay within bounds"""
        # Create element near boundary
        bbox = BoundingBox(8, 8, 10, 9) # Near top-right
        elem = LayoutElement(ElementType.DEVICE_INFO, bbox, (9, 9), element_id="1")
        
        # Set initial position outside bounds to test return
        elem.current_x = 11
        elem.bounding_box = BoundingBox(10, 8.5, 12, 9.5)
        
        self.manager.add_element(elem)
        self.manager.compute_layout(iterations=50)
        
        # Check if it came back
        print(f"Position after boundary check: ({elem.current_x}, {elem.current_y})")
        self.assertLess(elem.current_x, 10, "Element should be inside X bound")
        self.assertLess(elem.current_y, 10, "Element should be inside Y bound")

    def test_static_obstacle(self):
        """Test that static elements don't move and repel others"""
        # Static obstacle at (0,0)
        obs_bbox = BoundingBox(-2, -2, 2, 2)
        obs = LayoutElement(ElementType.SECTOR, obs_bbox, (0, 0), 
                           movable=False, static=True, element_id="obs")
        
        # Dynamic element overlapping obstacle
        elem_bbox = BoundingBox(-1, -1, 1, 1)
        elem = LayoutElement(ElementType.DEVICE_INFO, elem_bbox, (0, 0), element_id="elem")
        
        self.manager.add_element(obs)
        self.manager.add_element(elem)
        
        self.manager.compute_layout(iterations=50)
        
        # Static shouldn't move
        self.assertEqual(obs.current_x, 0)
        self.assertEqual(obs.current_y, 0)
        
        # Dynamic should move away
        dist = math.sqrt(elem.current_x**2 + elem.current_y**2)
        print(f"Dynamic element distance from obstacle: {dist}")
        self.assertGreater(dist, 2.0, "Element should be pushed out of obstacle")

if __name__ == '__main__':
    unittest.main()
