from django.views.generic import TemplateView, ListView, DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse, reverse_lazy
from annoying_master.annoying.decorators import ajax_request
from Insta.forms import CustomUserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from Insta.models import Post, Like, InstaUser, UserConnection


class HelloWorld(TemplateView):
    template_name = 'test.html'


class PostsView(ListView):
    model = Post
    template_name = 'index.html'

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Post.objects.all()
        current_user = self.request.user
        following = set()
        for conn in UserConnection.objects.filter(creator=current_user).select_related('following'):
            following.add(conn.following)
        following.add(current_user)
        return Post.objects.filter(author__in=following)


class ExploreView(ListView):
    model = Post
    template_name = 'explore.html'


class PostDetailView(DetailView):
    model = Post
    template_name = 'post_detail.html'


# Login check must be the first class
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'post_create.html'
    fields = '__all__'
    login_url = 'login'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(UpdateView):
    model = Post
    template_name = 'post_update.html'
    fields = ['title', 'image']


class PostDeleteView(DeleteView):
    model = Post
    template_name = 'post_delete.html'
    success_url = reverse_lazy('posts')


class UserDetailView(DetailView):
    model = InstaUser
    template_name = 'user_detail.html'


class UserDetailUpdateView(UpdateView):
    model = InstaUser
    template_name = 'user_detail_update.html'
    fields = ['username', 'profile_pic']


class SignUp(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'signup.html'
    # 在同时要对database操作时，用reverse_lazy
    success_url = reverse_lazy('login')


@ajax_request
def addLike(request):
    post_pk = request.POST.get('post_pk')
    post = Post.objects.get(pk=post_pk)
    try:
        like = Like(post=post, user=request.user)
        like.save()
        result = 1
    except Exception as e:
        like = Like.objects.get(post=post, user=request.user)
        like.delete()
        result = 0

    return {
        'result': result,
        'post_pk': post_pk
    }


@ajax_request
def toggleFollow(request):
    current_user = InstaUser.objects.get(pk=request.user.pk)
    follow_user_pk = request.POST.get('follow_user_pk')
    follow_user = InstaUser.objects.get(pk=follow_user_pk)

    try:
        if current_user != follow_user:
            if request.POST.get('type') == 'follow':
                connection = UserConnection(creator=current_user, following=follow_user)
                connection.save()
            elif request.POST.get('type') == 'unfollow':
                UserConnection.objects.filter(creator=current_user, following=follow_user).delete()
            result = 1
        else:
            result = 0
    except Exception as e:
        print(e)
        result = 0

    return {
        'result': result,
        'type': request.POST.get('type'),
        'follow_user_pk': follow_user_pk
    }
