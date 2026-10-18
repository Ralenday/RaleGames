from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import services
from .forms import EntradaForm, RegistroForm
from .models import Entrada

# Géneros de RAWG que se muestran como filtros en Explorar (slug, nombre)
GENEROS = [
    ('action', 'Acción'), ('adventure', 'Aventura'), ('role-playing-games-rpg', 'RPG'),
    ('strategy', 'Estrategia'), ('shooter', 'Shooter'), ('puzzle', 'Puzzle'),
    ('platformer', 'Plataformas'), ('simulation', 'Simulación'), ('indie', 'Indie'),
    ('racing', 'Carreras'), ('sports', 'Deportes'), ('casual', 'Casual'),
]


def inicio(request):
    contexto = {'animos': services.ANIMOS.values()}
    try:
        contexto['populares'] = services.populares()
        contexto['del_dia'] = services.juego_del_dia()
    except services.RawgError:
        contexto['error_api'] = True
    return render(request, 'games/inicio.html', contexto)


def registro(request):
    if request.user.is_authenticated:
        return redirect('bitacora')

    form = RegistroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'¡Bienvenido a RaleGames, {user.username}! Tu bitácora está lista.')
        return redirect('bitacora')
    return render(request, 'games/registro.html', {'form': form})


def explorar(request):
    texto = request.GET.get('q', '').strip()[:100]
    genero = request.GET.get('genero', '')
    if genero not in dict(GENEROS):
        genero = ''
    try:
        pagina = max(1, int(request.GET.get('pagina', 1)))
    except ValueError:
        pagina = 1

    contexto = {'q': texto, 'genero': genero, 'generos': GENEROS, 'pagina': pagina}
    try:
        contexto.update(services.buscar_juegos(texto, genero, pagina))
    except services.RawgError:
        contexto['error_api'] = True
    return render(request, 'games/explorar.html', contexto)


def juego_detalle(request, juego_id):
    try:
        juego = services.detalle_juego(juego_id)
    except services.RawgError:
        return render(request, 'games/juego.html', {'error_api': True})
    if juego is None:
        raise Http404('Ese juego no existe')

    entrada = None
    if request.user.is_authenticated:
        entrada = Entrada.objects.filter(user=request.user, rawg_id=juego_id).first()
    return render(request, 'games/juego.html', {'juego': juego, 'entrada': entrada})


def ruleta(request):
    # Funciona sin JavaScript (formulario GET); con JS, ruleta.js usa /api/ruleta/
    contexto = {
        'animos': services.ANIMOS.values(),
        'tiempos': [(clave, datos[0]) for clave, datos in services.TIEMPOS.items()],
        'animo': request.GET.get('animo', ''),
        'tiempo': request.GET.get('tiempo', 'cualquiera'),
    }
    if contexto['animo']:
        try:
            contexto['resultado'] = services.girar_ruleta(contexto['animo'], contexto['tiempo'])
            contexto['girado'] = True
        except services.RawgError:
            contexto['error_api'] = True
    return render(request, 'games/ruleta.html', contexto)


@login_required
def bitacora(request):
    entradas = request.user.entradas.all()
    resumen = {clave: 0 for clave, _ in Entrada.ESTADOS}
    for entrada in entradas:
        resumen[entrada.estado] += 1
    horas = sum(e.horas_estimadas for e in entradas if e.estado == 'terminado')

    columnas = [
        {'clave': clave, 'nombre': nombre, 'total': resumen[clave],
         'entradas': [(e, EntradaForm(instance=e, prefix=f'e{e.pk}')) for e in entradas if e.estado == clave]}
        for clave, nombre in Entrada.ESTADOS
    ]
    return render(request, 'games/bitacora.html', {
        'columnas': columnas,
        'total': len(entradas),
        'horas': horas,
    })


@login_required
@require_POST
def agregar_a_bitacora(request, juego_id):
    # Los datos del juego se vuelven a pedir a la API en el servidor;
    # no se confía en títulos o imágenes enviados desde el navegador
    try:
        juego = services.detalle_juego(juego_id)
    except services.RawgError:
        messages.error(request, 'No pudimos conectar con RAWG. Intenta de nuevo en un momento.')
        return redirect('juego', juego_id=juego_id)
    if juego is None:
        raise Http404('Ese juego no existe')

    estado = request.POST.get('estado', 'pendiente')
    if estado not in dict(Entrada.ESTADOS):
        estado = 'pendiente'
    try:
        with transaction.atomic():
            Entrada.objects.create(
                user=request.user, rawg_id=juego_id, titulo=juego['nombre'],
                imagen=juego['imagen'], horas_estimadas=juego['horas'], estado=estado,
            )
        messages.success(request, f'{juego["nombre"]} se agregó a tu bitácora.')
    except IntegrityError:
        messages.info(request, 'Ese juego ya estaba en tu bitácora.')
    return redirect('juego', juego_id=juego_id)


@login_required
@require_POST
def actualizar_entrada(request, pk):
    # Filtrar por user evita que alguien edite la bitácora de otra persona
    entrada = get_object_or_404(Entrada, pk=pk, user=request.user)
    form = EntradaForm(request.POST, instance=entrada, prefix=f'e{pk}')
    if form.is_valid():
        form.save()
        messages.success(request, f'Actualizaste {entrada.titulo}.')
    else:
        messages.error(request, 'Revisa los datos: la calificación va de 1 a 5 estrellas.')
    return redirect('bitacora')


@login_required
@require_POST
def eliminar_entrada(request, pk):
    entrada = get_object_or_404(Entrada, pk=pk, user=request.user)
    entrada.delete()
    messages.success(request, f'Quitaste {entrada.titulo} de tu bitácora.')
    return redirect('bitacora')
