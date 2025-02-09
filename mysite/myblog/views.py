from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator

from .models import Post

def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, status = Post.Status.PUBLISHED, 
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)                   
    return render(request, 'myblog/post/detail.html', {'post': post})


def post_list(request):
    post_list = Post.published.all()
    #Построчная разбивка с 5 постами на страницу
    paginator = Paginator(post_list, 5)
    page_number = request.GET.get('page', 1)
    posts = paginator.page(page_number)
    return render(request, 'myblog/post/list.html', {'posts': posts})