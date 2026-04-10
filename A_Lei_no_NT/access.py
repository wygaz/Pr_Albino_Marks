from functools import wraps
from urllib.parse import quote

from django.contrib.auth.models import Group
from django.shortcuts import redirect

from .models import AcessoUsuario


GRUPO_USUARIOS_HABILITADOS = "usuarios_habilitados_sermoes"


def get_or_create_acesso_usuario(user):
    acesso, _ = AcessoUsuario.objects.get_or_create(user=user)
    return acesso


def sincronizar_grupo_habilitado(user):
    acesso = get_or_create_acesso_usuario(user)
    grupo, _ = Group.objects.get_or_create(name=GRUPO_USUARIOS_HABILITADOS)
    if acesso.acesso_liberado:
        user.groups.add(grupo)
    else:
        user.groups.remove(grupo)
    return acesso


def usuario_habilitado(user):
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return True
    acesso = get_or_create_acesso_usuario(user)
    return acesso.acesso_liberado


def usuario_habilitado_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/conta/entrar/?next={quote(request.get_full_path())}")
        if usuario_habilitado(request.user):
            return view_func(request, *args, **kwargs)
        return redirect(f"/conta/aceite/?next={quote(request.get_full_path())}")

    return _wrapped
