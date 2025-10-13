# listings/views.py
from urllib.parse import quote
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from .models import Property, Category

# Import LeadForm (single, canonical import)
from .forms import LeadForm

# Optionally support UnitOption if present
try:
    from .models import UnitOption
    HAS_UNITOPTION = True
except Exception:
    HAS_UNITOPTION = False

def about(request):
    return render(request, 'listings/about.html')

def activities(request):
    return render(request, 'listings/activities.html')

def home(request):
    featured = Property.objects.filter(is_featured=True)[:6]
    return render(request, 'listings/home.html', {"featured": featured})


def property_list(request):
    qs = Property.objects.all().order_by('-created_at')

    q    = request.GET.get('q')
    cat  = request.GET.get('cat')
    minp = request.GET.get('minp')
    maxp = request.GET.get('maxp')

    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(location__icontains=q) |
            Q(description__icontains=q)
        )
    if cat:
        qs = qs.filter(category=cat)

    # Price filter works with legacy Property.price or any options__price
    if minp:
        if HAS_UNITOPTION:
            qs = qs.filter(Q(price__gte=minp) | Q(options__price__gte=minp))
        else:
            qs = qs.filter(price__gte=minp)
    if maxp:
        if HAS_UNITOPTION:
            qs = qs.filter(Q(price__lte=maxp) | Q(options__price__lte=maxp))
        else:
            qs = qs.filter(price__lte=maxp)

    qs = qs.distinct()

    paginator = Paginator(qs, 9)
    page = request.GET.get('page')
    properties = paginator.get_page(page)
    return render(request, 'listings/property_list.html', {
        'properties': properties,
        'Category': Category,
        'q': q, 'cat': cat, 'minp': minp, 'maxp': maxp,
    })


# listings/views.py (property_detail)
def property_detail(request, slug):
    obj = get_object_or_404(Property.objects.prefetch_related('options'), slug=slug)

    # Get options in a predictable order (by price; change to -created if you prefer)
    options = list(getattr(obj, 'options').all().order_by('price'))

    selected_option = None
    if HAS_UNITOPTION:
        selected_option_id = request.POST.get('option_id') or request.GET.get('option_id')
        if selected_option_id:
            from .models import UnitOption  # safe import
            try:
                selected_option = UnitOption.objects.get(id=selected_option_id, property=obj)
            except UnitOption.DoesNotExist:
                selected_option = None
        elif options:
            selected_option = options[0]  # preselect first

    form = LeadForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        lead = form.save(commit=False)
        lead.property = obj
        if HAS_UNITOPTION and selected_option:
            lead.option = selected_option
        lead.save()
        return redirect(obj.get_absolute_url())

    from urllib.parse import quote
    whatsapp_number = getattr(settings, 'WHATSAPP_NUMBER', '2347036067548')
    wa_text = f"I'm interested in {obj.title}"
    if selected_option:
        wa_text += f" – {selected_option.get_unit_type_display()}"
    wa_text += f" ({request.build_absolute_uri(obj.get_absolute_url())})"
    whatsapp_link = f"https://wa.me/{whatsapp_number}?text={quote(wa_text)}"

    return render(request, 'listings/property_detail.html', {
        'obj': obj,
        'form': form,
        'whatsapp_link': whatsapp_link,
        'selected_option': selected_option,
        'options': options,               # <-- pass explicitly
    })

