from django.db import models
from django.db.models import F, Func, Value
from django.core.exceptions import ValidationError
from paths.utils import base36decode, base36encode, xstr


class BaseNode(models.Model):
    """Abstract class for implementing a simple materialized path hierarchy."""

    path = models.CharField(
        max_length=255, db_index=True, null=True, blank=True)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, related_name="children", null=True, blank=True)

    _original_parent_id = None  # The parent_id when instantiated

    class Meta:
        abstract = True

    @property
    def depth(self):
        """
        :return: The depth of self in the tree starting with root at 0.
        """

        if not self.path:
            return 0

        ids = self.decode_path_to_ids(self.path)
        return len(ids)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_parent_id = self.parent_id

    @classmethod
    def encode_base36_id(cls, num):
        """
        Encodes an id to the format <length of encoded value><encoded value>.

        :param num: An integer value representing the object's id
        :return: An encoded string
        """
        num = base36encode(num)
        return str(len(num)) + num

    @classmethod
    def decode_base36_id(cls, base36_id):
        """
        Decodes a string from the format <length of encoded value><encoded value>.

        :param base36_id: A string value in the format <length of encoded value><encoded value>
        :return: An int
        """
        return base36decode(base36_id)

    @classmethod
    def decode_path_to_ids(cls, path):
        """
        Decodes a full 'path' into an ordered list of ids using decode_base36_id.

        :param path: A string path of concatenated values from encode_base36_id
        :return: A list of ordered int ids
        """
        cursor = 1
        ids = []

        if not path:
            return ids

        while cursor < len(path):
            b36len = int(path[cursor - 1])
            b36str = path[cursor:cursor + b36len]
            ids.append(cls.decode_base36_id(b36str))
            cursor = cursor + b36len + 1

        return ids

    @classmethod
    def encode_ids_to_path(cls, ids):
        """
        Encodes a list of ordered ids into a full 'path' using encode_base36_id.

        :param ids: A list of ordered int ids
        :return: A string path of concatenated values from encode_base36_id
        """
        path = ''
        for id_ in ids:
            path = path + cls.encode_base36_id(id_)

        return path

    def get_ancestors_ids(self, include_self=False):
        """
        :return: A list of ordered int ids or empty list
        """

        if not self.path and not include_self:
            return []

        ids = self.decode_path_to_ids(self.path)

        if include_self:
            ids.append(self.id)

        return ids

    def get_ancestors(self):
        """
        :return: A queryset containing all ancestors not including self or None
        """
        ids = self.get_ancestors_ids()

        if not ids:
            return None

        return self.__class__.objects.filter(pk__in=ids).all()

    def get_ancestor(self, depth: int = 0):
        """
        Fetches the ancestor at a specific depth.

        :param depth: An int with root depth starting at 0. Defaults to 0 (root)
        :return: The queryset containing the ancestor. Returns self if :depth equals self depth
        :raise: ValueError: If :depth is less than 0 or greater than self depth
        """
        if depth < 0:
            raise ValueError(f"The minimum depth is 0 - {depth} given.")

        if depth is 0:
            return self.get_root()

        self_depth = self.depth
        if self_depth is depth:
            return self

        if self_depth < depth:
            raise ValueError(
                'Cannot find ancestor at depth greater than or equal to self depth.')

        ids = self.decode_path_to_ids(self.path)
        return self.__class__.objects.get(pk=ids[depth])

    def get_descendants_search_partial(self):
        return xstr(self.path) + self.encode_base36_id(self.id)

    def get_descendants(self):
        """
        Fetches all descendants not including self.

        :return: A queryset of descendants
        """
        search_partial = self.get_descendants_search_partial()
        return self.__class__.objects.filter(path__startswith=search_partial).all()

    def get_descendants_ids(self):
        """
        :return: A list of ordered int ids or empty list
        """
        search_partial = self.get_descendants_search_partial()
        descendants = self.__class__.objects.filter(
            path__startswith=search_partial).values_list('id', flat=True).all()
        return list(descendants)

    def get_root(self):
        """
        Fetches the root ancestor.

        :return: A queryset containing the root ancestor or self (if self is root)
        """

        if not self.path:
            return self

        root_id = self.decode_path_to_ids(self.path)[0]
        return self.__class__.objects.get(id=root_id)

    def get_siblings(self):
        """
        Fetches all objects with the same parent object. Will also return all root objects if self is a root.

        :return: A queryset containing all siblings or None (if no siblings exist)
        """

        if not self.parent_id:
            return self.__class__.objects.filter(parent_id=None).exclude(pk=self.id).all()

        results = self.__class__.objects.filter(
            parent_id=self.parent_id).exclude(pk=self.id).all()
        if results:
            return results
        else:
            return None

    def is_child_of(self, ancestor_id):
        """
        Determines if self contains a specific ancestor.

        :param ancestor_id: An int value for the ancestor
        :return: ``True`` if self is descendant of ancestor, else ``False``
        """

        if not self.path:
            return False

        ids = self.decode_path_to_ids(self.path)
        if ancestor_id in ids:
            return True

        return False

    def has_children(self):
        """
        Determines if self has children/descendants.

        :return: ``True`` if self has descendants, else ``False``
        """
        if self.children.exists():
            return True

        return False

    def save(self, *args, **kwargs):

        if self._state.adding is True:
            if not getattr(self, 'parent', None):
                self.path = None
            elif getattr(self.parent, 'path', None):
                self.path = self.parent.path + \
                    self.encode_base36_id(self.parent.id)
            else:
                self.path = self.encode_base36_id(self.parent.id)

        elif self._original_parent_id != self.parent_id:

            b36str = self.encode_base36_id(self.id)
            search_partial = xstr(self.path) + b36str
            remove_partial = xstr(self.path)

            if self.parent_id:

                self.path = xstr(self.parent.path) + \
                    self.encode_base36_id(self.parent_id)

                # Do not allow your parent to be your child
                parent_ids = self.decode_path_to_ids(self.path)
                if self.id in parent_ids:
                    raise ValidationError(
                        "A node's parent cannot also be its child.")
            else:
                self.path = None

            self.__class__.objects.filter(path__startswith=search_partial).update(
                path=Func(
                    F('path'),
                    Value(remove_partial), Value(self.path),
                    function='replace',
                )
            )

        super().save(*args, **kwargs)
