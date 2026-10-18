# games/demo_data.py
# Catálogo de ejemplo que se usa cuando no hay RAWG_API_KEY en el .env,
# para que la página funcione (y las pruebas corran) sin conexión.
# Los datos tienen el mismo formato que devuelve services.normalizar_juego().

JUEGOS_DEMO = [
    {
        'id': 1, 'nombre': 'Hollow Knight', 'lanzamiento': '2017-02-24', 'rating': 4.4, 'metacritic': 87,
        'generos': ['Acción', 'Indie', 'Plataformas'], 'slugs': ['action', 'indie', 'platformer'],
        'tags': ['singleplayer', 'difficult'], 'plataformas': ['PC', 'Nintendo Switch', 'PlayStation 4', 'Xbox One'],
        'horas': 30,
        'descripcion': 'Explora Hallownest, un reino subterráneo de insectos en ruinas, en un metroidvania '
                       'dibujado a mano lleno de jefes exigentes y secretos.',
    },
    {
        'id': 2, 'nombre': 'Stardew Valley', 'lanzamiento': '2016-02-26', 'rating': 4.4, 'metacritic': 89,
        'generos': ['Simulación', 'Indie', 'RPG'], 'slugs': ['simulation', 'indie', 'role-playing-games-rpg'],
        'tags': ['relaxing', 'co-op'], 'plataformas': ['PC', 'Nintendo Switch', 'PlayStation 4', 'Móvil'],
        'horas': 50,
        'descripcion': 'Hereda la granja de tu abuelo, cultiva, pesca, haz amigos en el pueblo y olvídate '
                       'del reloj. Se puede jugar en cooperativo.',
    },
    {
        'id': 3, 'nombre': 'The Witcher 3: Wild Hunt', 'lanzamiento': '2015-05-18', 'rating': 4.7, 'metacritic': 93,
        'generos': ['RPG', 'Acción', 'Aventura'], 'slugs': ['role-playing-games-rpg', 'action', 'adventure'],
        'tags': ['story-rich', 'open-world'], 'plataformas': ['PC', 'PlayStation 5', 'Xbox Series X', 'Nintendo Switch'],
        'horas': 60,
        'descripcion': 'Geralt de Rivia busca a Ciri en un mundo abierto enorme, con decisiones que cambian '
                       'la historia y misiones secundarias memorables.',
    },
    {
        'id': 4, 'nombre': 'Portal 2', 'lanzamiento': '2011-04-18', 'rating': 4.6, 'metacritic': 95,
        'generos': ['Puzzle', 'Aventura'], 'slugs': ['puzzle', 'adventure'],
        'tags': ['co-op', 'story-rich', 'funny'], 'plataformas': ['PC', 'PlayStation 3', 'Xbox 360'],
        'horas': 9,
        'descripcion': 'Resuelve pruebas con la pistola de portales mientras GLaDOS te provoca. Incluye una '
                       'campaña cooperativa para dos.',
    },
    {
        'id': 5, 'nombre': 'Hades', 'lanzamiento': '2020-09-17', 'rating': 4.6, 'metacritic': 93,
        'generos': ['Acción', 'Indie', 'RPG'], 'slugs': ['action', 'indie', 'role-playing-games-rpg'],
        'tags': ['roguelike', 'story-rich'], 'plataformas': ['PC', 'Nintendo Switch', 'PlayStation 5', 'Xbox Series X'],
        'horas': 22,
        'descripcion': 'Zagreo intenta escapar del inframundo una y otra vez. Cada intento es distinto y la '
                       'historia avanza incluso cuando pierdes.',
    },
    {
        'id': 6, 'nombre': 'Celeste', 'lanzamiento': '2018-01-25', 'rating': 4.5, 'metacritic': 88,
        'generos': ['Plataformas', 'Indie'], 'slugs': ['platformer', 'indie'],
        'tags': ['difficult', 'story-rich'], 'plataformas': ['PC', 'Nintendo Switch', 'PlayStation 4', 'Xbox One'],
        'horas': 8,
        'descripcion': 'Ayuda a Madeline a escalar la montaña Celeste en un plataformero preciso que habla '
                       'sobre la ansiedad con mucho cariño.',
    },
    {
        'id': 7, 'nombre': 'Resident Evil 4', 'lanzamiento': '2023-03-24', 'rating': 4.5, 'metacritic': 93,
        'generos': ['Acción', 'Shooter'], 'slugs': ['action', 'shooter'],
        'tags': ['horror', 'survival'], 'plataformas': ['PC', 'PlayStation 5', 'Xbox Series X'],
        'horas': 16,
        'descripcion': 'Leon S. Kennedy viaja a una aldea española para rescatar a la hija del presidente. '
                       'Tensión, terror y mucha acción.',
    },
    {
        'id': 8, 'nombre': 'It Takes Two', 'lanzamiento': '2021-03-26', 'rating': 4.5, 'metacritic': 88,
        'generos': ['Aventura', 'Plataformas'], 'slugs': ['adventure', 'platformer'],
        'tags': ['co-op', 'local-multiplayer', 'story-rich'], 'plataformas': ['PC', 'PlayStation 5', 'Xbox Series X', 'Nintendo Switch'],
        'horas': 13,
        'descripcion': 'Una aventura exclusivamente cooperativa: una pareja convertida en muñecos debe '
                       'trabajar en equipo para volver a la normalidad.',
    },
    {
        'id': 9, 'nombre': 'Tetris Effect: Connected', 'lanzamiento': '2018-11-09', 'rating': 4.3, 'metacritic': 89,
        'generos': ['Puzzle', 'Arcade'], 'slugs': ['puzzle', 'arcade', 'casual'],
        'tags': ['relaxing', 'multiplayer'], 'plataformas': ['PC', 'PlayStation 4', 'Xbox Series X', 'Nintendo Switch'],
        'horas': 6,
        'descripcion': 'El Tetris de siempre envuelto en música y luces que reaccionan a cada pieza. '
                       'Hipnótico y relajante.',
    },
    {
        'id': 10, 'nombre': "Sid Meier's Civilization VI", 'lanzamiento': '2016-10-21', 'rating': 4.0, 'metacritic': 88,
        'generos': ['Estrategia'], 'slugs': ['strategy'],
        'tags': ['multiplayer', 'turn-based'], 'plataformas': ['PC', 'Nintendo Switch', 'PlayStation 4', 'Xbox One'],
        'horas': 80,
        'descripcion': 'Construye un imperio que resista el paso del tiempo, turno por turno, desde la edad '
                       'de piedra hasta la era de la información.',
    },
    {
        'id': 11, 'nombre': 'DOOM', 'lanzamiento': '2016-05-13', 'rating': 4.4, 'metacritic': 85,
        'generos': ['Acción', 'Shooter'], 'slugs': ['action', 'shooter'],
        'tags': ['fast-paced', 'gore'], 'plataformas': ['PC', 'PlayStation 4', 'Xbox One', 'Nintendo Switch'],
        'horas': 12,
        'descripcion': 'Shooter frenético contra las hordas del infierno en Marte. Nada de esconderse: '
                       'aquí se ataca de frente.',
    },
    {
        'id': 12, 'nombre': 'Rocket League', 'lanzamiento': '2015-07-07', 'rating': 3.9, 'metacritic': 86,
        'generos': ['Deportes', 'Carreras'], 'slugs': ['sports', 'racing'],
        'tags': ['multiplayer', 'competitive', 'local-multiplayer'], 'plataformas': ['PC', 'PlayStation 4', 'Xbox One', 'Nintendo Switch'],
        'horas': 4,
        'descripcion': 'Fútbol con coches propulsados por cohetes. Partidas de cinco minutos, ideales para '
                       'jugar con amigos.',
    },
    {
        'id': 13, 'nombre': 'Unpacking', 'lanzamiento': '2021-11-02', 'rating': 4.2, 'metacritic': 84,
        'generos': ['Puzzle', 'Casual', 'Indie'], 'slugs': ['puzzle', 'casual', 'indie'],
        'tags': ['relaxing', 'story-rich', 'cozy'], 'plataformas': ['PC', 'Nintendo Switch', 'PlayStation 5', 'Xbox One'],
        'horas': 3,
        'descripcion': 'Desempaca cajas en cada mudanza y descubre, sin una sola palabra, la historia de '
                       'la persona que vive ahí.',
    },
    {
        'id': 14, 'nombre': 'Outlast', 'lanzamiento': '2013-09-04', 'rating': 4.0, 'metacritic': 80,
        'generos': ['Aventura', 'Acción'], 'slugs': ['adventure', 'action'],
        'tags': ['horror', 'first-person'], 'plataformas': ['PC', 'PlayStation 4', 'Xbox One'],
        'horas': 5,
        'descripcion': 'Un periodista entra a un manicomio abandonado solo con una cámara de video. '
                       'No puedes pelear: solo correr y esconderte.',
    },
    {
        'id': 15, 'nombre': 'Red Dead Redemption 2', 'lanzamiento': '2018-10-26', 'rating': 4.6, 'metacritic': 97,
        'generos': ['Acción', 'Aventura'], 'slugs': ['action', 'adventure'],
        'tags': ['story-rich', 'open-world'], 'plataformas': ['PC', 'PlayStation 4', 'Xbox One'],
        'horas': 50,
        'descripcion': 'Arthur Morgan y la banda de Van der Linde huyen por un Salvaje Oeste que se acaba. '
                       'Una de las historias más cuidadas del medio.',
    },
    {
        'id': 16, 'nombre': 'Into the Breach', 'lanzamiento': '2018-02-27', 'rating': 4.2, 'metacritic': 90,
        'generos': ['Estrategia', 'Indie'], 'slugs': ['strategy', 'indie'],
        'tags': ['turn-based', 'roguelike'], 'plataformas': ['PC', 'Nintendo Switch', 'Móvil'],
        'horas': 10,
        'descripcion': 'Defiende ciudades de monstruos gigantes con mechas. Cada turno es un pequeño '
                       'rompecabezas donde ves venir todos los ataques.',
    },
]
