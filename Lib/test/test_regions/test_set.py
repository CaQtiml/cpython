import unittest
from regions import Region, is_local
from immutable import freeze, isfrozen


class TestRegionSet(unittest.TestCase):
    """Tests for basic set construction and LRC behavior with regions."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A
    
    def test_initial_lrc(self):
        r = Region()
        self.assertEqual(r._lrc, 1)

    def test_set_from_region_array_increases_lrc(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.arr = [r.word, r.word2]
        base_lrc = r._lrc

        s = set(r.arr)

        self.assertEqual(r._lrc, base_lrc + 2)

    def test_set_to_none_decreases_lrc(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.arr = [r.word, r.word2]
        base_lrc = r._lrc

        s = set(r.arr)
        self.assertEqual(r._lrc, base_lrc + 2)

        s = None
        self.assertEqual(r._lrc, base_lrc)

    def test_set_moved_into_region_adjusts_lrc(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.word3 = self.A()
        r.word4 = self.A()
        r.arr = [r.word, r.word2, r.word3, r.word4]
        base_lrc = r._lrc

        s = set(r.arr)
        # Set borrows all 4 elements
        self.assertEqual(r._lrc, base_lrc + 4)

        # Moving into region: region owns the set, elements no longer borrowed
        # but `s` still holds an external ref
        r.set = s
        self.assertEqual(r._lrc, base_lrc + 1)

    def test_set_from_set_in_region_increases_lrc(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.word3 = self.A()
        r.word4 = self.A()
        r.arr = [r.word, r.word2, r.word3, r.word4]
        s = set(r.arr)
        r.set = s
        base_lrc = r._lrc

        s2 = set(r.set)
        self.assertEqual(r._lrc, base_lrc + 4)

        s2 = None
        self.assertEqual(r._lrc, base_lrc)

    def test_set_from_dict_keys_with_object_keys(self):
        r = Region()
        r.word = {self.A(): "value", self.A(): "value2"}
        base_lrc = r._lrc

        s = set(r.word)
        self.assertEqual(r._lrc, base_lrc + 2)

    def test_set_from_dict_with_frozen_string_keys(self):
        r = Region()
        r.word = {"key": "value", "key2": "value2"}
        base_lrc = r._lrc

        s = set(r.word)
        # Frozen string keys don't bump LRC
        self.assertEqual(r._lrc, base_lrc)

    def test_set_move_into_region_fails_if_element_in_another_region(self):
        r = Region()
        r2 = Region()
        r2.word4 = self.A()

        aa = self.A()
        ab = self.A()
        ac = self.A()
        arr = [aa, ab, ac, r2.word4]
        s = set(arr)

        with self.assertRaises(Exception):
            r.set = s

        # Locals should still be local after the failed move
        self.assertTrue(is_local(aa))
        self.assertTrue(is_local(ab))
        self.assertTrue(is_local(ac))



class TestRegionSetDiscard(unittest.TestCase):
    """Tests for set discard/pop operations and their effect on LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_discard_decreases_lrc(self):
        r1 = Region()
        r2 = Region()
        r3 = Region()
        r4 = Region()

        s1 = set([r1, r2, r3])
        r4.s = s1
        self.assertEqual(r1.parent, r4)

        s1.discard(r1)
        self.assertIsNone(r1.parent)

        s1.discard(r2)
        self.assertIsNone(r2.parent)

        s1.discard(r3)
        self.assertIsNone(r3.parent)
        
    def test_discard_nonexistent_element_does_not_change_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.arr1 = [r.a, r.b]

        s1 = set(r.arr1)
        base_lrc = r._lrc

        s1.discard(r.a)   # exists, LRC - 1
        self.assertEqual(r._lrc, base_lrc - 1)

        s1.discard(r.a)   # already gone, should be no change
        self.assertEqual(r._lrc, base_lrc - 1)
    
    def test_pop_from_set_decreases_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr = [r.a, r.b, r.c]
        base_lrc = r._lrc
        s = set(r.arr)
        self.assertEqual(r._lrc, base_lrc + 3)
        popped = s.pop()
        self.assertEqual(r._lrc, base_lrc + 3) # Although the popped element is removed from the set, it still holds a reference to it until it's released, so LRC should not change until we release the popped element.
        popped = None
        self.assertEqual(r._lrc, base_lrc + 2) # Now that the popped element is released, LRC should decrease by 1.
    
    def test_pop_from_set_inside_region_object_outsude_region_decreases_lrc(self):
        r = Region()
        a = self.A()
        b = self.A()
        c = self.A()
        arr = [a, b, c]
        base_lrc = r._lrc
        r.s = set(arr)
        self.assertEqual(r._lrc, base_lrc + 6)
        popped = r.s.pop()
        self.assertEqual(r._lrc, base_lrc + 6 + 1) 


class TestRegionSetDifference(unittest.TestCase):
    """Tests for set difference operations and their effect on LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_set_difference_does_not_increase_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.a]
        r.arr3 = [r.b]

        original_lrc = r._lrc
        s1 = set(r.arr1)
        self.assertEqual(r._lrc, original_lrc + 3)
        s2 = set(r.arr2)
        self.assertEqual(r._lrc, original_lrc + 3 + 1)
        s3 = set(r.arr3)
        self.assertEqual(r._lrc, original_lrc + 3 + 1 + 1)
        base_lrc = r._lrc

        s4 = s1.difference(s2, s3)
        self.assertEqual(r._lrc, base_lrc + 1) # s4 borrows r.c, but not r.a or r.b

        # s4 only contains r.c, so LRC should reflect that
        self.assertTrue(is_local(s4))

    def test_set_difference_result_releases_lrc_on_none(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.a]
        r.arr3 = [r.b]

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        s3 = set(r.arr3)

        s4 = s1.difference(s2, s3)
        base_lrc = r._lrc

        s4 = None
        self.assertLess(r._lrc, base_lrc)

    def test_set_difference_result_releases_lrc_on_none_2_elem(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.a]

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        s3 = s1.difference(s2)
        self.assertEqual(r._lrc, base_lrc + 2)


class TestRegionSetSymmetricDifference(unittest.TestCase):
    """Tests for symmetric difference (XOR) operations on sets."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_symmetric_difference_result_is_local(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]

        original_lrc = r._lrc
        s1 = set(r.arr1)
        self.assertEqual(r._lrc, original_lrc + 3)
        s2 = set(r.arr2)
        self.assertEqual(r._lrc, original_lrc + 3 + 3)
        base_lrc = r._lrc

        result = s1.symmetric_difference(s2)
        self.assertEqual(r._lrc, base_lrc + 2)
        self.assertTrue(is_local(result))

    def test_symmetric_difference_lrc_released_on_none(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]

        s1 = set(r.arr1)
        s2 = set(r.arr2)

        result = s1.symmetric_difference(s2)
        base_lrc = r._lrc

        result = None
        # r.a and r.f are the unique elements, so LRC should drop by 2
        self.assertEqual(r._lrc, base_lrc - 2)

    def test_symmetric_difference_operator_matches_method(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        result_method = s1.symmetric_difference(s2)
        result_operator = s1 ^ s2
        self.assertEqual(r._lrc, base_lrc + 2 + 2) # both should borrow the same unique elements, and there are two result, +2 from result_method and +2 from result_operator

        self.assertEqual(result_method, result_operator)

class TestRegionFrozenSet(unittest.TestCase):
    """Tests for frozenset construction, ownership transfer, and copy behavior."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_frozenset_from_region_array_increases_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]
        base_lrc = r._lrc

        s1 = frozenset(r.arr1)
        self.assertEqual(r._lrc, base_lrc + 3)

    def test_frozenset_moved_into_region_adjusts_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]

        s1 = frozenset(r.arr1)
        r.set1 = s1
        base_lrc = r._lrc

        # s1 still holds an external ref but elements are now owned
        self.assertEqual(r._lrc, base_lrc)

    def test_frozenset_copy_is_same_object(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]

        s1 = frozenset(r.arr1)
        r.set1 = s1

        s2 = s1.copy()
        self.assertIs(s2, r.set1)

    def test_frozenset_copy_does_not_change_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]

        s1 = frozenset(r.arr1)
        r.set1 = s1
        base_lrc = r._lrc

        s2 = s1.copy()
        self.assertEqual(r._lrc, base_lrc + 1)

        s2 = None
        self.assertEqual(r._lrc, base_lrc)

    def test_frozenset_from_another_frozenset(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]

        s1 = frozenset(r.arr1)
        r.set1 = s1
        base_lrc = r._lrc

        s2 = frozenset(s1)
        self.assertIs(s2, s1)
        self.assertEqual(r._lrc, base_lrc + 1) # only the original reference to s1 increases LRC


class TestRegionSetCopy(unittest.TestCase):
    """Tests for set copy behavior and its effect on LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_copy_increases_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]

        s1 = set(r.arr1)
        base_lrc = r._lrc

        s2 = s1.copy()
        self.assertEqual(r._lrc, base_lrc + 3)

    def test_copy_released_decreases_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]

        s1 = set(r.arr1)
        base_lrc = r._lrc

        s2 = s1.copy()
        self.assertEqual(r._lrc, base_lrc + 3)

        s2 = None
        self.assertEqual(r._lrc, base_lrc)


class TestRegionSetIntersection(unittest.TestCase):
    """Tests for set intersection operations and their effect on LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_intersection_result_is_local(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]

        s1 = set(r.arr1)
        s2 = set(r.arr2)

        result = s1.intersection(s2)
        self.assertTrue(is_local(result))

    def test_intersection_lrc_reflects_common_elements(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.b, r.c, r.f]   # {b, c, f}

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        result = s1.intersection(s2)  # {b, c}
        self.assertEqual(r._lrc, base_lrc + 2)

        result = None
        self.assertEqual(r._lrc, base_lrc)

    def test_intersection_operator_matches_method(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        _ = s1 & s2
        self.assertEqual(r._lrc, base_lrc + 2) 
    def test_intersection_multiple_sets(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.d = self.A()
        r.e = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]
        r.arr3 = [r.b, r.d, r.e]

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        s3 = set(r.arr3)
        base_lrc = r._lrc

        result = s1.intersection(s2, s3)  # only {b}
        self.assertEqual(r._lrc, base_lrc + 1)

        result = None
        self.assertEqual(r._lrc, base_lrc)

    def test_intersection_multiple_sets_2_1(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]

        original_lrc = r._lrc
        r.s1 = set(r.arr1)
        self.assertEqual(r._lrc, original_lrc)
        s2 = set(r.arr2)
        self.assertEqual(r._lrc, original_lrc + 3)
        base_lrc = r._lrc

        result = r.s1.intersection(s2)
        self.assertEqual(r._lrc, base_lrc + 2)

    def test_intersection_multiple_sets_2_2(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.d = self.A()
        r.e = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]
        r.arr3 = [r.b, r.e, r.f]

        original_lrc = r._lrc
        r.s1 = set(r.arr1)
        self.assertEqual(r._lrc, original_lrc)
        s2 = set(r.arr2)
        self.assertEqual(r._lrc, original_lrc + 3)
        r.s3 = set(r.arr3)
        self.assertEqual(r._lrc, original_lrc + 3)
        base_lrc = r._lrc

        result = r.s1.intersection(s2, r.s3)
        self.assertEqual(r._lrc, base_lrc + 1)


class TestRegionSetIntersectionUpdate(unittest.TestCase):
    """Tests for in-place intersection (intersection_update / &=) and LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_intersection_update_removes_non_common_refs(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.b, r.c, r.f]   # {b, c, f}

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        s1.intersection_update(s2)  # s1 becomes {b, c}, drops ref to a
        # s1 now holds 2 refs (b, c), s2 holds 3 refs (b, c, f)
        self.assertEqual(r._lrc, base_lrc - 3 + 2) # -3 for dropping a b c, +2 for retaining b and c
    
    def test_intersection_update_removes_non_common_refs_2(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.b, r.c, r.f]   # {b, c, f}

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        s1 &= s2  # s1 becomes {b, c}, drops ref to a
        # s1 now holds 2 refs (b, c), s2 holds 3 refs (b, c, f)
        self.assertEqual(r._lrc, base_lrc - 3 + 2) # -3 for dropping a b c, +2 for retaining b and c

    def test_intersection_update_operator_matches_method(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]

        s1_method = set(r.arr1)
        s1_operator = set(r.arr1)
        s2 = set(r.arr2)

        s1_method.intersection_update(s2)
        s1_operator &= s2
        self.assertEqual(s1_method, s1_operator)
    
    def test_intersection_update_swap_bodies_different_region(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        original_lrc = r._lrc
        arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]
        self.assertEqual(r._lrc, original_lrc + 3) 

        s1 = set(arr1)
        r.s2 = set(r.arr2)
        self.assertEqual(r._lrc, original_lrc + 3 + 3) 
        base_lrc = r._lrc

        s1.intersection_update(r.s2)
        self.assertEqual(r._lrc, base_lrc - 3 + 2) # -3 for dropping a b c, +2 for retaining b and c

    def test_intersection_update_swap_bodies_different_region_2_intersection_update(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        original_lrc = r._lrc
        r.arr1 = [r.a, r.b, r.c]
        arr2 = [r.b, r.c, r.f]
        self.assertEqual(r._lrc, original_lrc + 3) 

        r.s1 = set(r.arr1)
        s2 = set(arr2)
        self.assertEqual(r._lrc, original_lrc + 3 + 3) 
        base_lrc = r._lrc

        r.s1.intersection_update(s2)
        self.assertEqual(r._lrc, base_lrc) # should not change since s1 is in the region. LRC should not be updated since s1 is in the region.

    @unittest.expectedFailure
    def test_intersection_update_swap_bodies_different_region_2_iand(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        original_lrc = r._lrc
        r.arr1 = [r.a, r.b, r.c]
        arr2 = [r.b, r.c, r.f]
        self.assertEqual(r._lrc, original_lrc + 3) 

        r.s1 = set(r.arr1)
        s2 = set(arr2)
        self.assertEqual(r._lrc, original_lrc + 3 + 3) 
        base_lrc = r._lrc

        r.s1 &= s2
        self.assertEqual(r._lrc, base_lrc) # should not change since s1 is in the region. LRC should not be updated since s1 is in the region.
    
    def test_intersection_update_multi_swap_bodies_different_region(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.d = self.A()
        r.e = self.A()
        r.f = self.A()
        original_lrc = r._lrc
        r.arr1 = [r.a, r.b, r.c]
        arr2 = [r.b, r.c, r.f]
        r.arr3 = [r.b, r.d, r.e]
        self.assertEqual(r._lrc, original_lrc + 3) 

        r.s1 = set(r.arr1)
        s2 = set(arr2)
        r.s3 = set(r.arr3)
        self.assertEqual(r._lrc, original_lrc + 3 + 3) 
        base_lrc = r._lrc

        r.s1.intersection_update(s2, r.s3)
        self.assertEqual(r._lrc, base_lrc) # should not change LRC since s1 is in the region. LRC should not be updated


class TestRegionSetUnion(unittest.TestCase):
    """Tests for set union operations and their effect on LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_union_result_is_local(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]

        s1 = set(r.arr1)
        s2 = set(r.arr2)

        result = s1 | s2
        self.assertTrue(is_local(result))

    def test_union_lrc_reflects_all_unique_elements(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.b, r.c, r.f]   # {b, c, f}

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        result = s1 | s2   # {a, b, c, f}
        self.assertEqual(r._lrc, base_lrc + 4)

        result = None
        self.assertEqual(r._lrc, base_lrc)

    def test_union_lrc_reflects_all_unique_elements_union(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.b, r.c, r.f]   # {b, c, f}

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        result = s1.union(s2)   # {a, b, c, f}
        self.assertEqual(r._lrc, base_lrc + 4)

        result = None
        self.assertEqual(r._lrc, base_lrc)

    def test_union_operator_matches_method(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]

        s1 = set(r.arr1)
        s2 = set(r.arr2)

        self.assertEqual(s1 | s2, s1.union(s2))


class TestRegionSetUnionUpdate(unittest.TestCase):
    """Tests for in-place union (|=) and LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_union_update_adds_new_refs(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.b, r.c, r.f]   # {b, c, f}

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        s1 |= s2   # s1 becomes {a, b, c, f}, gains ref to f
        self.assertEqual(r._lrc, base_lrc - 3 + 4) # -3 for original a b c, +4 for new a b c f (but a b c are still borrowed, so net +1 for f)
    
    def test_union_update_adds_new_refs_update(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.b, r.c, r.f]   # {b, c, f}

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        s1.update(s2)   # s1 becomes {a, b, c, f}, gains ref to f
        self.assertEqual(r._lrc, base_lrc - 3 + 4) # -3 for original a b c, +4 for new a b c f (but a b c are still borrowed, so net +1 for f)

    @unittest.expectedFailure
    def test_union_update_adds_new_refs_2(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.b, r.c, r.f]   # {b, c, f}

        r.s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        r.s1 |= s2 
        self.assertEqual(r._lrc, base_lrc)
    
    def test_union_update_adds_new_refs_2_update(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.b, r.c, r.f]   # {b, c, f}

        r.s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        r.s1.update(s2)
        self.assertEqual(r._lrc, base_lrc)

    def test_union_update_released_decreases_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.b, r.c, r.f]

        s2 = set(r.arr2)
        base_lrc = r._lrc

        s1 = set(r.arr1)
        s1 |= s2
        s1 = None
        # All s1 refs released, only s2's refs remain
        self.assertEqual(r._lrc, base_lrc)


class TestRegionSetDifferenceUpdate(unittest.TestCase):
    """Tests for in-place difference (-=) and LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_difference_update_removes_refs(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.a]              # {a}

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        s1 -= s2   # s1 becomes {b, c}, drops ref to a
        self.assertEqual(r._lrc, base_lrc - 3 + 2) # -3 for original a b c, +2 for remaining b and c

    def test_difference_update_removes_refs_difference_update(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.a]              # {a}

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        s1.difference_update(s2)   # s1 becomes {b, c}, drops ref to a
        self.assertEqual(r._lrc, base_lrc - 3 + 2) # -3 for original a b c, +2 for remaining b and c

    @unittest.expectedFailure
    def test_difference_update_removes_refs_2(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.a]              # {a}

        r.s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        r.s1 -= s2   # s1 becomes {b, c}, drops ref to a
        self.assertEqual(r._lrc, base_lrc) # -3 for original a b c, +2 for remaining b and c

    def test_difference_update_removes_refs_difference_2_update(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.a]              # {a}

        r.s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        r.s1.difference_update(s2)   # s1 becomes {b, c}, drops ref to a
        self.assertEqual(r._lrc, base_lrc) 

    def test_difference_update_result_released(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.a]

        s2 = set(r.arr2)
        base_lrc = r._lrc

        s1 = set(r.arr1)
        s1 -= s2
        s1 = None
        # Only s2's ref to a remains
        self.assertEqual(r._lrc, base_lrc)


class TestRegionSetSymmetricDifferenceUpdate(unittest.TestCase):
    """Tests for in-place symmetric difference (^= / symmetric_difference_update) and LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_symmetric_difference_update_adjusts_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c, r.f]   # {a, b, c, f}
        r.arr2 = [r.a, r.b, r.f]         # {a, b, f}

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        s1.symmetric_difference_update(s2)  # s1 becomes {c}
        self.assertEqual(r._lrc, base_lrc - 4 + 1) # -4 for original a b c f, +1 for remaining c

    def test_symmetric_difference_update_operator_matches_method(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.f = self.A()
        r.arr1 = [r.a, r.b, r.c, r.f]
        r.arr2 = [r.a, r.b, r.f]

        s1_method = set(r.arr1)
        s1_operator = set(r.arr1)
        s2 = set(r.arr2)

        s1_method.symmetric_difference_update(s2)
        s1_operator ^= s2
        self.assertEqual(s1_method, s1_operator)
    
    @unittest.expectedFailure
    def test_symmetric_difference_update_removes_refs_2(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.a]              # {a}

        r.s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        r.s1 ^= s2
        self.assertEqual(r._lrc, base_lrc)

    def test_symmetric_difference_update_removes_refs_difference_2_update(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]   # {a, b, c}
        r.arr2 = [r.a]              # {a}

        r.s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        r.s1.symmetric_difference_update(s2)
        self.assertEqual(r._lrc, base_lrc) 


class TestRegionSetSubsetSuperset(unittest.TestCase):
    """Tests for issubset / issuperset checks — these are read-only so LRC should not change."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_issubset_true(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a]
        r.arr2 = [r.a, r.b, r.c]

        s1 = set(r.arr1)
        s2 = set(r.arr2)

        self.assertTrue(s1.issubset(s2))

    def test_issubset_false(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a, r.b, r.c]
        r.arr2 = [r.a]

        s1 = set(r.arr1)
        s2 = set(r.arr2)

        self.assertFalse(s1.issubset(s2))

    def test_issubset_operator_matches_method(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a]
        r.arr2 = [r.a, r.b, r.c]

        s1 = set(r.arr1)
        s2 = set(r.arr2)

        self.assertEqual(s1.issubset(s2), s1 <= s2)

    def test_issubset_does_not_change_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a]
        r.arr2 = [r.a, r.b, r.c]

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        _ = s1.issubset(s2)
        self.assertEqual(r._lrc, base_lrc)

    def test_issuperset_true(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a]
        r.arr2 = [r.a, r.b, r.c]

        s1 = set(r.arr1)
        s2 = set(r.arr2)

        self.assertTrue(s2.issuperset(s1))

    def test_issuperset_false(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a]
        r.arr2 = [r.a, r.b, r.c]

        s1 = set(r.arr1)
        s2 = set(r.arr2)

        self.assertFalse(s1.issuperset(s2))

    def test_issuperset_strict_operator(self):
        r = Region()
        r.a = self.A()
        r.arr1 = [r.a]

        s1 = set(r.arr1)
        s2 = set(r.arr1)

        self.assertFalse(s2 > s1)

    def test_issuperset_does_not_change_lrc(self):
        r = Region()
        r.a = self.A()
        r.b = self.A()
        r.c = self.A()
        r.arr1 = [r.a]
        r.arr2 = [r.a, r.b, r.c]

        s1 = set(r.arr1)
        s2 = set(r.arr2)
        base_lrc = r._lrc

        _ = s2.issuperset(s1)
        self.assertEqual(r._lrc, base_lrc)


class TestRegionSetIterator(unittest.TestCase):
    """Tests for set iterator behavior and its effect on LRC."""

    def setUp(self):
        class A: pass
        freeze(A())
        self.A = A

    def test_iter_creation_does_not_change_lrc(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.arr = [r.word, r.word2]

        s = set(r.arr)
        base_lrc = r._lrc

        it = iter(s)
        self.assertEqual(r._lrc, base_lrc)

    def test_iter_creation_does_not_change_lrc_2(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.arr = [r.word, r.word2]

        s = set(r.arr)
        base_lrc = r._lrc

        r.it = iter(s)
        self.assertEqual(r._lrc, base_lrc-1)

    def test_iter_creation_does_not_change_lrc_3(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.arr = [r.word, r.word2]

        r.s = set(r.arr)
        base_lrc = r._lrc

        r.it = iter(r.s)
        self.assertEqual(r._lrc, base_lrc)

    def test_iter_creation_does_not_change_lrc_4(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.arr = [r.word, r.word2]

        r.s = set(r.arr)
        base_lrc = r._lrc

        it = iter(r.s) # iterator object points to the object in the region.
        self.assertEqual(r._lrc, base_lrc+1)

    def test_next_on_iter_increases_lrc(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.word3 = self.A()
        r.word4 = self.A()
        r.arr = [r.word, r.word2, r.word3, r.word4]

        s = set(r.arr)
        it = iter(s)
        base_lrc = r._lrc

        a1 = next(it)
        self.assertEqual(r._lrc, base_lrc + 1)

        a2 = next(it)
        self.assertEqual(r._lrc, base_lrc + 2)

        r.a3 = next(it)
        self.assertEqual(r._lrc, base_lrc + 2)

        a4 = next(it)
        self.assertEqual(r._lrc, base_lrc + 3)

    def test_next_on_iter_increases_lrc_2(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.word3 = self.A()
        r.word4 = self.A()
        r.arr = [r.word, r.word2, r.word3, r.word4]

        s = set(r.arr)
        r.it = iter(s)
        base_lrc = r._lrc

        r.a1 = next(r.it)
        self.assertEqual(r._lrc, base_lrc)

        r.a2 = next(r.it)
        self.assertEqual(r._lrc, base_lrc)

        r.a3 = next(r.it)
        self.assertEqual(r._lrc, base_lrc)

        r.a4 = next(r.it)
        self.assertEqual(r._lrc, base_lrc)

    def test_iter_to_none_releases_lrc(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.arr = [r.word, r.word2]

        s = set(r.arr)
        it = iter(s)
        base_lrc = r._lrc

        it = None
        self.assertEqual(r._lrc, base_lrc)

    def test_next_into_region_transfers_ownership(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.word3 = self.A()
        r.arr = [r.word, r.word2, r.word3]

        s = set(r.arr)
        it = iter(s)
        base_lrc = r._lrc

        a1 = next(it)   # external local ref, LRC + 1
        r.a3 = next(it) # moved into region, no external borrow
        self.assertEqual(r._lrc, base_lrc + 1)
    
    def test_iterator(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.arr = [r.word, r.word2]
        s = set(r.arr)
        base_lrc = r._lrc

        it0 = iter(s)
        self.assertEqual(r._lrc, base_lrc)
        r.it = iter(s)
        self.assertEqual(r._lrc, base_lrc-1+1) # s is moved into the region, but now it0 points to iterator that is moved into the region.
        it2 = iter(s)
        self.assertEqual(r._lrc, base_lrc+1) 

    def test_iterator2(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.arr = [r.word, r.word2]
        r.s = set(r.arr)
        base_lrc = r._lrc

        it = iter(r.s)
        self.assertEqual(r._lrc, base_lrc+1) # r.s is moved into the region.
        it2 = iter(r.s)
        self.assertEqual(r._lrc, base_lrc+2) 
        r.it3 = iter(r.s)
        self.assertEqual(r._lrc, base_lrc+2)

    def test_iterator_on_iterator(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.arr = [r.word, r.word2]
        s = set(r.arr)
        base_lrc = r._lrc

        r.it0 = iter(s)
        self.assertEqual(r._lrc, base_lrc-1)
        r.it = iter(r.it0)
        self.assertEqual(r._lrc, base_lrc-1)
        it2 = iter(r.it0)
        self.assertEqual(r._lrc, base_lrc-1+1)

    def test_iterator_on_iterator_2(self):
        r = Region()
        r.word = self.A()
        r.word2 = self.A()
        r.arr = [r.word, r.word2]
        r.s = set(r.arr)
        base_lrc = r._lrc

        r.it0 = iter(r.s)
        self.assertEqual(r._lrc, base_lrc)
        r.it = iter(r.it0)
        self.assertEqual(r._lrc, base_lrc)
        it2 = iter(r.it0)
        self.assertEqual(r._lrc, base_lrc+1)


if __name__ == "__main__":
    unittest.main()