# Generated by Django 3.2.6 on 2022-06-24 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0004_ustawieniabaselinker'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kategorie',
            name='kategoria_id',
            field=models.CharField(blank=True, max_length=3500, null=True),
        ),
    ]
