# Generated by Django 5.1.2 on 2024-12-15 22:00

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Calificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.TextField(blank=True, null=True)),
                ('calificacion', models.FloatField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Contrato',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('qr_code', models.ImageField(blank=True, upload_to='qrcodes/')),
                ('contract_state', models.CharField(blank=True, choices=[('Por confirmar', 'Por confirmar'), ('Activo', 'Activo'), ('Completado', 'Completado'), ('Cancelado', 'Cancelado')], max_length=100)),
                ('meeting_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Favorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='MediaPublicacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('media', models.FileField(null=True, upload_to='publication/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'mp4', 'mov'])])),
            ],
        ),
        migrations.CreateModel(
            name='Publicacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('publish_name', models.CharField(max_length=100)),
                ('category', models.CharField(choices=[('Tecnologico', 'Tecnologico'), ('Deportes', 'Deportes'), ('Juegos', 'Juegos'), ('Electrodomesticos', 'Electrodomesticos'), ('Automoviles', 'Automoviles'), ('Electrónica', 'Electrónica'), ('Muebles', 'Muebles'), ('Ropa y Accesorios', 'Ropa y Accesorios'), ('Vehículos', 'Vehículos'), ('Inmuebles', 'Inmuebles'), ('Servicios', 'Servicios'), ('Alimentos y Bebidas', 'Alimentos y Bebidas'), ('Salud y Bienestar', 'Salud y Bienestar'), ('Deportes y Ocio', 'Deportes y Ocio'), ('Hogar', 'Hogar'), ('Arte y Entretenimiento', 'Arte y Entretenimiento'), ('Mascotas', 'Mascotas'), ('Jardinería', 'Jardinería'), ('Herramientas y Equipos', 'Herramientas y Equipos'), ('Libros y Literatura', 'Libros y Literatura'), ('Educación y Formación', 'Educación y Formación'), ('Música', 'Música'), ('Viajes y Turismo', 'Viajes y Turismo'), ('Fotografía y Video', 'Fotografía y Video'), ('Coleccionables', 'Coleccionables'), ('Seguros', 'Seguros'), ('Servicios Profesionales', 'Servicios Profesionales')], max_length=100)),
                ('description', models.TextField(blank=True)),
                ('product_condition', models.CharField(blank=True, choices=[('Nuevo', 'Nuevo'), ('Casi nuevo', 'Casi nuevo'), ('Poco uso', 'Poco uso'), ('Usado', 'Usado'), ('Desgastado', 'Desgastado')], default='Usado', max_length=255, null=True)),
                ('publish_state', models.BooleanField(blank=True, default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('publish_type', models.CharField(choices=[('Articulos', 'Articulos'), ('Servicios', 'Servicios'), ('Bienes', 'Bienes')], default='Articulos', max_length=255)),
                ('valor_estimado', models.IntegerField(blank=True, default=0, null=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Reporte',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
