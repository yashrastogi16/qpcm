
from django.http import *
from django.template.loader import get_template
from django.template import Context, RequestContext
from django.utils.decorators import method_decorator
from django.shortcuts import render_to_response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView, View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User, Group, Permission
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import unittest
from qpcmms.forms import *
from qpcmms.models import *
from django.db.models import Count, Min, Sum, Max, Avg
from django.db import connection
import random, logging
import functools
from functools import wraps
from django.core.context_processors import csrf
import base64

from django.conf import settings



def render_template(request, template, data=None):
    errs =""
    if request.method == 'GET' and 'err' in request.GET:
        data.update({'errs':request.GET['err']})

    data.update({'STATIC_URL': settings.STATIC_URL})
    response = render_to_response(template, data,
                              context_instance=RequestContext(request))
    return response

def render_email(template, data=None):

  html = get_template(template)
  d = Context(data)
  html_content = html.render(d)
  return html_content

def login_required(f):
    def wrap(request, *args, **kwargs):
        if 'user' not in request.session:
           return HttpResponseRedirect('/logout')
        
        return f(request, *args, **kwargs)
    return wrap
    
class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self,request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)



