from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import Folder


class TestBaseNode(TestCase):

    @classmethod
    def create_subtree_with_x_levels(cls, x: int):

        nodes = []
        parent_node = None

        for i in range(x):
            node = Folder.objects.create(parent=parent_node)
            nodes.append(node)
            parent_node = node

        return nodes

    @classmethod
    def reset_parent_to(cls, instance, parent):
        instance.parent = parent
        instance.save()
        instance.refresh_from_db()

    def test_created_as_root(self):
        root = Folder.objects.create()

        self.assertIsNone(root.path)
        self.assertIsNone(root.parent)

    def test_decode_path_to_ids_with_null_path(self):
        self.assertListEqual([], Folder.decode_path_to_ids(None))

    def test_created_as_leaf(self):
        root, leaf = self.create_subtree_with_x_levels(2)

        expected_parent_id = root.id
        expected_path = Folder.encode_ids_to_path([root.id])
        self.assertEquals(expected_parent_id, leaf.parent_id)
        self.assertEquals(expected_path, leaf.path)

    def test_delete_cascades(self):
        root, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)

        sub_node_a_id = sub_node_a.id
        sub_node_aa_id = sub_node_aa.id

        sub_node_a.delete()
        self.assertTrue(Folder.objects.filter(pk=root.id).exists())
        self.assertFalse(Folder.objects.filter(pk=sub_node_a_id).exists())
        self.assertFalse(Folder.objects.filter(pk=sub_node_aa_id).exists())

    def test_move_leaf_to_root(self):
        root, sub_node_a = self.create_subtree_with_x_levels(2)

        expected_path = Folder.encode_ids_to_path([root.id])
        self.assertEquals(expected_path, sub_node_a.path)
        self.reset_parent_to(sub_node_a, None)

        self.assertIsNone(sub_node_a.path)

    def test_move_leaf_to_leaf(self):
        root, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)
        self.reset_parent_to(sub_node_aa, root)

        expected_parent_id = root.id
        expected_path = Folder.encode_ids_to_path([root.id])
        self.assertEquals(expected_parent_id, sub_node_aa.parent_id)
        self.assertEquals(expected_path, sub_node_aa.path)

    def test_move_root_to_leaf(self):
        root_a, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)
        root_b, sub_node_b, sub_node_bb = self.create_subtree_with_x_levels(3)
        self.reset_parent_to(root_a, sub_node_bb)

        expected_parent_id = sub_node_bb.id
        expected_path = Folder.encode_ids_to_path([root_b.id, sub_node_b.id, sub_node_bb.id])
        self.assertEquals(expected_parent_id, root_a.parent_id)
        self.assertEquals(expected_path, root_a.path)

    def test_move_root_to_subtree(self):
        root_a, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)
        root_b, sub_node_b, sub_node_bb = self.create_subtree_with_x_levels(3)
        self.reset_parent_to(root_a, sub_node_b)

        expected_parent_id = sub_node_b.id
        expected_path = Folder.encode_ids_to_path([root_b.id, sub_node_b.id])
        self.assertEquals(expected_parent_id, root_a.parent_id)
        self.assertEquals(expected_path, root_a.path)

    def test_move_root_to_own_subtree_should_error(self):
        root_a, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)

        root_a.parent = sub_node_a
        with self.assertRaises(ValidationError):
            root_a.save()

    def test_move_subtree_to_subtree(self):
        root_a, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)
        root_b, sub_node_b, sub_node_bb = self.create_subtree_with_x_levels(3)
        self.reset_parent_to(sub_node_a, sub_node_b)

        expected_parent_id = sub_node_b.id
        expected_path = Folder.encode_ids_to_path([root_b.id, sub_node_b.id])
        self.assertEquals(expected_parent_id, sub_node_a.parent_id)
        self.assertEquals(expected_path, sub_node_a.path)

    def test_get_ancestors_ids(self):
        root_a, sub_node_a, sub_node_aa, sub_node_aaa = self.create_subtree_with_x_levels(4)
        expected_list = [root_a.id, sub_node_a.id, sub_node_aa.id]
        self.assertListEqual([], root_a.get_ancestors_ids())
        self.assertListEqual(expected_list, sub_node_aaa.get_ancestors_ids())
        expected_list.append(sub_node_aaa.id)
        self.assertListEqual(expected_list, sub_node_aaa.get_ancestors_ids(include_self=True))

    def test_get_descendants_ids(self):
        root_a, sub_node_a, sub_node_aa, sub_node_aaa = self.create_subtree_with_x_levels(4)
        expected_list = [sub_node_a.id, sub_node_aa.id, sub_node_aaa.id]
        self.assertListEqual([], sub_node_aaa.get_descendants_ids())
        self.assertListEqual(expected_list, root_a.get_descendants_ids())

    def test_get_ancestors(self):
        root_a, sub_node_a, sub_node_aa, sub_node_aaa = self.create_subtree_with_x_levels(4)
        expected_list = [root_a, sub_node_a, sub_node_aa]
        self.assertIsNone(root_a.get_ancestors())
        self.assertListEqual(expected_list, list(sub_node_aaa.get_ancestors()))

    def test_get_descendants(self):
        root_a, sub_node_a, sub_node_aa, sub_node_aaa = self.create_subtree_with_x_levels(4)
        expected_list = [sub_node_a, sub_node_aa, sub_node_aaa]
        self.assertListEqual(expected_list, list(root_a.get_descendants()))

    def test_get_root_if_self(self):
        root_a, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)
        expected_root = root_a
        self.assertEqual(expected_root, root_a.get_root())

    def test_get_root_if_not_self(self):
        root_a, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)
        expected_root = root_a
        self.assertEqual(expected_root, sub_node_aa.get_root())

    def test_get_siblings_if_none_exist(self):
        root_a, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)
        self.assertIsNone(sub_node_a.get_siblings())

    def test_get_siblings_if_exist(self):
        root_a, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)
        sub_node_b = Folder.objects.create(parent=root_a)
        sub_node_c = Folder.objects.create(parent=root_a)

        expected_list = [sub_node_b, sub_node_c]
        self.assertListEqual(expected_list, list(sub_node_a.get_siblings()))

    def test_get_siblings_if_root(self):
        root_a, sub_node_a = self.create_subtree_with_x_levels(2)
        root_b, sub_node_b = self.create_subtree_with_x_levels(2)
        root_c, sub_node_c = self.create_subtree_with_x_levels(2)

        expected_list = [root_b, root_c]
        self.assertListEqual(expected_list, list(root_a.get_siblings()))

    def test_get_depth(self):
        root_a, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)
        self.assertEqual(0, root_a.depth)
        self.assertEqual(1, sub_node_a.depth)
        self.assertEqual(2, sub_node_aa.depth)

    def test_get_ancestor(self):
        root_a, sub_a, sub_aa, sub_aaa, sub_aaaa = self.create_subtree_with_x_levels(5)

        self.assertRaises(ValueError, sub_aaa.get_ancestor, depth=-1)
        self.assertRaises(ValueError, sub_aaa.get_ancestor, depth=4)

        self.assertEqual(root_a, root_a.get_ancestor())
        self.assertEqual(root_a, sub_aaaa.get_ancestor())
        self.assertEqual(sub_a, sub_aaaa.get_ancestor(1))
        self.assertEqual(sub_aaaa, sub_aaaa.get_ancestor(4))

    def test_is_child_of(self):
        root_a, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)

        self.assertFalse(root_a.is_child_of(sub_node_a))
        self.assertFalse(sub_node_a.is_child_of(sub_node_a.id))
        self.assertTrue(sub_node_aa.is_child_of(root_a.id))

    def test_has_children(self):
        root_a, sub_node_a, sub_node_aa = self.create_subtree_with_x_levels(3)

        self.assertTrue(root_a.has_children())
        self.assertTrue(sub_node_a.has_children())
        self.assertFalse(sub_node_aa.has_children())
