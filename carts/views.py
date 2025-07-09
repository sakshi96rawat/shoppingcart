from django.shortcuts import render, redirect, get_object_or_404
from .models import Cart, CartItem
from store.models import Product, Variations
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

def _cart_id(request):
    cart = request.session.session_key
    
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    # get the product
    product = Product.objects.get(id=product_id) 
    product_variations = []

    # get product variation
    if request.method == 'POST':
        # color   = request.POST('color')
        # size    = request.POST('size')
        for item in request.POST:
            key     = item
            value   = request.POST[key]
            print(key, value)
            # check if they match values from the model
            try:
                variation = Variations.objects.get(product=product, variation_category__iexact=key, variation_value__iexact=value)
                product_variations.append(variation)
            except:
                pass
    
    # get the cart
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request)) # get the cart using cart_id present in session
    
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
    cart.save()

    # get the cart items
    is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
    if is_cart_item_exists:
        cart_item = CartItem.objects.filter(product=product, cart=cart)
        
        # existing variation -> from db
        # current variations -> product_variations
        # item id -> db

        # check if curr variation is inside the existing variations
        ex_var_list = []
        var_id = []
        for item in cart_item:
            existing_variations = item.variations.all()
            ex_var_list.append(list(existing_variations))
            var_id.append(item.id)

        if product_variations in ex_var_list:
            # increase cart item quantity
            index = ex_var_list.index(product_variations)
            item_id = var_id[index]

            item = CartItem.objects.get(product=product, cart=cart, id=item_id)
            item.quantity += 1
            item.save()
        else:
            item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if len(product_variations) > 0:
                item.variations.clear()
                item.variations.add(*product_variations)
            item.save()

    else:
        cart_item = CartItem.objects.create(
            product     = product,
            cart        = cart,
            quantity    = 1,
            is_active   = True,
        )

        if len(product_variations) > 0:
            cart_item.variations.clear()
            cart_item.variations.add(*product_variations)
        cart_item.save()

    return redirect('carts') 

def cart(request, total=0, quantity=0, cart_items=None):
    try:
        tax = grand_total = 0
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        tax = (2 * total)/100
        grand_total = total + tax

    except ObjectDoesNotExist:
        pass
    
    context = {
        'cart'       : cart,
        'cart_items' : cart_items,
        'total'      : total,
        'quantity'   : quantity, 
        'tax'        : tax,
        'grand_total': grand_total,
    }

    return render(request, 'store/cart.html', context)

def remove_cart(request, product_id, cart_item_id):
    
    cart        = Cart.objects.get(cart_id=_cart_id(request))
    product     = get_object_or_404(Product, id=product_id)
    
    try:
        cart_item   = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass

    return redirect('carts')

def remove_cart_item(request, product_id, cart_item_id):
    cart        = Cart.objects.get(cart_id=_cart_id(request))
    product     = get_object_or_404(Product, id=product_id)
    cart_item   = CartItem.objects.get(cart=cart, product=product, id=cart_item_id)

    cart_item.delete()
    return redirect('carts')