# Generated by Django 3.2.6 on 2022-06-18 21:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_ustawieniastan_nazwa'),
    ]

    operations = [
        migrations.CreateModel(
            name='UstawieniaBaselinker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nazwa', models.CharField(blank=True, max_length=200, null=True)),
                ('token', models.CharField(blank=True, max_length=200, null=True)),
                ('inventory_id', models.IntegerField(blank=True, null=True)),
            ],
        ),
    ]
