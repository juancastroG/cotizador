# Generated by Django 5.1.3 on 2024-12-06 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_estudio_conexion_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='datosexternos',
            name='pct_instalacion',
            field=models.FloatField(default=0.1, help_text='Porcentaje de instalación'),
        ),
        migrations.AddField(
            model_name='datosexternos',
            name='pct_iva',
            field=models.FloatField(default=0.19, help_text='Porcentaje de IVA'),
        ),
    ]
