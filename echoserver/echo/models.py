from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    publication_year = models.IntegerField()
    genre = models.CharField(max_length=100)

    def Meta(self):
        db_table = "Books"
