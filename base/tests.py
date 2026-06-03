from datetime import timedelta
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from django.contrib.messages import get_messages
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .enums import EventKind
from .models import Event


class HomeViewUpcomingEventsTests(TestCase):
	def test_homepage_hides_upcoming_events_section_when_no_upcoming_events_exist(self):
		response = self.client.get(reverse('home'))

		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, 'Upcoming Events')
		self.assertEqual(response.context['upcoming_events'], [])

	def test_homepage_shows_only_upcoming_events(self):
		past_event = Event.objects.create(
			title='Past Event',
			description='Already happened.',
			kind=EventKind.WORKSHOP,
			address='Past Address',
			event_date=timezone.now() - timedelta(days=2),
		)
		first_upcoming_event = Event.objects.create(
			title='First Upcoming Event',
			description='This one should appear first.',
			kind=EventKind.BOOK_CLUB,
			address='First Address',
			event_date=timezone.now() + timedelta(days=1),
		)
		second_upcoming_event = Event.objects.create(
			title='Second Upcoming Event',
			description='This one should appear second.',
			kind=EventKind.AUTHOR_TALK,
			address='Second Address',
			event_date=timezone.now() + timedelta(days=3),
		)

		response = self.client.get(reverse('home'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Upcoming Events')
		self.assertContains(response, first_upcoming_event.title)
		self.assertContains(response, second_upcoming_event.title)
		self.assertNotContains(response, past_event.title)
		self.assertContains(response, reverse('event', args=[first_upcoming_event.id]))
		self.assertEqual(
			[event.id for event in response.context['upcoming_events']],
			[first_upcoming_event.id, second_upcoming_event.id],
		)


class LoginRedirectTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='reader', password='password123')

	def test_login_page_preserves_next_parameter_in_hidden_input(self):
		response = self.client.get(reverse('login'), {'next': '/events/1/'})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'type="hidden" name="next" value="/events/1/"')

	def test_login_redirects_to_next_parameter_after_successful_login(self):
		response = self.client.post(reverse('login'), {
			'username': self.user.username,
			'password': 'password123',
			'next': '/events/1/',
		})

		self.assertRedirects(response, '/events/1/', fetch_redirect_response=False)

	def test_login_falls_back_to_dashboard_for_unsafe_next_parameter(self):
		response = self.client.post(reverse('login'), {
			'username': self.user.username,
			'password': 'password123',
			'next': 'https://example.com/elsewhere',
		})

		self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)


class EventInterestAuthTests(TestCase):
	def setUp(self):
		self.event = Event.objects.create(
			title='Library Workshop',
			description='A hands-on event.',
			kind=EventKind.WORKSHOP,
			address='123 Library St',
			event_date=timezone.now() + timedelta(days=1),
		)

	def test_event_page_exposes_login_redirect_for_anonymous_users(self):
		response = self.client.get(reverse('event', args=[self.event.id]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'data-authenticated="false"')
		self.assertContains(response, f'data-login-url="/login/?next=/events/{self.event.id}/"')

	def test_toggle_interest_returns_login_redirect_for_anonymous_users(self):
		response = self.client.post(reverse('express_interest', args=[self.event.id]))

		self.assertEqual(response.status_code, 401)
		self.assertJSONEqual(
			response.content,
			{
				'error': 'User not authenticated',
				'login_url': f'/login/?next=/events/{self.event.id}/',
			},
		)

	def test_toggle_interest_still_works_for_authenticated_users(self):
		user = User.objects.create_user(username='reader', password='password123')
		self.client.force_login(user)

		first_response = self.client.post(reverse('express_interest', args=[self.event.id]))
		second_response = self.client.post(reverse('express_interest', args=[self.event.id]))

		self.assertJSONEqual(first_response.content, {'interested': True})
		self.assertJSONEqual(second_response.content, {'interested': False})
		self.assertFalse(self.event.interested_users.filter(id=user.id).exists())


class NewsletterSubscribeTests(TestCase):
	@patch('base.views.urlopen')
	def test_ajax_submission_returns_success_payload_with_default_message(self, mock_urlopen):
		mock_response = MagicMock()
		mock_response.__enter__.return_value = mock_response
		mock_response.getcode.return_value = 200
		mock_response.read.return_value = b'{"data":{"has_optin":false}}'
		mock_urlopen.return_value = mock_response

		response = self.client.post(
			reverse('newsletter_subscribe'),
			{
				'email': 'reader@example.com',
				'l': 'mailing-list-id',
			},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 200)
		self.assertJSONEqual(
			response.content,
			{
				'data': {'has_optin': False},
				'message': 'Thanks for subscribing!',
			},
		)

	@patch('base.views.urlopen')
	def test_ajax_submission_preserves_upstream_error_message(self, mock_urlopen):
		mock_urlopen.side_effect = HTTPError(
			'https://marketing.uahelp.ca/api/public/subscription',
			400,
			'Bad Request',
			None,
			BytesIO(b'{"message":"Invalid email."}'),
		)

		response = self.client.post(
			reverse('newsletter_subscribe'),
			{
				'email': 'invalid',
				'l': 'mailing-list-id',
			},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest',
		)

		self.assertEqual(response.status_code, 400)
		self.assertJSONEqual(response.content, {'message': 'Invalid email.'})

	@patch('base.views.urlopen')
	def test_standard_submission_redirects_back_with_message(self, mock_urlopen):
		mock_response = MagicMock()
		mock_response.__enter__.return_value = mock_response
		mock_response.getcode.return_value = 200
		mock_response.read.return_value = b'{"data":{"has_optin":false}}'
		mock_urlopen.return_value = mock_response

		response = self.client.post(
			reverse('newsletter_subscribe'),
			{
				'email': 'reader@example.com',
				'l': 'mailing-list-id',
				'next': '/events/',
			},
		)

		self.assertRedirects(response, '/events/', fetch_redirect_response=False)
		self.assertEqual([str(message) for message in get_messages(response.wsgi_request)], ['Thanks for subscribing!'])
