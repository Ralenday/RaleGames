# games/api.py
# Web services propios de RaleGames (Django REST Framework)

from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from . import services
from .serializers import EntradaSerializer


class BitacoraViewSet(viewsets.ModelViewSet):
    """CRUD de la bitácora. Requiere token JWT (o sesión iniciada) y cada
    usuario solo ve y modifica sus propias entradas."""
    serializer_class = EntradaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.entradas.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_buscar(request):
    """Proxy hacia RAWG: el navegador nunca ve la llave de la API."""
    texto = request.GET.get('q', '').strip()[:100]
    try:
        return Response(services.buscar_juegos(texto))
    except services.RawgError:
        return Response({'detail': 'RAWG no está disponible'}, status=503)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_ruleta(request):
    animo = request.GET.get('animo', '')
    if animo not in services.ANIMOS:
        return Response({'detail': 'Ánimo no válido', 'opciones': list(services.ANIMOS)}, status=400)
    try:
        juego = services.girar_ruleta(animo, request.GET.get('tiempo', 'cualquiera'))
    except services.RawgError:
        return Response({'detail': 'RAWG no está disponible'}, status=503)
    if juego is None:
        return Response({'detail': 'No encontramos juegos con ese filtro'}, status=404)
    return Response(juego)
