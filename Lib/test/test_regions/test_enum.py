import unittest
from regions import Region, is_local
from immutable import freeze
import sys

class TestRegionEnumerateBasic(unittest.TestCase):
    """Tests for basic enumerate construction and LRC behavior with regions."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_enumerate_from_region_iterator_increases_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        base_lrc = r._lrc

        obj = enumerate(r.it_arr)
        self.assertEqual(r._lrc, base_lrc + 1)

    def test_enumerate_set_to_none_decreases_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        base_lrc = r._lrc

        obj = enumerate(r.it_arr)
        self.assertEqual(r._lrc, base_lrc + 1)

        obj = None
        self.assertEqual(r._lrc, base_lrc)

    def test_enumerate_from_local_iterator_does_not_change_lrc(self):
        r = Region()
        base_lrc = r._lrc
        local1 = self.A()
        local2 = self.A()
        local_list = [local1, local2]
        obj = enumerate(local_list)
        self.assertEqual(r._lrc, base_lrc)
        self.assertTrue(is_local(obj))
        self.assertTrue(is_local(local1))
        self.assertTrue(is_local(local2))


class TestRegionEnumerateNext(unittest.TestCase):
    """Tests for next() calls on enumerate objects and their effect on LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A
    
    def disable_enum_optimization(self, r, iter):
        r._disable_op = next(iter)
        next(iter)
        ref_count = sys.getrefcount(r._disable_op)
        self.assertEqual(ref_count, 2)
        r._disable_op = None
        
    def test_next_on_enumerate_increases_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        base_lrc = r._lrc
        obj = enumerate(r.it_arr)
        self.assertEqual(r._lrc, base_lrc + 1) # Because enum object points to r.it_arr in the region

        re1 = next(obj)
        self.assertEqual(r._lrc, base_lrc + 2) # Now, re1 points to the first element of r.it_arr, which is r.a, so LRC increases by 1

    def test_next_on_enumerate_increases_lrc_each_call(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.d = self.A()
        r.arr = [r.a, r.b, r.c, r.d]
        r.it_arr = iter(r.arr)
        obj = enumerate(r.it_arr)
        base_lrc = r._lrc

        re1 = next(obj)
        self.assertEqual(r._lrc, base_lrc + 1)

        re2 = next(obj)
        self.assertEqual(r._lrc, base_lrc + 2)

        re3 = next(obj)
        self.assertEqual(r._lrc, base_lrc + 3)

        re4 = next(obj)
        self.assertEqual(r._lrc, base_lrc + 4)

    # @unittest.expectedFailure
    def test_next_result_moved_into_region_does_not_increase_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        obj = enumerate(r.it_arr)
        self.assertTrue(is_local(obj))
        base_lrc = r._lrc
        r.re1 = next(obj)
        self.assertFalse(is_local(r.re1))
        self.assertEqual(r._lrc, base_lrc+1)

    def test_next_result_moved_into_region_does_not_increase_lrc_2(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.d = self.A()
        r.arr = [r.a, r.b, r.c, r.d]
        r.it_arr = iter(r.arr)
        obj = enumerate(r.it_arr)
        base_lrc = r._lrc
        r.re1 = next(obj)
        self.assertEqual(r._lrc, base_lrc+1)
        r.re2 = next(obj)
        self.assertEqual(r._lrc, base_lrc)

    def test_next_result_moved_into_region_does_not_increase_lrc_3(self):
        r = Region()
        r.a = self.A(); r.b = self.A(); r.c = self.A(); r.d = self.A(); r.e = self.A()
        r.arr = [r.a, r.b, r.c, r.d, r.e]
        r.it_arr = iter(r.arr)
        obj = enumerate(r.it_arr)

        # Disable Optimization
        self.disable_enum_optimization(r, obj)
        self.assertTrue(is_local(obj))
        
        base_lrc = r._lrc
        r.re3 = next(obj)
        self.assertTrue(r.owns(r.re3))
        self.assertEqual(r._lrc, base_lrc)
        re4 = next(obj)
        self.assertFalse(r.owns(re4))
        self.assertEqual(r._lrc, base_lrc+1)

    def test_next_mixed_local_and_region_assignment(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.d = self.A()
        r.arr = [r.a, r.b, r.c, r.d]
        r.it_arr = iter(r.arr)
        obj = enumerate(r.it_arr)
        base_lrc = r._lrc

        re1 = next(obj)       # local borrow: LRC + 1
        r.re2 = next(obj)     # moved into region: LRC stays
        re3 = next(obj)       # local borrow: LRC + 1
        r.re4 = next(obj)     # moved into region: LRC stays
        self.assertEqual(r._lrc, base_lrc + 2)


class TestRegionEnumerateRelease(unittest.TestCase):
    """Tests for releasing enumerate results and their effect on LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    # @unittest.expectedFailure
    def test_setting_next_result_to_none_decreases_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        obj = enumerate(r.it_arr)

        re1 = next(obj)
        base_lrc = r._lrc

        re1 = None
        self.assertEqual(r._lrc, base_lrc)

    # @unittest.expectedFailure
    def test_setting_all_next_results_to_none_restores_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        obj = enumerate(r.it_arr)
        base_lrc = r._lrc

        re1 = next(obj)
        re2 = next(obj)
        self.assertEqual(r._lrc, base_lrc + 2)

        re1 = None
        self.assertEqual(r._lrc, base_lrc + 1)

        re2 = None
        self.assertEqual(r._lrc, base_lrc)

    def test_enumerate_set_to_none_after_next_releases_iterator_ref(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)

        re1 = next(enumerate(r.it_arr))
        base_lrc = r._lrc

        obj = enumerate(r.it_arr)
        self.assertEqual(r._lrc, base_lrc + 1)

        obj = None
        self.assertEqual(r._lrc, base_lrc)


class TestRegionEnumerateMoveIntoRegion(unittest.TestCase):
    """Tests for moving enumerate objects and results into regions."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def disable_enum_optimization(self, r, iter):
        r._disable_op = next(iter)
        next(iter)
        ref_count = sys.getrefcount(r._disable_op)
        self.assertEqual(ref_count, 2)
        r._disable_op = None

    def test_enumerate_moved_into_region_adjusts_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        obj = enumerate(r.it_arr)

        # Disable Optimization
        self.disable_enum_optimization(r, obj)
        self.assertTrue(is_local(obj))
        
        base_lrc = r._lrc
        r.obj = obj
        self.assertEqual(r._lrc, base_lrc)
        self.assertTrue(r.owns(obj))

    # @unittest.skip("GC ERROR")
    def test_next_on_region_owned_enumerate_does_not_increase_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        r.obj = enumerate(r.it_arr)
        base_lrc = r._lrc

        r.re1 = next(r.obj)
        self.assertEqual(r._lrc, base_lrc)

    # @unittest.skip("GC ERROR")
    def test_next_on_region_owned_enumerate_local_assignment_increases_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        r.obj = enumerate(r.it_arr)
        base_lrc = r._lrc

        re1 = next(r.obj)
        self.assertEqual(r._lrc, base_lrc + 1)
        re1 = None
        self.assertEqual(r._lrc, base_lrc)
        r = None


class TestRegionEnumerateFullLifecycle(unittest.TestCase):
    """End-to-end lifecycle tests matching the example script behavior."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_full_lifecycle_matches_example(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        base_lrc = r._lrc

        obj = enumerate(r.it_arr)
        self.assertEqual(r._lrc, base_lrc + 1)

        re1 = next(obj)
        self.assertEqual(r._lrc, base_lrc + 2)

        r.re2 = next(obj)
        self.assertEqual(r._lrc, base_lrc + 2)

        obj = None
        self.assertEqual(r._lrc, base_lrc + 1)

        re1 = None
        self.assertEqual(r._lrc, base_lrc)

    # @unittest.expectedFailure
    def test_full_lifecycle_matches_example_2(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        base_lrc = r._lrc

        obj = enumerate(r.it_arr)
        self.assertEqual(r._lrc, base_lrc + 1)

        re1 = next(obj)
        self.assertEqual(r._lrc, base_lrc + 2)

        r.re2 = next(obj)
        self.assertEqual(r._lrc, base_lrc + 2)

        re1 = None
        self.assertEqual(r._lrc, base_lrc + 1) # PROBLEM: LRC does not decrease

        obj = None
        self.assertEqual(r._lrc, base_lrc)

    def test_enumerate_result_index_and_value_correct(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        obj = enumerate(r.it_arr)

        idx0, val0 = next(obj)
        idx1, val1 = next(obj)

        self.assertEqual(idx0, 0)
        self.assertEqual(idx1, 1)
        self.assertIs(val0, r.a)
        self.assertIs(val1, r.b)

    def test_enumerate_with_start_offset(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr = [r.a, r.b]
        r.it_arr = iter(r.arr)
        base_lrc = r._lrc

        obj = enumerate(r.it_arr, start=5)
        self.assertEqual(r._lrc, base_lrc + 1)

        idx0, val0 = next(obj)
        self.assertEqual(idx0, 5)
        self.assertIs(val0, r.a)

    def test_enumerate_exhausted_raises_stop_iteration(self):
        r = Region()
        r.a = self.A()
        r.arr = [r.a]
        r.it_arr = iter(r.arr)
        obj = enumerate(r.it_arr)

        re1 = next(obj)
        base_lrc = r._lrc

        with self.assertRaises(StopIteration):
            next(obj)

        self.assertEqual(r._lrc, base_lrc)


class TestRegionEnumerateTwoRegions(unittest.TestCase):
    """Tests for enumerate behavior when elements span multiple regions."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A
    def disable_enum_optimization(self, r, iter):
        r._disable_op = next(iter)
        next(iter)
        ref_count = sys.getrefcount(r._disable_op)
        self.assertEqual(ref_count, 2)
        r._disable_op = None

    def test_enumerate_over_local_list_with_mixed_region_elements(self):
        r1 = Region()
        r2 = Region()
        r1.a = self.A()
        r2.b = self.A()

        local_list = [r1.a, r2.b]
        it = iter(local_list)
        obj = enumerate(it)

        base_r1 = r1._lrc
        base_r2 = r2._lrc

        re1 = next(obj)  # borrows r1.a
        self.assertEqual(r1._lrc, base_r1 + 1)
        self.assertEqual(r2._lrc, base_r2)

        re2 = next(obj)  # borrows r2.b
        self.assertEqual(r1._lrc, base_r1 + 1)
        self.assertEqual(r2._lrc, base_r2 + 1)

    def test_enumerate_over_local_list_with_mixed_region_elements_2(self):
        r1 = Region()
        r2 = Region()
        r1.a = self.A()
        r1.b = self.A()

        local_list = [r1.a, r1.b]
        base_r1 = r1._lrc
        base_r2 = r2._lrc
        it = iter(local_list)
        with self.assertRaises(Exception):
            r2.obj = enumerate(it)
        self.assertEqual(r1._lrc, base_r1)
        self.assertEqual(r2._lrc, base_r2)

    def test_next_on_enumerate_assigns_to_wrong_region_raises(self):
        r1 = Region()
        r2 = Region()
        r1.a = self.A()
        r1.b = self.A()
        r1.arr = [r1.a, r1.b]
        r1.it = iter(r1.arr)
        base_r1 = r1._lrc
        base_r2 = r2._lrc
        obj = enumerate(r1.it)
        self.disable_enum_optimization(r1, obj)

        with self.assertRaises(Exception):
            r2.re1 = next(obj)

        self.assertEqual(r1._lrc, base_r1+1) # obj points to r1.it, so LRC increases by 1
        self.assertEqual(r2._lrc, base_r2)

    def test_enumerate_moved_into_region_after_next_yielded_other_region_element_raises(self):
        r1 = Region()
        r2 = Region()
        r1.a = self.A()
        r1.b = self.A()
        r1.arr = [r1.a, r1.b]
        r1.it = iter(r1.arr)
        obj = enumerate(r1.it)
        re1 = next(obj)
        base_r1 = r1._lrc
        base_r2 = r2._lrc

        with self.assertRaises(Exception):
            r2.obj = obj

        self.assertEqual(r1._lrc, base_r1)
        self.assertEqual(r2._lrc, base_r2)

    def test_enumerate_spanning_two_regions_cannot_move_into_either(self):
        r1 = Region()
        r2 = Region()
        r1.a = self.A()
        r2.b = self.A()
        local_list = [r1.a, r2.b]
        it = iter(local_list)
        obj = enumerate(it)
        base_r1 = r1._lrc
        base_r2 = r2._lrc

        with self.assertRaises(Exception):
            r1.obj = obj

        self.assertTrue(is_local(obj))
        self.assertEqual(r1._lrc, base_r1)
        self.assertEqual(r2._lrc, base_r2)

        with self.assertRaises(Exception):
            r2.obj = obj

        self.assertTrue(is_local(obj))
        self.assertEqual(r1._lrc, base_r1)
        self.assertEqual(r2._lrc, base_r2)

    def test_two_enumerates_over_different_regions_do_not_interfere(self):
        r1 = Region()
        r2 = Region()
        r1.a = self.A()
        r1.b = self.A()
        r1.c = self.A()
        r1.d = self.A()
        r1.e = self.A()
        r2.a = self.A()
        r2.b = self.A()
        r2.c = self.A()
        r2.d = self.A()
        r2.e = self.A()
        r1.arr = [r1.a, r1.b, r1.c, r1.d, r1.e]
        r2.arr = [r2.c, r2.d, r2.c, r2.d, r2.e]
        r1.it = iter(r1.arr)
        r2.it = iter(r2.arr)
        base_r1 = r1._lrc
        base_r2 = r2._lrc

        obj1 = enumerate(r1.it)
        obj2 = enumerate(r2.it)
        self.assertEqual(r1._lrc, base_r1 + 1)
        self.assertEqual(r2._lrc, base_r2 + 1)

        # Disable Optimization
        self.disable_enum_optimization(r1, obj1)
        self.disable_enum_optimization(r2, obj2)

        re1 = next(obj1)
        self.assertEqual(r1._lrc, base_r1 + 2)
        self.assertEqual(r2._lrc, base_r2 + 1)

        re2 = next(obj2)
        self.assertEqual(r1._lrc, base_r1 + 2)
        self.assertEqual(r2._lrc, base_r2 + 2)

        re1 = None
        self.assertEqual(r1._lrc, base_r1 + 1) 
        self.assertEqual(r2._lrc, base_r2 + 2)

        re2 = None
        self.assertEqual(r1._lrc, base_r1 + 1)
        self.assertEqual(r2._lrc, base_r2 + 1)

        obj1 = None
        self.assertEqual(r1._lrc, base_r1)
        self.assertEqual(r2._lrc, base_r2 + 1)
        obj2 = None
        self.assertEqual(r1._lrc, base_r1)
        self.assertEqual(r2._lrc, base_r2)
    
    def test_enumerate_results_released_independently_per_region(self):
        r1 = Region()
        r2 = Region()
        r1.a = self.A()
        r2.b = self.A()

        local_list = [r1.a, r2.b]
        it = iter(local_list)
        obj = enumerate(it)

        idx0, val0 = next(obj)
        idx1, val1 = next(obj)

        base_r1 = r1._lrc
        base_r2 = r2._lrc

        val0 = None
        self.assertEqual(r1._lrc, base_r1 - 1)
        self.assertEqual(r2._lrc, base_r2)

        val1 = None
        self.assertEqual(r1._lrc, base_r1 - 1)
        self.assertEqual(r2._lrc, base_r2 - 1)


if __name__ == "__main__":
    unittest.main()