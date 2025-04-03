from django.contrib import admin
from .models import Document, Chapter, Sentence

# Register your models here.
admin.site.register(Document)
admin.site.register(Chapter)
admin.site.register(Sentence)