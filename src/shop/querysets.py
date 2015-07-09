from django.db import models


class ProductQuerySet(models.QuerySet):
    def active(self):
        return self.filter(active=True)
