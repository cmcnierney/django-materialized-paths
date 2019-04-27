from django.test import TestCase
from paths.utils import base36encode


class TestUtils(TestCase):

    def test_base36encode(self):
        with self.assertRaises(TypeError):
            base36encode("string")

        with self.assertRaises(ValueError):
            base36encode(-1)
