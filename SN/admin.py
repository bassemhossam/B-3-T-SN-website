from django.contrib import admin

# Register your models here.
from . models import SNUser,Post,Like,Comment,Friend
admin.site.register(SNUser)
admin.site.register(Post)
admin.site.register(Like)
admin.site.register(Comment)
admin.site.register(Friend)