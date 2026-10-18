from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from . import services
from .models import Entrada, Perfil


def datos_registro(**cambios):
    datos = {
        'username': 'axel_gamer',
        'email': 'axel@ejemplo.com',
        'plataforma': 'pc',
        'password1': 'Contrasena2026!',
        'password2': 'Contrasena2026!',
        'terminos': 'on',
    }
    datos.update(cambios)
    return datos


# Todas las pruebas usan el modo demo: no dependen de internet ni de la llave
@override_settings(RAWG_API_KEY='')
class PantallasTests(TestCase):
    def test_inicio_muestra_juegos(self):
        respuesta = self.client.get(reverse('inicio'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Juego del día')
        self.assertContains(respuesta, 'Modo demo')

    def test_explorar_busca_por_nombre(self):
        respuesta = self.client.get(reverse('explorar'), {'q': 'hollow'})
        self.assertContains(respuesta, 'Hollow Knight')
        self.assertNotContains(respuesta, 'Stardew Valley')

    def test_explorar_filtra_por_genero(self):
        respuesta = self.client.get(reverse('explorar'), {'genero': 'strategy'})
        self.assertContains(respuesta, 'Into the Breach')
        self.assertNotContains(respuesta, 'Celeste')

    def test_detalle_de_juego(self):
        respuesta = self.client.get(reverse('juego', args=[3]))
        self.assertContains(respuesta, 'The Witcher 3')

    def test_juego_inexistente_da_404(self):
        self.assertEqual(self.client.get(reverse('juego', args=[999])).status_code, 404)

    def test_bitacora_requiere_sesion(self):
        respuesta = self.client.get(reverse('bitacora'))
        self.assertRedirects(respuesta, f"{reverse('login')}?next={reverse('bitacora')}")


@override_settings(RAWG_API_KEY='')
class RegistroTests(TestCase):
    def test_registro_correcto_crea_usuario_y_perfil(self):
        respuesta = self.client.post(reverse('registro'), datos_registro())
        self.assertRedirects(respuesta, reverse('bitacora'))
        user = User.objects.get(username='axel_gamer')
        self.assertEqual(user.perfil.plataforma, 'pc')
        # La contraseña se guarda cifrada, nunca en texto plano
        self.assertNotEqual(user.password, 'Contrasena2026!')
        self.assertTrue(user.check_password('Contrasena2026!'))

    def test_gamertag_con_caracteres_invalidos(self):
        respuesta = self.client.post(reverse('registro'), datos_registro(username='axel ramirez!'))
        self.assertContains(respuesta, 'letras, números o guion bajo')
        self.assertFalse(User.objects.exists())

    def test_correo_repetido(self):
        User.objects.create_user('otro', 'axel@ejemplo.com', 'Contrasena2026!')
        respuesta = self.client.post(reverse('registro'), datos_registro(email='AXEL@ejemplo.com'))
        self.assertContains(respuesta, 'Ya existe una cuenta con ese correo')

    def test_contrasenas_distintas(self):
        respuesta = self.client.post(reverse('registro'), datos_registro(password2='OtraCosa2026!'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_contrasena_debil(self):
        respuesta = self.client.post(reverse('registro'), datos_registro(password1='12345678', password2='12345678'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(User.objects.exists())

    def test_debe_aceptar_terminos(self):
        datos = datos_registro()
        del datos['terminos']
        respuesta = self.client.post(reverse('registro'), datos)
        self.assertContains(respuesta, 'Debes aceptar')


@override_settings(RAWG_API_KEY='')
class BitacoraTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('axel', 'a@ejemplo.com', 'Contrasena2026!')
        Perfil.objects.create(user=self.user, plataforma='pc')
        self.client.force_login(self.user)

    def test_agregar_juego_toma_datos_de_la_api(self):
        self.client.post(reverse('agregar', args=[2]), {'estado': 'jugando', 'titulo': 'Nombre falso'})
        entrada = Entrada.objects.get(user=self.user)
        self.assertEqual(entrada.titulo, 'Stardew Valley')
        self.assertEqual(entrada.estado, 'jugando')

    def test_no_se_duplica_un_juego(self):
        self.client.post(reverse('agregar', args=[2]))
        self.client.post(reverse('agregar', args=[2]))
        self.assertEqual(Entrada.objects.count(), 1)

    def test_agregar_solo_por_post(self):
        self.assertEqual(self.client.get(reverse('agregar', args=[2])).status_code, 405)

    def test_actualizar_entrada(self):
        entrada = Entrada.objects.create(user=self.user, rawg_id=1, titulo='Hollow Knight')
        self.client.post(reverse('actualizar', args=[entrada.pk]),
                         {f'e{entrada.pk}-estado': 'terminado', f'e{entrada.pk}-calificacion': 5, f'e{entrada.pk}-nota': 'GOTY'})
        entrada.refresh_from_db()
        self.assertEqual((entrada.estado, entrada.calificacion), ('terminado', 5))

    def test_no_puede_tocar_bitacora_ajena(self):
        otro = User.objects.create_user('intruso', 'i@ejemplo.com', 'Contrasena2026!')
        ajena = Entrada.objects.create(user=otro, rawg_id=1, titulo='Hollow Knight')
        self.assertEqual(self.client.post(reverse('eliminar', args=[ajena.pk])).status_code, 404)
        self.assertTrue(Entrada.objects.filter(pk=ajena.pk).exists())

    def test_bitacora_muestra_resumen(self):
        Entrada.objects.create(user=self.user, rawg_id=1, titulo='Hollow Knight', estado='terminado', horas_estimadas=30)
        respuesta = self.client.get(reverse('bitacora'))
        self.assertContains(respuesta, 'Hollow Knight')
        self.assertEqual(respuesta.context['horas'], 30)


@override_settings(RAWG_API_KEY='')
class RuletaTests(TestCase):
    def test_cada_animo_devuelve_un_juego_que_coincide(self):
        for clave, animo in services.ANIMOS.items():
            juego = services.girar_ruleta(clave)
            self.assertIsNotNone(juego, clave)
            original = next(j for j in services.JUEGOS_DEMO if j['id'] == juego['id'])
            self.assertTrue(animo.coincide(original), clave)

    def test_filtro_de_tiempo(self):
        for _ in range(10):
            juego = services.girar_ruleta('historia', 'corto')
            self.assertLessEqual(juego['horas'], 10)

    def test_animo_invalido(self):
        self.assertIsNone(services.girar_ruleta('hackear'))


@override_settings(RAWG_API_KEY='')
class ApiTests(TestCase):
    def setUp(self):
        cache.clear()  # reinicia los contadores de throttling
        self.api = APIClient()
        self.user = User.objects.create_user('axel', 'a@ejemplo.com', 'Contrasena2026!')

    def token(self):
        respuesta = self.api.post(reverse('token_obtain_pair'), {'username': 'axel', 'password': 'Contrasena2026!'})
        return respuesta.data['access']

    def test_bitacora_sin_token_da_401(self):
        self.assertEqual(self.api.get('/api/bitacora/').status_code, 401)

    def test_crud_bitacora_con_jwt(self):
        self.api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token()}')
        creada = self.api.post('/api/bitacora/', {'rawg_id': 5, 'titulo': 'Hades', 'estado': 'jugando'})
        self.assertEqual(creada.status_code, 201)
        repetida = self.api.post('/api/bitacora/', {'rawg_id': 5, 'titulo': 'Hades'})
        self.assertEqual(repetida.status_code, 400)
        lista = self.api.get('/api/bitacora/')
        self.assertEqual(len(lista.data), 1)

    def test_api_solo_lista_entradas_propias(self):
        otro = User.objects.create_user('otro', 'o@ejemplo.com', 'Contrasena2026!')
        Entrada.objects.create(user=otro, rawg_id=1, titulo='Hollow Knight')
        self.api.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token()}')
        self.assertEqual(self.api.get('/api/bitacora/').data, [])

    def test_api_ruleta(self):
        respuesta = self.api.get(reverse('api-ruleta'), {'animo': 'miedo'})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(respuesta.data['nombre'], ['Resident Evil 4', 'Outlast'])
        self.assertEqual(self.api.get(reverse('api-ruleta'), {'animo': 'x'}).status_code, 400)

    def test_api_buscar(self):
        respuesta = self.api.get(reverse('api-buscar'), {'q': 'portal'})
        self.assertEqual(respuesta.data['juegos'][0]['nombre'], 'Portal 2')


@override_settings(RAWG_API_KEY='llave-de-prueba')
class RawgClienteTests(TestCase):
    """Prueba el cliente real de RAWG simulando la respuesta (sin internet)."""

    def setUp(self):
        cache.clear()

    @patch('games.services.requests.get')
    def test_envia_la_llave_y_normaliza(self, get):
        get.return_value.status_code = 200
        get.return_value.json.return_value = {
            'next': None,
            'results': [{'id': 3498, 'name': 'Grand Theft Auto V', 'background_image': 'https://img/gta.jpg',
                         'released': '2013-09-17', 'rating': 4.47, 'metacritic': 92, 'playtime': 74,
                         'genres': [{'name': 'Action'}], 'platforms': [{'platform': {'name': 'PC'}}]}],
        }
        resultado = services.buscar_juegos('gta')
        self.assertEqual(get.call_args.kwargs['params']['key'], 'llave-de-prueba')
        self.assertEqual(resultado['juegos'][0]['nombre'], 'Grand Theft Auto V')
        self.assertEqual(resultado['juegos'][0]['plataformas'], ['PC'])

    @patch('games.services.requests.get')
    def test_error_de_rawg_muestra_aviso(self, get):
        get.return_value.status_code = 500
        respuesta = self.client.get(reverse('explorar'))
        self.assertContains(respuesta, 'No pudimos conectar con RAWG')
