from django.db import models

class DatosExternos(models.Model):
    hsp = models.FloatField(help_text="Horas Solar Pico")
    security_factor = models.FloatField(help_text="Factor de seguridad")
    imprevistos = models.FloatField(help_text="Porcentaje para imprevistos")
    material_electrico = models.FloatField(help_text="Costo de material eléctrico")
    certificacion_retie_v1 = models.FloatField(help_text="valor #1 para la operacion de certificación RETIE", default=0)
    certificacion_retie_v2 = models.FloatField(help_text="valor #2 para la operacion de certificación RETIE", default=0)


    class Meta:
        verbose_name = "Datos Externos"
        verbose_name_plural = "Datos Externos"

class Estudio_conexion(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.FloatField()

    def __str__(self):
        return self.nombre

class TipoTeja(models.Model):
    nombre = models.CharField(max_length=100)
    precio_antes_de_iva = models.FloatField()
    imagen = models.ImageField(upload_to='tejas/')

    def __str__(self):
        return self.nombre

class Viaticos(models.Model):
    precio_hospedaje = models.FloatField()
    precio_viaticos = models.FloatField()

    class Meta:
        verbose_name = "Viáticos"
        verbose_name_plural = "Viáticos"

class Ubicacion(models.Model):
    nombre = models.CharField(max_length=100)
    km_desde_medellin = models.FloatField()

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"

    def __str__(self):
        return self.nombre
