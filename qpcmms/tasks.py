# from celery.registry import task
# from celery.task import Task
from __future__ import absolute_import
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mass_mail

from celery.decorators import task
from celery import Celery
import logging
log = logging.getLogger(__name__)
from celery.task.schedules import crontab
from celery.decorators import periodic_task
# from myapp.utils import scrapers
from celery.utils.log import get_task_logger
from datetime import datetime

app = Celery('tasks', backend='amqp', broker='amqp://')


@app.task(ignore_result=True)
def UserMail(uobj):
    subject,from_email, to = 'Welcome to QP', 'Venugopal<venu@gmail.com>' ,uobj.emailid
    # print uobj.userid

    html_content = render_to_string('PasswordReset.html',{'user':uobj.name,'emailid':uobj.userid,'password':uobj.password})
    text_content = strip_tags(html_content)
    msg = EmailMultiAlternatives(subject,text_content,from_email,[to])
    msg.attach_alternative(html_content,'text/html')
    msg.send()


@app.task
def NotifySupervisor(datatuple):
    send_mass_mail(datatuple, fail_silently = True)

@app.task
def hello_world(datatuple):
    # send_mass_mail(datatuple, fail_silently = True)
    print 'helo'
