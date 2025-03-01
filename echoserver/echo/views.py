from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Book
from .forms import BookForm
from django.core.paginator import Paginator


def book_list(request):
    book_objects = Book.objects.all()
    paginator = Paginator(book_objects, 3)
    page = request.GET.get('page')
    books = paginator.get_page(page)
    return render(request, 'echo/book_list.html', {'books': books})


def book_create(request):
    if request.method == "POST":
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'echo/book_form.html', {'form': form})


def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'echo/book_form.html', {'form': form})


def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == "POST":
        book.delete()
        return redirect('book_list')
    return render(request, 'echo/book_confirm_delete.html', {'book': book})

# def homePageView(request):
#     return HttpResponse('Hello, World!')
