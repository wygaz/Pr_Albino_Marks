from django.contrib import messages

def informar_titulo_ajustado(request, titulo):
    messages.info(request, f"Título ajustado automaticamente para: “{titulo}”.")

def sucesso_artigo_salvo(request):
    messages.success(request, "✅ Artigo salvo com sucesso.")

def aviso_artigo_oculto(request):
    messages.warning(request, "⚠️ Este artigo está com visibilidade desativada. Ele não será exibido ao público no site.")

def erro_slug_duplicado(request):
    messages.error(request, "❌ Já existe um artigo com o mesmo slug. Revise o título ou conteúdo.")

def debug_salvamento(request, info_extra):
    messages.debug(request, f"[DEBUG] {info_extra}")
