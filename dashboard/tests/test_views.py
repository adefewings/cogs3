from django.test import TestCase

from users.middleware import SCWRemoteUserMiddleware

# Once we’ve forced a login, never log the session out if headers are missing
SCWRemoteUserMiddleware.force_logout_if_no_header = False

from django.urls import reverse

from institution.models import Institution
from users.models import CustomUser, Profile


class DashboardViewTests(TestCase):
    fixtures = [
        'institution/fixtures/tests/institutions.json',
        'users/fixtures/tests/users.json',
    ]

    def setUp(self):
        self.institution = Institution.objects.get(name='Example University')

        # Approved fixture user
        self.registered_user = CustomUser.objects.get(
            email='shibboleth.user@example.ac.uk'
        )
        self.registered_user.profile.account_status = Profile.APPROVED
        self.registered_user.profile.save()

        # Unapproved user
        self.unregistered_user, _ = CustomUser.objects.get_or_create(
            email=f'unreg@{self.institution.base_domain}',
            defaults={
                'username': f'unreg@{self.institution.base_domain}',
                'is_shibboleth_login_required': True,
            }
        )
        # leave profile.account_status at default (awaiting)

        # Pre‑compute the raw Shibboleth headers for tests
        self.shib_headers = {
            'REMOTE_USER': self.registered_user.email,
            'Shib-Identity-Provider': self.institution.identity_provider,
        }
        self.unreg_headers = {
            'REMOTE_USER': self.unregistered_user.email,
            'Shib-Identity-Provider': self.institution.identity_provider,
        }

    def test_anonymous_redirects_to_login(self):
        r = self.client.get(reverse('home'))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse('login'), r.url)

    def test_registered_user_sees_dashboard(self):
        # 1) Force‑login into session
        self.client.force_login(self.registered_user)

        # 2) GET home *with* Shibboleth headers
        r = self.client.get(reverse('home'), **self.shib_headers)
        self.assertEqual(r.status_code, 200)

    def test_unregistered_user_redirects_to_terms_and_conditions(self):
        self.client.force_login(self.unregistered_user)

        # GET home *with* Shibboleth headers
        r = self.client.get(reverse('home'), **self.unreg_headers)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, reverse('terms-of-service'))

        # 2) Follow into T&C *with headers* so middleware won't log you out
        r2 = self.client.get(reverse('terms-of-service'), **self.unreg_headers)
        self.assertEqual(r2.status_code, 200)
        self.assertTemplateUsed(r2, 'terms_of_service/index.html')

        # 3) Simulate accepting the T&C (POST) *with headers*
        data = {'accepted_terms_and_conditions': True}
        r3 = self.client.post(reverse('terms-of-service'), data, **self.unreg_headers)
        self.assertRedirects(r3, reverse('home'))

