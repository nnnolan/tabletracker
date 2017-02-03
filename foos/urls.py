from django.conf.urls import url

from . import views

app_name = 'foos'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^game/new/$', views.new_game, name='new_game'),
    url(r'^player/(?P<player_id>[0-9]+)/$', views.player, name='player'),
]
