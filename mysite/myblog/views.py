from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from django.views.generic import ListView
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.contrib.postgres.search import (SearchVector, SearchQuery, 
                                            SearchRank, TrigramSimilarity)
from taggit.models import Tag

from .models import Post, Comment
from .forms import EmailPostForm, CommentForm, SearchForm

def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])
    #Построчная разбивка с 5 постами на страницу
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        #Если page_number не целое число, то выдать первую страницу
        posts = paginator.page(1)
    except EmptyPage:
        #Если page_number находится вне диапазона, то выдать последнюю страницу
        posts = paginator.page(paginator.num_pages)
    return render(request, 'myblog/post/list.html', {'posts': posts, 'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, status = Post.Status.PUBLISHED, 
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    #Список активных комментариев к этому посту
    comments = post.comments.filter(active=True)
    #Форма для комментирования пользователями
    form = CommentForm()

    #Список схожих постов
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]                   
    return render(request, 'myblog/post/detail.html', {'post': post, 'comments': comments, 
                                                       'form': form, 'similar_posts': similar_posts})

class PostListView(ListView):
    """
    Альтернативное представление списка постов
    """
    queryset = Post.published.all()
    context_object_name='posts'
    paginate_by = 5
    template_name = 'myblog/post/list.html'

def post_share(request, post_id):
    #Извлечь пост по идентификатору id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':
        #Форма была передана на обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():
            #Поля формы успешно прошли валидацию
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'your_account@gmail.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'myblog/post/share.html', {'post': post, 'form': form, 'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    #Комментарий был отправлен
    form = CommentForm(data=request.POST)
    if form.is_valid():
        #Создать объект класса Comment, не сохраняя его в базе данных
        comment = form.save(commit=False)
        #Назначить пост комментарию
        comment.post = post
        #Сохранить комментарий в базе данных
        comment.save()
    return render(request, 'myblog/post/comment.html', {'post': post, 'form': form, 'comment' : comment})


def post_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Post.published.annotate(
                similarity=TrigramSimilarity('title', query),
            ).filter(similarity__gt=0.1).order_by('-similarity')
    return render(request, 'myblog/post/search.html', {'form': form, 'query': query, 'results': results})
