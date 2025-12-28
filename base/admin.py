from django.contrib import admin
from .models import Book, Loan, Member, FeaturedItem, HeroSection

class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'published_date', 'added_date', 'isbn_number']
    list_filter = ['author', 'published_date', 'added_date']
    search_fields = ['title', 'author', 'isbn_number']
    readonly_fields = ['added_date']

class MemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'join_date']
    list_filter = ['join_date']
    readonly_fields = ['join_date']

class LoanAdmin(admin.ModelAdmin):
    list_display = ['item', 'member', 'loan_date', 'due_date', 'return_date']
    list_filter = ['loan_date', 'due_date', 'return_date']
    search_fields = ['item__title', 'member__user__username']

admin.site.register(Book, BookAdmin)
admin.site.register(Member, MemberAdmin)
admin.site.register(Loan, LoanAdmin)
admin.site.register(FeaturedItem)
admin.site.register(HeroSection)

# Register your models here.
