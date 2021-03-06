from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User

from my_messages.forms import LoginForm, SignUpForm, LeagueForm
from my_messages.models import League, Invite, Message

@login_required(login_url='/login')
def home_page(request):
    if request.method == 'POST':
        room = request.POST['room']
        username = request.POST['username']
        request.session['username'] = username
        return redirect('chat', permanent=True, room=room)
    return render(request, 'home.html')

@login_required(login_url='/login')
def chat_page(request, room):
    league, created  = League.objects.get_or_create(name=room)
    members = league.members.all()
    if request.user not in members:
        return render(request, 'not_member.html')
    messages = league.messages.all().order_by('-timestamp')
    return render(request, 'chat.html',
            {
                'username': request.user.username,
                'messages': messages,
                'league_name': room,
            }
        )

@login_required(login_url='/login')
def accept_invite(request, invite_id):
    invite = Invite.objects.get(pk=invite_id)
    invite.league.members.add(invite.user)
    invite.delete()
    return redirect('leagues', permanent=True)

class LoginView(View):

    def get(self, request):
        form  = LoginForm()
        return render(request, 'login.html', {'form': form})

    def post(self, request):
        user = request.POST
        user = authenticate(username=user['username'],
                            password=user['password1'])
        login(request, user)
        return redirect('leagues')

class SignUpView(View):

    def get(self, request):
        form = SignUpForm()
        return render(request, 'signup.html', {'form': form})

    def post(self, request):
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('leagues', permanent=True)

class LeagueView(View):

    @method_decorator(login_required(login_url='/login'))
    def get(self, request):
        leagues = request.user.member_of.all()
        form = LeagueForm()
        return render(request, 'leagues.html', {'leagues': leagues, 'form': form})

    @method_decorator(login_required(login_url='/login'))
    def post(self, request):
        form = LeagueForm(request.POST)
        if form.is_valid():
            room = request.POST['name']
            league, created = League.objects.get_or_create(name=room)
            if created:
                league.add_member(request.user)
            return redirect('chat', permanent=True, room=room)

class InviteView(View):

    @method_decorator(login_required(login_url='/login'))
    def get(self, request):
        invites = request.user.invite_set.all()
        return render(request, 'invites.html', {'invites': invites})

    @method_decorator(login_required(login_url='/login'))
    def post(self, request):
        username = request.POST['username']
        invited = User.objects.get(username=username)
        league = League.objects.get(name=request.POST['league_name'])
        invite = Invite.objects.get_or_create(user=invited, league=league)
        return render(request, 'invite_sent.html')
