from django.db import models
from paths.models import BaseNode

class Folder(BaseNode):
    name = models.CharField(max_length=255)
