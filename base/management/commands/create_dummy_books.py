from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random
from faker import Faker
from base.models import Book
from base.enums import Genre, Language, Theme, Tone, Audience, LanguageLevel

class Command(BaseCommand):
    help = 'Create dummy book data for the library'
    
    def __init__(self):
        super().__init__()
        self.fake = Faker(['en_US', 'fr_FR', 'uk_UA'])
        
    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=25,
            help='Number of books to create (default: 25)'
        )
    
    def handle(self, *args, **options):
        count = options['count']
        
        # Pre-defined book data for more realistic titles and authors
        book_templates = [
            {"title": "The Silent Garden", "author": "Elena Rodriguez", "genre": Genre.MYSTERY},
            {"title": "Quantum Dreams", "author": "Dr. Michael Chen", "genre": Genre.SCIFI},
            {"title": "Hearts of the Valley", "author": "Sarah Williams", "genre": Genre.ROMANCE},
            {"title": "The Last Kingdom's Shadow", "author": "Alexander Stone", "genre": Genre.FANTASY},
            {"title": "Midnight in Paris", "author": "Claire Dubois", "genre": Genre.CONTEMPORARY},
            {"title": "The Digital Revolution", "author": "James Patterson", "genre": Genre.TECHNOLOGY},
            {"title": "Cooking with Love", "author": "Maria Gonzalez", "genre": Genre.COOKING},
            {"title": "The Art of War Revisited", "author": "General Thompson", "genre": Genre.HISTORY},
            {"title": "Children of Tomorrow", "author": "Anna Johnson", "genre": Genre.CHILDREN},
            {"title": "The Philosopher's Mind", "author": "Dr. Richard Barnes", "genre": Genre.PHILOSOPHY},
            {"title": "Ocean's Secrets", "author": "Captain Morgan", "genre": Genre.ADVENTURE},
            {"title": "The Healing Path", "author": "Dr. Lisa Chang", "genre": Genre.HEALTH},
            {"title": "Business Empire", "author": "Robert Mills", "genre": Genre.BUSINESS},
            {"title": "Songs of the Heart", "author": "Emily Frost", "genre": Genre.POETRY},
            {"title": "The Time Traveler's Guide", "author": "Professor Smith", "genre": Genre.SCIFI},
            {"title": "Shadows of the Past", "author": "Detective Brown", "genre": Genre.CRIME},
            {"title": "Love in the Digital Age", "author": "Jennifer Walsh", "genre": Genre.CONTEMPORARY},
            {"title": "The Magic Portal", "author": "Wizard Blackwood", "genre": Genre.FANTASY},
            {"title": "Understanding the Mind", "author": "Dr. Psychology", "genre": Genre.PSYCHOLOGY},
            {"title": "The Great Adventure", "author": "Explorer Jones", "genre": Genre.ADVENTURE},
            {"title": "Mysteries of Ancient Rome", "author": "Professor Davis", "genre": Genre.HISTORY},
            {"title": "The Young Hero's Journey", "author": "Teen Writer", "genre": Genre.YOUNG_ADULT},
            {"title": "Laughter and Life", "author": "Comedy King", "genre": Genre.HUMOR},
            {"title": "The Artist's Vision", "author": "Painter Green", "genre": Genre.ARTS},
            {"title": "Travel the World", "author": "Globe Trotter", "genre": Genre.TRAVEL},
        ]
        
        created_books = []
        
        for i in range(count):
            template = book_templates[i % len(book_templates)]
            
            # Generate unique title variation
            title_suffix = f" - Volume {i // len(book_templates) + 1}" if i >= len(book_templates) else ""
            title = template["title"] + title_suffix
            
            # Generate French and Ukrainian translations (simplified)
            title_fr = self.fake.catch_phrase() if random.choice([True, False]) else ""
            title_uk = self.fake.catch_phrase() if random.choice([True, False]) else ""
            
            # Generate description
            description = self.fake.paragraph(nb_sentences=random.randint(3, 8))
            description_fr = self.fake.paragraph(nb_sentences=random.randint(2, 5)) if title_fr else ""
            description_uk = self.fake.paragraph(nb_sentences=random.randint(2, 5)) if title_uk else ""
            
            # Author variations
            author_variations = [
                template["author"],
                f"{self.fake.first_name()} {template['author'].split()[-1]}",
                f"{template['author'].split()[0]} {self.fake.last_name()}"
            ]
            author = random.choice(author_variations)
            author_fr = f"{self.fake.first_name()} {self.fake.last_name()}" if title_fr else ""
            author_uk = f"{self.fake.first_name()} {self.fake.last_name()}" if title_uk else ""
            
            # Generate publication date (within last 50 years)
            start_date = date.today() - timedelta(days=50*365)
            end_date = date.today()
            published_date = self.fake.date_between(start_date=start_date, end_date=end_date)
            
            # Random ISBN (simplified - just 13 digits)
            isbn = ''.join([str(random.randint(0, 9)) for _ in range(13)])
            
            # Random choices from enums
            genre = template["genre"]
            theme = random.choice([choice[0] for choice in Theme.choices])
            audience = random.choice([choice[0] for choice in Audience.choices])
            tone = random.choice([choice[0] for choice in Tone.choices])
            language = random.choice([choice[0] for choice in Language.choices])
            language_level = random.choice([choice[0] for choice in LanguageLevel.choices])
            
            # Random copies count (1-5)
            total_copies = random.randint(1, 5)
            
            try:
                book = Book.objects.create(
                    title=title,
                    description=description,
                    title_fr=title_fr,
                    description_fr=description_fr,
                    title_uk=title_uk,
                    description_uk=description_uk,
                    published_date=published_date,
                    total_copies=total_copies,
                    author=author,
                    author_fr=author_fr,
                    author_uk=author_uk,
                    genre=genre,
                    theme=theme,
                    audience=audience,
                    tone=tone,
                    language=language,
                    language_level=language_level,
                    isbn_number=isbn
                )
                created_books.append(book)
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create book {title}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {len(created_books)} books')
        )
        
        # Display some stats
        if created_books:
            self.stdout.write("\\nCreated books summary:")
            for book in created_books[:10]:  # Show first 10
                self.stdout.write(f"  - {book.title} by {book.author} ({book.genre})")
            if len(created_books) > 10:
                self.stdout.write(f"  ... and {len(created_books) - 10} more books")