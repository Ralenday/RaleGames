from . import services


def modo_demo(request):
    # Disponible en todas las plantillas para mostrar el aviso de modo demo
    return {'modo_demo': services.modo_demo()}
