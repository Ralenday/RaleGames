from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


# Perfil gamer: datos extra que se piden en el registro
class Perfil(models.Model):
    PLATAFORMAS = [
        ('pc', 'PC'),
        ('playstation', 'PlayStation'),
        ('xbox', 'Xbox'),
        ('nintendo', 'Nintendo'),
        ('movil', 'Móvil'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    plataforma = models.CharField(max_length=20, choices=PLATAFORMAS, verbose_name='Plataforma favorita')

    def __str__(self):
        return f'{self.user.username} ({self.get_plataforma_display()})'


# Bitácora: los juegos que el usuario guarda desde RAWG con su estado personal
class Entrada(models.Model):
    ESTADOS = [
        ('pendiente', 'Quiero jugarlo'),
        ('jugando', 'Jugando'),
        ('terminado', 'Terminado'),
        ('abandonado', 'Abandonado'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='entradas')
    rawg_id = models.PositiveIntegerField(verbose_name='ID en RAWG')
    titulo = models.CharField(max_length=255)
    imagen = models.URLField(blank=True)
    horas_estimadas = models.PositiveIntegerField(default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    calificacion = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    nota = models.CharField(max_length=280, blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Entrada de bitácora'
        verbose_name_plural = 'Entradas de bitácora'
        ordering = ['-actualizado']
        # Un mismo juego no se puede guardar dos veces por usuario
        constraints = [
            models.UniqueConstraint(fields=['user', 'rawg_id'], name='juego_unico_por_usuario'),
        ]

    def __str__(self):
        return f'{self.titulo} - {self.user.username}'
