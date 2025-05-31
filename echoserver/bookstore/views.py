from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Cart, CartItem, Order, Book, OrderItem
from .forms import BookForm, UserRegistrationForm, UserLoginForm, UserProfileForm
from decimal import Decimal
from django.http import JsonResponse

def is_admin(user):
    return user.is_authenticated and user.is_admin()

class BookListView(ListView):
    model = Book
    template_name = 'bookstore/book_list.html'
    context_object_name = 'books'
    paginate_by = 5

    def get_queryset(self):
        return Book.objects.all().order_by('-created_at')

@login_required
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save()
            messages.success(request, 'Книга успешно добавлена!')
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'bookstore/book_form.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            messages.success(request, 'Книга успешно обновлена!')
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'bookstore/book_form.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        messages.success(request, 'Книга успешно удалена!')
        return redirect('book_list')
    return render(request, 'bookstore/book_confirm_delete.html', {'book': book})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Вы успешно зарегистрировались!')
            return redirect('book_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'bookstore/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('book_list')
    else:
        form = UserLoginForm()
    return render(request, 'bookstore/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.info(request, 'Вы вышли из системы.')
    return redirect('book_list')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem, Order, Book
from .forms import UserProfileForm


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'bookstore/profile.html', {'form': form})


@require_POST
def add_to_cart(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    cart = request.session.get('cart', {})
    book_id_str = str(book_id)

    if book_id_str in cart:
        cart[book_id_str]['quantity'] += 1
    else:
        cart[book_id_str] = {
            'quantity': 1,
            'price': str(book.price),
            'title': book.title
        }

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('cart_view')

    request.session['cart'] = cart
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'book_id': book_id,
        'quantity': cart[book_id_str]['quantity'],
        'cart_total': sum(item['quantity'] for item in cart.values())
    })


@login_required
def cart_detail(request):
    try:
        cart = Cart.objects.get(user=request.user)
    except Cart.DoesNotExist:
        cart = Cart.objects.create(user=request.user)

    total = sum(item.book.price * item.quantity for item in cart.items.all())
    return render(request, 'bookstore/cart.html', {
        'cart': cart,
        'total': total
    })


def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0

    for book_id, item in cart.items():
        try:
            book = Book.objects.get(id=book_id)
            quantity = item['quantity']
            price = float(item['price'])
            subtotal = price * quantity

            cart_items.append({
                'book': book,
                'quantity': quantity,
                'price': price,
                'subtotal': subtotal
            })
            total_price += subtotal
        except Book.DoesNotExist:
            continue

    return render(request, 'bookstore/cart.html', {
        'cart_items': cart_items,
        'total_price': total_price
    })


@require_http_methods(["POST"])
@login_required
def remove_from_cart(request, item_id):
    # Получаем ID из URL или из POST данных
    book_id = item_id or request.POST.get('book_id') or request.GET.get('book_id')

    if not book_id:
        messages.error(request, "Не указан ID товара")
        return redirect('cart_view')

    cart = request.session.get('cart', {})
    book_id_str = str(book_id)

    if book_id_str in cart:
        del cart[book_id_str]
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, 'Товар удален из корзины')
    else:
        messages.warning(request, 'Товар не найден в корзине')

    return redirect('cart_view')

@login_required
def checkout(request):
    cart = request.session.get('cart', {})
    if not cart:
        return redirect('cart')

    total = sum(Decimal(item['price']) * item['quantity'] for item in cart.values())
    order = Order.objects.create(
        user=request.user,
        total_price=total,
        status='P'
    )

    for book_id, item in cart.items():
        book = Book.objects.get(pk=book_id)
        order.items.create(
            book=book,
            quantity=item['quantity'],
            price=item['price']
        )

    request.session['cart'] = {}
    return redirect('order_detail', order_id=order.id)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    return render(request, 'bookstore/order_detail.html', {'order': order})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'bookstore/order_list.html', {'orders': orders})

@login_required
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Количество обновлено")
        else:
            cart_item.delete()
            messages.success(request, "Товар удален из корзины")
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Товар удален из корзины")
    return redirect('cart')


def book_list(request):
    books = Book.objects.all()
    cart = request.session.get('cart', {})

    # Добавляем информацию о количестве в корзине для каждой книги
    for book in books:
        book.cart_quantity = cart.get(str(book.id), {}).get('quantity', 0)

    return render(request, 'bookstore/book_list.html', {
        'books': books
    })


# ("adsdasd = %s", [input])
# ("adsdasd = {input}")