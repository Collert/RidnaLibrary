from datetime import date

from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse
from django.utils.functional import SimpleLazyObject

from base.enums import Genre
from base.models import Book

from .enums import InteractionWeight
from .models import Interaction, UserTagScore
from .views import record_interaction


class AnonymousInteractionTests(TestCase):
	def setUp(self):
		self.book = Book.objects.create(
			title='Anonymous-safe item',
			description='Regression fixture for anonymous interaction tracking.',
			published_date=date(1989, 2, 10),
			total_copies=1,
			author='Test Author',
			genre=Genre.FANTASY,
			isbn_number='9780000000002',
		)

	def test_record_interaction_ignores_lazy_anonymous_user(self):
		scores = record_interaction(
			SimpleLazyObject(lambda: AnonymousUser()),
			self.book,
			InteractionWeight.VIEW,
		)

		self.assertEqual(scores, [])
		self.assertFalse(Interaction.objects.exists())
		self.assertFalse(UserTagScore.objects.exists())

	def test_item_view_allows_anonymous_requests_without_creating_interactions(self):
		response = self.client.get(reverse('item', args=[self.book.id]))

		self.assertEqual(response.status_code, 200)
		self.assertFalse(Interaction.objects.exists())
