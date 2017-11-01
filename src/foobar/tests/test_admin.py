from django.apps import apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test import TestCase


class TestAdminViews(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username='bananaman',
            email='donkey@kong.com',
            password='hunter2',
        )
        self.client.force_login(self.user)

    def test_admin_views(self):
        for model in apps.get_models():
            if model in admin.site._registry:
                app_label = model._meta.app_label
                model_name = model._meta.model_name
                admin_model = admin.site._registry[model]
                fake_request = type('request', (), {'user': self.user})

                # Add view
                if admin_model.has_add_permission(fake_request):
                    name = 'admin:{app_label}_{model_name}_add'
                    url = reverse(name.format(
                        app_label=app_label,
                        model_name=model_name,
                    ))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)

                # Change view
                if admin_model.has_change_permission(fake_request):
                    name = 'admin:{app_label}_{model_name}_changelist'
                    url = reverse(name.format(
                        app_label=app_label,
                        model_name=model_name,
                    ))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
