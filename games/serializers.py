from rest_framework import serializers

from .models import Entrada


class EntradaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entrada
        fields = ['id', 'rawg_id', 'titulo', 'imagen', 'horas_estimadas', 'estado',
                  'calificacion', 'nota', 'creado', 'actualizado']
        read_only_fields = ['creado', 'actualizado']

    def validate_rawg_id(self, valor):
        user = self.context['request'].user
        repetidas = Entrada.objects.filter(user=user, rawg_id=valor)
        if self.instance:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError('Ese juego ya está en tu bitácora.')
        return valor
