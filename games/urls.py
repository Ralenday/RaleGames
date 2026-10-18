from django.contrib.auth import views as auth_views
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api, views

router = DefaultRouter()
router.register('bitacora', api.BitacoraViewSet, basename='api-bitacora')

urlpatterns = [
    # Pantallas
    path('', views.inicio, name='inicio'),
    path('registro/', views.registro, name='registro'),
    path('entrar/', auth_views.LoginView.as_view(template_name='games/login.html',
                                                 redirect_authenticated_user=True), name='login'),
    path('salir/', auth_views.LogoutView.as_view(), name='logout'),
    path('explorar/', views.explorar, name='explorar'),
    path('juego/<int:juego_id>/', views.juego_detalle, name='juego'),
    path('juego/<int:juego_id>/agregar/', views.agregar_a_bitacora, name='agregar'),
    path('ruleta/', views.ruleta, name='ruleta'),
    path('bitacora/', views.bitacora, name='bitacora'),
    path('bitacora/<int:pk>/actualizar/', views.actualizar_entrada, name='actualizar'),
    path('bitacora/<int:pk>/eliminar/', views.eliminar_entrada, name='eliminar'),

    # Web services (API REST)
    path('api/juegos/', api.api_buscar, name='api-buscar'),
    path('api/ruleta/', api.api_ruleta, name='api-ruleta'),
    path('api/', include(router.urls)),
]
