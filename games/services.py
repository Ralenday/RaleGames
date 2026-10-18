# games/services.py
# Capa de servicios: aquí vive el consumo de la API externa RAWG y la lógica
# de la ruleta, separadas de las vistas.

import random
from datetime import date, timedelta

import requests
from django.conf import settings
from django.core.cache import cache

from .demo_data import JUEGOS_DEMO

RAWG_URL = 'https://api.rawg.io/api'
TIEMPO_ESPERA = 8      # segundos máximos esperando a RAWG
CACHE_SEGUNDOS = 60 * 30


class RawgError(Exception):
    """La API externa no respondió o respondió con error."""


def modo_demo():
    # Sin llave en el .env se usan los datos de ejemplo de demo_data.py
    return not settings.RAWG_API_KEY


# ---------------------------------------------------------------------------
# Cliente de RAWG
# ---------------------------------------------------------------------------

def _get(ruta, **params):
    """Hace un GET a RAWG agregando la llave del .env. La llave nunca llega
    al navegador: el frontend solo habla con nuestro servidor."""
    clave_cache = f'rawg:{ruta}:{sorted(params.items())}'
    datos = cache.get(clave_cache)
    if datos is not None:
        return datos

    params['key'] = settings.RAWG_API_KEY
    try:
        respuesta = requests.get(f'{RAWG_URL}/{ruta}', params=params, timeout=TIEMPO_ESPERA)
    except requests.RequestException as error:
        raise RawgError('No se pudo conectar con RAWG') from error

    if respuesta.status_code == 404:
        return None
    if respuesta.status_code != 200:
        raise RawgError(f'RAWG respondió con código {respuesta.status_code}')

    datos = respuesta.json()
    cache.set(clave_cache, datos, CACHE_SEGUNDOS)
    return datos


def normalizar_juego(crudo):
    """Convierte la respuesta de RAWG (en inglés y muy anidada) al formato
    sencillo que usan las plantillas."""
    return {
        'id': crudo['id'],
        'nombre': crudo.get('name', ''),
        'imagen': crudo.get('background_image') or '',
        'lanzamiento': crudo.get('released') or '',
        'rating': crudo.get('rating') or 0,
        'metacritic': crudo.get('metacritic'),
        'generos': [g['name'] for g in crudo.get('genres') or []],
        'plataformas': [p['platform']['name'] for p in crudo.get('platforms') or []],
        'horas': crudo.get('playtime') or 0,
        'descripcion': crudo.get('description_raw', ''),
        'desarrolladores': [d['name'] for d in crudo.get('developers') or []],
        'sitio': crudo.get('website') or '',
        'capturas': [],
    }


def _demo(juego):
    # Copia con los mismos campos que normalizar_juego()
    return {**juego, 'imagen': '', 'desarrolladores': [], 'sitio': '', 'capturas': []}


# ---------------------------------------------------------------------------
# Patrón estructural (Facade): las vistas solo llaman a estas funciones y no
# saben si los datos vienen de RAWG, de la caché o del modo demo
# ---------------------------------------------------------------------------

def buscar_juegos(texto='', genero='', pagina=1):
    if modo_demo():
        juegos = [_demo(j) for j in JUEGOS_DEMO]
        if texto:
            juegos = [j for j in juegos if texto.lower() in j['nombre'].lower()]
        if genero:
            juegos = [j for j in juegos if genero in j['slugs']]
        return {'juegos': juegos, 'hay_mas': False}

    params = {'page': pagina, 'page_size': 20}
    if texto:
        params['search'] = texto
    else:
        params['ordering'] = '-added'
    if genero:
        params['genres'] = genero
    datos = _get('games', **params)
    return {
        'juegos': [normalizar_juego(j) for j in datos['results']],
        'hay_mas': bool(datos.get('next')),
    }


def populares():
    """Juegos más agregados por la comunidad durante el último año."""
    if modo_demo():
        return sorted((_demo(j) for j in JUEGOS_DEMO), key=lambda j: -j['metacritic'])[:8]

    hoy = date.today()
    datos = _get('games', dates=f'{hoy - timedelta(days=365)},{hoy}', ordering='-added', page_size=8)
    return [normalizar_juego(j) for j in datos['results']]


def juego_del_dia():
    """Siempre el mismo juego durante todo el día, distinto al día siguiente."""
    lista = populares()
    if not lista:
        return None
    return lista[date.today().toordinal() % len(lista)]


def detalle_juego(juego_id):
    if modo_demo():
        juego = next((j for j in JUEGOS_DEMO if j['id'] == juego_id), None)
        return _demo(juego) if juego else None

    crudo = _get(f'games/{juego_id}')
    if crudo is None:
        return None
    juego = normalizar_juego(crudo)
    capturas = _get(f'games/{juego_id}/screenshots', page_size=6) or {'results': []}
    juego['capturas'] = [c['image'] for c in capturas['results']]
    return juego


# ---------------------------------------------------------------------------
# Ruleta "¿Qué juego hoy?"
# Patrón de comportamiento (Strategy): cada estado de ánimo sabe qué filtros
# pedirle a RAWG y cómo filtrar el catálogo demo; todos comparten la interfaz
# ---------------------------------------------------------------------------

class Animo:
    clave = ''
    nombre = ''
    icono = ''
    descripcion = ''
    generos = ''   # slugs de RAWG separados por coma
    tags = ''

    def params_rawg(self):
        params = {}
        if self.generos:
            params['genres'] = self.generos
        if self.tags:
            params['tags'] = self.tags
        return params

    def coincide(self, juego):
        buscados = set(self.generos.split(',') + self.tags.split(',')) - {''}
        return bool(buscados & set(juego['slugs'] + juego['tags']))


class Relajado(Animo):
    clave, nombre, icono = 'relajado', 'Relajado', '🌿'
    descripcion = 'Algo tranquilo para desconectarse'
    generos = 'casual,puzzle,simulation'


class Adrenalina(Animo):
    clave, nombre, icono = 'adrenalina', 'Con adrenalina', '⚡'
    descripcion = 'Acción rápida, sin pausas'
    generos = 'action,shooter,fighting,racing'


class Historia(Animo):
    clave, nombre, icono = 'historia', 'Quiero una historia', '📖'
    descripcion = 'Personajes y trama que atrapen'
    tags = 'story-rich'


class Miedo(Animo):
    clave, nombre, icono = 'miedo', 'Quiero pasar miedo', '👻'
    descripcion = 'Terror y tensión'
    tags = 'horror'


class Amigos(Animo):
    clave, nombre, icono = 'amigos', 'Con amigos', '🎮'
    descripcion = 'Cooperativo o competitivo'
    tags = 'co-op,local-multiplayer,multiplayer'


class Cerebro(Animo):
    clave, nombre, icono = 'cerebro', 'Usar el cerebro', '🧠'
    descripcion = 'Estrategia y rompecabezas'
    generos = 'strategy,puzzle'


ANIMOS = {a.clave: a for a in (Relajado(), Adrenalina(), Historia(), Miedo(), Amigos(), Cerebro())}

# Horas promedio de juego (dato "playtime" de RAWG)
TIEMPOS = {
    'corto': ('Una tarde (menos de 10 h)', 1, 10),
    'medio': ('Un par de semanas (10 a 30 h)', 10, 30),
    'largo': ('Para todo el mes (más de 30 h)', 30, 10_000),
    'cualquiera': ('Me da igual', 0, 10_000),
}


def girar_ruleta(clave_animo, clave_tiempo='cualquiera'):
    """Devuelve un juego al azar que encaje con el ánimo y el tiempo elegidos,
    o None si el ánimo no existe."""
    animo = ANIMOS.get(clave_animo)
    if animo is None:
        return None
    _, minimo, maximo = TIEMPOS.get(clave_tiempo, TIEMPOS['cualquiera'])

    if modo_demo():
        candidatos = [_demo(j) for j in JUEGOS_DEMO if animo.coincide(j)]
    else:
        # Una página al azar entre las primeras para que no salga siempre lo mismo
        datos = _get('games', ordering='-added', page_size=40, page=random.randint(1, 3), **animo.params_rawg())
        candidatos = [normalizar_juego(j) for j in (datos or {}).get('results', [])]

    por_tiempo = [j for j in candidatos if minimo <= j['horas'] <= maximo]
    # Si el filtro de tiempo deja la lista vacía, mejor sugerir algo que nada
    candidatos = por_tiempo or candidatos
    return random.choice(candidatos) if candidatos else None
