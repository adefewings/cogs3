# users/tests/test_middleware.py

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

from institution.models import Institution
from users.middleware import SCWRemoteUserMiddleware
from users.models import CustomUser, Profile


class ShibMiddlewareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        # Pass a no‑op get_response to both middleware
        self.session_mw = SessionMiddleware(get_response=lambda r: None)
        self.auth_mw    = AuthenticationMiddleware(get_response=lambda r: None)
        self.shib_mw    = SCWRemoteUserMiddleware(get_response=lambda r: None)

        self.institution = Institution.objects.create(
            name="X Uni", base_domain="x.ac.uk",
            identity_provider="https://idp.x.ac.uk/shibboleth",
            academic=True, commercial=False, service_provider=True,
        )
        self.user = CustomUser.objects.create_user(
            username=f"user@{self.institution.base_domain}",
            email=f"user@{self.institution.base_domain}",
            is_shibboleth_login_required=True,
        )
        self.user.profile.account_status = Profile.APPROVED
        self.user.profile.save()

    def _apply_all_middleware(self, request):
        # Sessions first
        self.session_mw.process_request(request)
        request.session.save()
        # Auth second
        self.auth_mw.process_request(request)
        return request

    def test_middleware_logs_in_registered_user(self):
        req = self.factory.get(
            reverse('home'),
            **{
                'REMOTE_USER': self.user.username,
                'Shib-Identity-Provider': self.institution.identity_provider,
            }
        )
        req = self._apply_all_middleware(req)
        resp = self.shib_mw.process_request(req)

        # After middleware, request.user should be our user
        from django.contrib.auth import get_user
        self.assertEqual(get_user(req), self.user)
        self.assertIsNone(resp)  # no redirect

    def test_middleware_redirects_unregistered_user(self):
        bad_email = f"new@{self.institution.base_domain}"
        req = self.factory.get(
            reverse('home'),
            **{
                'REMOTE_USER': bad_email,
                'Shib-Identity-Provider': self.institution.identity_provider,
            }
        )
        req = self._apply_all_middleware(req)
        resp = self.shib_mw.process_request(req)

        # Should get an HttpResponseRedirect to register
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], reverse('register'))
