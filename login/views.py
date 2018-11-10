from django.shortcuts import render

# Create your views here.
#views.py
from login.forms import *
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from memberships.models import Membership,UserMembership,Subscription
from django.urls import reverse
from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout
)
 
@csrf_protect
def register(request):
    if request.user.is_authenticated is False:
        if request.method == 'POST':
            form = RegistrationForm(request.POST)
            if form.is_valid():
                user = User.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1'],
                email=form.cleaned_data['email']
                )
                username=form.cleaned_data['username']
                password=form.cleaned_data['password1']
                new_user = authenticate(username=username, password=password)
                login(request, new_user)

                selected_membership_type = request.POST.get('membership_type')

                selected_membership_qs = Membership.objects.filter(
                    membership_type=selected_membership_type)
                if selected_membership_qs.exists():
                    selected_membership = selected_membership_qs.first()


                request.session['selected_membership_type'] = selected_membership.membership_type
                return HttpResponseRedirect(reverse('memberships:payment'))
                # return HttpResponseRedirect('/accounts/login/')
        else:
            form = RegistrationForm()
            variables =  {
                'form' : form,
                'membership_list' : Membership.objects.all(),
            }
            return render(request, 'registration/register.html', variables)
    else:
        return HttpResponseRedirect('/courses/')
 
def register_success(request):
    return render_to_response(
    'registration/success.html',
    )
 
def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')

def redirect_to_home(request):
    return HttpResponseRedirect('/courses/')