from django.shortcuts import render, HttpResponse, redirect
from django.conf import settings
from django.views.generic import View, ListView, CreateView
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .forms import RiderRegisterForm, HubManagerRegisterForm
from .models import Account, Rider

class HubManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_hubmanager

class AllUserAccount(HubManagerRequiredMixin, View):

    # model = Account
    template_name = 'accounts/all-users.html'
    def get(self, request, *args, **kwargs):
        rider = Rider.objects.filter(area_location=request.user.area_location)
        return render(request, self.template_name, {'rider': rider})

class LoginView(View):
    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('/')
        template_name = 'accounts/login.html'
        return render(self.request, template_name)
        
    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)

                return redirect('account:login_view')
            else:
                return HttpResponse("Inactive user.")
        else:
            return redirect('account:login_view')

class LogoutView(View): 
    def get(self, *args, **Kwargs):
        logout(self.request)
        return redirect('account:login_view')

class RiderRegisterView(HubManagerRequiredMixin, CreateView):
    template_name = 'accounts/rider-register.html'
    form_class = RiderRegisterForm 
    success_url = reverse_lazy('account:all_users')

    def form_valid(self, form):
        form.instance.is_rider = True
        return super(RiderRegisterView, self).form_valid(form)

class HubManagerRegisterView(HubManagerRequiredMixin, CreateView):
    template_name = 'accounts/hubmanager-register.html'
    form_class = HubManagerRegisterForm 
    success_url = reverse_lazy('account:all_users')

    def form_valid(self, form):
        form.instance.is_hubmanager = True
        return super(HubManagerRegisterView, self).form_valid(form)


def password_reset_request_view(request):
    if request.method == "POST":
        password_reset_form = PasswordResetForm(request.POST)
        if password_reset_form.is_valid():
            data = password_reset_form.cleaned_data['email']
            associated_users = Account.objects.filter(Q(email=data))
            if associated_users.exists():
                for user in associated_users:
                    subject = "Password Reset Requested"
                    email_template_name = "password_reset/password_reset_email.html"
                    site = get_current_site(request)
                    messages_ = {
                        "email":user.email,
					    'domain': site.domain, 
					    'site_name': 'Website',
					    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
					    "user": user,
					    'token': default_token_generator.make_token(user),
					    'protocol': 'http',
					}
                    email = render_to_string(email_template_name, messages_)
                    from_email = settings.EMAIL_HOST_USER
                    try:
                        send_mail(subject, email, from_email , [user.email], fail_silently=False)
                        return redirect('/')
                    except BadHeaderError:
                        return HttpResponse('Invalid header found.')
                        return redirect ("/password_reset/done/")
    password_reset_form = PasswordResetForm()
    return render(request=request, template_name="password_reset/password_reset.html", context={"password_reset_form":password_reset_form})