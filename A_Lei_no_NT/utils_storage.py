from typing import Union
from urllib.parse import urlparse
from django.core.files.storage import default_storage
from django.core.files.base import File
from django.db.models.fields.files import FieldFile

def is_url(s: str) -> bool:
    try:
        p = urlparse(s)
        return p.scheme in ("http", "https")
    except Exception:
        return False

def get_file_url(obj: Union[FieldFile, str]) -> str:
    """
    Retorna URL pública do arquivo:
      - FieldFile => .url
      - string com caminho relativo no storage => default_storage.url(name)
      - string já http(s) => devolve como está
    """
    if isinstance(obj, FieldFile):
        return obj.url
    if isinstance(obj, str):
        if is_url(obj):
            return obj
        return default_storage.url(obj)  # 'name' no storage
    raise TypeError("get_file_url: parâmetro inválido.")

def open_file(obj: Union[FieldFile, str], mode: str = "rb") -> File:
    """
    Abre o arquivo de forma storage-agnostic:
      - FieldFile => default_storage.open(field.name)
      - string => default_storage.open(name)
    """
    if isinstance(obj, FieldFile):
        return default_storage.open(obj.name, mode)
    if isinstance(obj, str):
        return default_storage.open(obj, mode)
    raise TypeError("open_file: parâmetro inválido.")
