
# # from celery.registry import task
# # from celery.task import Task
from __future__ import absolute_import
# from django.template.loader import render_to_string
# from django.utils.html import strip_tags

# from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mass_mail

from qpcmms.models import *

from celery.decorators import task
from celery import Celery
import logging
log = logging.getLogger(__name__)
from celery.task.schedules import crontab
from celery.decorators import periodic_task
# from celery.task.base import periodic_task
# from myapp.utils import scrapers
from celery.utils.log import get_task_logger
from datetime import datetime,timedelta,date
from collections import deque

app = Celery('crons', backend='amqp', broker='amqp://')

'''Cron for Near Renewal Members'''
# A periodic task that will run every minute (the symbol "*" means every)
# @periodic_task(run_every=(timedelta(seconds=5)))
@periodic_task(run_every=crontab(hour=16, minute=46,day_of_week=0))
def mytask():
	# log.debug("Executing task")
	expires = clubstatus.objects.filter(status='Active')

	supervisor = role.objects.get(rolename='Supervisor')
	qpuser_lst = qpuser.objects.filter(role_id=supervisor.id)
	email_lst = []
	user_name = []
	

	ren_list = deque()

	for i in expires:
		if i.date_of_expiry != None:
			if (i.date_of_expiry.year==date.today().year) and (i.date_of_expiry.month==date.today().month) and date.today().day-i.date_of_expiry.day<=15:
				email_lst.append(i.emailid)
				i.status = 'Pending-Renewal'

				for u in qpuser_lst:
					if u.role.rolename == 'Supervisor' or u.role.rolename =='supervisor':
						l = u.clubsallowed
						clubs = []
						li = []
						clubs_list = club.objects.all()

						for j in clubs_list:
							clubs.append(j.name)


						for k in clubs:
							if k in l:                
								li.append(k)
						new_cl = club.objects.filter(name__in=li)
						for l in new_cl:
							# for j in clubs_list:
								if l.id == i.club.id:
									email_lst.append(u.emailid)
				i.save()


	datatuple = (
					('Test', 'Test', 'venugopal@techanipr.com', email_lst),
					)

	send_mass_mail(datatuple, fail_silently = True)


	print 'its executing',email_lst
	return True


@periodic_task(run_every=(timedelta(seconds=30)))
def childern_age_expiry():

	''' Cron for Child Age Expiry '''

	obj_listf=family.objects.filter(age__range=(19,25))
	today=date.today()
	difference = timedelta(days=15)
	dif=timedelta(days=21*365.245)

	obj_list=deque()
	supervisor = role.objects.get(rolename='Supervisor')
	qpuser_lst = qpuser.objects.filter(role_id=supervisor.id)

	email_lst = []

	# print 'im der',obj_listf

	com_date=today +difference
	for l in obj_listf:
		for u in qpuser_lst:
			if u.role.rolename == 'Supervisor' or u.role.rolename == 'Steward':
				l1 = u.clubsallowed
				clubs = []
				li = []
				clubs_list = club.objects.all()

				for j in clubs_list:
					clubs.append(j.name)


				for k in clubs:
					if k in l1:                
						li.append(k)
				new_cl = club.objects.filter(name__in=li)
				mem = clubstatus.objects.filter(member_id=l.member_id)
				# print mem
				for m in new_cl:
					for j in mem:
						if m.id == j.club.id:
							email_lst.append(u.emailid)
							email_lst.append(l.member.emailid)

		if l.status=="Active":
			exp_date=l.dob+dif
			  
			dic = {}
			age=int((com_date.year-l.dob.year)/1.0+(com_date.month-l.dob.month)/12.0+(com_date.day-l.dob.day)/365.0)
			if age==21 and today<=exp_date and (l.status != 'Cancelled-Age21' or l.status != 'Pending-Crossed-Age21'):

				email_lst.append(l.member.emailid)

				l.status = 'Pending-Crossed-Age21'
				l.save()
	print 'im also being calling'

@periodic_task(run_every=(timedelta(seconds=40)))
def member_revoke():
	''' Cron for Revoking Suspended Members'''

	print 'im here now'

	expirations = suspension.objects.filter(todate=date.today(),status='Suspended')
	mems = deque()
	clubs = deque()
	for i in expirations:

		mems.append(i.member_id)

		clubs.append(i.club_id)

	cls = clubstatus.objects.filter(member_id__in=mems,status='Suspended',club_id__in=clubs)

	print cls


@periodic_task(run_every=(timedelta(seconds=40)))
def test():

	print 'test mail'

	datatuple = (
					('Test', 'Test', 'venugopal@techanipr.com', ['venugopal@anipr.in']),
					)

	send_mass_mail(datatuple, fail_silently = True)


