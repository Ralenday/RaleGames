import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Entrada, Perfil


class RegistroForm(UserCreationForm):
    """Registro con validación en el servidor. El navegador también valida
    (registro.js), pero nunca se confía solo en el lado del cliente."""

    email = forms.EmailField(label='Correo electrónico', max_length=254)
    plataforma = forms.ChoiceField(label='Plataforma favorita', choices=[('', 'Elige una…')] + Perfil.PLATAFORMAS)
    terminos = forms.BooleanField(
        label='Acepto que RaleGames guarde mi bitácora de juegos',
        error_messages={'required': 'Debes aceptar para crear tu cuenta.'},
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {'username': 'Gamertag'}

    def clean_username(self):
        username = self.cleaned_data['username']
        if not re.fullmatch(r'[A-Za-z0-9_]{3,20}', username):
            raise forms.ValidationError('Usa de 3 a 20 caracteres: letras, números o guion bajo.')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('Ese gamertag ya está ocupado.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con ese correo.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Perfil.objects.create(user=user, plataforma=self.cleaned_data['plataforma'])
        return user


class EntradaForm(forms.ModelForm):
    class Meta:
        model = Entrada
        fields = ['estado', 'calificacion', 'nota']
        widgets = {
            'calificacion': forms.Select(choices=[('', 'Sin calificar')] + [(i, '★' * i) for i in range(1, 6)]),
            'nota': forms.TextInput(attrs={'placeholder': 'Una nota corta (opcional)', 'maxlength': 280}),
        }
