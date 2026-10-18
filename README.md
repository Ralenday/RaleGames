# RaleGames 🎮

**RaleGames no vende juegos: te ayuda a decidir cuál jugar.**

Le dices cómo te sientes (relajado, con adrenalina, con miedo, con amigos…) y cuánto tiempo tienes, y la
*ruleta* elige un juego real de la base de datos de [RAWG](https://rawg.io) (más de 500,000 títulos).
Después lo guardas en tu **bitácora**, un tablero personal donde llevas el control de lo que quieres jugar,
lo que estás jugando, lo que terminaste y lo que abandonaste.

## Pantallas

| Ruta | Pantalla |
| --- | --- |
| `/` | **Inicio**: juego del día, ánimos y lo más jugado del año |
| `/registro/` | **Registro** con validación en el navegador (JS) y en el servidor (Django) |
| `/entrar/` | Inicio de sesión |
| `/explorar/` | Buscador de juegos con filtros por género (API RAWG) |
| `/juego/<id>/` | Detalle del juego: descripción, capturas, plataformas, Metacritic |
| `/ruleta/` | La ruleta “¿Qué juego hoy?” |
| `/bitacora/` | Tablero personal (requiere sesión) |

## Unidad 3: seguridad, web services y APIs

**API externa**: [RAWG Video Games Database](https://rawg.io/apidocs) (gratuita). Se consume desde
`games/services.py` con `requests`; las respuestas se guardan en caché 30 minutos.

**Llaves en `.env`**: `SECRET_KEY` y `RAWG_API_KEY` se leen con `python-dotenv` en `ralegames/settings.py`.
El archivo `.env` está en `.gitignore`; en el repositorio solo va `.env.example` como plantilla.

**Web services propios** (Django REST Framework):

| Método | Ruta | Descripción | Auth |
| --- | --- | --- | --- |
| POST | `/api/token/` | Obtiene el token JWT (`access` y `refresh`) | — |
| POST | `/api/token/refresh/` | Renueva el token | — |
| GET/POST | `/api/bitacora/` | Lista / agrega juegos a la bitácora | JWT |
| GET/PUT/PATCH/DELETE | `/api/bitacora/<id>/` | Detalle, edición o borrado | JWT |
| GET | `/api/juegos/?q=zelda` | Búsqueda (proxy a RAWG) | Pública |
| GET | `/api/ruleta/?animo=miedo&tiempo=corto` | Gira la ruleta | Pública |

Ánimos válidos: `relajado`, `adrenalina`, `historia`, `miedo`, `amigos`, `cerebro`.
Tiempos: `corto`, `medio`, `largo`, `cualquiera`.

**Medidas de seguridad**

- Llaves fuera del código (`.env`) y la de RAWG **nunca llega al navegador**: el frontend llama a nuestro
  servidor y éste llama a RAWG (proxy).
- Contraseñas cifradas por Django (PBKDF2) y validadores de fuerza (mínimo 8, no solo números, no comunes,
  distinta al usuario).
- Validación doble del registro: `static/games/js/registro.js` y `games/forms.py`.
- Protección CSRF en todos los formularios; las acciones que modifican datos solo aceptan POST.
- Cada usuario solo puede ver y modificar **su** bitácora (web y API).
- Al guardar un juego, los datos se vuelven a pedir a RAWG en el servidor: no se confía en lo que manda el navegador.
- API protegida con JWT y con límite de peticiones (*throttling*: 60/hora anónimo, 600/hora con sesión).
- Cookies `HttpOnly`, `X-Frame-Options: DENY`, `nosniff`; con `DEBUG=False` las cookies son solo HTTPS.
- Los datos de la API se insertan en la página con `textContent` (JS) o con el autoescape de Django: sin XSS.

**Patrones de diseño** (como en la Unidad 1): *Facade* en `services.py` (las vistas no saben si los datos
vienen de RAWG, de la caché o del modo demo) y *Strategy* para los ánimos de la ruleta.

## Cómo correrlo

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # y llena SECRET_KEY y RAWG_API_KEY
python manage.py migrate
python manage.py runserver
```

Abre http://127.0.0.1:8000. La llave de RAWG es gratuita: crea una cuenta en https://rawg.io/apidocs.
**Sin llave la página funciona en modo demo** con 16 juegos de ejemplo (útil para probar sin internet).

## Pruebas

```bash
python manage.py test
```

28 pruebas: pantallas, validaciones del registro, bitácora, permisos entre usuarios, ruleta, API con JWT
y el cliente de RAWG simulado. GitHub Actions las corre en cada push (`.github/workflows/tests.yml`).
