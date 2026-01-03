from django.contrib import admin
from .models import Book, Loan, Member, FeaturedItem, HeroSection
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group

class MyAdminSite(admin.AdminSite):
    site_header = "Ridna Library Admin"
    site_title = "Ridna Library Admin"
    index_title = "Dashboard"

    class Media:
        css = {
            "all": ("admin/custom.css",)
        }

admin_site = MyAdminSite(name="myadmin")

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
    list_display = ['item', 'user', 'loan_date', 'due_date', 'return_date']
    list_filter = ['loan_date', 'due_date', 'return_date']
    search_fields = ['item__title', 'user__username']

admin_site.register(User, UserAdmin)
admin_site.register(Group, GroupAdmin)
admin_site.register(Book, BookAdmin)
admin_site.register(Member, MemberAdmin)
admin_site.register(Loan, LoanAdmin)
admin_site.register(FeaturedItem)
admin_site.register(HeroSection)