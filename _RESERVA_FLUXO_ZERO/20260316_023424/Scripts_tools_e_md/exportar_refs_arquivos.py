import csv
from django.apps import apps
from django.db.models import FileField, ImageField

saida = "referencias_arquivos_site.csv"

with open(saida, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["app", "model", "pk", "field", "path"])

    for model in apps.get_models():
        file_fields = [
            field for field in model._meta.get_fields()
            if isinstance(field, (FileField, ImageField))
        ]
        if not file_fields:
            continue

        for obj in model.objects.all().iterator():
            for field in file_fields:
                try:
                    valor = getattr(obj, field.name)
                    nome = getattr(valor, "name", "") or ""
                except Exception:
                    nome = ""

                if nome:
                    w.writerow([
                        model._meta.app_label,
                        model.__name__,
                        obj.pk,
                        field.name,
                        nome,
                    ])

print(f"OK: arquivo gerado -> {saida}")