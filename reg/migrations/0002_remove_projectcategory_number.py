# Generated by Django 2.0 on 2017-12-18 11:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reg', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='projectcategory',
            name='number',
        ),
    ]
