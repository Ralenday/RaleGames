# games/services.py
# Capa de servicios: aquí vive el consumo de la API externa IGDB y la lógica
# de la ruleta, separadas de las vistas.

import hashlib
import random
import time
from datetime import datetime, timezone

import requests
from django.conf import settings
from django.core.cache import cache

from .demo_data import JUEGOS_DEMO

IGDB_URL = 'https://api.igdb.com/v4'
TWITCH_TOKEN_URL = 'https://id.twitch.tv/oauth2/token'
IMAGEN_URL = 'https://images.igdb.com/igdb/image/upload/t_{tamano}/{id}.jpg'
TIEMPO_ESPERA = 8      # segundos máximos esperando a IGDB
CACHE_SEGUNDOS = 60 * 30

# Campos que se piden a IGDB en los listados y en el detalle
CAMPOS_LISTA = ('name, first_release_date, total_rating, aggregated_rating, genres.name, '
                'platforms.name, cover.image_id, artworks.image_id, screenshots.image_id')
CAMPOS_DETALLE = CAMPOS_LISTA + ', summary, storyline, url, involved_companies.company.name, involved_companies.developer'
# Solo juegos completos (principal, remake, remaster, edición ampliada): sin DLCs, paquetes ni ports
SOLO_JUEGOS = 'game_type = (0,8,9,10) & version_parent = null'


class IgdbError(Exception):
    """La API externa no respondió o respondió con error."""


def modo_demo():
    # Sin credenciales en el .env se usan los datos de ejemplo de demo_data.py
    return not (settings.TWITCH_CLIENT_ID and settings.TWITCH_CLIENT_SECRET)


# ---------------------------------------------------------------------------
# Cliente de IGDB
# ---------------------------------------------------------------------------

def _token(renovar=False):
    """IGDB usa OAuth2 de Twitch (client credentials): con el Client ID y el
    Client Secret del .env se pide un token temporal, que se guarda en caché
    hasta poco antes de que expire."""
    token = None if renovar else cache.get('igdb:token')
    if token:
        return token
    try:
        respuesta = requests.post(TWITCH_TOKEN_URL, timeout=TIEMPO_ESPERA, data={
            'client_id': settings.TWITCH_CLIENT_ID,
            'client_secret': settings.TWITCH_CLIENT_SECRET,
            'grant_type': 'client_credentials',
        })
    except requests.RequestException as error:
        raise IgdbError('No se pudo conectar con Twitch') from error
    if respuesta.status_code != 200:
        raise IgdbError('Twitch rechazó las credenciales (revisa el .env)')

    datos = respuesta.json()
    cache.set('igdb:token', datos['access_token'], max(60, datos['expires_in'] - 300))
    return datos['access_token']


def _consultar(endpoint, consulta):
    """Manda una consulta en lenguaje Apicalypse a IGDB. Las credenciales
    nunca llegan al navegador: el frontend solo habla con nuestro servidor."""
    # Las consultas son largas: se usa su hash como llave de la caché
    clave_cache = 'igdb:' + hashlib.sha256(f'{endpoint}:{consulta}'.encode()).hexdigest()
    datos = cache.get(clave_cache)
    if datos is not None:
        return datos

    for intento in range(2):
        cabeceras = {
            'Client-ID': settings.TWITCH_CLIENT_ID,
            'Authorization': f'Bearer {_token(renovar=intento > 0)}',
        }
        try:
            respuesta = requests.post(f'{IGDB_URL}/{endpoint}', data=consulta.encode(),
                                      headers=cabeceras, timeout=TIEMPO_ESPERA)
        except requests.RequestException as error:
            raise IgdbError('No se pudo conectar con IGDB') from error
        # 401: el token caducó antes de tiempo, se pide uno nuevo y se reintenta
        if respuesta.status_code != 401:
            break

    if respuesta.status_code != 200:
        raise IgdbError(f'IGDB respondió con código {respuesta.status_code}')

    datos = respuesta.json()
    cache.set(clave_cache, datos, CACHE_SEGUNDOS)
    return datos


def _imagen(imagen_id, tamano):
    return IMAGEN_URL.format(tamano=tamano, id=imagen_id)


def normalizar_juego(crudo):
    """Convierte la respuesta de IGDB (en inglés y muy anidada) al formato
    sencillo que usan las plantillas."""
    # Para las tarjetas (16:9) se prefiere un arte o captura antes que la portada vertical
    horizontal = (crudo.get('artworks') or crudo.get('screenshots') or [None])[0]
    if horizontal:
        imagen = _imagen(horizontal['image_id'], 'screenshot_big')
    elif crudo.get('cover'):
        imagen = _imagen(crudo['cover']['image_id'], 'cover_big')
    else:
        imagen = ''

    fecha = crudo.get('first_release_date')
    critica = crudo.get('aggregated_rating')
    return {
        'id': crudo['id'],
        'nombre': crudo.get('name', ''),
        'imagen': imagen,
        'lanzamiento': datetime.fromtimestamp(fecha, timezone.utc).date().isoformat() if fecha else '',
        'rating': round((crudo.get('total_rating') or 0) / 20, 1),   # IGDB califica de 0 a 100
        'metacritic': round(critica) if critica else None,          # promedio de la crítica
        'generos': [g['name'] for g in crudo.get('genres') or []],
        'plataformas': [p['name'] for p in crudo.get('platforms') or []],
        'horas': 0,
        'descripcion': crudo.get('summary') or crudo.get('storyline') or '',
        'desarrolladores': [c['company']['name'] for c in crudo.get('involved_companies') or [] if c.get('developer')],
        'sitio': crudo.get('url') or '',
        'capturas': [_imagen(c['image_id'], 'screenshot_big') for c in (crudo.get('screenshots') or [])[:6]],
    }


def _agregar_horas(juegos):
    """IGDB guarda la duración en otro endpoint (game_time_to_beats, en segundos).
    Se pide en una sola consulta para toda la lista."""
    if not juegos:
        return juegos
    ids = ','.join(str(j['id']) for j in juegos)
    try:
        tiempos = _consultar('game_time_to_beats', f'fields game_id, normally, hastily; where game_id = ({ids}); limit 500;')
    except IgdbError:
        return juegos  # sin duración la página sigue funcionando
    horas = {t['game_id']: round((t.get('normally') or t.get('hastily') or 0) / 3600) for t in tiempos}
    for juego in juegos:
        juego['horas'] = horas.get(juego['id'], 0)
    return juegos


def _limpiar(texto):
    # Evita que comillas o barras del usuario rompan la consulta Apicalypse
    return texto.replace('\\', '').replace('"', '')


def _demo(juego):
    # Copia con los mismos campos que normalizar_juego()
    return {**juego, 'imagen': '', 'desarrolladores': [], 'sitio': '', 'capturas': []}


# Géneros que se muestran como filtros en Explorar: slug -> (nombre, campo de IGDB, id)
# En IGDB "Acción" y "Terror" son temas (themes), no géneros
GENEROS = {
    'action': ('Acción', 'themes', 1),
    'adventure': ('Aventura', 'genres', 31),
    'rpg': ('RPG', 'genres', 12),
    'strategy': ('Estrategia', 'genres', 15),
    'shooter': ('Shooter', 'genres', 5),
    'puzzle': ('Puzzle', 'genres', 9),
    'platformer': ('Plataformas', 'genres', 8),
    'simulation': ('Simulación', 'genres', 13),
    'indie': ('Indie', 'genres', 32),
    'racing': ('Carreras', 'genres', 10),
    'sports': ('Deportes', 'genres', 14),
    'horror': ('Terror', 'themes', 19),
}


# ---------------------------------------------------------------------------
# Patrón estructural (Facade): las vistas solo llaman a estas funciones y no
# saben si los datos vienen de IGDB, de la caché o del modo demo
# ---------------------------------------------------------------------------

POR_PAGINA = 20


def buscar_juegos(texto='', genero='', pagina=1):
    if modo_demo():
        juegos = [_demo(j) for j in JUEGOS_DEMO]
        if texto:
            juegos = [j for j in juegos if texto.lower() in j['nombre'].lower()]
        if genero:
            juegos = [j for j in juegos if genero in j['slugs'] + j['tags']]
        return {'juegos': juegos, 'hay_mas': False}

    filtros = [SOLO_JUEGOS]
    if genero in GENEROS:
        _, campo, id_igdb = GENEROS[genero]
        filtros.append(f'{campo} = ({id_igdb})')
    texto = _limpiar(texto)
    if texto:
        # "search" ordena solo por parecido del nombre y no se puede combinar con sort:
        # se piden 50 coincidencias y se ordenan aquí por popularidad (una sola página)
        resultados = _consultar('games', (
            f'fields {CAMPOS_LISTA}, total_rating_count; search "{texto}"; '
            f'where {" & ".join(filtros)}; limit 50;'
        ))
        resultados.sort(key=lambda j: -(j.get('total_rating_count') or 0))
        juegos = [normalizar_juego(j) for j in resultados[:POR_PAGINA]]
        return {'juegos': _agregar_horas(juegos), 'hay_mas': False}

    filtros.append('total_rating_count > 0')
    resultados = _consultar('games', (
        f'fields {CAMPOS_LISTA}; where {" & ".join(filtros)}; sort total_rating_count desc; '
        f'limit {POR_PAGINA + 1}; offset {(pagina - 1) * POR_PAGINA};'
    ))
    juegos = [normalizar_juego(j) for j in resultados[:POR_PAGINA]]
    # Se pidió uno de más solo para saber si existe una página siguiente
    return {'juegos': _agregar_horas(juegos), 'hay_mas': len(resultados) > POR_PAGINA}


def populares():
    """Juegos con más reseñas de la comunidad entre los que salieron en el último año."""
    if modo_demo():
        return sorted((_demo(j) for j in JUEGOS_DEMO), key=lambda j: -j['metacritic'])[:8]

    ahora = int(time.time())
    hace_un_ano = ahora - 365 * 24 * 3600
    resultados = _consultar('games', (
        f'fields {CAMPOS_LISTA}; '
        f'where first_release_date >= {hace_un_ano} & first_release_date <= {ahora} & total_rating_count > 0 & {SOLO_JUEGOS}; '
        'sort total_rating_count desc; limit 8;'
    ))
    return _agregar_horas([normalizar_juego(j) for j in resultados])


def juego_del_dia():
    """Siempre el mismo juego durante todo el día, distinto al día siguiente."""
    lista = populares()
    if not lista:
        return None
    return lista[datetime.now().toordinal() % len(lista)]


def detalle_juego(juego_id):
    if modo_demo():
        juego = next((j for j in JUEGOS_DEMO if j['id'] == juego_id), None)
        return _demo(juego) if juego else None

    resultados = _consultar('games', f'fields {CAMPOS_DETALLE}; where id = {int(juego_id)};')
    if not resultados:
        return None
    return _agregar_horas([normalizar_juego(resultados[0])])[0]


# ---------------------------------------------------------------------------
# Ruleta "¿Qué juego hoy?"
# Patrón de comportamiento (Strategy): cada estado de ánimo sabe qué filtros
# pedirle a IGDB y cómo filtrar el catálogo demo; todos comparten la interfaz
# ---------------------------------------------------------------------------

class Animo:
    clave = ''
    nombre = ''
    icono = ''
    descripcion = ''
    generos = ()     # ids de géneros de IGDB
    temas = ()       # ids de temas de IGDB
    modos = ()       # ids de modos de juego de IGDB
    etiquetas = ()   # slugs y tags del catálogo demo

    def filtro_igdb(self):
        partes = []
        for campo, ids in (('genres', self.generos), ('themes', self.temas), ('game_modes', self.modos)):
            if ids:
                partes.append(f'{campo} = ({",".join(map(str, ids))})')
        return '(' + ' | '.join(partes) + ')'

    def coincide(self, juego):
        return bool(set(self.etiquetas) & set(juego['slugs'] + juego['tags']))


class Relajado(Animo):
    clave, nombre, icono = 'relajado', 'Relajado', '🌿'
    descripcion = 'Algo tranquilo para desconectarse'
    generos = (9, 13)                    # Puzzle, Simulador
    etiquetas = ('casual', 'puzzle', 'simulation', 'relaxing')


class Adrenalina(Animo):
    clave, nombre, icono = 'adrenalina', 'Con adrenalina', '⚡'
    descripcion = 'Acción rápida, sin pausas'
    generos = (4, 5, 10, 25)             # Pelea, Shooter, Carreras, Hack and slash
    temas = (1,)                         # Acción
    etiquetas = ('action', 'shooter', 'fighting', 'racing')


class Historia(Animo):
    clave, nombre, icono = 'historia', 'Quiero una historia', '📖'
    descripcion = 'Personajes y trama que atrapen'
    generos = (12, 31, 34)               # RPG, Aventura, Novela visual
    temas = (31,)                        # Drama
    etiquetas = ('story-rich',)


class Miedo(Animo):
    clave, nombre, icono = 'miedo', 'Quiero pasar miedo', '👻'
    descripcion = 'Terror y tensión'
    temas = (19,)                        # Terror
    etiquetas = ('horror',)


class Amigos(Animo):
    clave, nombre, icono = 'amigos', 'Con amigos', '🎮'
    descripcion = 'Cooperativo o competitivo'
    modos = (2, 3, 4)                    # Multijugador, Cooperativo, Pantalla dividida
    etiquetas = ('co-op', 'local-multiplayer', 'multiplayer')


class Cerebro(Animo):
    clave, nombre, icono = 'cerebro', 'Usar el cerebro', '🧠'
    descripcion = 'Estrategia y rompecabezas'
    generos = (9, 11, 15, 16, 24)        # Puzzle, RTS, Estrategia, Por turnos, Táctico
    etiquetas = ('strategy', 'puzzle')


ANIMOS = {a.clave: a for a in (Relajado(), Adrenalina(), Historia(), Miedo(), Amigos(), Cerebro())}

# Horas para terminar el juego (dato "time to beat" de IGDB)
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
        # Los 100 juegos más valorados por la comunidad que encajan con el ánimo
        resultados = _consultar('games', (
            f'fields {CAMPOS_LISTA}; '
            f'where {animo.filtro_igdb()} & total_rating_count > 50 & total_rating > 70 & {SOLO_JUEGOS}; '
            'sort total_rating_count desc; limit 100;'
        ))
        candidatos = _agregar_horas([normalizar_juego(j) for j in resultados])

    por_tiempo = [j for j in candidatos if minimo <= j['horas'] <= maximo]
    # Si el filtro de tiempo deja la lista vacía, mejor sugerir algo que nada
    candidatos = por_tiempo or candidatos
    return random.choice(candidatos) if candidatos else None
