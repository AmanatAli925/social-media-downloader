from django.urls import path

from . import views

urlpatterns=[
	path('', views.index, name='index'),
	path('robots.txt', views.robotstxt, name='robotstxt'),
	path('download-video/<str:site>', views.index),
	path('process/<str:identifier>', views.process, name='process'),
	path('progress/<str:identifier>', views.progress, name='progress'),
	path('BingSiteAuth.xml', views.bingxml, name="bingxml")
]
 
