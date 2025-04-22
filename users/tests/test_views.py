
from django.test import TestCase
from users.middleware import SCWRemoteUserMiddleware

# Don’t log out force‑logged tokens just because headers are missing:
SCWRemoteUserMiddleware.force_logout_if_no_header = False

from django.urls import reverse
from institution.models import Institution
from users.models import CustomUser
from users.models import Profile
from users.views import RegisterView


class RegisterViewTests(TestCase):
    fixtures = [
        'institution/fixtures/tests/institutions.json',
        'users/fixtures/tests/users.json',
    ]

    def setUp(self):
        # Load the example institution
        self.inst = Institution.objects.get(name='Example University')
        # An approved fixture user
        self.registered = CustomUser.objects.get(
            email='shibboleth.user@example.ac.uk'
        )
        self.registered.profile.account_status = Profile.APPROVED
        self.registered.profile.save()
        # A fresh email for registration tests
        self.new_email = f'unreg@{self.inst.base_domain}'

    def seed_shib_session(self, email):
        """Helper to simulate SSO middleware by seeding session['shib']"""
        session = self.client.session
        session['shib'] = {'username': email}
        session.save()

    def test_register_view_as_an_authorised_application_user(self):
        """An already‑approved user with a shib session is sent to home."""
        # Seed SSO metadata and login
        self.seed_shib_session(self.registered.email)
        self.client.force_login(self.registered)
        # Now hitting /register/ should see dispatch redirect to home
        resp = self.client.get(reverse('register'))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('home'))

    def test_unregistered_renders_form_and_post(self):
        """An unapproved user with a shib session sees form and can post → login."""
        # Seed SSO metadata only
        self.seed_shib_session(self.new_email)
        # GET form
        resp = self.client.get(reverse('register'))
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'registration/register.html')
        # POST form data
        form_data = {
            'first_name': 'Alice',
            'last_name': 'Anderson',
            'reason_for_account': 'Testing',
            'accepted_terms_and_conditions': True,
        }
        post = self.client.post(reverse('register'), form_data)
        self.assertEqual(post.status_code, 302)
        self.assertEqual(post.url, reverse('login'))



class LoginViewTests(TestCase):

    fixtures = RegisterViewTests.fixtures

    def setUp(self):
        self.institution = Institution.objects.get(name='Example University')
        # Approved fixture user
        self.authorised = CustomUser.objects.get(
            email='shibboleth.user@example.ac.uk'
        )
        self.authorised.profile.account_status = Profile.APPROVED
        self.authorised.profile.save()

        # Unauthorised = not approved (awaiting)
        self.unauthorised, _ = CustomUser.objects.get_or_create(
            email=f'unreg@{self.institution.base_domain}',
            defaults={
                'username': f'unreg@{self.institution.base_domain}',
                'is_shibboleth_login_required': True
            }
        )
        # Pre-compute raw headers
        self.auth_headers = {
            'REMOTE_USER': self.authorised.email,
            'Shib-Identity-Provider': self.institution.identity_provider,
        }
        self.unreg_headers = {
            'REMOTE_USER': self.unauthorised.email,
            'Shib-Identity-Provider': self.institution.identity_provider,
        }

    def test_login_view_as_an_authorised_user(self):
        """A session‑logged approved user hitting /login/ gets sent to home."""
        self.client.force_login(self.authorised)
        resp = self.client.get(reverse('login'), **self.auth_headers)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('home'))

    def test_login_view_as_an_unauthorised_user(self):
        """A session‑logged unapproved user hitting /login/ gets sent to register."""
        self.client.force_login(self.unauthorised)
        resp = self.client.get(reverse('login'), **self.unreg_headers)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('terms-of-service'))



class LogoutViewTests(TestCase):

    fixtures = RegisterViewTests.fixtures

    def setUp(self):
        self.institution = Institution.objects.get(name='Example University')
        # reuse authorised / unauthorised from above
        self.registered = CustomUser.objects.get(
            email='shibboleth.user@example.ac.uk'
        )
        self.registered.profile.account_status = Profile.APPROVED
        self.registered.profile.save()

        self.unregistered, _ = CustomUser.objects.get_or_create(
            email=f'unreg@{self.institution.base_domain}',
            defaults={
                'username': f'unreg@{self.institution.base_domain}',
                'is_shibboleth_login_required': True
            }
        )
        # Pre-compute raw headers
        self.reg_headers = {
            'REMOTE_USER': self.registered.email,
            'Shib-Identity-Provider': self.institution.identity_provider,
        }
        self.unreg_headers = {
            'REMOTE_USER': self.unregistered.email,
            'Shib-Identity-Provider': self.institution.identity_provider,
        }

    def test_logout_view_as_an_authorised_user(self):
        """An approved user can log out and lands on logged_out."""
        self.client.force_login(self.registered)
        resp = self.client.get(reverse('logout'), **self.reg_headers)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('logged_out'))

    def test_logout_view_as_an_unauthorised_user(self):
        """An unapproved user hitting /logout/ gets sent to logged_out."""
        self.client.force_login(self.unregistered)
        resp = self.client.get(reverse('logout'), **self.unreg_headers)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse('logged_out'))
