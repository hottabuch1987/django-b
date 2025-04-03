from django.db import models

class Document(models.Model):
    name = models.CharField("Название документа", max_length=255, null=True, blank=True)
    file = models.FileField("Файл", upload_to='documents/%Y/%m/%d/', null=True, blank=True)

    def __str__(self):
        return f"Документ {self.name}"
    class Meta:
        verbose_name = "Документ"
        verbose_name_plural = "Документы"
        ordering = ['name']

class Chapter(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chapters', verbose_name="Глава")
    number = models.IntegerField("Номер главы", blank=True, null=True)

    def __str__(self):
        return f"Глава {self.number}"
    class Meta:
        verbose_name = "Глава"
        verbose_name_plural = "Главы"
        ordering = ['number']

class Sentence(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='sentences', verbose_name="Параграф")
    number = models.IntegerField("Номер параграфа", blank=True, null=True)
    text = models.TextField("Текст", blank=True, null=True)

    def __str__(self):
        return f"Параграф {self.number}"
    class Meta:
        verbose_name = "Параграф"
        verbose_name_plural = "Параграфы"
        ordering = ['number']

