# RaleGames 🎮

**RaleGames no vende juegos: te ayuda a decidir cuál jugar.**

Le dices cómo te sientes (relajado, con adrenalina, con miedo, con amigos…) y cuánto tiempo tienes, y la
*ruleta* elige un juego real de la base de datos de [IGDB](https://www.igdb.com) (la base de datos de
videojuegos de Twitch, con cientos de miles de títulos).
Después lo guardas en tu **bitácora**, un tablero personal donde llevas el control de lo que quieres jugar,
lo que estás jugando, lo que terminaste y lo que abandonaste.

## Pantallas

| Ruta | Pantalla |
| --- | --- |
| `/` | **Inicio**: juego del día, ánimos y lo mejor valorado del último año |
| `/registro/` | **Registro** con validación en el navegador (JS) y en el servidor (Django) |
| `/entrar/` | Inicio de sesión |
| `/explorar/` | Buscador de juegos con filtros por género (API IGDB) |
| `/juego/<id>/` | Detalle del juego: descripción, capturas, plataformas, calificación de la crítica |
| `/ruleta/` | La ruleta “¿Qué juego hoy?” |
| `/bitacora/` | Tablero personal (requiere sesión) |

## Unidad 3: seguridad, web services y APIs

**API externa**: [IGDB](https://api-docs.igdb.com) (gratuita, de Twitch). Se consume desde `games/services.py`
con `requests`. Usa **OAuth2 (client credentials)**: con el Client ID y el Client Secret el servidor pide un
token temporal a Twitch, lo guarda en caché y lo renueva solo cuando vence. Las consultas a IGDB se escriben
en su lenguaje *Apicalypse* y las respuestas se guardan en caché 30 minutos.

**Llaves en `.env`**: `SECRET_KEY`, `TWITCH_CLIENT_ID` y `TWITCH_CLIENT_SECRET` se leen con `python-dotenv` en
`ralegames/settings.py`.
El archivo `.env` está en `.gitignore`; en el repositorio solo va `.env.example` como plantilla.

**Web services propios** (Django REST Framework):

| Método | Ruta | Descripción | Auth |
| --- | --- | --- | --- |
| POST | `/api/token/` | Obtiene el token JWT (`access` y `refresh`) | — |
| POST | `/api/token/refresh/` | Renueva el token | — |
| GET/POST | `/api/bitacora/` | Lista / agrega juegos a la bitácora | JWT |
| GET/PUT/PATCH/DELETE | `/api/bitacora/<id>/` | Detalle, edición o borrado | JWT |
| GET | `/api/juegos/?q=zelda` | Búsqueda (proxy a IGDB) | Pública |
| GET | `/api/ruleta/?animo=miedo&tiempo=corto` | Gira la ruleta | Pública |

Ánimos válidos: `relajado`, `adrenalina`, `historia`, `miedo`, `amigos`, `cerebro`.
Tiempos: `corto`, `medio`, `largo`, `cualquiera`.

**Medidas de seguridad**

- Llaves fuera del código (`.env`) y las de IGDB **nunca llegan al navegador**: el frontend llama a nuestro
  servidor y éste llama a IGDB (proxy).
- Autenticación OAuth2 con Twitch; el token caduca y se renueva automáticamente.
- El texto de búsqueda se limpia antes de armar la consulta a IGDB (no se puede inyectar otra consulta).
- Contraseñas cifradas por Django (PBKDF2) y validadores de fuerza (mínimo 8, no solo números, no comunes,
  distinta al usuario).
- Validación doble del registro: `static/games/js/registro.js` y `games/forms.py`.
- Protección CSRF en todos los formularios; las acciones que modifican datos solo aceptan POST.
- Cada usuario solo puede ver y modificar **su** bitácora (web y API).
- Al guardar un juego, los datos se vuelven a pedir a IGDB en el servidor: no se confía en lo que manda el navegador.
- API protegida con JWT y con límite de peticiones (*throttling*: 60/hora anónimo, 600/hora con sesión).
- Cookies `HttpOnly`, `X-Frame-Options: DENY`, `nosniff`; con `DEBUG=False` las cookies son solo HTTPS.
- Los datos de la API se insertan en la página con `textContent` (JS) o con el autoescape de Django: sin XSS.

**Patrones de diseño** (como en la Unidad 1): *Facade* en `services.py` (las vistas no saben si los datos
vienen de IGDB, de la caché o del modo demo) y *Strategy* para los ánimos de la ruleta.

## Cómo correrlo

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # y llena SECRET_KEY, TWITCH_CLIENT_ID y TWITCH_CLIENT_SECRET
python manage.py migrate
python manage.py runserver
```

Abre http://127.0.0.1:8000. **Sin credenciales la página funciona en modo demo** con 16 juegos de ejemplo.

### Cómo obtener las credenciales de IGDB (gratis)

1. Crea una cuenta en [twitch.tv](https://www.twitch.tv) (o entra con la tuya).
2. Activa la **verificación en dos pasos** en *Configuración → Seguridad y privacidad*. Twitch la exige para
   registrar aplicaciones.
3. Entra a [dev.twitch.tv/console/apps](https://dev.twitch.tv/console/apps) → **Register Your Application**:
   - Name: `RaleGames` (o cualquier nombre único)
   - OAuth Redirect URLs: `http://localhost`
   - Category: `Website Integration`
   - Client Type: `Confidential`
4. Abre la aplicación con **Manage**: copia el **Client ID** y pulsa **New Secret** para generar el **Client Secret**.
5. Pégalos en tu `.env` como `TWITCH_CLIENT_ID` y `TWITCH_CLIENT_SECRET` y reinicia el servidor.

## Pruebas

```bash
python manage.py test
```

30 pruebas: pantallas, validaciones del registro, bitácora, permisos entre usuarios, ruleta, API con JWT
y el cliente de IGDB simulado (token OAuth, renovación del token e intentos de inyección). GitHub Actions las corre en cada push (`.github/workflows/tests.yml`).
