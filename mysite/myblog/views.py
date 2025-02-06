from django.shortcuts import render, get_object_or_404
from django.http import Http404

from .models import Post

def post_detail(request, id):
    post = get_object_or_404(Post, id=id, status = Post.Status.PUBLISHED)                   
    return render(request, 'myblog/post/detail.html', {'post': post})


def post_list(request):
    posts = Post.published.all()
    return render(request, 'myblog/post/list.html', {'posts': posts})