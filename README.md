# Django Materialized Paths

A simple and lightweight implementation of materialized path tree structures in Django.  

## Installation

To install, run:

```
pip install django-materialized-paths
```

## Configuration

Add the following into the INSTALLED_APPS of your projects: 

```python
INSTALLED_APPS = (
 ...
 'django-materialized-paths',
)
```

## Usage

To use, extend the `BaseNode` into your model:

```python
from django-materialized-paths import BaseNode

class FolderExample(BaseNode):
    """My folder class"""
    name = models.CharField(max_length=48)
```

The model overrides Django's `django.db.models.Model` save() method to automatically manage changes to inheritance: 

```python
from .models import FolderExample # concrete class from above

root = FolderExample.objects.create(name="root")
child = FolderExample.objects.create(name="child", parent=root)
grandchild = FolderExample.objects.create(name="child", parent=child)
```

For example, to convert `grandchild` to a root:

```python
grandchild.parent = None
grandchild.save()
```

### Usage - Properties and Inherited 

```python
BaseNode.depth # Root is 0
BaseNode.parent
BaseNode.children # Only returns direct descendants

BaseNode.save() # Set the parent field to automatically manage hierarchy
BaseNode.delete() # NOTE: The BaseNode.parent field is set to cascade, so deleting a parent will delete all children 
```

### Usage - Methods 

Note that these methods generally return querysets 

```python
# Accessors

BaseNode.get_root()
BaseNode.get_ancestor(depth=int)
BaseNode.get_ancestors() 
BaseNode.get_descendants() 
BaseNode.get_siblings() 

# Convenience

BaseNode.has_children()
BaseNode.is_child_of(parent_id=int)

# ID-based accessors - computed directly from path without accessing db

BaseNode.get_ancestors_ids()
BaseNode.get_descendants_ids()
```

## Authors

* **Cameron McNierney** - *Original author* - https://github.com/cmcnierney

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
