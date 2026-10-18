from django.contrib import admin

from .models import Entrada, Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ['user', 'plataforma']


@admin.register(Entrada)
class EntradaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'user', 'estado', 'calificacion', 'actualizado']
    list_filter = ['estado']
    search_fields = ['titulo', 'user__username']
