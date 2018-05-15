from django.views import generic
from .models import SNUser, Post, Friend, Like, Comment
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib.auth import authenticate, login
from django.views.generic import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .forms import SNUserForm, AddPostForm, AddCommentForm
from django.shortcuts import render, redirect, get_object_or_404,Http404
from django.db.models import Count, Max
from itertools import chain
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import SNUserSerializer, PostSerializer
from rest_framework import status
from django.contrib.auth import views as auth_views
from django.http import   HttpResponseRedirect
import os

def ProfileView(request, pk=None):
    if request.user.is_anonymous is True:
        return redirect('SN:login')
    if pk:
        friendsobject, created = Friend.objects.get_or_create(current_user=request.user)
        snuser = SNUser.objects.get(pk=pk)
        if created == False:
            current_user_friend = friendsobject.friends.all()
            if snuser in current_user_friend:
                addremove = "Remove"
            else:
                addremove = "Add"
        else:
            addremove = "Add"
        return render(request, 'SN/profile.html', {'snuser': snuser, 'addremove': addremove, 'current_user':request.user})
    else:
        return


def MyProfileView(request):
    if request.user.is_anonymous is True:
        return redirect('SN:login')

    snuser = request.user

    return render(request, 'SN/profile.html', {'snuser': snuser,'current_user':request.user})


# user
class UserFormView(View):
    template_name = 'SN/registration_form.html'
    form_class = SNUserForm

    # display blank form for signup

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    # process form data
    def post(self, request):

        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():

            user = form.save(commit=False)

            # clean data
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()

            # return user object if credentials are correct
            user = authenticate(username=username, password=password)

            if user is not None:

                if user.is_active:
                    login(request, user)
                    return redirect('SN:home')

        return render(request, self.template_name, {'form': form})


class UserUpdate(UpdateView):
    model = SNUser
    fields = ['first_name', 'last_name', 'username', 'profile_pic', 'birth_date', 'gender']
    success_url = reverse_lazy('SN:myprofile')


class UserDelete(DeleteView):
    model = SNUser
    success_url = reverse_lazy('SN:login')


# user


def home(request):

    if request.user.is_anonymous is True:
        return redirect('SN:login')
    if request.user.is_superuser is True:
        allposts = Post.objects.all()
        template = 'SN/home.html'
        form = AddCommentForm(request.POST)
        context = {'logged_in_user_posts': allposts, 'currentuser' :request.user, 'form' :form}
        return render(request, template, context)

    logged_in_user = request.user
    current_user_posts = Post.objects.filter(owner=logged_in_user)  # this user's posts only
    friends_posts = []
    friend_obj = Friend.objects.filter(current_user=logged_in_user)  # all friends of logged-in user
    queryset = SNUser.objects.none()

    for current_friends in friend_obj.all():
        for current_friend in current_friends.friends.all():
            for post in Post.objects.filter(owner=current_friend.pk):
                friends_posts.append(post)

    for this_post in current_user_posts:
        if Like.objects.filter(owner=request.user, post=this_post):
            this_post.current_user_like = True
        else:
            this_post.current_user_like = False

    for this_post in friends_posts:
        if Like.objects.filter(owner=request.user, post=this_post):
            this_post.current_user_like = True
        else:
            this_post.current_user_like = False

    # suggested friends part
    friend, create = Friend.objects.get_or_create(current_user=request.user)
    if create == False:
        friendss = friend.friends.all()
        queryset = SNUser.objects.none()

        for frienduser in friendss:
            friendobject, create = Friend.objects.get_or_create(current_user=frienduser)
            if create == False:
                queryset = queryset | friendobject.friends.all()

        friendsoffriends = queryset.exclude(id__in=friendss).exclude(id=request.user.id)
    else:
        friendsoffriends=[]
    # suggested friends part
    template = 'SN/home.html'
    form = AddCommentForm(request.POST)
    context = {'logged_in_user_posts': current_user_posts, 'friends_posts': friends_posts, 'form': form
               , 'friendsoffriends': friendsoffriends, 'currentuser': request.user}
    return render(request, template, context)


# post
class Addpostview(View):

    template_name = 'SN/post_form.html'
    form_class = AddPostForm

    # display blank form for signup

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form': form})

    # process form data
    def post(self, request):
        #  if not request.user.is_authenticated():
        # return render(request, 'SN/login.html')
        # return
        # else:
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            post = form.save(commit=False)
            post.owner = request.user
            # post.photo = request.FILES['photo']
            post.save()
            return redirect('SN:home')
    # return render(request, self.template_name, {'form': form})


def add_comment_to_post(request, pk):
    if request.user.is_anonymous is True:
        return redirect('SN:login')
    this_post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = AddCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = this_post
            comment.owner = request.user
            comment.save()
            return redirect('SN:post_details', pk=pk)
    return redirect('SN:post_details', pk=pk)


def change_like_post(request, operation, pk):
    if request.user.is_anonymous is True:
        return redirect('SN:login')
    this_post = get_object_or_404(Post, pk=pk)
    if operation == 'Like':
        Like.objects.create(post=this_post, owner=request.user)

    elif operation == 'Unlike':
        Like.objects.filter(owner=request.user, post=this_post).delete()

    return redirect('SN:home')


# post


# friend
def FriendsView(request):
    if request.user.is_anonymous is True:
        return redirect('SN:login')
    friend, create = Friend.objects.get_or_create(current_user=request.user)
    if create == False:
        friendss = friend.friends.all()
        queryset = SNUser.objects.none()

        for frienduser in friendss:
            friendobject, create = Friend.objects.get_or_create(current_user=frienduser)
            if create == False:
               queryset = queryset | friendobject.friends.all()

        friendsoffriends = queryset.exclude(id__in=friendss).exclude(id=request.user.id)
    else:
        friendss = None
    followers = []
    allfriendobjects=Friend.objects.all()
    for friendobj in allfriendobjects:
        if request.user in friendobj.friends.all():
            followers.append(friendobj.current_user)

    return render(request, 'SN/friends.html', {'friendss': friendss, 'friendsoffriends': friendsoffriends,'followers': followers})



def change_friends(request, operation, pk):
    if request.user.is_anonymous is True:
        return redirect('SN:login')
    friend = SNUser.objects.get(pk=pk)
    if operation == 'Add':
        Friend.make_friend(request.user, friend)
    elif operation == 'Remove':
        Friend.lose_friend(request.user, friend)
    return redirect('SN:friends')


# friend

def post_details(request, pk):
    if request.user.is_anonymous is True:
        return redirect('SN:login')
    this_post = get_object_or_404(Post, pk=pk)
    template = 'SN/post_details.html'
    fileName, fileExtension = os.path.splitext(this_post.photo.name)
    form = AddCommentForm(request.POST)
    context = {'this_post': this_post, 'form': form,'fileextension':fileExtension,'currentuser':request.user}
    return render(request, template, context)


def graph(request):
    if request.user.is_anonymous is True:
        return redirect('SN:login')
    if request.user.is_superuser is False:
        return redirect('/admin/')

    all_users = SNUser.objects.all()
    all_relationships = Friend.objects.all()
    context = {'all_users': all_users, 'all_friends': all_relationships}
    template = 'SN/graph.html'
    return render(request, template, context)


# Search
def search(request):
    if request.user.is_anonymous is True:
        return redirect('SN:login')
    template = 'SN/search_results.html'
    q = request.GET['q']
    search_result = SNUser.objects.filter(first_name__icontains=q) | SNUser.objects.filter(last_name__icontains=q)
    return render(request, template, {'search_result': search_result, 'q': q})


def analysis(request):
    if request.user.is_anonymous is True:
        return redirect('SN:login')
    postswithlikes = Post.objects.annotate(like_count=Count('like'))
    maxnlikes = postswithlikes.aggregate(maxlikes=Max('like_count'))
    nmaxlikes=maxnlikes['maxlikes']
    postwithmaxlikes = postswithlikes.filter(like_count=nmaxlikes).first()

    postswithcomments = Post.objects.annotate(comments_count=Count('comments'))
    maxncomments = postswithcomments.aggregate(maxcomments=Max('comments_count'))
    nmaxcomments = maxncomments['maxcomments']
    postwithmaxcomments = postswithcomments.filter(comments_count=nmaxcomments).first()

    userswithlikes = SNUser.objects.annotate(userlike_count=Count('likes'))
    maxuserlikes = userswithlikes.aggregate(maxuser_likes=Max('userlike_count'))
    nmaxuserlikes = maxuserlikes['maxuser_likes']
    userwithmaxlikes = userswithlikes.filter(userlike_count=nmaxuserlikes).first()

    userswithcomments= SNUser.objects.annotate(usercomments_count=Count('usercomments'))
    maxusercomments = userswithcomments.aggregate(maxuser_comments=Max('usercomments_count'))
    nmaxusercomments = maxusercomments['maxuser_comments']
    userwithmaxcomments = userswithcomments.filter(usercomments_count=nmaxusercomments).first()


    friendswithcount = Friend.objects.annotate(friendscount=Count('friends'))
    maxfriendscount = friendswithcount.aggregate(maxfriendcount=Max('friendscount'))
    nmaxfirendscount = maxfriendscount['maxfriendcount']
    userwithmaxfriends =friendswithcount.filter(friendscount=nmaxfirendscount).first().current_user


    userswithposts= SNUser.objects.annotate(posts_count=Count('posts'))
    maxuserposts = userswithposts.aggregate(maxuser_posts=Max('posts_count'))
    nmaxuserposts = maxuserposts['maxuser_posts']
    userwithmaxposts = userswithposts.filter(posts_count=nmaxuserposts).first()

    allfriendobjects = Friend.objects.all()
    maxfollowersuser=[]
    maxfollowerscount = 0
    for thisuser in SNUser.objects.all():
        followerscount = 0
        for friendobj in allfriendobjects:
            if thisuser in friendobj.friends.all():
                followerscount += 1
        if followerscount > maxfollowerscount:
            maxfollowersuser = thisuser
            maxfollowerscount = followerscount

    context = {'maxlikes': nmaxlikes, 'mlpost': postwithmaxlikes
               , 'maxcomments': nmaxcomments, 'mcpost': postwithmaxcomments
               , 'maxuserlikes': nmaxuserlikes, 'maxlikesuser': userwithmaxlikes
               , 'maxusercomments': nmaxusercomments, 'maxcommentsuser': userwithmaxcomments
               , 'maxuserposts': nmaxuserposts, 'maxpostsuser': userwithmaxposts
               , 'maxfriends': nmaxfirendscount, 'userwithmaxfriends': userwithmaxfriends
               , 'maxfollowersuser': maxfollowersuser ,'maxfollowerscount': maxfollowerscount}

    template = 'SN/analysis.html'
    return render(request, template, context)



#xml
class UsersList(APIView):

    def get(self,request):
        userslist = SNUser.objects.all()
        serializer = SNUserSerializer(userslist, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = SNUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SNUserDetail(APIView):
    def get_object(self, pk):
        try:
            return SNUser.objects.get(pk=pk)
        except SNUser.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        snippet = self.get_object(pk)
        serializer = SNUserSerializer(snippet)
        return Response(serializer.data)

    def put(self, request, pk):
        snippet = self.get_object(pk)
        serializer = SNUserSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        snippet = self.get_object(pk)
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostsList(APIView):

    def get(self,request):
        postslist = Post.objects.all()
        serializer = PostSerializer(postslist, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PostSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PostDetail(APIView):
    def get_object(self, pk):
        try:
            return Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        snippet = self.get_object(pk)
        serializer = PostSerializer(snippet)
        return Response(serializer.data)

    def put(self, request, pk):
        snippet = self.get_object(pk)
        serializer = PostSerializer(snippet, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        snippet = self.get_object(pk)
        snippet.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PostUpdate(UpdateView):
    model = Post
    fields = ['text', 'photo']
    success_url = reverse_lazy('SN:home')


class PostDelete(DeleteView):
    model = Post
    success_url = reverse_lazy("SN:home")


class CommentDelete(DeleteView):
    model = Comment
    success_url = reverse_lazy("SN:home")