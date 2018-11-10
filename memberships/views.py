from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
# Create your views here.
from django.views.generic import ListView
from django.conf import settings
import stripe
from .models import Membership,UserMembership,Subscription

def profile_view(request):
    user_membership = get_user_membership(request)
    user_subscription = get_user_subscription(request)
    print(user_membership.membership)
    print(user_subscription)
    context = {
        'user_membership' : user_membership,
        'user_subscription' : user_subscription
    }
    return render(request,"memberships/profile.html", context)

def get_user_membership(request):
    user_membership_qs = UserMembership.objects.filter(user=request.user)
    if user_membership_qs.exists():
        return user_membership_qs.first()
    return None

def get_user_subscription(request):
    user_subscription_qs = Subscription.objects.filter(
        user_membership = get_user_membership(request))
    if user_subscription_qs.exists():
        user_subscription = user_subscription_qs.first()
        return user_subscription
    return None

def get_selected_membership(request):
    membership_type = request.session['selected_membership_type']
    selected_membership_qs = Membership.objects.filter(
            membership_type=membership_type)
    if selected_membership_qs.exists():
        return selected_membership_qs.first()
    return None

class MembershipSelectView(ListView):
    model = Membership
    
    def get_context_data(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            context = super().get_context_data(**kwargs)
            current_membership = get_user_membership(self.request)
            context['current_membership'] = str(current_membership.membership)
            return context
        else:
            context = super().get_context_data(**kwargs)
            return context

    def post(self, request, **kwargs):
		user_membership = get_user_membership(request)
		user_subscription = get_user_subscription(request)

		selected_membership_type = request.POST.get('membership_type')

		selected_membership_qs = Membership.objects.filter(
				membership_type=selected_membership_type)
		selected_membership = selected_membership_qs.first()

		if user_membership.membership == selected_membership:
			if user_subscription != None:
				messages.info(request, "You already have this membership. Your \
					next payment is due {}".format('get this value from stripe'))
				return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

		# assign to the session
		request.session['selected_membership_type'] = selected_membership.membership_type

		return HttpResponseRedirect(reverse('memberships:payment'))


def PaymentView(request):
    if request.user.is_authenticated:
        user_membership = get_user_membership(request)

	selected_membership = get_selected_membership(request)

	publishKey = settings.STRIPE_PUBLISHABLE_KEY

	if request.method == "POST":
		try:
			token = request.POST['stripeToken']
			subscription = stripe.Subscription.create(
			  customer=user_membership.stripe_customer_id,
			  items=[
			    {
			      "plan": selected_membership.stripe_plan_id,
			    },
			  ],
			  source=token # 4242424242424242
			)

			return redirect(reverse('memberships:update-transactions',
				kwargs={
					'subscription_id': subscription.id
				}))

		except stripe.error.CardError as e:
			messages.info(request, "Your card has been declined")

    else:
        messages.info(request, 'Please sign in to your account first')
        return redirect('/accounts/login/')
        
    context = {
		'publishKey': publishKey,
		'selected_membership': selected_membership
	}

	return render(request, "memberships/membership_payment.html", context)

def updateTransactions(request,subscription_id):
    
    user_membership = get_user_membership(request)
    selected_membership = get_selected_membership(request)

    user_membership.membership = selected_membership
    user_membership.save() 

    sub, created = Subscription.objects.get_or_create(user_membership=user_membership)
    sub.stripe_subscription_id = subscription_id
    sub.active = True
    sub.save()

    try:
        del request.session['selected_membership_type']
    except:
        pass

    messages.info(request, "Successfully created {} membership".format(selected_membership))
    return redirect('/courses')

def cancelSubscription(request):
    user_sub = get_user_membership(request)

    if user_sub.active == False:
        messages.info(request, "You dont have an active meembership")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    sub = stripe.Subscription.retrieve(user_sub.stripe_subscription_id)
    sub.delete()

    user_sub.active = False
    user_sub.save()

    free_membership = Membership.objects.filter(membership_type='Free').first()
    user_membership = get_user_membership(request)
    user_membership.membership = free_membership
    user_membership.save()

    messages.info(request, "Successfully cancelled membership. We have sent an email")

    return redirect('/memberships')






