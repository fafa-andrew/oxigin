from django.db import models


class Feed(models.Model):
    name = models.CharField(max_length=255)
    rss_url = models.URLField(unique=True)
    is_active = models.BooleanField(default=False)
    last_fetched_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
