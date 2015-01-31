# Create your views here.
from django.http import HttpResponse
from models import *
from django.db.models import Q
from django.shortcuts import render_to_response, HttpResponseRedirect
# from datetime import *
from forms import *
from django.template import RequestContext
from django.core.context_processors import csrf
from django.core.paginator import *
import xlrd
from qpcm import *
from django.template.loader import render_to_string
import datetime
import gc
import time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.pagesizes import landscape
from reportlab.platypus import Image
import hashlib
# import datetime
import random
from datetime import datetime, timedelta, date
from django.conf import settings as conf_settings
import os
# from django.core.mail import send_mail
from django.template.loader import get_template
from django.template import Context, RequestContext
from django.core.mail import send_mail,  EmailMultiAlternatives
from django.contrib import messages
from django.core.mail import send_mass_mail
import xlwt
from tasks import UserMail,NotifySupervisor

from crons import *
from django.core.exceptions import ObjectDoesNotExist
from collections import deque
import json as simplejson
import calendar

def user_login_required(f):
        def wrap(request, *args, **kwargs):
                #this check the session if userid key exist, if not it will redirect to login page
                if 'user' not in request.session.keys():
                    return HttpResponseRedirect("/login")
                # if 'user' in request.session.keys():
                #     return HttpResponseRedirect('/')

                return f(request, *args, **kwargs)
        wrap.__doc__=f.__doc__
        wrap.__name__=f.__name__
        return wrap

def hashpass(password):
    password_obj = hashlib.md5(password)
    return password_obj.hexdigest()

# @user_login_required
def login(request):

    form = UserForm(request.POST)
    content = {}
    content['form'] = form
    if 'user' in request.session.keys():
        return HttpResponseRedirect("/index")

    content.update(csrf(request))

    if request.method == "POST":
        username = request.POST['userid']
        # password = request.POST['password']
        password = request.POST['password']
        # password = hashpass(in_password)

        user_list = qpuser.objects.filter(userid=username, password=password)
        if(user_list):
            userobj = user_list[0]
            # hello_world.delay(userobj)
            s = userlogin(username = userobj.name, userid = userobj.userid, role = userobj.role, logintime = datetime.now())
            s.save()   
            request.session['user'] = userobj
            return HttpResponseRedirect("/index")
        else:
            content['err_msg'] = 'Invalid Credentials'
        return render_to_response('login.html', content, context_instance=RequestContext(request))

    return render_to_response('login.html', content, context_instance=RequestContext(request))

@user_login_required

def logout(request):
    user = request.session['user']
    s=userlogout(username = user.name, userid = user.userid, role = user.role, logouttime = datetime.now())            
    s.save()
    session_keys = request.session.keys()
    form = UserForm(request.POST)
    for key in session_keys:
        del request.session[key]
    # content.update(csrf(request))
    return HttpResponseRedirect("/login")
    # return render_to_response('login.html', {'form': form}, context_instance=RequestContext(request))

@user_login_required

def index(request):

    content = {}

    user = request.session['user']
    content['username'] = user.name

    if str(user.role) == 'Steward':
        return HttpResponseRedirect("/members")  
    
    if str(user.role) == 'Receptionist':
        return HttpResponseRedirect('/today-visitors')

    if 'Admin' in str(user.role.rolename):
        return HttpResponseRedirect("/users")

    userclubs = []
    l = user.clubsallowed
    clubs = []
    clubs_list = club.objects.all()

    for i in clubs:
        if i in l:                
            userclubs.append(i)
    li=[]
    # l = mem_obj.clubsallowed
   
    clubs = []
    clubs_list = club.objects.all()

    for i in clubs_list:
        clubs.append(i.name)

    for i in clubs:
        if i in l:                
            li.append(i)
    

    x =  club.objects.filter(name__in=li).values('id')
    m = []
    for k in x.iterator():
        m.append(k['id'])


    cls = clubstatus.objects.filter(club_id__in=m).values('member')

    # b = clubstatus.objects.filter(club_id__in=m).select_related('member_id')
    # # This does not make another call on the database
    # for i in b:
    #     print i.member
    n = deque()

    for b in cls.iterator():
        n.append(b['member'])

    my_queryset = member.objects.filter(id__in=n)

    all_family = family.objects.filter(member_id__in=n).exclude(status='Inactive')
    all_guest = guest.objects.filter(memberid__in=n).exclude(status='Inactive')

    todate =date.today()
    todate+=timedelta(days=1)
    year,mnth,day = str(todate).split("-")
    sdate = date(int(year), int(mnth), int(day))
    difference = timedelta(days=5)
    fromdate= sdate-difference
    
    pendind_mems = my_queryset.filter(status='Pending')

    new_mem = my_queryset.filter(datetime__range=(fromdate, todate),status='Active').count()

    qporg = organization.objects.get(name="QP")

    non_qporg = organization.objects.get(name__contains="Non")

    qp_mem = my_queryset.filter(organization=qporg.id,status='Active').exclude(status='Inactive').count()

    nqp_mems = my_queryset.filter(organization=non_qporg.id,status='Active').exclude(status='Inactive').count()
    
    
    
    renewals = renewal.objects.filter(datetime__range=(fromdate, todate),member_id__in=n).order_by('-id')[:10]
    
    trans1 = transaction.objects.filter(datetime__gte=date.today())



    
    trns_list=[]

    rfd = deque()

    for k in my_queryset:
        rfd.append(k.rfidcardno)

    for k in all_family:
        rfd.append(k.rfidcardno)

    for k in all_guest:
        rfd.append(k.rfidcardno)

    for j in li:
        dic={}
        mem_visit = deque()
        
        
        # for k in my_queryset:
        for i in trans1:
            if k.rfidcardno in rfd and i.club.name==j:
                if i not in mem_visit:
                    mem_visit.append(i)
        # for k in all_family:
        for i in trans1:
            if k.rfidcardno in rfd and i.club.name==j:
                if i not in mem_visit:
                    mem_visit.append(i)   
        # for k in all_guest:
        for i in trans1:
            if k.rfidcardno in rfd and i.club.name==j:
                if i not in mem_visit:
                    mem_visit.append(i)
        dic['club']=j
        dic['visitor']=len(mem_visit)
        trns_list.append(dic)
    
    content.update(csrf(request))

    content={'username':user.name,'count':qp_mem+nqp_mems,'pending_members':len(pendind_mems),'new_members':new_mem,'to_approve':pendind_mems[:10],'renewals':renewals, 'clubs_list':userclubs,'qp_list':qp_mem,'nonqp_list':nqp_mems,'total_clubs':len(x),'clubutil':trns_list}
    
    
    if str(user.role) == 'Supervisor':
        return render_to_response('index.html',content,context_instance=RequestContext(request))
    



@user_login_required
def members(request):
    pend_result = []
    # page = request.GET.get('page')
    user = request.session['user']
    userclubs = []
    l = user.clubsallowed
    clubs = []

    for i in clubs:
        if i in l:                
            userclubs.append(i)
    li=[]
    # l = mem_obj.clubsallowed
   
    clubs = []
    clubs_list = club.objects.all()

    for i in clubs_list.iterator():
        clubs.append(i.name)

    for i in clubs:
        if i in l:                
            li.append(i)
    

    x =  club.objects.filter(name__in=li)
    m = []
    for k in x.iterator():
        m.append(k.id)


    cls = clubstatus.objects.filter(club_id__in=m).values('member_id')
    n = deque()

    
    for b in cls.iterator():
        n.append(b['member_id'])
    
    all_mems=[]
    all_fams=[]
    all_gst=[]

    my_queryset = member.objects.filter(id__in=n).values('id','name','rfidcardno','member_uid','dob','status')

    clubs = []
    active_members = my_queryset.filter(~Q(status='Membership-Rejected'))
    result = []
    page = request.GET.get('page')
    
    try:
        for i in my_queryset.iterator(): 
            result.append(i)    
        paginator = Paginator(result, 100)
        result = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        result = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        result = paginator.page(paginator.num_pages)

    if request.is_ajax():
        result = []
        page = 1
        if 'page' in request.GET:
            query = request.GET.get('page')
            active_members1 = my_queryset.filter(~Q(status='Membership-Rejected')).values('id','name','rfidcardno','member_uid','dob','status')
            if query is not None:
                page = query
            try:
                for i in active_members1.iterator(): 
                    result.append(i)    
                paginator = Paginator(result, 100)
                result = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                result = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                result = paginator.page(paginator.num_pages)
            content = {'active_members':result}

        if 'pend_page' in request.GET:
            query = request.GET.get('pend_page')
            pend_members = my_queryset.filter(status='Pending').values('id','name','rfidcardno','member_uid','dob','status')
            if query is not None:
                page = query
            try:
                for i in pend_members.iterator(): 
                    result.append(i)    
                paginator = Paginator(result, 100)
                result = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                result = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                result = paginator.page(paginator.num_pages)
            content = {'members':result}

        if 'sus_page' in request.GET:
            query = request.GET.get('sus_page')
            sus_members = my_queryset.filter(status='Pending-Suspension').values('id','name','rfidcardno','member_uid','dob','status')
            if query is not None:
                page = query
            try:
                for i in sus_members.iterator(): 
                    result.append(i)    
                paginator = Paginator(result, 100)
                result = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                result = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                result = paginator.page(paginator.num_pages)
            content = {'suspend_mem':result}


        if 'can_page' in request.GET:
            query = request.GET.get('can_page')
            can_members = my_queryset.filter(status='Pending-Cancel').values('id','name','rfidcardno','member_uid','dob','status')
            if query is not None:
                page = query
            try:
                for i in can_members.iterator(): 
                    result.append(i)    
                paginator = Paginator(result, 100)
                result = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                result = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                result = paginator.page(paginator.num_pages)
            content = {'pend_cancle':result}


        if 'oth_page' in request.GET:
            query = request.GET.get('oth_page')
            can_members = my_queryset.filter(status='Pending-Cancel').values('id','name','rfidcardno','member_uid','dob','status')
            if query is not None:
                page = query
            try:
                for i in can_members.iterator(): 
                    result.append(i)    
                paginator = Paginator(result, 100)
                result = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                result = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                result = paginator.page(paginator.num_pages)
            content = {'others':result}
        if str(user.role) == 'Steward':
            return render_to_response('Steward/members.html',content,context_instance=RequestContext(request))  
        return render_to_response('members.html',content,context_instance=RequestContext(request))  

    content={}
    content.update(csrf(request))

    pend_members = my_queryset.filter(status='Pending').values('id','name','rfidcardno','member_uid','dob','status').order_by('-id')


    pend_page_result = []
    pend_page = request.GET.get('pend_page')
    try:
        for i in pend_members.iterator(): 
            pend_page_result.append(i)    
        paginator = Paginator(pend_page_result, 100)
        pend_page_result = paginator.page(pend_page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        pend_page_result = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        pend_page_result = paginator.page(paginator.num_pages)




    suspend_members = my_queryset.filter(status='Pending-Suspension').values('id','name','rfidcardno','member_uid','dob','status')


    sus_page_result = []
    sus_page = request.GET.get('sus_page')
    try:
        for i in suspend_members.iterator(): 
            sus_page_result.append(i)    
        paginator = Paginator(sus_page_result, 100)
        sus_page_result = paginator.page(sus_page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        sus_page_result = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        sus_page_result = paginator.page(paginator.num_pages)



    suspend_fmembers = family.objects.filter(member_id__in=n,status='Pending-Crossed-Age 21')

    pend_cancle = my_queryset.filter(status='Pending-Cancel').values('id','name','rfidcardno','member_uid','dob','status')


    can_page_result = []
    can_page = request.GET.get('can_page')
    try:
        for i in pend_cancle.iterator(): 
            can_page_result.append(i)    
        paginator = Paginator(can_page_result, 100)
        can_page_result = paginator.page(can_page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        can_page_result = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        can_page_result = paginator.page(paginator.num_pages)


    
    others = my_queryset.filter(Q(status ='Suspended') | Q(status='Membership-Suspended') | Q(status='Pending-Renewal') | Q(status='Rejected-Renewal') | Q(status='Pending-Suspension-Revoke') | Q(status='Membership-Rejected')).values('id','name','rfidcardno','member_uid','dob','status')

    oth_page_page_result = []
    oth_page = request.GET.get('oth_page')
    try:
        for i in others.iterator(): 
            oth_page_page_result.append(i)    
        paginator = Paginator(oth_page_page_result, 100)
        oth_page_page_result = paginator.page(oth_page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        oth_page_page_result = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        oth_page_page_result = paginator.page(paginator.num_pages)

    sus_flist = []
   
    content={'active_members':result,'sus_familylist':suspend_fmembers,'username' :user.name,'members':pend_page_result,'suspend_mem':sus_page_result,'pend_cancle':can_page_result,'others':oth_page_page_result}
    if str(user.role) == 'Steward':
        return render_to_response('Steward/members.html',content,context_instance=RequestContext(request))  

    return render_to_response('members.html',content,context_instance=RequestContext(request))
    

@user_login_required   
def membershipform(request):

    # member = []
    data = {}
    url = '/membershipform/'
    content={}
    content.update(csrf(request))
    user = request.session['user']
    # MemberFormObj = MemberForm()
    if 'emid' in request.GET:
        emid = request.GET['emid']
        mem_obj = member.objects.get(id=emid)
        data['name'] = mem_obj.name
        data['first_name_1'] = mem_obj.first_name_1
        data['first_name_2'] = mem_obj.first_name_2
        data['first_name_3'] = mem_obj.first_name_3
        data['initials'] = mem_obj.initials
        data['member_uid'] = mem_obj.member_uid
        data['residencelocation'] = mem_obj.residencelocation
        data['nationality'] = mem_obj.nationality
        data['office_fax_no'] = mem_obj.office_fax_no
        data['cont_type'] = mem_obj.cont_type
        data['cont_term_reason'] = mem_obj.cont_term_reason
        data['cont_expiry_date'] = mem_obj.cont_expiry_date
        data['No_of_dependents'] = mem_obj.No_of_dependents
        # company = associatecompany.objects.get(id=mem_obj.associatecompany)
        data['associatecompany'] = mem_obj.associatecompany
        data['maritalstatus'] = mem_obj.maritalstatus
        data['mobileno'] = mem_obj.mobileno
        data['gender'] = mem_obj.gender
        data['emailid'] = mem_obj.emailid
        data['dob'] = mem_obj.dob
        data['member_uid'] = mem_obj.member_uid
        data['date_of_joining'] = mem_obj.date_of_joining
        data['date_of_expiry'] = mem_obj.date_of_expiry
        data['rfidcardno'] = mem_obj.rfidcardno       
        data['extract_run_date'] = mem_obj.extract_run_date       
        data['pos_desc'] = mem_obj.pos_desc       
        data['worklocation'] = mem_obj.worklocation       
        li=[]
        cls = clubstatus.objects.filter(member_id=mem_obj.id)
        for i in cls:
            li.append(i.club_id)
        # tot_clubs = club.objects.filter(name__in=li)
        data['clubsallowed'] = li
        data['status'] = mem_obj.status
        data['department'] = mem_obj.department
        data['membership_grade'] = mem_obj.membership_grade
        data['membership_category'] = mem_obj.membership_category
        data['organization'] = mem_obj.organization
        data['attachment'] = mem_obj.attachment
        data['qpuser'] = mem_obj.qpuser
        data['datetime'] = mem_obj.datetime
        form=MemberForm(initial=data,user=user)

        # form.fields['rfidcardno'].widget.attrs['readonly'] = True 

        content = {'form':form,'mid':emid,'photo':mem_obj.photo,'IMAGE_URL':conf_settings.IMAGE_URL}
        
        # if str(user.role) == 'Steward':
        #     return render_to_response('non-qpaddmember.html',content, context_instance=RequestContext(request))
        return render_to_response('non-qpaddmember.html', content,context_instance=RequestContext(request))


    if 'mid' in request.POST:   
        emid = request.POST['mid']
        if emid:
            
            member_form = MemberForm(user,request.POST)        
            if member_form.is_valid():
                clubs1 = member_form.cleaned_data['clubsallowed']
                li=[]
                l = user.clubsallowed
               
                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in l:                
                        li.append(i)
                uclubs = club.objects.filter(name__in=li)
                # for i in clubs1:
                #     if i not in uclubs:
                #         return HttpResponse('<script type="text/javascript">alert("You are not allowed to do any Operation of other Club Member!");</script>')
                memberedit = member.objects.get(id=emid)
                if 'Imagefile' in request.FILES:
                    f = request.FILES['Imagefile']
                    #f = open(settings.IMAGE_ROOT,"ListingImages\\Customer-%s.%s" %(cid,flist[1]), "wb")
                    file_name = f.name
                    flist = file_name.split(".")
                    data = f.read()
                    f.close()
                    f = open(conf_settings.IMAGE_ROOT + "%s.%s" %(memberedit.member_uid,flist[1]),"wb")
                    # size = (100,100)
                    # f.thumbnail(size, Image.ANTIALIAS)
                    # f.save(outfile, "JPEG")
                    f.write(data)
                    f.close()
                    imageUrl  = "%s.%s" %(memberedit.member_uid,flist[1])
                    # memberedit.photo =  imageUrl
                member_form = MemberForm(user,request.POST, instance = memberedit)
                member_form.save()
                mem_obj = member.objects.get(id=emid)
                li=[]
                l = mem_obj.clubsallowed
               
                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in l:                
                        li.append(i)
                tot_clubs = club.objects.filter(name__in=li)
                date = datetime.now()
                for i in tot_clubs:
                    status_obj = clubstatus.objects.filter(member_id=mem_obj.id,club_id=i.id)
                    if not status_obj:
                        date_of_expiry = "%s-%s-%s" % (date.year+1, date.month, date.day)
                        cl_obj = clubstatus(member_id=mem_obj.id,club_id=i.id,status=mem_obj.status,date_of_expiry=date_of_expiry)
                        cl_obj.save()

                if 'Imagefile' in request.FILES:
                    f = request.FILES['Imagefile']
                    if f:
                        memobj = member.objects.get(id=emid)
                        memobj.photo = imageUrl
                        memobj.save()
                if 'attachment' in request.FILES:
                    memobj = member.objects.get(id=emid)
                    memobj.attachment = request.FILES['attachment']
                    memobj.save()
                family_obj = family.objects.filter(member_id=emid)
                for i in family_obj:
                    i.clubsallowed = clubs1
                    i.save()
                l = mem_obj.clubsallowed
               
                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in l:                
                        li.append(i)
                new_clubs = club.objects.filter(name__in=li)
                status_obj = clubstatus.objects.filter(member_id=mem_obj.id)

                return HttpResponse('<script type="text/javascript">window.close();window.opener.location.reload(true);</script>')
    if 'mid' in request.GET:
        mid = request.GET['mid']
        mem_obj = member.objects.get(id=mid)
        sus_obj = suspension()
        sus_obj.member_id = mem_obj.id
        sus_obj.doneby = user
        li=[]
        l = mem_obj.clubsallowed
       
        clubs = []
        clubs_list = club.objects.all()

        for i in clubs_list:
            clubs.append(i.name)

        for i in clubs:
            if i in l:                
                li.append(i)
        cl_list = club.objects.filter(name__in=li)

        family_obj = family.objects.filter(member_id=mem_obj.id)
        for i in family_obj:
            if i.age >= 21 and i.relationship != 'W' and not i.date_of_expiry:
                i.status = 'Pending-Suspension'
            else:
                i.status = mem_obj.status
            i.save()

        memobj = member.objects.get(id=mid)
        li = []
        clubs = club.objects.all()
        sus_obj = suspension.objects.filter(member_id=mem_obj.id).order_by('-id')
        sus_obj = sus_obj[0]
        li=[]
        l = sus_obj.clubsallowed
       
        clubs = []
        clubs_list = club.objects.all()

        for i in clubs_list:
            clubs.append(i.name)

        for i in clubs:
            if i in l:                
                li.append(i)
        new_cl = club.objects.filter(name__in=li)

        for i in new_cl:

            status_obj = clubstatus.objects.filter(member_id=mem_obj.id,club_id=i.id)
            status_obj = status_obj[0]

            if str(sus_obj.status) == 'Suspension-Revoke':
                status_obj.status = 'Active'

            if str(sus_obj.status) == 'Membership-Cancelled':
                mem_obj.status = 'Inactive'
                mem_obj.save()

            if str(sus_obj.status) == 'Active':
                status_obj.status = 'Active'
                mem_obj.status = 'Active'
                mem_obj.save()   

            else:
                status_obj.status = sus_obj.status
            # # date_of_joining = "%s-%s-%s" % (date.year, date.month, date.day)
        return HttpResponseRedirect('/members/')
    else:
        if request.method == 'POST':
            form=MemberForm(user,request.POST,request.POST)
            if form.is_valid():
                member_uid = form.cleaned_data['member_uid']
                clubs1 = form.cleaned_data['clubsallowed']
                obj = form.save(commit=False)
                obj.datetime = datetime.now()
                li=[]
                l = user.clubsallowed
               
                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in l:                
                        li.append(i)
                uclubs = club.objects.filter(name__in=li)
                for i in clubs1:
                    if i not in uclubs:
                        return HttpResponse('<script type="text/javascript">alert("You are not allowed to do any Operation of other Club Member!");</script>')
                if str(user.role) == 'Supervisor':
                    obj.status = 'Active'
                # obj.user_id = user.id
                if 'Imagefile' in request.FILES:
                    f = request.FILES['Imagefile']
                    file_name = f.name
                    flist = file_name.split(".")
                    data = f.read()
                    f.close()
                    f = open(os.path.join(conf_settings.IMAGE_ROOT, "%s.%s" %(member_uid,flist[1])), "wb")
                    f.write(data)
                    f.close()
                if 'Imagefile' in request.FILES:
                    if f:
                        # memObj = member.objects.latest('id')
                        imageUrl  = "%s.%s" %(member_uid,flist[1])
                        obj.photo =  imageUrl
                if 'Imagefile' not in request.FILES:
                    imageUrl  = 'People.jpg'
                    obj.photo =  imageUrl
                #     # customer.save()
                if 'attachment' in request.FILES:
                    obj.attachment = request.FILES['attachment']
                obj.save()
                memobj = member.objects.filter(qpuser=user.id).latest('id')
                memobj.member_uid = '9000000' + str(memobj.id)
                # memobj = member.objects.filter(qpuser=userid.id).latest('id')
                clubstatus_obj = clubstatus()

                # memship = membership()
                clubstatus_obj.member_id = memobj.id
                li=[]
                # l = mem_obj.clubsallowed

                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in memobj.clubsallowed:
                        li.append(i)

                date = datetime.now()
                for i in li:
                    c_obj = club.objects.get(name=i)
                    # # date_of_joining = "%s-%s-%s" % (date.year, date.month, date.day)
                    date_of_expiry = "%s-%s-%s" % (date.year+1, date.month, date.day)
                    memship = clubstatus(member_id=memobj.id,club_id=c_obj.id,status=memobj.status,date_of_expiry=date_of_expiry)

                    memship.save()
                memobj.save()
                url = '/common/?mid=%s'%(memobj.id)

                return HttpResponseRedirect(url)

    organization1 = organization.objects.all().exclude(name="QP")
    
    form=MemberForm(initial={'qpuser':user.id, 'status':'Pending', 'organization': organization1[0].id},user=user)


    content = {'username':user.name,'form':form, 'url':url}

    if str(user.role) == 'Steward':
         return render_to_response('Steward/membershipform.html',content,context_instance=RequestContext(request))
    return render_to_response('membershipform.html',content,context_instance=RequestContext(request))
    
    
@user_login_required    
def users(request):
    url = '/users/'

    users = qpuser.objects.filter( id__isnull=False).order_by('-id')
    userobj = request.session['user']

    content = {'username' :userobj.name,'url':url,'users':users}
    if str(userobj.role) == 'Supervisor':
         return render_to_response('users.html', content,context_instance=RequestContext(request)) 
    else:
        return render_to_response('Admin/users.html',content, context_instance=RequestContext(request))
    
@user_login_required
def common(request):

    content = {}
    data={}
    url = '/membershipform/'
    user = request.session['user']
    content['username'] = user.name
    memberFormObj = MemberForm(user=user)
    content.update(csrf(request))
    mid=None
    suspendForm = SuspensionForm(mid=mid,user=user,cid=None)
    if 'mid' in request.GET:
        mid = request.GET['mid']
        try:
            mem_obj = member.objects.get(id=mid)
        except ObjectDoesNotExist:
            return HttpResponse('<script type="text/javascript">alert("Member Does not Exists !");</script>')
        # emp_obj = employment.objects.get(id=mem_obj.employment_id)
        data['name'] = mem_obj.name
        data['nationality'] = mem_obj.nationality
        data['maritalstatus'] = mem_obj.maritalstatus
        data['mobileno'] = mem_obj.mobileno
        data['gender'] = mem_obj.gender
        data['dob'] = mem_obj.dob
        data['rfidcardno'] = mem_obj.rfidcardno
        data['clubsallowed'] = mem_obj.clubsallowed
        data['status'] = mem_obj.status
        data['department'] = mem_obj.department
        # data['membership'] = mem_obj.membership
        data['organization'] = mem_obj.organization
        # data['employment'] = mem_obj.employment
        data['qpuser'] = mem_obj.qpuser
        rform = MemberForm(initial=data,user=user)
        content['id'] = mem_obj.id
        content['mid'] = mid
        content['form'] = rform
        content['url'] = url
        content['name'] = mem_obj.name + ' ' + mem_obj.first_name_1+' ' + mem_obj.first_name_2+' ' + mem_obj.first_name_3
        content['nationality'] = mem_obj.nationality
        content['maritalstatus'] = mem_obj.maritalstatus
        content['mobileno'] = mem_obj.mobileno
        content['gender'] = mem_obj.gender
        content['member_uid'] = mem_obj.member_uid
        content['dob'] = mem_obj.dob
        content['rfidcardno'] = mem_obj.rfidcardno
        content['date_of_joining'] = mem_obj.date_of_joining
        content['date_of_expiry'] = mem_obj.date_of_expiry
        content['clubsallowed'] = mem_obj.clubsallowed
        # if 'Pending-' in str(mem_obj.status):
        #     obj= suspension.objects.filter(member_id=mem_obj.id).order_by('-id')[0]
        #     if obj:
        #         content['reason'] = obj.reason
        content['status'] = mem_obj.status
        content['IMAGE_URL'] = conf_settings.IMAGE_URL
        content['photo'] = mem_obj.photo
        if mem_obj.attachment != False:
            content['attachment'] = mem_obj.attachment
        content['worklocation'] = mem_obj.worklocation
        content['officephone'] = mem_obj.office_fax_no
        content['department'] = mem_obj.department
        content['emailid'] = mem_obj.emailid
        content['organization'] = mem_obj.organization
        if mem_obj.organization:
            content['org'] = mem_obj.organization.name
        # content['employment'] = mem_obj.employment
        content['qpuser'] = mem_obj.qpuser
        # content['s_form'] = suspendForm
        li = []
        li2 = []
        sus_list = []
        act_list = []
        pend_cancel = []
        pend_sus = []
        pend_sus_rev = []
        pending_lst = []
        pending_ren = []
        ren_list = []
        inact_list = []
        pend_react = []
        status_obj = clubstatus.objects.filter(member_id=mem_obj.id)
        userclubs = []
        l = user.clubsallowed
        clubs = []
        clubs_list = club.objects.all()

        for i in clubs_list:
            clubs.append(i.name)

        for i in clubs:
            if i in l:                
                userclubs.append(i)

        uclubs = club.objects.filter(name__in=userclubs)

        # print 'cl',status_obj,
        # print 'uclubs',uclubs

        own_member = False

        for i in uclubs:
            for j in status_obj:
                if j.club in uclubs:
                    own_member = True


        if status_obj:
            # status_obj = status_obj[0]
            for i in status_obj:
                for j in uclubs:
                    dic = {}
                    cname = club.objects.get(id=i.club_id)
                    dic['club'] = cname.name
                    dic['status'] = i.status
                    dic['expiry'] = i.date_of_expiry
                    dic['id'] = cname.id
                    if i.club.id == j.id:
                        if i.status == 'Suspended':
                            sus_list.append(i)
                        if i.status == 'Pending-Suspension-Revoke':
                            pend_sus_rev.append(i)
                        if i.status == 'Pending':
                            pending_lst.append(i)

                        if i.status == 'Pending-Suspension':
                            pend_sus.append(i)

                        if i.status == 'Pending-Cancel':
                            pend_cancel.append(i)

                        if i.status == 'Active':
                            act_list.append(i)

                        if i.status == 'Inactive':
                            inact_list.append(i)


                        if i.status == 'Pending-Renewal':
                            pending_ren.append(i)

                        if i.status == 'Pending-Cancel-Reactivate':
                            pend_react.append(i)

                        if i.date_of_expiry != None:
                            if (i.date_of_expiry.year==date.today().year) and (i.date_of_expiry.month==date.today().month) and (date.today().day-i.date_of_expiry.day<=15) and i.status != 'Pending-Renewal':
                                ren_list.append(i)


                li2.append(dic)
        
        l = mem_obj.clubsallowed
       
        clubs = []
        clubs_list = club.objects.all()

        for i in clubs_list:
            clubs.append(i.name)

        for i in clubs:
            if i in l:                
                li.append(i)
        content['sus_list'] = sus_list
        content['act_list'] = act_list
        content['pending_ren'] = pending_ren
        content['ren_list'] = ren_list
        content['pend_sus'] = pend_sus
        content['pend_sus_rev'] = pend_sus_rev
        content['pend_cancel'] = pend_cancel
        content['pending_lst'] = pending_lst
        content['inact_list'] = inact_list
        content['clubs_list'] = li2
        content['pend_react'] = pend_react
        content['count'] = len(li)
        suspendForm = SuspensionForm(cid=None,mid=mid,initial={'fromdate':datetime.today(),'clubsallowed':li},user=user)
        content['s_form'] = suspendForm
        

        if own_member == True:
            if str(user.role) == 'Supervisor':
                return render_to_response("common.html", content,context_instance=RequestContext(request))

            else:
                return render_to_response('Steward/common.html',content,context_instance=RequestContext(request))  
        else:
            if str(user.role) == 'Steward':
                return render_to_response("Steward/non_member_profile.html", content,context_instance=RequestContext(request))

            else:
                return render_to_response("non_member_profile.html", content,context_instance=RequestContext(request))

    else:
        content['form'] = memberFormObj
        if str(user.role) == 'Steward':
            return render_to_response('Steward/common.html',content,context_instance=RequestContext(request))  
        return render_to_response("common.html",content,context_instance=RequestContext(request))
       
    return render_to_response('common.html',content,context_instance=RequestContext(request))

@user_login_required
def userform(request):

    url = '/userform/'
    user = request.session['user']
    content={}
    data = {}
    content.update(csrf(request))
    form=UserForm()
    content = {'username' :user.name,'form':form, 'url':url}
    if request.method == "POST":
        if 'uid' in request.POST:   
            uid = request.POST['uid']
        if 'pwd' in request.POST:
            pwd = request.POST['pwd']
            if uid:
                user_form = UserForm(request.POST)
                if user_form.is_valid():
                    uobj = qpuser.objects.get(id=uid)
                    uobj.password = pwd
                    user_form = UserForm(request.POST, instance = uobj)
                    user_form.save()
                    u_newobj = qpuser.objects.get(id=uid)
                    u_newobj.password = pwd
                    u_newobj.save()
                    return HttpResponseRedirect('/users/')
            else:
                form=UserForm(request.POST)
                for name, field in form.fields.iteritems():
                    field.required = False
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.status = 'Active'
                    # obj.password = hashpass(password)
                    obj.save()
                    uobj = qpuser.objects.latest('id')
                    pwd = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(5))
                    uobj.password = pwd

                    uobj.save()
                    content['emailid'] = uobj.userid
                    content['password'] = pwd
                    content['first_name'] = uobj.name
                    html = render_email('PasswordReset.html', content)
                    #USER MAIL HERE
                    # SendEMail("Password Reset", html, str(uobj.emailid))
                    UserMail.delay(uobj)
                    suc_msg = 'Password Has been Sent to User Email'

                    content['suc_msg'] = suc_msg
                    return HttpResponseRedirect('/users/')

    if 'uid' in request.GET:
        uid = request.GET['uid']
        u_obj = qpuser.objects.get(id=uid)
        data['name'] = u_obj.name
        data['userid'] = u_obj.userid
        data['officephone'] = u_obj.officephone
        data['mobileno'] = u_obj.mobileno
        data['residencelocation'] = u_obj.residencelocation
        data['emailid'] = u_obj.emailid
        content['pwd'] = u_obj.password
        l = u_obj.clubsallowed
        li = []
        clubs = []
        clubs_list = club.objects.all()

        for i in clubs_list:
            clubs.append(i.name)

        for i in clubs:
            if i in l:                
                li.append(i)
        data['clubsallowed'] = club.objects.filter(name__in=li)  
        data['status'] = u_obj.status
        data['role'] = u_obj.role
        rform=UserForm(initial = data)
        content['form'] = rform
        content['uid'] = u_obj.id
        return render_to_response('Admin/userform.html',content, context_instance=RequestContext(request))
        
    if str(user.role) == 'Supervisor':
        return render_to_response('userform.html',content,context_instance=RequestContext(request))
    else:
        return render_to_response('Admin/userform.html',content, context_instance=RequestContext(request))
    
    
@user_login_required
def reports(request):    

    url = '/reports/'
    content={}
    
    content.update(csrf(request))
    msg = ''
    user = request.session['user']
    content['username']=user.name
    content['url']=url
    userclubs=[]
    userclub1=[]
    userclub1.append('All')
    l = user.clubsallowed
    clubs = []
    clubs_list = club.objects.all()

    
    li=[]
    # l = mem_obj.clubsallowed
   
    clubs = []
    clubs_list = club.objects.all()

    for i in clubs_list:
        clubs.append(i.name)

    for i in clubs:
        if i in l:                
            li.append(i)
            userclubs.append(i)
            userclub1.append(i)
    content['userclubs']=userclub1        
    content['url'] = url
    content['clubs']=len(userclubs)
    content['userclubs']=userclub1
    
    if request.method == "POST":
        filter=request.POST["filter"]
        club_q = request.POST["club"]
        content['club_q']=club_q
        content['filter']=filter
        x =  club.objects.filter(name__in=li)
        m = []
        for k in x:
            m.append(k.id)


        cls = clubstatus.objects.filter(club_id__in=m).values('member_id')
        n = deque()
        for b in cls:
            n.append(b['member_id'])

        obj_listg = guest.objects.all()
        obj_listm = member.objects.filter(id__in=n,status="Active").exclude(status='Inactive')
        obj_listf=family.objects.filter(member_id__in=n).exclude(status='Inactive')
        #print "ffaaaaaaaaaaaaaaaaaaaaaaaamlyyyyy",obj_listf
        guest_list=[]
        fam_list=[]
        mem_adult=[]
        guest_adult=[]
        guest_child=[]
        #family_child=[]
        #family_adult=[]
        family_child =  obj_listf.filter(age__lte=21)
        #print "chhhhhhotaaa bachhaaa",family_child
        family_adult=obj_listf.filter(age__gt=21)
        #print "Baaaadddaddaaa bachhhhaa",family_adult

        #obj_listm.extend(family_adult)
        mem_adult =obj_listm
        # [mem_adult].extend([family_adult])
        # mem_adult.extend(family_adult)
        # for i in obj_listm:
        #     for j in li:
        #         if j in i.clubsallowed:
        #             if i not in mem_adult:
        #                 mem_adult.append(i)    
        # for i in obj_listf:
        #     for j in li:
        #         if j in i.member.clubsallowed:
        #             if i not in fam_list:
        #                 fam_list.append(i)                
        # for j in fam_list:            
        #     age=int((date.today().year-j.dob.year)/1.0+(date.today().month-j.dob.month)/12.0+(date.today().day-j.dob.day)/365.0)
            
        #     if age>=21:
        #         mem_adult.append(j)
        #     else:
        #         family_child.append(j)            
        for i in obj_listg:
            for j in li:

                if j in i.clubsallowed:
                    if i not in guest_list:
                        guest_list.append(i)
        
        for j in guest_list:            
            age=int((date.today().year-j.dob.year)/1.0+(date.today().month-j.dob.month)/12.0+(date.today().day-j.dob.day)/365.0)
            
            if age>=21:
                guest_adult.append(j)
            else:
                guest_child.append(j)

        if filter == "daily":
            fromdate = request.POST["fromdate"]
            todate = request.POST["todate"] 
            content['fromdated']=fromdate
            content['todated']=str(todate)
            year,mnth,day = todate.split("-")
            try:
                sdate = date(int(year), int(mnth), int(day))
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('reports.html',content,context_instance=RequestContext(request))
            difference = timedelta(days=1)
            todate= sdate+difference
            try:
                tr=transaction.objects.filter(datetime__range=(fromdate, todate))
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('reports.html',content,context_instance=RequestContext(request))
            y1,m1,d1 = str(todate).split("-")
            y2,m2,d2 = str(fromdate).split("-")
            
            tdate = date(int(y1), int(m1), int(d1))
            frdate = date(int(y2), int(m2), int(d2))
            content['fromdate']=frdate
            content['todate']=sdate
            dateDiff = tdate - frdate   
            frmdat=frdate
            trxn_list=[]
            
            for single_date in (frdate + timedelta(n) for n in range(1,(dateDiff.days)+1)):
                
                todat=single_date
                trans=tr.filter(datetime__range=(frmdat, todat))

                for j in userclubs:
                    # print j
                    dic={}
                    
                    adult_member=[];child_member=[];adult_guest=[];child_guest=[]

                    for i in mem_adult:                        
                        for l in trans:
                            if i.rfidcardno == l.rfidcardid:                             
                                if j == l.club.name:
                                    if l not in adult_member:
                                        adult_member.append(l)
                    for i in family_adult:                        
                        for l in trans:
                            if i.rfidcardno == l.rfidcardid:                             
                                if j == l.club.name:
                                    if l not in adult_member:
                                        adult_member.append(l)                    
                                
                    for i in family_child:
                        for l in trans:
                            if i.rfidcardno == l.rfidcardid:
                                if j==l.club.name:
                                    if l not in child_member:
                                        child_member.append(l)
                    for i in guest_adult:
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in adult_guest:
                                        adult_guest.append(l)    
                    for i in guest_child:
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in child_guest:
                                       child_guest.append(l)
                    # print 'adults',adult_member
                    dic['club']=j 
                    dic['adult_member']=len(adult_member)
                    dic['child_member']=len(child_member)
                    dic['adult_guest']=len(adult_guest)
                    dic['child_guest']=len(child_guest)
                    dic['fdate']=frmdat
                    dic['total']=len(adult_member)+len(child_member)+len(adult_guest)+len(child_guest)
                    trxn_list.append(dic)
                    
                frmdat=todat
            txn_new_list=[]
            if club_q=="All":  
                content['trxn_list']=trxn_list        
            else:
                for i in trxn_list:
                    if i['club']==club_q:
                        txn_new_list.append(i)
                content['trxn_list']=txn_new_list 
            content['daily']=1

        if filter=="weekly":
            # print "chhhhhhotaaa bachhaaa",family_child
            # print "Baaaadddaddaaa bachhaaa",family_adult
            month = request.POST["month"]
            year = request.POST["yearpicker"]
            content['monthw']=month
            content['yearw']=year
            
            moonth=''
            if month=='1':
                moonth="JAN"
            if month=='2':
                moonth="FEB"
            if month=='3':
                moonth="MAR"
            if month=='4':
                moonth="APR"
            if month=='5':
                moonth="MAY"
            if month=='6':
                moonth="JUN"
            if month=='7':
                moonth="JUL"
            if month=='8':
                moonth="AUG"
            if month=='9':
                moonth="SEP"
            if month=='10':
                moonth="OCT"
            if month=='11':
                moonth="NOV"
            if month=='12':
                moonth="DEC"   
            content['year']=year
            content['month']=moonth
            ldate=0
            if month=='1':
                ldate=31
            if month=='2':
                ldate=28
            if month=='3':
                ldate=31
            if month=='4':
                ldate=30
            if month=='5':
                ldate=31
            if month=='6':
                ldate=30
            if month=='7':
                ldate=31
            if month=='8':
                ldate=31
            if month=='9':
                ldate=30
            if month=='10':
                ldate=31
            if month=='11':
                ldate=30    
            if month=='12':
                ldate=31  
            frmdt=date(int(year),int(month),01)
            todt=date(int(year),int(month),ldate)
            dateDiff=todt-frmdt
            tr=transaction.objects.filter(datetime__range=(frmdt, todt))
            m=0
            trxn_list=[]
            # print "Baaaadddaddaaa bachhaaa",family_adult
            for single_date in (frmdt + timedelta(7) for n in range(0,((dateDiff.days)/7)+1)):
                
                todat=single_date
                trans=tr.filter(datetime__range=(frmdt, todat))
                
                m=m+1

                for j in userclubs:
                    dic={}
                    
                    adult_member=[];child_member=[];adult_guest=[];child_guest=[]
                    for i in mem_adult:                        
                        for l in trans:
                            if i.rfidcardno == l.rfidcardid:                             
                                if j == l.club.name:
                                    if l not in adult_member:
                                        adult_member.append(l)

                    for i in family_adult:                        
                        for l in trans:
                            if i.rfidcardno == l.rfidcardid:                             
                                if j == l.club.name:
                                    if l not in adult_member:
                                        adult_member.append(l)                    
                         
                    for i in family_child:
                        for l in trans:
                            if i.rfidcardno == l.rfidcardid:
                                if j == l.club.name:
                                    if l not in child_member:
                                        child_member.append(l)
                    for i in guest_adult:
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in adult_guest:
                                        adult_guest.append(l)    
                    for i in guest_child:
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in child_guest:
                                        child_guest.append(l)
                    
                    dic['club']=j 
                    dic['adult_member']=len(adult_member)
                    dic['child_member']=len(child_member)
                    dic['adult_guest']=len(adult_guest)
                    dic['child_guest']=len(child_guest)
                    dic['fdate']="WEEK-"+str(m)
                    dic['total']=len(adult_member)+len(child_member)+len(adult_guest)+len(child_guest)
                    trxn_list.append(dic)
                
                frmdt=todat
            txn_new_list=[]
            if club_q=="All":  
                content['trxn_list']=trxn_list        
            else:
                for i in trxn_list:
                    if i['club']==club_q:
                        txn_new_list.append(i)
                content['trxn_list']=txn_new_list
            content['weekly']=1

            

        if filter=="monthly":

            year = request.POST["yearpicker"]
            mnth=request.POST["month1"]
            content['yearofmonth']=year
            content['monthm']=mnth
            frmdt=''
            todt=''
            if mnth=='all':
                frmdt=date(int(year),01,01)
                todt=date(int(year),12,31)
            else:
                ldate=0
                if mnth=='1':
                    ldate=31
                if mnth=='2':
                    ldate=28
                if mnth=='3':
                    ldate=31
                if mnth=='4':
                    ldate=30
                if mnth=='5':
                    ldate=31
                if mnth=='6':
                    ldate=30
                if mnth=='7':
                    ldate=31
                if mnth=='8':
                    ldate=31
                if mnth=='9':
                    ldate=30
                if mnth=='10':
                    ldate=31
                if mnth=='11':
                    ldate=30    
                if mnth=='12':
                    ldate=31  
            
                frmdt=date(int(year),int(mnth),01)
                todt=date(int(year),int(mnth),ldate)
                
                content['year']=frmdt.year
            dateDiff=todt-frmdt
            tr=transaction.objects.filter(datetime__range=(frmdt, todt))
            m=0
            trxn_list=[]
            k=0
            if mnth=='2':
                k=27
            else:
                k=30
            for single_date in (frmdt + timedelta(k) for n in range(1,((dateDiff.days)/k)+1)):
                
                todat=single_date
                trans=tr.filter(datetime__range=(frmdt, todat))
                
                m=m+1
                moonth=''
                if mnth=='all':
                    moonth="All"
                if m==1:
                    moonth="JAN"
                if m==2:
                    moonth="FEB"
                if m==3:
                    moonth="MAR"
                if m==4:
                    moonth="APR"
                if m==5:
                    moonth="MAY"
                if m==6:
                    moonth="JUN"
                if m==7:
                    moonth="JUL"
                if m==8:
                    moonth="AUG"
                if m==9:
                    moonth="SEP"
                if m==10:
                    moonth="OCT"
                if m==11:
                    moonth="NOV"
                if m==12:
                    moonth="DEC" 
                content['month']=moonth
                for j in userclubs:
                    dic={}
                    
                    adult_member=[];child_member=[];adult_guest=[];child_guest=[]
                    for i in mem_adult:                        
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:                             
                                if j==l.club.name:
                                    if l not in adult_member:
                                        adult_member.append(l)

                    for i in family_adult:                        
                        for l in trans:
                            if i.rfidcardno == l.rfidcardid:                             
                                if j == l.club.name:
                                    if l not in adult_member:
                                        adult_member.append(l)                    
                                             
                                
                    for i in family_child:
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in child_member:
                                        child_member.append(l)
                    for i in guest_adult:
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in adult_guest:
                                        adult_guest.append(l)    
                    for i in guest_child:
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in child_guest:
                                        child_guest.append(l)
                    
                    dic['club']=j 
                    dic['adult_member']=len(adult_member)
                    dic['child_member']=len(child_member)
                    dic['adult_guest']=len(adult_guest)
                    dic['child_guest']=len(child_guest)
                    if mnth=='all':
                        dic['fdate']=moonth+"-"+str(year)
                    else:
                        moonth=''
                        if todt.month==1:
                            moonth="JAN"
                        if todt.month==2:
                            moonth="FEB"
                        if todt.month==3:
                            moonth="MAR"
                        if todt.month==4:
                            moonth="APR"
                        if todt.month==5:
                            moonth="MAY"
                        if todt.month==6:
                            moonth="JUN"
                        if todt.month==7:
                            moonth="JUL"
                        if todt.month==8:
                            moonth="AUG"
                        if todt.month==9:
                            moonth="SEP"
                        if todt.month==10:
                            moonth="OCT"
                        if todt.month==11:
                            moonth="NOV"
                        if todt.month==12:
                            moonth="DEC" 
                        dic['fdate']=moonth+"-"+str(year)
                        
                    dic['total']=len(adult_member)+len(child_member)+len(adult_guest)+len(child_guest)
                    trxn_list.append(dic)
                
                frmdt=todat
            txn_new_list=[]
            if club_q=="All":  
                content['trxn_list']=trxn_list        
            else:
                for i in trxn_list:
                    if i['club']==club_q:
                        txn_new_list.append(i)
                content['trxn_list']=txn_new_list
            content['monthly']=1    
        if filter=="yearly":
            yearf = request.POST["yearpicker2"]
            yeart = request.POST["yearpicker3"]
            content['yearf']=yearf
            content['yeart']=yeart
            frmdt=date(int(yearf),01,01)
            todt=date(int(yeart)+1,01,01)
            dateDiff=todt-frmdt
            tr=transaction.objects.filter(datetime__range=(frmdt, todt))
            m=int(yearf)
            trxn_list=[]
            for single_date in (frmdt + timedelta(365) for n in range(1,((dateDiff.days)/365)+1)):
                
                todat=single_date
                trans=tr.filter(datetime__range=(frmdt, todat))
                for j in userclubs:
                    dic={}
                    
                    adult_member=[];child_member=[];adult_guest=[];child_guest=[]
                    for i in mem_adult:                        
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:                             
                                if j==l.club.name:
                                    if l not in adult_member:
                                        adult_member.append(l)
                                
                    for i in family_child:
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in child_member:
                                        child_member.append(l)

                    for i in family_adult:                        
                        for l in trans:
                            if i.rfidcardno == l.rfidcardid:                             
                                if j == l.club.name:
                                    if l not in adult_member:
                                        adult_member.append(l)                    
                                             
                                        
                    for i in guest_adult:
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in adult_guest:
                                        adult_guest.append(l)    
                    for i in guest_child:
                        for l in trans:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in child_guest:
                                        child_guest.append(l)
                    
                    dic['club']=j 
                    dic['adult_member']=len(adult_member)
                    dic['child_member']=len(child_member)
                    dic['adult_guest']=len(adult_guest)
                    dic['child_guest']=len(child_guest)
                    dic['fdate']=m
                    dic['total']=len(adult_member)+len(child_member)+len(adult_guest)+len(child_guest)
                    trxn_list.append(dic)
                m=m+1
                frmdt=todat
            txn_new_list=[]
            if club_q=="All":  
                content['trxn_list']=trxn_list        
            else:
                for i in trxn_list:
                    if i['club']==club_q:
                        txn_new_list.append(i)
                content['trxn_list']=txn_new_list
            content['yearly']=1
        if filter=="hourly":
            datefor= request.POST["dateh"]
            timefrom= request.POST["timefrom"]
            timeto= request.POST["timeto"]
            content['datefornew']=datefor
            content['timefrom']=timefrom
            content['timeto']=timeto
            hr1,min1=timefrom.split(":")
            min12=min1.split(" ")
            if min12[1]=='PM' and hr1!='12':
                hr1=int(hr1)+12
            if min12[1]=='AM' and hr1=='12':
                hr1=00
                
            hr2,min2=timeto.split(":")
            min22=min2.split(" ")
            if min22[1]=='PM' and hr2!='12':
                hr2= int(hr2)+12
            if min22[1]=='AM' and hr2=='12':
                hr2=00    
                
            year,mnth,day = datefor.split("-")
            try:
                ser_date=date(int(year),int(mnth),int(day))
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('reports.html',content,context_instance=RequestContext(request))
            datetime_start=datetime(int(year),int(mnth),int(day),int(hr1),int(min12[0]),00)
            datetime_end=datetime(int(year),int(mnth),int(day),int(hr2),int(min22[0]),00)
            trans_list=transaction.objects.filter(datetime__range=(datetime_start,datetime_end))
            content['datefor']=ser_date
            content['fromtime']=datetime_start.time()
            content['totime']=datetime_end.time()
            dateDiff=int(((datetime_end-datetime_start).total_seconds())/3600)
            start_time=datetime_start
            hourr=int(hr1)
            trxn_list=[]
            for n in range(0,dateDiff):
                hourr+=1
                end_time=datetime(int(year),int(mnth),int(day),hourr,int(min12[0]),00)
                filterd_tran=trans_list.filter(datetime__range=(start_time,end_time))
                
                #trans=tr.filter(datetime__range=(frmdat, todat))
                
                
                for j in userclubs:
                    dic={}
                    
                    adult_member=[];child_member=[];adult_guest=[];child_guest=[]
                    for i in mem_adult:                        
                        for l in filterd_tran:
                            if i.rfidcardno==l.rfidcardid:                             
                                if j==l.club.name:
                                    if l not in adult_member:
                                        adult_member.append(l)

                    for i in family_adult:                        
                        for l in filterd_tran:
                            if i.rfidcardno == l.rfidcardid:                             
                                if j == l.club.name:
                                    if l not in adult_member:
                                        adult_member.append(l)                    
                                     
                    for i in family_child:
                        for l in filterd_tran:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in child_member:
                                        child_member.append(l)
                    for i in guest_adult:
                        for l in filterd_tran:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in adult_guest:
                                        adult_guest.append(l)    
                    for i in guest_child:
                        for l in filterd_tran:
                            if i.rfidcardno==l.rfidcardid:
                                if j==l.club.name:
                                    if l not in child_guest:
                                        child_guest.append(l)
                    dic['club']=j 
                    dic['adult_member']=len(adult_member)
                    dic['child_member']=len(child_member)
                    dic['adult_guest']=len(adult_guest)
                    dic['child_guest']=len(child_guest)
                    dic['fdate']=start_time.time()
                    dic['tdate']=end_time.time()
                    dic['total']=len(adult_member)+len(child_member)+len(adult_guest)+len(child_guest)
                    trxn_list.append(dic)
                    
                start_time=end_time
            txn_new_list=[]
            if club_q=="All":  
                content['trxn_list']=trxn_list        
            else:
                for i in trxn_list:
                    if i['club']==club_q:
                        txn_new_list.append(i)
                content['trxn_list']=txn_new_list 
                
            content['time']=1    
    if request.method == "GET":
        
        if 'export' in request.GET:
            type = request.GET["typ"]
            filter=request.GET["filter"]
            club_q = request.GET["club"]

            content['club_q']=club_q
            content['filter']=filter
            x =  club.objects.filter(name__in=li)
            m = []
            for k in x:
                m.append(k.id)


            cls = clubstatus.objects.filter(club_id__in=m).values('member_id')
            n = deque()
            for b in cls:
                n.append(b['member_id'])

            obj_listg = guest.objects.all()
            obj_listm = member.objects.filter(id__in=n,status="Active").exclude(status='Inactive')
            obj_listf=family.objects.filter(member_id__in=n).exclude(status='Inactive')
            #print "ffaaaaaaaaaaaaaaaaaaaaaaaamlyyyyy",obj_listf
            guest_list=[]
            fam_list=[]
            mem_adult=[]
            guest_adult=[]
            guest_child=[]
            family_child =  obj_listf.filter(age__lte=21)
            family_adult=obj_listf.filter(age__gt=21)
            mem_adult =obj_listm         
            for i in obj_listg:
                for j in li:
                    if j in i.clubsallowed:
                        if i not in guest_list:
                            guest_list.append(i)
            
            for j in guest_list:            
                age=int((date.today().year-j.dob.year)/1.0+(date.today().month-j.dob.month)/12.0+(date.today().day-j.dob.day)/365.0)
                
                if age>=21:
                    guest_adult.append(j)
                else:
                    guest_child.append(j)

            if filter=="daily":
                fromdate = request.GET["fromdate"]
                todate = request.GET["todate"] 
                year,mnth,day = todate.split("-")
                sdate = date(int(year), int(mnth), int(day))
                difference = timedelta(days=1)
                todatee= sdate+difference
                tr=transaction.objects.filter(datetime__range=(fromdate, todatee))
                y1,m1,d1 = str(todatee).split("-")
                y2,m2,d2 = str(fromdate).split("-")
                
                tdate = date(int(y1), int(m1), int(d1))
                frdate = date(int(y2), int(m2), int(d2))
                
                dateDiff = tdate - frdate   
                frmdat=frdate

                trxn_list=[]
                
                for single_date in (frdate + timedelta(n) for n in range(1,(dateDiff.days)+1)):
                    
                    todat=single_date
                    trans=tr.filter(datetime__range=(frmdat, todat))
                    
                    
                    for j in li:
                        dic={}
                        
                        adult_member=[];child_member=[];adult_guest=[];child_guest=[]
                        for i in mem_adult:                        
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:                             
                                    if j==l.club.name:
                                        if l not in adult_member:
                                            adult_member.append(l)

                        for i in family_adult:                        
                            for l in trans:
                                if i.rfidcardno == l.rfidcardid:                             
                                    if j == l.club.name:
                                        if l not in adult_member:
                                            adult_member.append(l)


                        for i in family_child:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in child_member:
                                            child_member.append(l)
                        for i in guest_adult:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in adult_guest:
                                            adult_guest.append(l)    
                        for i in guest_child:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in child_guest:
                                            child_guest.append(l)
                        dic['club']=j 
                        dic['adult_member']=len(adult_member)
                        dic['child_member']=len(child_member)
                        dic['adult_guest']=len(adult_guest)
                        dic['child_guest']=len(child_guest)
                        dic['fdate']=frmdat
                        dic['total']=len(adult_member)+len(child_member)+len(adult_guest)+len(child_guest)
                        trxn_list.append(dic)
                    
                    frmdat=todat
                txn_new_list=[]
                if club_q=="All":  
                    pass        
                else:
                    for i in trxn_list:
                        if i['club']==club_q:
                            txn_new_list.append(i)
                    trxn_list=txn_new_list 

                if type == 'excel':
                    
                    filename = "Daily Club-Utilization Report"
                    
                    response = HttpResponse(content_type='application/ms-excel')
                    response['Content-Disposition'] = 'attachment; filename='+filename+"(" +str(fromdate)+' to '+str(todate)+" )"+ ".xls"
                    wb = xlwt.Workbook(encoding='utf-8')
                    ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                    row_num = 3
                    columns = [
                        (u"Date", 3000),
                        (u"Club", 6000),
                        (u"Adult Member",3200),
                        (u"Child Member",3200),
                        (u"Adult Guest",2800),
                        (u"Child Guest",2800),
                        (u"Total",2200),
                    ]
                    style = xlwt.easyxf('font: bold 1')
                    font_style = xlwt.XFStyle()
                    font_style.font.bold = True
                    ws.write(0,2,filename, font_style)

                    ws.write(1,1,"(Input Data: From Date="+" "+fromdate+", To Date="+" "+todate+", Club="+club_q+")")
                    for col_num in xrange(len(columns)):
                        ws.write(row_num, col_num, columns[col_num][0], font_style)
                        # set column width
                        ws.col(col_num).width = columns[col_num][1]
                    font_style = xlwt.XFStyle()
                    font_style.alignment.wrap =-1
                    for obj in trxn_list:
                        row_num += 1
                        row = [
                            str(obj['fdate']),
                            obj['club'],
                            obj['adult_member'],
                            obj['child_member'],
                            obj['adult_guest'],
                            obj['child_guest'],
                            obj['total'],
                        ]
                        
                        for col_num in xrange(len(row)):
                            ws.write(row_num, col_num, row[col_num], font_style)
                            
                    wb.save(response)
                    return response            
                    
            if filter=="weekly":
                month = request.GET["month"]
                year = request.GET["yearpicker"]
                moonth=''
                if month=='1':
                    moonth="JAN"
                if month=='2':
                    moonth="FEB"
                if month=='3':
                    moonth="MAR"
                if month=='4':
                    moonth="APR"
                if month=='5':
                    moonth="MAY"
                if month=='6':
                    moonth="JUN"
                if month=='7':
                    moonth="JUL"
                if month=='8':
                    moonth="AUG"
                if month=='9':
                    moonth="SEP"
                if month=='10':
                    moonth="OCT"
                if month=='11':
                    moonth="NOV"
                if month=='12':
                    moonth="DEC"   
                
                ldate=0
                if month=='1':
                    ldate=31
                if month=='2':
                    ldate=28
                if month=='3':
                    ldate=31
                if month=='4':
                    ldate=30
                if month=='5':
                    ldate=31
                if month=='6':
                    ldate=30
                if month=='7':
                    ldate=31
                if month=='8':
                    ldate=31
                if month=='9':
                    ldate=30
                if month=='10':
                    ldate=31
                if month=='11':
                    ldate=30    
                if month=='12':
                    ldate=31  
                frmdt=date(int(year),int(month),01)
                todt=date(int(year),int(month),ldate)
                
                dateDiff=todt-frmdt
                tr=transaction.objects.filter(datetime__range=(frmdt, todt))
                m=0
                trxn_list=[]
                for single_date in (frmdt + timedelta(7) for n in range(0,((dateDiff.days)/7)+1)):
                    
                    todat=single_date
                    trans=tr.filter(datetime__range=(frmdt, todat))
                    
                    m=m+1
                    for j in userclubs:
                        dic={}
                        
                        adult_member=[];child_member=[];adult_guest=[];child_guest=[]
                         
                        for i in mem_adult:                        
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:                             
                                    if j==l.club.name:
                                        if l not in adult_member:
                                            adult_member.append(l)

                        for i in family_adult:                        
                            for l in trans:
                                if i.rfidcardno == l.rfidcardid:                             
                                    if j == l.club.name:
                                        if l not in adult_member:
                                            adult_member.append(l)


                        for i in family_child:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in child_member:
                                            child_member.append(l)
                        for i in guest_adult:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in adult_guest:
                                            adult_guest.append(l)    
                        for i in guest_child:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in child_guest:
                                            child_guest.append(l)
                        
                        dic['club']=j 
                        dic['adult_member']=len(adult_member)
                        dic['child_member']=len(child_member)
                        dic['adult_guest']=len(adult_guest)
                        dic['child_guest']=len(child_guest)
                        dic['fdate']="WEEK-"+str(m)
                        dic['total']=len(adult_member)+len(child_member)+len(adult_guest)+len(child_guest)
                        trxn_list.append(dic)
                    
                    frmdt=todat
                txn_new_list=[]
                if club_q=="All":  
                    pass        
                else:
                    for i in trxn_list:
                        if i['club']==club_q:
                            txn_new_list.append(i)
                    trxn_list=txn_new_list
                if type == 'excel':
                    
                    filename = "Weekly Club-Utilization Report"
                    fromdate=date.today()
                    response = HttpResponse(content_type='application/ms-excel')
                    response['Content-Disposition'] = 'attachment; filename='+filename+"("+moonth+"-"+year+")"+".xls"
                    wb = xlwt.Workbook(encoding='utf-8')
                    ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                    row_num = 3
                    columns = [
                        (u"Week", 3000),
                        (u"Club", 6000),
                        (u"Adult Member",3200),
                        (u"Child Member",3200),
                        (u"Adult Guest",2800),
                        (u"Child Guest",2800),
                        (u"Total",2200),
                    ]
                    style = xlwt.easyxf('font: bold 1')
                    font_style = xlwt.XFStyle()
                    font_style.font.bold = True
                    ws.write(0,2,filename, font_style)
                    ws.write(1,1,"(Input Data: Month="+" "+moonth+", Year="+" "+year+", Club="+club_q+")")
                    for col_num in xrange(len(columns)):
                        ws.write(row_num, col_num, columns[col_num][0], font_style)
                        # set column width
                        ws.col(col_num).width = columns[col_num][1]
                    font_style = xlwt.XFStyle()
                    font_style.alignment.wrap =-1
                    for obj in trxn_list:
                        row_num += 1
                        row = [
                            obj['fdate'],
                            obj['club'],
                            obj['adult_member'],
                            obj['child_member'],
                            obj['adult_guest'],
                            obj['child_guest'],
                            obj['total'],
                        ]
                        
                        for col_num in xrange(len(row)):
                            ws.write(row_num, col_num, row[col_num], font_style)
                            
                    wb.save(response)
                    return response        
                   
            if filter=="monthly":
                year = request.GET["yearpicker"]
                mnth=request.GET["month1"]
                frmdt=''
                todt=''
                if mnth=='all':
                    frmdt=date(int(year),01,01)
                    todt=date(int(year),12,31)
                else:
                    ldate=0
                    if mnth=='1':
                        ldate=31
                    if mnth=='2':
                        ldate=28
                    if mnth=='3':
                        ldate=31
                    if mnth=='4':
                        ldate=30
                    if mnth=='5':
                        ldate=31
                    if mnth=='6':
                        ldate=30
                    if mnth=='7':
                        ldate=31
                    if mnth=='8':
                        ldate=31
                    if mnth=='9':
                        ldate=30
                    if mnth=='10':
                        ldate=31
                    if mnth=='11':
                        ldate=30    
                    if mnth=='12':
                        ldate=31  
                
                    frmdt=date(int(year),int(mnth),01)
                    todt=date(int(year),int(mnth),ldate)
                    
                    content['year']=frmdt.year
                dateDiff=todt-frmdt
                tr=transaction.objects.filter(datetime__range=(frmdt, todt))
                m=0
                trxn_list=[]
                k=0
                if mnth=='2':
                    k=27
                else:
                    k=30
                for single_date in (frmdt + timedelta(k) for n in range(1,((dateDiff.days)/k)+1)):
                    
                    todat=single_date
                    trans=tr.filter(datetime__range=(frmdt, todat))
                    
                    m=m+1
                    moonth=''
                    if mnth=='all':
                        moonth="All"
                    if m==1:
                        moonth="JAN"
                    if m==2:
                        moonth="FEB"
                    if m==3:
                        moonth="MAR"
                    if m==4:
                        moonth="APR"
                    if m==5:
                        moonth="MAY"
                    if m==6:
                        moonth="JUN"
                    if m==7:
                        moonth="JUL"
                    if m==8:
                        moonth="AUG"
                    if m==9:
                        moonth="SEP"
                    if m==10:
                        moonth="OCT"
                    if m==11:
                        moonth="NOV"
                    if m==12:
                        moonth="DEC" 
                    content['month']=moonth
                    for j in userclubs:
                        dic={}
                        
                        adult_member=[];child_member=[];adult_guest=[];child_guest=[]
                        for i in mem_adult:                        
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:                             
                                    if j==l.club.name:
                                        if l not in adult_member:
                                            adult_member.append(l)

                        for i in family_adult:                        
                            for l in trans:
                                if i.rfidcardno == l.rfidcardid:                             
                                    if j == l.club.name:
                                        if l not in adult_member:
                                            adult_member.append(l)
                                              
                        for i in family_child:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in child_member:
                                            child_member.append(l)
                        for i in guest_adult:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in adult_guest:
                                            adult_guest.append(l)    
                        for i in guest_child:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in child_guest:
                                            child_guest.append(l)
                        
                        dic['club']=j 
                        dic['adult_member']=len(adult_member)
                        dic['child_member']=len(child_member)
                        dic['adult_guest']=len(adult_guest)
                        dic['child_guest']=len(child_guest)
                        if mnth=='all':
                            dic['fdate']=moonth+"-"+str(year)
                        else:
                            moonth=''
                            if todt.month==1:
                                moonth="JAN"
                            if todt.month==2:
                                moonth="FEB"
                            if todt.month==3:
                                moonth="MAR"
                            if todt.month==4:
                                moonth="APR"
                            if todt.month==5:
                                moonth="MAY"
                            if todt.month==6:
                                moonth="JUN"
                            if todt.month==7:
                                moonth="JUL"
                            if todt.month==8:
                                moonth="AUG"
                            if todt.month==9:
                                moonth="SEP"
                            if todt.month==10:
                                moonth="OCT"
                            if todt.month==11:
                                moonth="NOV"
                            if todt.month==12:
                                moonth="DEC" 
                            dic['fdate']=moonth+"-"+str(year)
                            
                        dic['total']=len(adult_member)+len(child_member)+len(adult_guest)+len(child_guest)
                        trxn_list.append(dic)
                    
                    frmdt=todat
                txn_new_list=[]
                if club_q=="All":  
                    pass        
                else:
                    for i in trxn_list:
                        if i['club']==club_q:
                            txn_new_list.append(i)
                    trxn_list=txn_new_list
                
                if type == 'excel':
                    
                    filename = "Monthly Club-Utilization Report"
                    fromdate=date.today()
                    response = HttpResponse(content_type='application/ms-excel')
                    response['Content-Disposition'] = 'attachment; filename='+filename+"("+moonth+"-"+str(year)+")"+".xls"
                    wb = xlwt.Workbook(encoding='utf-8')
                    ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                    row_num = 3
                    columns = [
                        (u"Month", 3000),
                        (u"Club", 6000),
                        (u"Adult Member",3200),
                        (u"Child Member",3200),
                        (u"Adult Guest",2800),
                        (u"Child Guest",2800),
                        (u"Total",2200),
                    ]
                    style = xlwt.easyxf('font: bold 1')
                    font_style = xlwt.XFStyle()
                    font_style.font.bold = True
                    ws.write(0,2,filename, font_style)
                    ws.write(1,1,"(Input Data: Month="+" "+moonth+", Year="+" "+year+", Club="+club_q+")")
                    for col_num in xrange(len(columns)):
                        ws.write(row_num, col_num, columns[col_num][0], font_style)
                        # set column width
                        ws.col(col_num).width = columns[col_num][1]
                    font_style = xlwt.XFStyle()
                    font_style.alignment.wrap =-1
                    for obj in trxn_list:
                        row_num += 1
                        row = [
                            obj['fdate'],
                            obj['club'],
                            obj['adult_member'],
                            obj['child_member'],
                            obj['adult_guest'],
                            obj['child_guest'],
                            obj['total'],
                        ]
                        
                        for col_num in xrange(len(row)):
                            ws.write(row_num, col_num, row[col_num], font_style)
                            
                    wb.save(response)
                    return response    
            if filter=="yearly":
                yearf = request.GET["yearpicker2"]
                yeart = request.GET["yearpicker3"]
                frmdt=date(int(yearf),01,01)
                todt=date(int(yeart)+1,01,01)
                dateDiff=todt-frmdt
                tr=transaction.objects.filter(datetime__range=(frmdt, todt))
                m=int(yearf)
                trxn_list=[]
                for single_date in (frmdt + timedelta(365) for n in range(1,((dateDiff.days)/365)+1)):
                    
                    todat=single_date
                    
                    trans=tr.filter(datetime__range=(frmdt, todat))
                     
                    for j in userclubs:
                        dic={}
                        
                        adult_member=[];child_member=[];adult_guest=[];child_guest=[]
                        for i in mem_adult:                        
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:                             
                                    if j==l.club.name:
                                        if l not in adult_member:
                                            adult_member.append(l)

                        for i in family_adult:                        
                            for l in trans:
                                if i.rfidcardno == l.rfidcardid:                             
                                    if j == l.club.name:
                                        if l not in adult_member:
                                            adult_member.append(l)                    
                                    
                        for i in family_child:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in child_member:
                                            child_member.append(l)
                        for i in guest_adult:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in adult_guest:
                                            adult_guest.append(l)    
                        for i in guest_child:
                            for l in trans:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in child_guest:
                                            child_guest.append(l)
                        
                        dic['club']=j 
                        dic['adult_member']=len(adult_member)
                        dic['child_member']=len(child_member)
                        dic['adult_guest']=len(adult_guest)
                        dic['child_guest']=len(child_guest)
                        dic['fdate']=m
                        dic['total']=len(adult_member)+len(child_member)+len(adult_guest)+len(child_guest)
                        trxn_list.append(dic)
                    m=m+1
                    frmdt=todat
                txn_new_list=[]
                if club_q=="All":  
                    pass        
                else:
                    for i in trxn_list:
                        if i['club']==club_q:
                            txn_new_list.append(i)
                            trxn_list=txn_new_list
                if type == 'excel':
                    
                    filename = "Yearly Club-Utilization Report"
                    fromdate=date.today()
                    response = HttpResponse(content_type='application/ms-excel')
                    response['Content-Disposition'] = 'attachment; filename='+filename+"("+yearf+"-"+yeart+")"+".xls"
                    wb = xlwt.Workbook(encoding='utf-8')
                    ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                    row_num = 3
                    columns = [
                        (u"Year", 3000),
                        (u"Club", 6000),
                        (u"Adult Member",3200),
                        (u"Child Member",3200),
                        (u"Adult Guest",2800),
                        (u"Child Guest",2800),
                        (u"Total",2200),
                    ]
                    style = xlwt.easyxf('font: bold 1')
                    font_style = xlwt.XFStyle()
                    font_style.font.bold = True
                    ws.write(0,2,filename+"("+yearf+"-"+yeart+")", font_style)
                    ws.write(1,1,"(Input Data: Year From="+" "+yearf+", Year To="+" "+yeart+", Club="+club_q+")")
                    for col_num in xrange(len(columns)):
                        ws.write(row_num, col_num, columns[col_num][0], font_style)
                        # set column width
                        ws.col(col_num).width = columns[col_num][1]
                    font_style = xlwt.XFStyle()
                    font_style.alignment.wrap =-1
                    for obj in trxn_list:
                        row_num += 1
                        row = [
                            obj['fdate'],
                            obj['club'],
                            obj['adult_member'],
                            obj['child_member'],
                            obj['adult_guest'],
                            obj['child_guest'],
                            obj['total'],
                        ]
                        
                        for col_num in xrange(len(row)):
                            ws.write(row_num, col_num, row[col_num], font_style)
                            
                    wb.save(response)
                    return response
            if filter=="hourly":
                datefor= request.GET["dateh"]
                timefrom= request.GET["timefrom"]
                timeto= request.GET["timeto"]
                hr1,min1=timefrom.split(":")
                min12=min1.split(" ")
                if min12[1]=='PM' and hr1!='12':
                    hr1=int(hr1)+12
                if min12[1]=='AM' and hr1=='12':
                    hr1=00
                    
                hr2,min2=timeto.split(":")
                min22=min2.split(" ")
                if min22[1]=='PM' and hr2!='12':
                    hr2= int(hr2)+12
                if min22[1]=='AM' and hr2=='12':
                    hr2=00    
                    
                year,mnth,day = datefor.split("-")
                ser_date=date(int(year),int(mnth),int(day))
                datetime_start=datetime(int(year),int(mnth),int(day),int(hr1),int(min12[0]),00)
                datetime_end=datetime(int(year),int(mnth),int(day),int(hr2),int(min22[0]),00)
                trans_list=transaction.objects.filter(datetime__range=(datetime_start,datetime_end))
                
                content['datefor']=ser_date
                content['fromtime']=datetime_start.time()
                content['totime']=datetime_end.time()
                dateDiff=int(((datetime_end-datetime_start).total_seconds())/3600)
                
                start_time=datetime_start
                hourr=int(hr1)
                trxn_list=[]
                txn_new_list=[]
                for n in range(0,dateDiff):
                    hourr+=1
                    
                    
                    end_time=datetime(int(year),int(mnth),int(day),hourr,int(min12[0]),00)
                    
                    filterd_tran=trans_list.filter(datetime__range=(start_time,end_time))
                    
                    #trans=tr.filter(datetime__range=(frmdat, todat))
                    
                    
                    for j in userclubs:
                        dic={}
                        
                        adult_member=[];child_member=[];adult_guest=[];child_guest=[]
                        for i in mem_adult:                        
                            for l in filterd_tran:
                                if i.rfidcardno==l.rfidcardid:                             
                                    if j==l.club.name:
                                        if l not in adult_member:
                                            adult_member.append(l)

                        for i in family_adult:                        
                            for l in filterd_tran:
                                if i.rfidcardno == l.rfidcardid:                             
                                    if j == l.club.name:
                                        if l not in adult_member:
                                            adult_member.append(l)                    
                                    
                        for i in family_child:
                            for l in filterd_tran:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in child_member:
                                            child_member.append(l)
                        for i in guest_adult:
                            for l in filterd_tran:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in adult_guest:
                                            adult_guest.append(l)    
                        for i in guest_child:
                            for l in filterd_tran:
                                if i.rfidcardno==l.rfidcardid:
                                    if j==l.club.name:
                                        if l not in child_guest:
                                            child_guest.append(l)
                        dic['club']=j 
                        dic['adult_member']=len(adult_member)
                        dic['child_member']=len(child_member)
                        dic['adult_guest']=len(adult_guest)
                        dic['child_guest']=len(child_guest)
                        dic['fdate']=start_time.time()
                        dic['tdate']=end_time.time()
                        dic['total']=len(adult_member)+len(child_member)+len(adult_guest)+len(child_guest)
                        trxn_list.append(dic)
                        
                    start_time=end_time
                
                if club_q=="All":  
                    pass      
                else:
                    for i in trxn_list:
                        if i['club']==club_q:
                            txn_new_list.append(i)
                            trxn_list=txn_new_list
                     
                if type == 'excel':
                    
                    filename = "Hourly Club-Utilization Report"
                    fromdate=date.today()
                    response = HttpResponse(content_type='application/ms-excel')
                    response['Content-Disposition'] = 'attachment; filename='+filename+"("+datefor+")"+"("+timefrom+" to "+timeto+")"+".xls"
                    wb = xlwt.Workbook(encoding='utf-8')
                    ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                    row_num = 3
                    columns = [
                        (u"Time", 6000),
                        (u"Club", 6000),
                        (u"Adult Member",3200),
                        (u"Child Member",3200),
                        (u"Adult Guest",2800),
                        (u"Child Guest",2800),
                        (u"Total",2200),
                    ]
                    style = xlwt.easyxf('font: bold 1')
                    font_style = xlwt.XFStyle()
                    font_style.font.bold = True
                    ws.write(0,2,filename, font_style)
                    ws.write(1,1,"(Input Data: From Time="+" "+timefrom+", To Time="+" "+timeto+", Club="+club_q+")")
                    for col_num in xrange(len(columns)):
                        ws.write(row_num, col_num, columns[col_num][0], font_style)
                        # set column width
                        ws.col(col_num).width = columns[col_num][1]
                    font_style = xlwt.XFStyle()
                    font_style.alignment.wrap =-1
                    for obj in trxn_list:
                        row_num += 1
                        row = [
                            str(obj['fdate'])+"-"+str(obj['tdate']),
                            obj['club'],
                            obj['adult_member'],
                            obj['child_member'],
                            obj['adult_guest'],
                            obj['child_guest'],
                            obj['total'],
                        ]
                        
                        for col_num in xrange(len(row)):
                            ws.write(row_num, col_num, row[col_num], font_style)
                            
                    wb.save(response)
                    return response    
                            
    return render_to_response('reports.html',content,context_instance=RequestContext(request))             
    
@user_login_required
def settings(request):

    userid = request.session['user']
    form = MemberForm(user=userid)
    content = {}
    content['name'] = userid.name
    content.update(csrf(request))
    content['userid'] = userid.userid
    content['role'] = userid.role
    # status_obj = qpuser.objects.filter(member_id=mem_obj.id)
    li = []
    l = userid.clubsallowed
               
    clubs = []
    clubs_list = club.objects.all()

    for i in clubs_list:
        clubs.append(i.name)

    for i in clubs:
        if i in l:                
            li.append(i)

    content['clubsallowed'] = li
    content['residencelocation'] = userid.residencelocation
    content['username']=userid.name
    content['officephone'] = userid.officephone
    content['mobileno'] = userid.mobileno
    ids = []
    
    if str(userid.role) == 'Steward':
         return render_to_response('Steward/settings.html',content, context_instance=RequestContext(request))

    if str(userid.role) == 'Receptionist':
         return render_to_response('Receptionist/settings.html',content, context_instance=RequestContext(request))
   
    return render_to_response('settings.html',content, context_instance=RequestContext(request))

@user_login_required
def familyform(request):
    m_id = ' '
    url = '/familyform/'
    user = request.session['user']
    data = {}
    content={}
    content.update(csrf(request))


    if 'mid' in request.GET:
        mid = request.GET['mid']
        family_members = family.objects.filter(member=mid)
        mobj = member.objects.get(id=mid)
        li2 = []
        status_obj = clubstatus.objects.filter(member_id=mobj.id)
        userclubs = []
        l = user.clubsallowed
        clubs = []
        clubs_list = club.objects.all()

        for i in clubs_list:
            clubs.append(i.name)

        for i in clubs:
            if i in l:                
                userclubs.append(i)

        uclubs = club.objects.filter(name__in=userclubs)

        if status_obj:
            # status_obj = status_obj[0]
            for i in status_obj:
                for j in uclubs:
                    dic = {}
                    cname = club.objects.get(id=i.club_id)
                    dic['club'] = cname.name
                    dic['status'] = i.status
                    dic['expiry'] = i.date_of_expiry
                    dic['id'] = cname.id
                li2.append(dic)

        content = {'clubs_list':li2,'parent_name':mobj.name+' '+mobj.first_name_1,'staffid':mobj.member_uid,'username' :user.name,'url':url,'mid':mid,'family_members':family_members}
        if str(user.role) == 'Steward':
            return render_to_response('Steward/family_members.html',content, context_instance=RequestContext(request))
        else:
            return render_to_response('family_members.html',content, context_instance=RequestContext(request))

    if 'm_id' in request.GET:
        m_id = request.GET['m_id']
        memberobj = member.objects.get(id=m_id)
        data['member'] = m_id
        if memberobj.organization.name == 'QP':
            content['famid'] = memberobj.member_uid
        li = []
        l = memberobj.clubsallowed
       
        clubs = []
        clubs_list = club.objects.all()

        for i in clubs_list:
            clubs.append(i.name)

        if l:
            for i in clubs:
                if i in l:                
                    li.append(i)
        data['clubsallowed'] = club.objects.filter(name__in=li)

    form=FamilyForm(initial=data,user=user)
    if request.method == "POST":
        # if 'Cancel' in request.POST:
        #     return HttpResponseRedirect('/members')
        if 'mid' in request.POST:
            mid = request.POST['mid']
            fid = request.POST['fid']

            if not fid:
                form=FamilyForm(user,request.POST)
                for name, field in form.fields.iteritems():
                    field.required = False
                profile = form.save(commit=False)
                profile.datetime = datetime.now()
                mem_obj = member.objects.get(id=mid)
                profile.status = mem_obj.status
                profile.save()
                f_newid = family.objects.filter(member_id=mid).order_by('-id')
                if 'Imagefile' in request.FILES:
                    f = request.FILES['Imagefile']
                    file_name = f.name
                    flist = file_name.split(".")
                    data = f.read()
                    f.close()
                    f = open(os.path.join(conf_settings.IMAGE_ROOT, "%s.%s" %(mem_obj.member_uid+'_'+str(f_newid[0].id),flist[1])), "wb")
                    f.write(data)
                    f.close()
                if 'Imagefile' in request.FILES:
                    f = request.FILES['Imagefile']
                    if f:
                        # memObj = member.objects.latest('id')
                        imageUrl  = "%s.%s" %(mem_obj.member_uid+'_'+str(f_newid[0].id),flist[1])
                        # print imageUrl
                        f_obj = family.objects.get(id=f_newid[0].id)
                        f_obj.photo =  imageUrl
                        f_obj.save()
                if 'Imagefile' not in request.FILES:
                    f_obj = family.objects.get(id=f_newid[0].id)
                    imageUrl  = 'People.jpg'
                    f_obj.photo =  imageUrl
                    f_obj.save()
                f_obj = family.objects.get(id=f_newid[0].id)
                f_obj.family_uid = str(mem_obj.member_uid)+'000'+str(f_obj.id)
                days_in_year = 365.2425
                if 'dob' in request.POST:
                    d1 = request.POST['dob']
                else:
                    d1=data[5]
                day,month,year = d1.split('-')
                mt=1
                if month=="JAN":
                    mt=1
                elif month=="FEB":
                    mt=2
                elif month=="MAR":
                    mt=3
                elif month=="APR":
                    mt=4
                elif month=="MAY":
                    mt=5
                elif month=="JUN":
                    mt=6
                elif month=="JUL":
                    mt=7
                elif month=="AUG":
                    mt=8
                elif month=="SEP":
                    mt=9
                elif month=="OCT":
                    mt=10
                elif month=="NOV":
                    mt=11  
                elif month=="DEC":
                    mt=12          

                if int(year)>=40:
                    year='19'+year
                    
                else:
                    year='20'+year
                    
                #dob=date(int(year),mt,int(day))
                age = int((date.today() - f_obj.dob).days / days_in_year)
                if age >= 21 and f_obj.relationship != 'W' and not f_obj.date_of_expiry:
                    f_obj.status = 'Pending-Crossed-Age 21'

                if f_obj.relationship == 'H' or f_obj.relationship == 'W':
                    f_obj.status = mem_obj.status
                f_obj.age = age
                f_obj.save()
                return HttpResponse('<script type="text/javascript">window.close();window.opener.location.reload(true);</script>')     
                # return HttpResponseRedirect('/members')
            if fid:
                form=FamilyForm(user,request.POST)
                print form.errors
                if form.is_valid():
                    f_obj = family.objects.get(id=fid)
                    f_form = FamilyForm(user,request.POST, instance = f_obj)
                    f_form.save()
                    if 'Imagefile' in request.FILES:
                        f = request.FILES['Imagefile']
                        #f = open(settings.IMAGE_ROOT,"ListingImages\\Customer-%s.%s" %(cid,flist[1]), "wb")
                        file_name = f.name
                        flist = file_name.split(".")
                        data = f.read()
                        f.close()
                        f = open(conf_settings.IMAGE_ROOT + "%s.%s" %(f_obj.family_uid+'_'+str(f_obj.id),flist[1]),"wb")
                        f.write(data)
                        f.close()
                        imageUrl  = "%s.%s" %(f_obj.family_uid+'_'+str(f_obj.id),flist[1])
                    if 'Imagefile' in request.FILES:
                        f = request.FILES['Imagefile']
                        f_obj = family.objects.get(id=fid)
                        f_obj.photo = imageUrl
                        f_obj.save()
                    fobj = family.objects.get(id=fid)
                    days_in_year = 365.2425    
                    age = int((date.today() - fobj.dob).days / days_in_year)
                    if age >= 21 and fobj.relationship != 'W' and not fobj.date_of_expiry:
                        fobj.status = 'Pending-Crossed-Age 21'
                    else:
                        fobj.status = fobj.member.status

                    if fobj.relationship == 'H':
                        fobj.status = fobj.member.status
                    
                    if fobj.date_of_expiry:
                        if fobj.date_of_expiry < date.today():
                            fobj.status = 'Pending-Crossed-Age 21'
                    fobj.age = age
                    fobj.save()
                    return HttpResponse('<script type="text/javascript">window.close();window.opener.location.reload(true);</script>')
        
        
        if 'famid' in request.POST:
            famid=request.POST['famid']
            if famid:
                path = os.path.join(os.path.dirname(__file__))
                book=xlrd.open_workbook(path + '/static/Qpfam.xlsx')
                sheet = book.sheet_by_index(0)
                r = sheet.row(0)
                c = sheet.col_values(1)      
                
                for i in range(len(c)):
                    data = []
                    if(c[i] == famid):                
                        r = sheet.row(i)
                       
                        for j in range(len(r)):
                            data.append(r[j].value)
                        
                        if famid not in c:
                            err_msg = 'Sorry! There is no Family with this ID'
                            content = {'username':user.name,'err_msg':err_msg,'form':form}
                            if str(user.role) == 'Steward':
                                return render_to_response('Steward/familyform.html',content,context_instance=RequestContext(request))
                            else:
                                return render_to_response('familyform.html',content, context_instance=RequestContext(request))
                        fname = data[2]
                        sname =data[3]
                        family_uid = data[1]
                        # if data[4] == 'W':
                        #     relationship = 'Spouse'
                        # else:
                        #     relationship = 'Children'
                        relationship = data[4]
                        d1=data[5]
                        day,month,year=d1.split('-')
                        mt=1
                        if month=="JAN":
                            mt=1
                        elif month=="FEB":
                            mt=2
                        elif month=="MAR":
                            mt=3
                        elif month=="APR":
                            mt=4
                        elif month=="MAY":
                            mt=5
                        elif month=="JUN":
                            mt=6
                        elif month=="JUL":
                            mt=7
                        elif month=="AUG":
                            mt=8
                        elif month=="SEP":
                            mt=9
                        elif month=="OCT":
                            mt=10
                        elif month=="NOV":
                            mt=11  
                        elif month=="DEC":
                            mt=12          

                        if int(year)>40:
                            year='19'+year
                            
                        else:
                            year='20'+year
                            
                        dob=date(int(year),mt,int(day))
                        dependent_sequence=data[6]
                        datetimee = datetime.now()
                        mmid=member.objects.filter(member_uid=famid).exclude(status='InActive')
                        if not mmid:
                            return HttpResponse('<script type="text/javascript">alert("No Member with this ID");window.close();</script>')
                        # except Exception:
                        #     pass
                        #     return HttpResponse('<script type="text/javascript">alert("No Member with this ID");window.close();</script>')
                        else:
                            mmid = mmid[0]
                        mem = mmid.name
                        status = mmid.status
                        l = mmid.clubsallowed
                        li = []
                        clubs = []
                        clubs_list = club.objects.all()

                        for i in clubs_list:
                            clubs.append(i.name)

                        for i in clubs:
                            if i in l:                
                                li.append(i)
                        # data['clubsallowed'] = club.objects.filter(name__in=li)
                        clubs = club.objects.filter(name__in=li)
                        f=family(datetime=datetime.now(),dapendent_first_name1=fname,dependent_family_name=sname,dependent_sequence=dependent_sequence,relationship=relationship,dob=dob,date_of_joining=mmid.date_of_joining,date_of_expiry=mmid.date_of_expiry,family_uid=family_uid,status=status,member=mmid,clubsallowed=clubs,photo='People.jpg')    
                        fm_id=family.objects.filter(member=mmid,dapendent_first_name1=fname)
                        
                        if not fm_id:
                            f.save()
                            fobj = family.objects.latest('id')
                            memobj = member.objects.get(id=fobj.member_id)
                            fobj.family_uid = str(memobj.member_uid)+'000'+str(fobj.id)
                            days_in_year = 365.2425    
                            age = int((date.today() - fobj.dob).days / days_in_year)
                            fobj.age = age
                            if age >= 21 and fobj.relationship != 'W' and not fobj.date_of_expiry:
                                fobj.status = 'Pending-Crossed-Age 21'

                            if fobj.relationship == 'H':
                                fobj.status = memobj.status
                            fobj.save()
        return HttpResponse('<script type="text/javascript">window.close();window.opener.location.reload(true);</script>')
                    # else:
                        # return HttpResponse('<script type="text/javascript">window.close();</script>')
                    # if fm_id!=[]:
                        # msg="These Family Members Are Already Added"
                        # content={'err_msg':msg}
                        # return render_to_response('familyform.html',content, context_instance=RequestContext(request))
    if 'fid' in request.GET:
        fid = request.GET['fid']
        f_obj = family.objects.get(id=fid)
        data['dapendent_first_name1'] = f_obj.dapendent_first_name1
        data['dependent_family_name'] = f_obj.dependent_family_name
        data['dependent_sequence'] = f_obj.dependent_sequence
        data['family_uid'] = f_obj.family_uid
        data['contact_no'] = f_obj.contact_no
        li = []
        m_obj = member.objects.get(id=f_obj.member_id)
        cls = clubstatus.objects.filter(member_id=m_obj.id)
        for i in cls:
            li.append(i.club_id)
        # tot_clubs = club.objects.filter(name__in=li)
        data['clubsallowed'] = li
        #data['gender'] = f_obj.gender
        data['emailid'] = f_obj.emailid
        data['nationality'] = f_obj.nationality
        data['date_of_joining'] = f_obj.date_of_joining
        data['date_of_expiry'] = f_obj.date_of_expiry
        data['contact_no'] = f_obj.contact_no
        data['rfidcardno'] = f_obj.rfidcardno
        #data['organization'] = f_obj.organization
        data['dob'] = f_obj.dob
        #data['age'] = f_obj.age
        data['status'] = f_obj.status
        data['relationship'] = f_obj.relationship
        data['member'] = f_obj.member
        content['photo'] = f_obj.photo
        content['IMAGE_URL'] = conf_settings.IMAGE_URL
        data['datetime'] = f_obj.datetime
        rform = FamilyForm(initial=data,user=user)
        content['mid'] = f_obj.member
        content['form'] = rform
        content['url'] = url
        content['username'] = user.name
        content['fid'] = fid
        if str(user.role) == 'Steward':
            return render_to_response('Steward/familyform.html',content, context_instance=RequestContext(request))
        else:
             return render_to_response('familyform.html',content, context_instance=RequestContext(request))

    # content = {'username' :user.name,'form':form, 'url':url,'mid':m_id}
    content['form'] = form
    content['url'] = url
    content['mid'] = m_id
    content['username'] = user.name
    if str(user.role) == 'Steward':
        return render_to_response('Steward/familyform.html',content,context_instance=RequestContext(request))
    return render_to_response('familyform.html',content, context_instance=RequestContext(request))


@user_login_required
def search(request):

    user = request.session['user']
    mem_list = []

    content={}
    content.update(csrf(request))

    if request.method == 'POST':
        search_text = request.POST['search_text']
        if search_text:
            mems = member.objects.filter(Q(name__icontains=search_text)|Q(member_uid__icontains=search_text)).exclude(status='Inactive')[:20]
            # f_mems = family.objects.filter(Q(family_uid__icontains=search_text)).exclude(status='Inactive')[:20]
            # print f_mems
            # if f_mems:
            #     for i in f_mems:
            #         mems.append(i.member)
            # print mems
            if mems:
            #     li=[]
            #     l = user.clubsallowed
                   
            #     clubs = []
            #     clubs_list = club.objects.all()

            #     for i in clubs_list:
            #         clubs.append(i.name)

            #     for i in clubs:
            #         if i in l:                
            #             li.append(i)
            #     for i in mems:
            #         for j in li:
            #             if j in i.clubsallowed:
            #                 mem_list.append(i)
                for i in mems:
                    mem_list.append(str(i.member_uid))
                    mem_list.append(str(i.name))
            json_stuff = simplejson.dumps({"list_of_jsonstuffs" : mem_list})    
            return HttpResponse(json_stuff, content_type ="application/json")



@user_login_required
def nearrenewal(request):
    url = '/nearrenewal/'
    msg = ''
    content={}
    content.update(csrf(request))
    #txnew_list=[]
    user = request.session['user']
    
    content['username']=user.name
    content['url'] = url
    userclubs=[]
    userclub1=[]
    userclub1.append('All')
    l = user.clubsallowed
    clb_list=[]
    clubs =club.objects.all()   
    for i in clubs:
        clb_list.append(i.name)
    for i in clb_list:
        if i in l:                
            userclubs.append(i)
            userclub1.append(i)
    content['userclubs']=userclub1  
    near_renw_obj=[]
    if request.method == "POST":
        club_q=request.POST['club']
        content['club_q']=club_q
        if club_q=='All':
            renew_mem=clubstatus.objects.all().exclude(status='Inactive')
        else:
            club_id=club.objects.get(name=club_q)
            renew_mem=clubstatus.objects.filter(club=club_id).exclude(status='Inactive')
        for i in renew_mem:
            if i.date_of_expiry != None:
                if (i.date_of_expiry-date.today()).days <=15:
                    for j in userclubs:
                        if j==i.club.name:
                            near_renw_obj.append(i)
                    content['renew_mem']=near_renw_obj
        if len(near_renw_obj) == 0:
            msg = 'No records found !!!' 
            content['msg']=msg
            if str(user.role) == 'Steward':
               return render_to_response('Steward/nearrenewalreport.html',content,context_instance=RequestContext(request))
            return render_to_response('nearrenewalreport.html',content,context_instance=RequestContext(request))
        
    
    if request.method == "GET":
        if 'export' in request.GET:

            typ = request.GET['type']
            club_q=request.GET['club']
            if club_q=='All':
                renew_mem=clubstatus.objects.all().exclude(status='Inactive')
            else:
                club_id=club.objects.get(name=club_q)
                renew_mem=clubstatus.objects.filter(club=club_id).exclude(status='Inactive')
            for i in renew_mem:
                if i.date_of_expiry != None:
                    if (i.date_of_expiry-date.today()).days <=15:
                        for j in userclubs:
                            if j==i.club.name:
                                near_renw_obj.append(i)
                        content['renew_mem']=near_renw_obj
                        
            if typ == 'excel':
                filename = "Near Renewal Report"
                fromdate=date.today()
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename='+filename+"("+str(fromdate)+").xls"
                wb = xlwt.Workbook(encoding='utf-8')
                ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                row_num = 3
                columns = [
                    (u"Staff Id", 6000),
                    (u"Name", 6000),
                    (u"Date Of Expiry",4000),
                    (u"Club",4000),
                    
                ]
                style = xlwt.easyxf('font: bold 1')
                font_style = xlwt.XFStyle()
                font_style.font.bold = True
                ws.write(0,1,filename+" On "+str(fromdate), font_style)
                font_style1 = xlwt.XFStyle()
                font_style1.font.bold = False
                ws.write(1,1,"(Input Data: Club= "+club_q+")", font_style1)
                for col_num in xrange(len(columns)):
                    ws.write(row_num, col_num, columns[col_num][0], font_style)
                    # set column width
                    ws.col(col_num).width = columns[col_num][1]
                font_style = xlwt.XFStyle()
                font_style.alignment.wrap =-1
                for obj in near_renw_obj:
                    row_num += 1
                    row = [
                        obj.member.member_uid,
                        obj.member.name+" "+obj.member.first_name_1+" "+obj.member.first_name_2,
                        str(obj.date_of_expiry),
                        str(obj.club),
                   
                    ]
                    for col_num in xrange(len(row)):
                        ws.write(row_num, col_num, row[col_num], font_style)
                        
                wb.save(response)
                return response
            
    if str(user.role) == 'Steward':
           return render_to_response('Steward/nearrenewalreport.html',content,context_instance=RequestContext(request))                
    return render_to_response('nearrenewalreport.html',content,context_instance=RequestContext(request))

@user_login_required
def attendancereport(request):
    url = '/attendancereport/'
    msg = ''
    obj_list={}
    txnew_list=[] 
    content={}
    content.update(csrf(request))
    user = request.session['user']
    content['username']=user.name
    content['url'] = url
    userclubs=[]
    userclub1=[]
    userclub1.append('All')
    l = user.clubsallowed
    clb_list=[]
    clubs =club.objects.all()   
    for i in clubs:
        clb_list.append(i.name)
    for i in clb_list:
        if i in l:                
            userclubs.append(i)
            userclub1.append(i)
    content['userclubs']=userclub1        
    if request.method == "POST":
        fromdate = request.POST["fromdate"]
        content['frmdate'] = fromdate
        todate = request.POST["todate"]
        club_q=request.POST["club"]
        content['club_q'] = club_q
        content['tdate'] = todate
        year,mnth,day = todate.split("-")
        try:
            sdate = date(int(year), int(mnth), int(day))
        except:
            msssg="The Date You Entered Is Invalid"
            content['msssg']=msssg
            return render_to_response('attendancereport.html',content,context_instance=RequestContext(request))    
        difference = timedelta(days=1)
        todate= sdate+difference
        member_id = request.POST["member"]

        content['mid'] = member_id
        obj_listm=[]
        obj_listf=[]
        year1,mnth1,day1 = fromdate.split("-")
        ndate=date(int(year1), int(mnth1), int(day1))
        content['fromdate']=ndate
        content['todate']=sdate
        content['member_id']=member_id
        try:
            obj_listm = member.objects.get(member_uid=member_id)
        except Exception:
            pass
        try:
            obj_listf = family.objects.get(family_uid=member_id)           
        except Exception:
            pass
        if not obj_listm and not obj_listf:    
            msg="This Member Id Does Not Exist"
            content['msg']=msg
            return render_to_response('attendancereport.html',content,context_instance=RequestContext(request))
            
        if obj_listm:    
            card_id=obj_listm.rfidcardno 
            try:
                obj_list= transaction.objects.filter(rfidcardid=card_id,datetime__range=(fromdate, todate))
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('attendancereport.html',content,context_instance=RequestContext(request))
            for i in obj_list:
                dic = {}        
                
                if i.club.name in userclubs:                  
                    dic['club']=i.club.name
                    dic['datetime'] = i.datetime
                    txnew_list.append(dic)
            txn_new_list=[]        
            if club_q=="All":  
                content['report_list']=txnew_list
                
            else:
                for i in txnew_list:
                    if i['club']==club_q:
                        txn_new_list.append(i)
                        
                content['report_list']=txn_new_list 
                     
            if len(txnew_list) == 0:
                msg = 'No records found !!!' 
                content['msg']=msg
            if len(txn_new_list) == 0 and club_q != "All":
                msg = 'No records found !!!' 
                content['msg']=msg       
                return render_to_response('attendancereport.html',content,context_instance=RequestContext(request))
            return render_to_response('attendancereport.html',content,context_instance=RequestContext(request))
        if obj_listf:    
            card_id=obj_listf.rfidcardno 
            try:
                obj_list= transaction.objects.filter(rfidcardid=card_id,datetime__range=(fromdate, todate))
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('attendancereport.html',content,context_instance=RequestContext(request))
            for i in obj_list:
                dic = {}        
                
                if i.club.name in userclubs:                  
                    dic['club']=i.club.name
                    dic['datetime'] = i.datetime
                    txnew_list.append(dic)                        
            txn_new_list=[]        
            if club_q=="All":  
                content['report_list']=txnew_list
                
            else:
                for i in txnew_list:
                    if i['club']==club_q:
                        txn_new_list.append(i)
                        
                content['report_list']=txn_new_list        
            if len(txnew_list) == 0:
                msg = 'No records found !!!' 
                content['msg']=msg
                    
                return render_to_response('attendancereport.html',content,context_instance=RequestContext(request))
            return render_to_response('attendancereport.html',content,context_instance=RequestContext(request))
    
    if request.method == "GET":
        if 'd1' in request.GET:
            fromdate = request.GET["d1"]
            tdate = request.GET["d2"]
            typ = request.GET["type"]
            club_q = request.GET["club"]
            member_id = request.GET['mid']
            year,mnth,day = tdate.split("-")
            sdate = date(int(year), int(mnth), int(day))
            difference = timedelta(days=1)
            todate= sdate+difference
            obj_listf = []
            obj_listm=[]
            txn_new_list=[]
            try:
                obj_listm = member.objects.get(member_uid=member_id)
            except Exception:
                pass
            try:
                obj_listf = family.objects.get(family_uid=member_id)           
            except Exception:
                pass
                
            if obj_listm:    
                card_id=obj_listm.rfidcardno 
                obj_list= transaction.objects.filter(rfidcardid=card_id,datetime__range=(fromdate, todate))
                
                for i in obj_list:
                    dic = {}        
                    
                    if i.club.name in userclubs:                  
                        dic['uid']=obj_listm.member_uid
                        dic['club']=i.club.name
                        dic['datetime'] = i.datetime
                        txnew_list.append(dic)
                if club_q=="All":  
                    txn_new_list=txnew_list
                    
                else:
                    for i in txnew_list:
                        if i['club']==club_q:
                            txn_new_list.append(i)
            if obj_listf:    
                card_id=obj_listf.rfidcardno 
                obj_list= transaction.objects.filter(rfidcardid=card_id,datetime__range=(fromdate, todate))
                
                for i in obj_list:
                    dic = {}        
                    
                    if i.club.name in userclubs:   
                        dic['uid']=obj_listf.family_uid
                        dic['club'] = i.club.name
                        dic['datetime'] = i.datetime
                        txnew_list.append(dic)
                        
                if club_q=="All":  
                    txn_new_list=txnew_list
                    
                else:
                    for i in txnew_list:
                        if i['club']==club_q:
                            txn_new_list.append(i)
                            
                        
            
            if typ == 'excel':
                filename = "Attendance Report"
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename='+filename+"("+str(fromdate)+" To "+str(tdate)+").xls"
                wb = xlwt.Workbook(encoding='utf-8')
                ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                row_num = 3
                columns = [
                    (u"Staff Id", 6000),
                    (u"Date Of Visit", 6000),
                    (u"Club Visited", 6000),
                ]
                style = xlwt.easyxf('font: bold 1')
                font_style = xlwt.XFStyle()
                font_style.font.bold = True
                ws.write(0,1,filename, font_style)
                font_style1 = xlwt.XFStyle()
                font_style1.font.bold = False
                ws.write(1,0,"(Input Data: From Date="+" "+fromdate+" To Date="+" "+tdate+" Staff Id= "+member_id +" Club="+club_q+")", font_style1)
                for col_num in xrange(len(columns)):
                    ws.write(row_num, col_num, columns[col_num][0], font_style)
                    # set column width
                    ws.col(col_num).width = columns[col_num][1]
                font_style = xlwt.XFStyle()
                font_style.alignment.wrap =-1
                for obj in txn_new_list:
                    row_num += 1
                    row = [
                        obj['uid'],
                        str(obj['datetime']),
                        str(obj['club']),
                    ]
                    for col_num in xrange(len(row)):
                        ws.write(row_num, col_num, row[col_num], font_style)
                        
                wb.save(response)
                return response
            
    return render_to_response('attendancereport.html',content,context_instance=RequestContext(request))


@user_login_required
def newmembershipreport(request):
    url = '/newmemberreport/'
    msg = ''
    obj_listm={}
    txnew_list=[] 
    content={}
    content.update(csrf(request))
    user = request.session['user']
    content['username']=user.name
    userclubs=[]
    userclub1=[]
    userclub1.append('All')

    
    # l = user.clubsallowed
    # clb_list=[]
    # clubs =club.objects.all()   
    # for i in clubs:
    #     clb_list.append(i.name)
    # for i in clb_list:
    #     if i in l:                
    #         userclubs.append(i)
    #         userclub1.append(i)
    l = user.clubsallowed
    clubs = []
    clubs_list = club.objects.all()

    for i in clubs:
        if i in l:                
            userclubs.append(i)

    li=[]
    # l = mem_obj.clubsallowed
   
    clubs = []
    clubs_list = club.objects.all()

    for i in clubs_list:
        clubs.append(i.name)

    for i in clubs:
        if i in l:                
            li.append(i)
            userclub1.append(i)
    content['userclubs']=userclub1        
    content['url'] = url
    fromdate=''
    todate=''
    if request.method == "POST":
        

        x =  club.objects.filter(name__in=li)
        m = []
        for k in x:
            m.append(k.id)


        cls = clubstatus.objects.filter(club_id__in=m)
        n = deque()
        m_clubs = deque()
        for b in cls:
            # if b.member_id not in n:
                n.append(b.member_id)

        fromdate = request.POST["fromdate"]
        content['frmdate'] = fromdate
        todate = request.POST["todate"]
        content['tdate'] = todate
        club_q = request.POST["club"]
        content['club_q'] = club_q
        year,mnth,day = todate.split("-")
        try:
            sdate = date(int(year), int(mnth), int(day))
        except:
            msssg="The Date You Entered Is Invalid"
            content['msssg']=msssg
            return render_to_response('newmemberreport.html',content,context_instance=RequestContext(request))
        difference = timedelta(days=1)
        todate= sdate+difference
        #try:
        #print m[0]
        obj_listm = member.objects.filter(datetime__range=(fromdate, todate),id__in=n,status="Active")
        # except:
        #     msssg="The Date You Entered Is Invalid"
        #     content['msssg']=msssg
        #     return render_to_response('newmemberreport.html',content,context_instance=RequestContext(request))
        # result = []
        # page = request.GET.get('page')
        # try:
        #     for i in obj_listm: 
        #         result.append(i)    
        #     paginator = Paginator(result, 100)
        #     result = paginator.page(page)
        # except PageNotAnInteger:
        #     # If page is not an integer, deliver first page.
        #     result = paginator.page(1)
        # except EmptyPage:
        #     # If page is out of range (e.g. 9999), deliver last page of results.
        #     result = paginator.page(paginator.num_pages)
        #     print result
        
        year1,mnth1,day1 = fromdate.split("-")
        ndate=date(int(year1), int(mnth1), int(day1))
        content['fromdate']=ndate
        content['todate']=sdate
        # obj_list = transaction.objects.all()       
        #result1 = []
        # if request.is_ajax():
        #     result1 = []
        #     page = 1
        #     if 'page' in request.GET:
        #         query = request.GET.get('page')
        #         #active_members = member.objects.all().exclude(status='Membership-Rejected')
        #         if query is not None:
        #             page = query
        #         try:
        #             for i in obj_listm: 
        #                 result1.append(i)    
        #             paginator = Paginator(result, 100)
        #             result = paginator.page(page)
        #         except PageNotAnInteger:
        #             # If page is not an integer, deliver first page.
        #             result = paginator.page(1)
        #         except EmptyPage:
        #             # If page is out of range (e.g. 9999), deliver last page of results.
        #             result1 = paginator.page(paginator.num_pages)
        #         result = result1
   
        #obj_list1 = member.objects.all().exclude(status='Inactive')         
        for i in obj_listm:
            #print "fooooooooorrrrrrrrrrrrrrr"
            dic = {}
            mem_clubs=[]
            for j in li:
                if j in i.clubsallowed:
                   mem_clubs.append(str(j))
            length=1       
            # if mem_clubs:            
            dic['uid'] = i.member_uid
            dic['rfidcardid'] = i.rfidcardno
            dic['date_of_joining'] = i.datetime.date()
            dic['name'] = i.name+" "+i.first_name_1
            if club_q == 'All':
                dic['clubs'] = mem_clubs
            else:
                dic['clubs'] = club_q
                length=0
                
            dic['doneby'] =i.qpuser.name
            content['length']= length   
            txnew_list.append(dic)
        txn_new_list=[]        
        if club_q == "All":
            content['report_list'] = txnew_list
        else:    
            for i in txnew_list:
                if club_q in i['clubs']:
                    txn_new_list.append(i)
                    
            content['report_list'] = txn_new_list
            
        if len(obj_listm)==0 or len(txnew_list)== 0 or (len(txn_new_list)==0 and club_q!="All"):
            msg = 'No record found !!!' 
            content['msg']=msg
       
    if request.method == "GET":
        
        if 'd1' in request.GET:
            print "geeeeet"
            fromdate = request.GET["d1"]
            tdate = request.GET["d2"]
            typ = request.GET["type"]
            club_q = request.GET["club"]
            year,mnth,day = tdate.split("-")
            sdate = date(int(year), int(mnth), int(day))
            difference = timedelta(days=1)
            todate= sdate+difference
            x =  club.objects.filter(name__in=li)
            m = []
            for k in x:
                m.append(k.id)


            cls = clubstatus.objects.filter(club_id__in=m)
            n = deque()
            for b in cls:
                if b.member_id not in n:
                    n.append(b.member_id)
            obj_listm = member.objects.filter(datetime__range=(fromdate, todate),id__in=n,status='Active')         
            for i in obj_listm:
            
                dic = {}
                mem_clubs=[]
                for j in li:
                    if j in i.clubsallowed:
                       mem_clubs.append(str(j))
                if mem_clubs:            
                    dic['uid'] = i.member_uid
                    dic['rfidcardid'] = i.rfidcardno
                    dic['date_of_joining'] = i.datetime.date()
                    dic['name'] = i.name+" "+i.first_name_1
                    dic['clubs'] =mem_clubs
                    dic['doneby'] =i.qpuser.name
                
                    txnew_list.append(dic)
            txn_new_list=[]        
            if club_q=="All":
                txn_new_list=txnew_list
            else:    
                for i in txnew_list:
                    if club_q in i['clubs']:
                        txn_new_list.append(i)
            #print txn_new_list          
                #content['report_list']=txn_new_list        
            if typ == 'excel':
                #print "geeeeet"
                filename = "New Membership Report"
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename='+filename+"("+str(fromdate)+" TO "+str(tdate)+").xls"
                wb = xlwt.Workbook(encoding='utf-8')
                ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                if club_q=="All":
                    row_num =3
                    columns = [
                        (u"Staff ID", 5000),
                        (u"Name", 6000),
                        (u"Date of Joining",6000,),
                        (u"Clubs", 8000),
                        (u"Added By", 8000),
                    ]
                    style = xlwt.easyxf('font: bold 1')
                    font_style = xlwt.XFStyle()
                    font_style.font.bold = True
                    ws.write(0,2,filename, font_style)
                    font_style1 = xlwt.XFStyle()
                    font_style1.font.bold = False
                    ws.write(1,1,"(Input Data: From Date="+" "+fromdate+" To Date="+" "+tdate+" Club="+club_q+")", font_style1)
                    for col_num in xrange(len(columns)):
                        ws.write(row_num, col_num, columns[col_num][0], font_style)
                        # set column width
                        ws.col(col_num).width = columns[col_num][1]
                    font_style = xlwt.XFStyle()
                    font_style.alignment.wrap =-1
                    for obj in txn_new_list:
                        row_num += 1
                        row = [
                            obj['uid'],
                            obj['name'],
                            str(obj['date_of_joining']),
                            str(obj['clubs']),
                            str(obj['doneby'])
                        ]
                        for col_num in xrange(len(row)):
                            ws.write(row_num, col_num, row[col_num], font_style)
                            
                    wb.save(response)
                    return response
                else:
                    row_num =3
                    columns = [
                        (u"Staff ID", 5000),
                        (u"Name", 6000),
                        (u"Date of Joining",6000,),
                        
                        (u"Added By", 8000),
                    ]
                    style = xlwt.easyxf('font: bold 1')
                    font_style = xlwt.XFStyle()
                    font_style.font.bold = True
                    ws.write(0,2,filename, font_style)
                    font_style1 = xlwt.XFStyle()
                    font_style1.font.bold = False
                    ws.write(1,1,"(Input Data: From Date="+" "+fromdate+" To Date="+" "+tdate+" Club="+club_q+")", font_style1)
                    for col_num in xrange(len(columns)):
                        ws.write(row_num, col_num, columns[col_num][0], font_style)
                        # set column width
                        ws.col(col_num).width = columns[col_num][1]
                    font_style = xlwt.XFStyle()
                    font_style.alignment.wrap =-1
                    for obj in txn_new_list:
                        row_num += 1
                        row = [
                            obj['uid'],
                            obj['name'],
                            str(obj['date_of_joining']),
                            
                            str(obj['doneby'])
                        ]
                        for col_num in xrange(len(row)):
                            ws.write(row_num, col_num, row[col_num], font_style)
                            
                    wb.save(response)
                    return response    
            
        return render_to_response('newmemberreport.html',content,context_instance=RequestContext(request))
    return render_to_response('newmemberreport.html',content,context_instance=RequestContext(request))




@user_login_required
def suspensionreport(request):
    url = '/suspensionreport/'
    
    msg = ''
    obj_listm={}
    txnew_list=[] 
    content={}
    content.update(csrf(request))
    user = request.session['user']
    content['username']=user.name
    content['url'] = url
    userclubs=[]
    userclub1=[]
    userclub1.append('All')
    l = user.clubsallowed
    clb_list=[]
    clubs =club.objects.all()   
    for i in clubs:
        clb_list.append(i.name)
    for i in clb_list:
        if i in l:                
            userclubs.append(i)
            userclub1.append(i)
    content['userclubs']=userclub1        
    if request.method == "POST":
        fromdate = request.POST["fromdate"]
        content['frmdate'] = fromdate
        todate = request.POST["todate"]
        club_q = request.POST["club"]
        content['club_q'] = club_q
        content['tdate'] = todate
        year,mnth,day = todate.split("-")
        try:
            sdate = date(int(year), int(mnth), int(day))
        except:
            msssg="The Date You Entered Is Invalid"
            content['msssg']=msssg
            return render_to_response('suspensionrevokereport.html',content,context_instance=RequestContext(request))    
        difference = timedelta(days=1)
        todate= sdate+difference
        if club_q=='All':
            try:
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),status='Suspended')
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('suspensionrevokereport.html',content,context_instance=RequestContext(request))
        else:
            club_id=club.objects.get(name=club_q)
            try:
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),club=club_id,status='Suspended')
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('suspensionrevokereport.html',content,context_instance=RequestContext(request))    
        year1,mnth1,day1 = fromdate.split("-")
        ndate=date(int(year1), int(mnth1), int(day1))
        content['fromdate']=ndate
        content['todate']=sdate
        # obj_list = transaction.objects.all()       
           
        #obj_list1 = member.objects.all()         
        for i in obj_listm:
            if i.member.status != 'Inactive':
                dic = {}        
                mid = i.id


                dic['reason'] = i.reason
                dic['uid'] = i.member.member_uid
                dic['datetime'] = i.datetime.date()
                dic['name'] = str(i.member.name+"    "+i.member.first_name_1+"    "+i.member.first_name_2)
                dic['doneby']=i.doneby.name
                mem_clubs=[]
                for j in userclubs:
                    if j in i.clubsallowed:
                        mem_clubs.append(str(j))    
                        dic['clubs']=str(j)
                if mem_clubs:
                    txnew_list.append(dic)

        if len(obj_listm)==0 or len(txnew_list) == 0:
            msg = 'No records found !!!' 
            content['msg']=msg
        content['report_list']=txnew_list

    if request.method == "GET":
        if 'd1' in request.GET:
            fromdate = request.GET["d1"]
            tdate = request.GET["d2"]
            typ = request.GET["type"]
            club_q = request.GET["club"]
            year,mnth,day = tdate.split("-")
            sdate = date(int(year), int(mnth), int(day))
            difference = timedelta(days=1)
            todate= sdate+difference
            if club_q=='All':
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),status='Suspended')
            else:
                club_id=club.objects.get(name=club_q)
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),club=club_id,status='Suspended')
                 
            for i in obj_listm:
                if i.member.status != 'Inactive':
                    dic = {}        
                    mid = i.id


                    dic['reason'] = i.reason
                    dic['uid'] = i.member.member_uid
                    dic['datetime'] = i.datetime.date()
                    dic['name'] = str(i.member.name+"    "+i.member.first_name_1+"    "+i.member.first_name_2)
                    dic['doneby']=i.doneby.name
                    mem_clubs=[]
                    for j in userclubs:
                        if j in i.clubsallowed:
                            mem_clubs.append(str(j))    
                            dic['clubs']=str(j)
                    if mem_clubs:
                        txnew_list.append(dic)
            if typ == 'excel':
                filename = "Suspension Report"
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename='+filename+"("+str(fromdate)+" To "+str(tdate)+").xls"
                wb = xlwt.Workbook(encoding='utf-8')
                ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                row_num = 3
                columns = [
                    (u"Staff ID", 5000),
                    (u"Name", 6000),
                    (u"Date of Suspension",3000,),
                    (u"Reason Of Suspension",6000,),
                    (u"Club Suspended From", 8000),
                    (u"Done By", 3000),
                ]
                style = xlwt.easyxf('font: bold 1')
                font_style = xlwt.XFStyle()
                font_style.font.bold = True
                ws.write(0,2,filename, font_style)
                font_style1 = xlwt.XFStyle()
                font_style1.font.bold = False
                ws.write(1,1,"(Input Data: From Date="+" "+fromdate+", To Date="+" "+tdate+", Club="+club_q+")", font_style1)
                for col_num in xrange(len(columns)):
                    ws.write(row_num, col_num, columns[col_num][0], font_style)
                    # set column width
                    ws.col(col_num).width = columns[col_num][1]
                font_style = xlwt.XFStyle()
                font_style.alignment.wrap =-1
                for obj in txnew_list:
                    row_num += 1
                    row = [
                        obj['uid'],
                        obj['name'],
                        str(obj['datetime']),
                        obj['reason'],
                        str(obj['clubs']),
                        obj['doneby'],
                    ]
                    
                    for col_num in xrange(len(row)):
                        ws.write(row_num, col_num, row[col_num], font_style)
                        
                wb.save(response)
                return response
             
        return render_to_response('suspension-report.html',content,context_instance=RequestContext(request))
    return render_to_response('suspension-report.html',content,context_instance=RequestContext(request))
    
@user_login_required    
def suspensionrevokereport(request):
    url = '/suspensionrevokereport/'
    
    msg = ''
    obj_listm={}
    txnew_list=[] 
    content={}
    content.update(csrf(request))
    user = request.session['user']
    content['username']=user.name
    content['url'] = url
    userclubs=[]
    userclub1=[]
    userclub1.append('All')
    l = user.clubsallowed
    clb_list=[]
    clubs =club.objects.all()   
    for i in clubs:
        clb_list.append(i.name)
    for i in clb_list:
        if i in l:                
            userclubs.append(i)
            userclub1.append(i)
    content['userclubs']=userclub1                
    if request.method == "POST":
        fromdate = request.POST["fromdate"]
        content['frmdate'] = fromdate
        todate = request.POST["todate"]
        content['tdate'] = todate
        club_q=request.POST["club"]
        content['club_q']=club_q
        year,mnth,day = todate.split("-")
        try:
            sdate = date(int(year), int(mnth), int(day))
        except:
            msssg="The Date You Entered Is Invalid"
            content['msssg']=msssg
            return render_to_response('suspensionrevokereport.html',content,context_instance=RequestContext(request))    
        difference = timedelta(days=1)
        todate= sdate+difference
        if club_q=='All':
            try:
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),status='Suspended')
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('suspensionrevokereport.html',content,context_instance=RequestContext(request))       
        else:
            club_id=club.objects.get(name=club_q)
            try:
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),club=club_id,status='Suspended')
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('suspensionrevokereport.html',content,context_instance=RequestContext(request))   
        year1,mnth1,day1 = fromdate.split("-")
        ndate=date(int(year1), int(mnth1), int(day1))
        content['fromdate']=ndate
        content['todate']=sdate
        # obj_list = transaction.objects.all()       
           
        #obj_list1 = member.objects.all()         
        for i in obj_listm:
            dic = {}        
            mid = i.id
            if i.member.status != 'Inactive':
                dic['reason'] = i.reason
                dic['uid'] = i.member.member_uid
                dic['datetime'] = i.datetime.date()
                dic['name'] = i.member.name+" "+i.member.first_name_1+" "+i.member.first_name_2
                dic['doneby']=i.doneby.name
                mem_clubs=[]
                for j in userclubs:
                    if j ==i.club.name:
                        mem_clubs.append(j)
                        dic['clubs']=j
                if mem_clubs:
                    txnew_list.append(dic)
    
        if len(obj_listm)==0 or len(txnew_list) == 0:
            msg = 'No records found !!!' 
            content['msg']=msg
        content['report_list']=txnew_list

    if request.method == "GET":
        if 'd1' in request.GET:
            fromdate = request.GET["d1"]
            tdate = request.GET["d2"]
            typ = request.GET["type"]
            club_q = request.GET["club"]
            year,mnth,day = tdate.split("-")
            sdate = date(int(year), int(mnth), int(day))
            difference = timedelta(days=1)
            todate= sdate+difference
            if club_q=='All':
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),status='Suspended')
            else:
                club_id=club.objects.get(name=club_q)
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),club=club_id,status='Suspended')
            # obj_list = transaction.objects.all()       
               
            #obj_list1 = member.objects.all()         
            for i in obj_listm:
                dic = {}        
                mid = i.id


                dic['reason'] = i.reason
                dic['uid'] = i.member.member_uid
                dic['datetime'] = i.datetime.date()
                dic['name'] = i.member.name+" "+i.member.first_name_1+" "+i.member.first_name_2
                dic['doneby'] = i.doneby.name
                mem_clubs=[]
                for j in userclubs:
                    if j in i.clubsallowed:
                        mem_clubs.append(str(j))
                dic['clubs']=mem_clubs
                if mem_clubs:
                    txnew_list.append(dic)

                content['report_list']=txnew_list
        
            # if len(obj_listm)==0 or len(txnew_list) == 0:
            #     msg = 'No records found !!!' 
            #     content['msg']=msg

            if typ == 'excel':
                filename = "Suspension Revoke Report"
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename='+filename+"("+str(fromdate)+" To "+str(tdate)+").xls"
                wb = xlwt.Workbook(encoding='utf-8')
                ws = wb.add_sheet("MyModel",{'default_date_format':'mm/dd/yy'})
                row_num = 3
                columns = [
                    (u"Staff ID", 4000),
                    (u"Name", 6000),
                    (u"Date of Revoke Done",3000,),
                    (u"Reason Of Suspension Revoke",6000,),
                    (u"Club", 8000),
                    (u"Done By", 3000),
                ]
                style = xlwt.easyxf('font: bold 1')
                font_style = xlwt.XFStyle()
                font_style.font.bold = True
                ws.write(0,2,filename, font_style)
                font_style1 = xlwt.XFStyle()
                font_style1.font.bold = False
                ws.write(1,1,"(Input Data: From Date="+" "+fromdate+", To Date="+" "+tdate+", club="+club_q+")", font_style1)
                for col_num in xrange(len(columns)):
                    ws.write(row_num, col_num, columns[col_num][0], font_style)
                    # set column width
                    ws.col(col_num).width = columns[col_num][1]
                font_style = xlwt.XFStyle()
                font_style.alignment.wrap =-1
                for obj in txnew_list:
                    row_num += 1
                    row = [
                        obj['uid'],
                        obj['name'],
                        str(obj['datetime']),
                        obj['reason'],
                        str(obj['clubs']),
                        obj['doneby'],
                    ]
                    for col_num in xrange(len(row)):
                        ws.write(row_num, col_num, row[col_num], font_style)
                        
                wb.save(response)
                return response
                
        return render_to_response('suspensionrevokereport.html',content,context_instance=RequestContext(request))
    return render_to_response('suspensionrevokereport.html',content,context_instance=RequestContext(request))


@user_login_required
def cancellationreport(request):
    url = '/cancellationreport/'
    content={}
    content.update(csrf(request))
    user = request.session['user']
    content['username']=user.name
    msg = ''
    obj_listm={}
    txnew_list=[] 
    userclubs=[]
    userclub1=[]
    userclub1.append('All') 
    l = user.clubsallowed
    clb_list=[]
    clubs =club.objects.all()   
    for i in clubs:
        clb_list.append(i.name)
    for i in clb_list:
        if i in l:                
            userclubs.append(i)
            userclub1.append(i)
    content['userclubs']=userclub1         
    content['url'] = url
    if request.method == "POST":
        fromdate = request.POST["fromdate"]
        content['frmdate'] = fromdate
        todate = request.POST["todate"]
        club_q = request.POST["club"]
        content['club_q']=club_q
        
        content['tdate'] = todate
        year,mnth,day = todate.split("-")
        try:
            sdate = date(int(year), int(mnth), int(day))
        except:
            msssg="The Date You Entered Is Invalid"
            content['msssg']=msssg
            return render_to_response('cancellationreport.html',content,context_instance=RequestContext(request))    
        difference = timedelta(days=1)
        todate= sdate+difference
        if club_q=='All':
            try:
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),status='Membership-Cancelled')
                
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('cancellationreport.html',content,context_instance=RequestContext(request))
        else:
            club_id=club.objects.get(name=club_q)
            try:
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),club=club_id,status='Membership-Cancelled')
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('cancellationreport.html',content,context_instance=RequestContext(request))    
        year1,mnth1,day1 = fromdate.split("-")
        ndate=date(int(year1), int(mnth1), int(day1))
        content['fromdate']=ndate
        content['todate']=sdate
        # obj_list = transaction.objects.all()       
           
        #obj_list1 = member.objects.all()         
        for i in obj_listm:
            dic = {}        
            mid = i.id
            

            dic['reason'] = i.reason
            dic['datetime'] = i.datetime.date()
            dic['name'] = i.member.name+" "+i.member.first_name_1+" "+i.member.first_name_2
            dic['uid']=i.member.member_uid
            dic['doneby']=i.doneby.name
            mem_clubs=[]
            
            for j in userclubs:
                if j in i.clubsallowed:
                    mem_clubs=j
                    
            dic['clubs']=mem_clubs
            if mem_clubs:
                txnew_list.append(dic)
        if len(obj_listm)==0 or len(txnew_list) == 0:
            msg = 'No records found !!!' 
            content['msg']=msg
        content['report_list']=txnew_list

    if request.method == "GET":
        if 'd1' in request.GET:
            fromdate = request.GET["d1"]
            tdate = request.GET["d2"]
            club_q = request.GET["club"]
            typ = request.GET["type"]
            year,mnth,day = tdate.split("-")
            sdate = date(int(year), int(mnth), int(day))
            difference = timedelta(days=1)
            todate= sdate+difference
            if club_q=='All':
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),status='Membership-Cancelled')
            else:
                club_id=club.objects.get(name=club_q)
                obj_listm = suspension.objects.filter(datetime__range=(fromdate, todate),club=club_id,status='Membership-Cancelled')
            year1,mnth1,day1 = fromdate.split("-")
            ndate=date(int(year1), int(mnth1), int(day1))
            content['fromdate']=ndate
            content['todate']=sdate
            # obj_list = transaction.objects.all()       
               
            #obj_list1 = member.objects.all()         
            for i in obj_listm:
                dic = {}        
                mid = i.id
                

                dic['reason'] = i.reason
                dic['datetime'] = i.datetime.date()
                dic['name'] = i.member.name+" "+i.member.first_name_1+" "+i.member.first_name_2
                dic['uid']=i.member.member_uid
                dic['doneby']=i.doneby.name
                mem_clubs=[]
                
                for j in userclubs:
                    if j in i.clubsallowed:
                        mem_clubs=j
                        
                dic['clubs']=mem_clubs
                if mem_clubs:
                    txnew_list.append(dic)
                
            if typ == 'excel':
                filename = "Cancellation Report"
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename='+filename+"("+str(fromdate)+" To "+str(tdate)+").xls"
                wb = xlwt.Workbook(encoding='utf-8')
                ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                row_num = 3
                columns = [
                    (u"Staff ID", 5000),
                    (u"Name", 6000),
                    (u"Date of Cancellation",5000,),
                    (u"Reason Of Cancellation",6000,),
                    (u"Club", 8000),
                    (u"Done By", 3000),
                ]
                style = xlwt.easyxf('font: bold 1')
                font_style = xlwt.XFStyle()
                font_style.font.bold = True
                ws.write(0,2,filename, font_style)
                font_style1 = xlwt.XFStyle()
                font_style1.font.bold = False
                ws.write(1,1,"(Input Data: From Date= " +str(fromdate)+", To Date="+str(tdate)+", Club="+club_q+")", font_style1)
                for col_num in xrange(len(columns)):
                    ws.write(row_num, col_num, columns[col_num][0], font_style)
                    # set column width
                    ws.col(col_num).width = columns[col_num][1]
                font_style = xlwt.XFStyle()
                font_style.alignment.wrap =-1
                for obj in txnew_list:
                    row_num += 1
                    row = [
                        obj['uid'],
                        obj['name'],
                        str(obj['datetime']),
                        obj['reason'],
                        str(obj['clubs']),
                        obj['doneby'],
                    ]
                    for col_num in xrange(len(row)):
                        ws.write(row_num, col_num, row[col_num], font_style)
                        
                wb.save(response)
                return response
            
        return render_to_response('cancellationreport.html',content,context_instance=RequestContext(request))
    return render_to_response('cancellationreport.html',content,context_instance=RequestContext(request))

@user_login_required
def renewalreport(request):
    url = '/renewalreport/'
    content={}
    content.update(csrf(request))
    user = request.session['user']
    content['username']=user.name
    msg = ''
    obj_listm={}
    txnew_list=[] 
    userclubs=[]
    userclub1=[]
    userclub1.append('All')
    l = user.clubsallowed
    clb_list=[]
    clubs =club.objects.all()   
    for i in clubs:
        clb_list.append(i.name)
    for i in clb_list:
        if i in l:                
            userclubs.append(i) 
            userclub1.append(i) 
    content['userclubs']=userclub1             
    content['url'] = url
    if request.method == "POST":
        fromdate = request.POST["fromdate"]
        content['frmdate'] = fromdate
        todate = request.POST["todate"]
        club_q = request.POST["club"]
        content['club_q']=club_q
        content['tdate'] = todate
        year,mnth,day = todate.split("-")
        try:
            sdate = date(int(year), int(mnth), int(day))
        except:
            msssg="The Date You Entered Is Invalid"
            content['msssg']=msssg
            return render_to_response('renewalreport.html',content,context_instance=RequestContext(request)) 
        difference = timedelta(days=1)
        todate= sdate+difference
        if club_q=='All':
            try:
                obj_listm = renewal.objects.filter(datetime__range=(fromdate, todate))
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('renewalreport.html',content,context_instance=RequestContext(request))    
        else:
            club_id=club.objects.get(name=club_q)
            try:
                obj_listm = renewal.objects.filter(datetime__range=(fromdate, todate),club=club_id)
            except:
                msssg="The Date You Entered Is Invalid"
                content['msssg']=msssg
                return render_to_response('renewalreport.html',content,context_instance=RequestContext(request))        
        year1,mnth1,day1 = fromdate.split("-")
        ndate=date(int(year1), int(mnth1), int(day1))
        content['fromdate']=ndate
        content['todate']=sdate         
        for i in obj_listm:
            dic = {}
            if i.member.status != 'Inactive':      
                mid = i.id
                dic['datetime'] = i.datetime.date()
                dic['name'] = i.member.name+" "+i.member.first_name_1+" "+i.member.first_name_2
                dic['uid'] = i.member.member_uid
                dic['doneby'] = i.renewalby.name
                mem_clubs=[]
                
                for j in userclubs:
                    if j == i.club.name:
                        mem_clubs.append(i)
                        dic['clubs'] = i.club.name
                if mem_clubs:    
                    txnew_list.append(dic)
                               
        if len(obj_listm)==0 or len(txnew_list) == 0:
            msg = 'No records found !!!' 
            content['msg']=msg
        content['report_list']=txnew_list


    if request.method == "GET":
        if 'd1' in request.GET:
            fromdate = request.GET["d1"]
            tdate = request.GET["d2"]
            typ = request.GET["type"]
            club_q=request.GET["club"]
            year,mnth,day = tdate.split("-")
            sdate = date(int(year), int(mnth), int(day))
            difference = timedelta(days=1)
            todate= sdate+difference
            if club_q=='All':
                obj_listm = renewal.objects.filter(datetime__range=(fromdate, todate))
            else:
                club_id=club.objects.get(name=club_q)
                obj_listm = renewal.objects.filter(datetime__range=(fromdate, todate),club=club_id)

            # obj_list = transaction.objects.all()       
               
            #obj_list1 = member.objects.all()         
            for i in obj_listm:
                dic = {}        
                mid = i.id
                dic['datetime'] = i.datetime.date()
                dic['name'] = i.member.name+" "+i.member.first_name_1+" "+i.member.first_name_2
                dic['uid']=i.member.member_uid
                dic['doneby']=i.renewalby.name
                mem_clubs=[]
                
                for j in userclubs:
                    if j == i.club.name:
                        mem_clubs.append(i)
                        dic['clubs'] = i.club.name
                if mem_clubs:    
                    txnew_list.append(dic)
                    
            if typ == 'excel':
                filename = "Renewal Report"
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename='+filename+"("+str(fromdate)+" To "+str(tdate)+").xls"
                wb = xlwt.Workbook(encoding='utf-8')
                ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                row_num = 3
                columns = [
                    (u"Staff ID", 6000),
                    (u"Name", 6000),
                    (u"Date of Renewal",3000,),
                    (u"Clubs", 8000),
                    (u"Done By", 3000),
                ]
                style = xlwt.easyxf('font: bold 1')
                font_style = xlwt.XFStyle()
                font_style.font.bold = True
                
                ws.write(0,2,filename, font_style)
                font_style1 = xlwt.XFStyle()
                font_style1.font.bold = False
                
                ws.write(1,1,"(Input Data: From Date " +str(fromdate)+", To Date "+str(tdate)+", Club="+club_q+")", font_style1)
                for col_num in xrange(len(columns)):
                    ws.write(row_num, col_num, columns[col_num][0], font_style)
                    # set column width
                    ws.col(col_num).width = columns[col_num][1]
                font_style = xlwt.XFStyle()
                font_style.alignment.wrap =-1
                for obj in txnew_list:
                    row_num += 1
                    row = [
                        obj['uid'],
                        obj['name'],
                        str(obj['datetime']),
                        str(obj['clubs']),
                        obj['doneby'],
                    ]
                    for col_num in xrange(len(row)):
                        ws.write(row_num, col_num, row[col_num], font_style)
                        
                wb.save(response)
                return response
                

                return response
        return render_to_response('renewalreport.html',content,context_instance=RequestContext(request))
    return render_to_response('renewalreport.html',content,context_instance=RequestContext(request))


@user_login_required
def dependents(request):
    url = '/dependents/'
    msg = ''
    drc=0
    content={}
    content.update(csrf(request))
    user = request.session['user']
    content['username']=user.name
    content['url'] = url
    userclubs=[]
    userclub1=[]
    userclub1.append('All')
    l = user.clubsallowed
    clb_list=[]
    clubs =club.objects.all()
    for i in clubs:
        clb_list.append(i.name)
    for i in clb_list:
        if i in l:
            userclubs.append(i)
            userclub1.append(i)
    content['userclubs']=userclub1 
    if request.method=="POST":
        club_q=request.POST['club']
        content['club_q']=club_q
        obj_listm = member.objects.filter(status="Active").exclude(status='Inactive')
        rept_list=[]

        if club_q=="All":
            for k in range(len(userclubs)):
                dic={}
                mem=0;total=0;fam=0;clubn=''
                for i in obj_listm:
                    clubstobj=clubstatus.objects.filter(member=i.id,status="Active")
                    if clubstobj:
                        famobj=family.objects.filter(member=i.id)                    
                    for l in clubstobj:
                        if str(l.club)==str(userclubs[k]):
                            mem+=1
                            fam+=len(famobj)
                            total=mem+fam
                clubn=str(userclubs[k])
                dic['club']=clubn
                dic['dep']=fam
                dic['mem']=mem
                dic['total']=total
                rept_list.append(dic)
        else:
            dic={}
            mem=0;total=0;fam=0;clubn=''
            for i in obj_listm:
                
                club_id=club.objects.get(name=club_q)
                clubstobj=clubstatus.objects.filter(member=i.id,club=club_id,status="Active")
                if clubstobj:
                    famobj=family.objects.filter(member=i.id)

                for l in clubstobj:
                    if str(l.club)==club_q:
                        mem+=1
                        fam+=len(famobj)
                        total=mem+fam
            
            dic['club']=club_q
            dic['dep']=fam
            dic['mem']=mem
            dic['total']=total
            rept_list.append(dic)
        content['rept_list']=rept_list
        if len(rept_list) == 0:
            msg = 'No records found !!!'
            content['msg']=msg
            return render_to_response('dependents.html',content,context_instance=RequestContext(request))
    

    if request.method == "GET":
        if 'export' in request.GET:

            typ = request.GET['type']
            club_q = request.GET['club']
            obj_listm = member.objects.filter(status="Active").exclude(status='Inactive')
            rept_list=[]

            if club_q=="All":
                for k in range(len(userclubs)):
                    dic={}
                    mem=0;total=0;fam=0;clubn=''
                    for i in obj_listm:
                        
                        clubstobj=clubstatus.objects.filter(member=i.id,status="Active")
                        if clubstobj:
                            famobj=family.objects.filter(member=i.id)
                        for l in clubstobj:
                            if str(l.club)==str(userclubs[k]):
                                mem+=1
                                fam+=len(famobj)
                                total=mem+fam
                    clubn=str(userclubs[k])
                    dic['club']=clubn
                    dic['dep']=fam
                    dic['mem']=mem
                    dic['total']=total
                    rept_list.append(dic)
            else:
                dic={}
                print club_q
                mem=0;total=0;fam=0;clubn=''
                for i in obj_listm:
                    club_id=club.objects.get(name=club_q)
                    clubstobj=clubstatus.objects.filter(member=i.id,club=club_id,status="Active")
                    if clubstobj:
                        famobj=family.objects.filter(member=i.id)
                    for l in clubstobj:
                        if str(l.club)==club_q:
                            mem+=1
                            fam+=len(famobj)
                            total=mem+fam
                
                dic['club']=club_q
                dic['dep']=fam
                dic['mem']=mem
                dic['total']=total
                rept_list.append(dic)
            if typ == 'excel':
                filename = "Dependents Report"
                fromdate=date.today()
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename='+filename+"("+str(fromdate)+").xls"
                wb = xlwt.Workbook(encoding='utf-8')
                ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                row_num = 3
                columns = [
                    (u"Club Name", 6000),
                    (u"Active Members",4000,),
                    (u"Active Dependant", 3000),
                    (u"Total", 3000),
                    
                ]
                style = xlwt.easyxf('font: bold 1')
                font_style = xlwt.XFStyle()
                font_style.font.bold = True
                ws.write(0,1,filename+" On "+str(fromdate), font_style)
                font_style1 = xlwt.XFStyle()
                font_style1.font.bold = False
                ws.write(1,1,"(Input Data: Club="+club_q+")", font_style1)
                for col_num in xrange(len(columns)):
                    ws.write(row_num, col_num, columns[col_num][0], font_style)
                    # set column width
                    ws.col(col_num).width = columns[col_num][1]
                font_style = xlwt.XFStyle()
                font_style.alignment.wrap =-1
                for obj in rept_list:
                    row_num += 1
                    row = [
                        obj['club'],
                        obj['mem'],
                        obj['dep'],
                        obj['total'],
                    ]
                    for col_num in xrange(len(row)):
                        ws.write(row_num, col_num, row[col_num], font_style)
                        
                wb.save(response)
                return response
            
    return render_to_response('dependents.html',content,context_instance=RequestContext(request))
@user_login_required
def guestEntry(request):
    url = '/guestEntry/'
    user = request.session['user']
    userclubs = []
    l = user.clubsallowed
    clubs = []
    clubs_list = club.objects.all()

    for i in clubs_list:
        clubs.append(i.name)

    for i in clubs:
        if i in l:                
            userclubs.append(i)
    clubsallowed = club.objects.filter(name__in=userclubs)
    #print clubsallowed
    form=GuestForm(initial={'clubsallowed':clubsallowed,'status':'Active','period':'1'})
    data={}
    content={}
    content.update(csrf(request))
    userobj = request.session['user']
    if request.method == 'POST':
        # print "postttttttttttttttttttttttt"
        if 'gid' in request.POST:
            
            gid = request.POST['gid']
            if gid:
                # print "if gid in pooooooooooooosssst"
                guest_form = GuestForm(request.POST)
                rfidcardno=request.POST['rfidcardno']
                guest_obj = guest.objects.get(id=gid)
                guest_obj.rfidcardno=rfidcardno
                imageUrl = guest_obj.photo
                if 'Imagefile' in request.FILES:
                    f = request.FILES['Imagefile']
                    file_name = f.name
                    flist = file_name.split(".")
                    data = f.read()
                    f.close()
                    f = open(conf_settings.IMAGE_ROOT + "%s.%s" %('guest_'+str(gid),flist[1]),"wb")
                    f.write(data)
                    f.close()
                    imageUrl  = "%s.%s" %('guest_'+str(gid),flist[1])
                guest_obj.photo = imageUrl   
                guest_obj.save()
                if guest_form.is_valid():
                    
                    imageUrl = guest_obj.photo
                    if 'Imagefile' in request.FILES:
                        f = request.FILES['Imagefile']
                        file_name = f.name
                        flist = file_name.split(".")
                        data = f.read()
                        f.close()
                        f = open(conf_settings.IMAGE_ROOT + "%s.%s" %('guest_'+str(gid),flist[1]),"wb")
                        f.write(data)
                        f.close()
                        imageUrl  = "%s.%s" %('guest_'+str(gid),flist[1])
                        # guest_obj.save()
                    # exp_date=date.today()+timedelta(int(guest_obj1.period))
                    # guest_obj1.date_of_expiry = exp_date    
                    guest_form = GuestForm(request.POST, instance = guest_obj)
                    guest_form.save()
                    #print guest_form.save()
                    # guest_obj1 = guest.objects.get(id=gid)
                    # guest_obj1.photo = imageUrl
                    
                    # guest_obj1.save()
                    if 'Imagefile' in request.FILES:
                        f = request.FILES['Imagefile']
                        if f:
                            gusobj = guest.objects.get(id=gid)
                            gusobj.photo = imageUrl
                            gusobj.save()
            if not gid:
                # print "if not gid in pooooooooooooosssst"
                guest_form = GuestForm(request.POST)
                if guest_form.is_valid():
                    guest_form.save()
                    # print guest_form
                    obj = guest.objects.latest('id')
                    guest_obj = guest.objects.get(id=obj.id)
                    # exp_date=date.today()+timedelta(int(guest_obj.period))
                    # print exp_date
                    # guest_obj.date_of_expiry = exp_date
                    months=int(guest_obj.period)
                    sourcedate=date.today()
                    month = sourcedate.month - 1 + months
                    year = sourcedate.year + month / 12
                    month = month % 12 + 1
                    day = min(sourcedate.day,calendar.monthrange(year,month)[1])
                    exp_date =date(year,month,day-1)
                    guest_obj.date_of_expiry = exp_date
                    if 'Imagefile' in request.FILES:
                        f = request.FILES['Imagefile']
                        file_name = f.name
                        flist = file_name.split(".")
                        data = f.read()
                        f.close()
                        f = open(conf_settings.IMAGE_ROOT + "%s.%s" %('guest_'+str(obj.id),flist[1]),"wb")
                        f.write(data)
                        f.close()
                        imageUrl  = "%s.%s" %('guest_'+str(obj.id),flist[1])
                        guest_obj.photo = imageUrl
                        
                    if not 'Imagefile' in request.FILES:
                        guest_obj.photo = 'People.jpg'
                    guest_obj.save()

                    subject = 'New Guest Profile Has Been Created By:%s'%(user.name)
                    message = 'Dear Supervisor,\n\n\n'
                    message += 'A New Guest : %s'%(guest_obj.name)
                    message += 'In Club : %s'%(userclubs[0])
                    message += 'For : %s Month '%(guest_obj.period)
                    # 
                    from_email = 'venugopal@techanipr.com'
                    # to_list = ['ashok@indiadens.com']
                    # return HttpResponse(message)
                    role_id=role.objects.get(rolename="Supervisor" )
                    user_obj=qpuser.objects.filter(role=role_id)
                    # print user_obj
                    club_supervisor=[]
                    for n in user_obj:
                        #print userclubs
                        for i in n.clubsallowed: 
                            if i==clubsallowed[0].name:
                                club_supervisor.append(user_obj)
                                print "club_supervisorgggggggggggggggg"

                    email_lst=['asif@techanipr.com']
                    datatuple = (
                    (subject, message, from_email, email_lst),
                    )

                    # send_mass_mail(datatuple, fail_silently = True)
                    NotifySupervisor.delay(datatuple)

            return HttpResponseRedirect('/guestList')
                    
                    # return HttpResponseRedirect('/guestList')
    if request.method == 'GET':
        timediff=''
        if 'gid' in  request.GET:
            # print "if gid"
            gid = request.GET['gid']
            guest_obj = guest.objects.get(id=gid)
            data['name'] = guest_obj.name
            data['uid'] = guest_obj.id 
            data['gender'] = guest_obj.gender
            data['dob'] =  guest_obj.dob
            data['period'] = guest_obj.period
            data['photo'] = guest_obj.photo 
            data['phone_no'] = guest_obj.phone_no
            data['rfidcardno'] = guest_obj.rfidcardno
            data['date_of_expiry'] = guest_obj.date_of_expiry
            content['expiry'] = guest_obj.date_of_expiry
            content['status'] = guest_obj.status
            # print data['date_of_expiry']
            li=[]
            li=[]
            l = guest_obj.clubsallowed
           
            clubs = []
            clubs_list = club.objects.all()

            for i in clubs_list:
                clubs.append(i.name)

            for i in clubs:
                if i in l:                
                    li.append(i)
            tot_clubs = club.objects.filter(name__in=li)
            data['clubsallowed'] = tot_clubs
            data['emailid'] = guest_obj.emailid
            data['residencelocation'] = guest_obj.residencelocation
            data['nationality'] = guest_obj.nationality
            data['memberid'] = guest_obj.memberid
            data['status'] = guest_obj.status
            g_form = GuestForm(initial=data)
            timediff=guest_obj.date_of_expiry-date.today()
            # print timediff.days
            content['timediff'] = timediff.days
            if timediff.days <= 7:
                content['timediffff'] = 1
                
            if guest_obj.status=="Active":
                content['deactive'] = 1 
            if guest_obj.status=="Inactive":
                content['active'] = 1
            if timediff.days<=0:
                content['date_expir']=1  
                   
            content['form'] = g_form
            content['gid'] = guest_obj.id
            content['photo'] = guest_obj.photo
            content['IMAGE_URL'] = conf_settings.IMAGE_URL
            return render_to_response('Receptionist/guest.html',content, context_instance=RequestContext(request))
    
    content = {'form':form,'username' :userobj.name,'url':url,'guests':users}


    return render_to_response('Receptionist/guest.html',content, context_instance=RequestContext(request))

@user_login_required
def guestList(request):
    url = '/guestList/'
    user = request.session['user']
    g_list = []

    l = user.clubsallowed

    clubs = []
    clubs_list = club.objects.all()

    for i in clubs:
        if i in l:                
            userclubs.append(i)
    
    li=[]
    clubs = []
    clubs_list = club.objects.all()

    for i in clubs_list:
        clubs.append(i.name)

    for i in clubs:
        if i in l:                
            li.append(i)

    x =  club.objects.filter(name__in=li)
    m = []
    for k in x:
        m.append(k.id)


    cls = clubstatus.objects.filter(club_id__in=m).values("member")

    n  = []

    ids = deque()

    guest_n = deque()
    for b in cls:
        # n.append(b.member_id)

        guest_n.append(b['member'])

    mems = member.objects.filter(id__in=guest_n).values('member_uid')

    for i in mems:
        ids.append(i['member_uid'])
    #need to filter guest based on user club.
    guests = guest.objects.all().exclude(status="Inactive")
    userobj = request.session['user']
    content = {'username' :userobj.name,'url':url,'guests':guests}
    return render_to_response('Receptionist/guestList.html',content, context_instance=RequestContext(request))


@user_login_required
def employmentform(request):
    
    url = '/employmentform/'
    content={}
    content.update(csrf(request))
    if request.method == 'POST':
        form = EmploymentForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse('<script type="text/javascript">window.close();window.opener.parent.location.href = "/membershipform/";</script>') 
    else:
        
        form = EmploymentForm()
        content = {'form':form,'url':url}
    return render_to_response('employmentform.html',content, context_instance=RequestContext(request))

    
   
@user_login_required
def organizationform(request):
    
    url = '/organizationform/'
    content={}
    content.update(csrf(request))
    if request.method == 'POST':
        form = OrganizationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponse('<script type="text/javascript">window.close();window.opener.parent.location.href = "/membershipform/";</script>') 
    else:       
        form = OrganizationForm()
        content = {'form':form,'url':url}
    return render_to_response('organizationform.html',content, context_instance=RequestContext(request))


@user_login_required
def companyform(request):
    
    url = '/companyform/'
    content={}
    data={}
    user = request.session['user']
    content['username'] = user.name
    content['url'] = url
    content.update(csrf(request))
    if 'cid' in request.GET:
        cid = request.GET['cid']
        c_obj = associatecompany.objects.get(id=cid)
        data['name'] = c_obj.name
        data['status'] = c_obj.status
        c_form = AssociateCompanyForm(initial=data)
        content['form'] = c_form
        content['cid'] = c_obj.id
        return render_to_response('Admin/companyform.html',content, context_instance=RequestContext(request))
    
    if request.method == 'POST':
        if 'cid' in request.POST:
            cid = request.POST['cid']
            if cid:
                c_obj = associatecompany.objects.get(id=cid)
                form = AssociateCompanyForm(request.POST,instance=c_obj)
                form.save()
                return HttpResponse('<script type="text/javascript">window.close();window.opener.parent.location.href = "/companies/";</script>') 
            else:
                form = AssociateCompanyForm(request.POST)
                if form.is_valid():
                    form.save()
                    return HttpResponse('<script type="text/javascript">window.close();window.opener.parent.location.href = "/companies/";</script>') 
    else:       
        form = AssociateCompanyForm(initial={'status':'Active'})
        content = {'form':form,'url':url}
    return render_to_response('Admin/companyform.html',content, context_instance=RequestContext(request))


@user_login_required
def companies(request):
    content={}
    content.update(csrf(request))
    user = request.session['user']
    content['username'] = user.name
    companies = associatecompany.objects.all()
    content['companies'] = companies
    return render_to_response('Admin/companies.html',content, context_instance=RequestContext(request))

@user_login_required
def clubs(request):
    content={}
    content.update(csrf(request))
    user = request.session['user']
    content['username'] = user.name
    clubs = club.objects.all()
    content['clubs'] = clubs
    return render_to_response('Admin/clubs.html',content, context_instance=RequestContext(request))

@user_login_required
def clubform(request):
    
    url = '/clubform/'
    content={}
    data={}
    user = request.session['user']
    content['username'] = user.name
    content['url'] = url
    content.update(csrf(request))
    if 'cid' in request.GET:
        cid = request.GET['cid']
        c_obj = club.objects.get(id=cid)
        data['name'] = c_obj.name
        # data['status'] = c_obj.status
        c_form = ClubForm(initial=data)
        content['form'] = c_form
        content['cid'] = c_obj.id
        return render_to_response('Admin/clubform.html',content, context_instance=RequestContext(request))
    
    if request.method == 'POST':
        if 'cid' in request.POST:
            cid = request.POST['cid']
            if cid:
                c_obj = club.objects.get(id=cid)
                form = ClubForm(request.POST,instance=c_obj)
                form.save()
                return HttpResponse('<script type="text/javascript">window.close();window.opener.parent.location.href = "/clubs/";</script>') 
            else:
                form = ClubForm(request.POST)
                if form.is_valid():
                    form.save()
                    return HttpResponse('<script type="text/javascript">window.close();window.opener.parent.location.href = "/clubs/";</script>') 
    else:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("gmail.com",80))
        ip = (s.getsockname()[0])
        s.close()
        data['ip'] = ip
        form = ClubForm(initial=data)
        content = {'form':form,'url':url}
    return render_to_response('Admin/clubform.html',content, context_instance=RequestContext(request))

@user_login_required
def club_delete(request):
    content = {}
    user = request.session['user']
    content['username'] = user.name
    if 'cid' in request.GET:
        cid = request.GET['cid']
        c_obj = club.objects.get(id = cid)
        c_obj.delete()
        url = "/clubs"
        return HttpResponseRedirect(url)

@user_login_required
def company_delete(request):
    content = {}
    user = request.session['user']
    content['username'] = user.name
    if 'cid' in request.GET:
        cid = request.GET['cid']
        c_obj = associatecompany.objects.get(id = cid)
        c_obj.delete()
        url = "/companies"
        return HttpResponseRedirect(url)


@user_login_required
def print_card(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="MembershipCard.pdf"'
    p = canvas.Canvas(response)
    if 'fid' in request.GET:
        fmem_id=request.GET['fid']
        fmem_obj = family.objects.get(id=fmem_id)
        path = os.path.join(os.path.dirname(__file__))
        back_logo = path+'/static/id-acard.jpg'
        p.drawInlineImage(back_logo, 20,500, width=550.0,height=330.0)
        p.setFont('Helvetica-Bold',30,leading=None)
        p.drawCentredString(290,780,"Club Membership")
        seal = conf_settings.IMAGE_ROOT + "%s" %(fmem_obj.photo)
        try:
            p.drawImage(seal,30, 590, width=100.0, height=130.0)
        except:
            pass
            msg="Please provide Image In JPG Format."
        p.setFont('Helvetica',20,leading=None)
        p.drawCentredString(200,700,"Name")
        p.drawCentredString(400,700,fmem_obj.dapendent_first_name1+' '+fmem_obj.dependent_family_name)
        p.drawCentredString(240,650,"Membership ID")
        p.drawCentredString(450,650,fmem_obj.family_uid)
        p.drawCentredString(230,600,"Relationship")
        if fmem_obj.relationship:
            p.drawCentredString(400,600,fmem_obj.relationship)
        p.showPage()
        p.save()
        # return HttpResponseRedirect(fmem_id)
    if 'id' in request.GET:
        mem_id=request.GET['id']
        mem_obj = member.objects.get(id=mem_id)
        path = os.path.join(os.path.dirname(__file__))
        back_logo = path+'/static/id-acard.jpg'
        p.drawInlineImage(back_logo, 20,500, width=550.0,height=330.0)
        p.setFont('Helvetica-Bold',30,leading=None)
        p.drawCentredString(290,780,"Club Membership")
        seal = conf_settings.IMAGE_ROOT + "%s" %(mem_obj.photo)
        p.drawImage(seal,30, 590, width=100.0, height=130.0)
        p.setFont('Helvetica',20,leading=None)
        p.drawCentredString(200,720,"Name")
        p.drawCentredString(400,720,mem_obj.name +' '+ mem_obj.first_name_2+ ' ' + mem_obj.first_name_3)
        p.drawCentredString(240,670,"Membership ID")
        p.drawCentredString(400,670,mem_obj.member_uid)
        p.drawCentredString(200,620,"Grade")
        if str(mem_obj.membership_grade):
            p.drawCentredString(442,620,str(mem_obj.membership_grade))
        p.drawCentredString(225,580,"Department")
        if str(mem_obj.membership_grade):
            p.drawCentredString(430,580,str(mem_obj.department))
        org = organization.objects.get(name='QP')
        # if not mem_obj.organization_id == org.id:
        #     p.drawCentredString(225,555,"Expiry Date")
        #     date = str(mem_obj.date_of_expiry)
        #     p.drawCentredString(400,555,date)
        if mem_obj.organization.name != 'QP' and mem_obj.associatecompany:
            p.drawCentredString(260,520,"Associate Company")
            p.drawCentredString(400,520,mem_obj.associatecompany.name)
        p.showPage()
        p.save()
        # pdf = buffer.getvalue()
        # buffer.close()
        # response.write(pdf)

    return response

@user_login_required
def display(request):
    userid = request.session['user'] 
    content={}
    content['name'] = userid.name    
    content['userid'] = userid.userid
    content['role'] = userid.role
    content['clubsallowed'] = userid.clubsallowed
    content['residencelocation'] = userid.residencelocation
    content['username']=userid.name
    content['expirydate']=  ' '
    content.update(csrf(request))
    userclubs=[]
    l = userid.clubsallowed
    clb_list=[]
    clubs =club.objects.all()
    
    for i in clubs:
        clb_list.append(i.name)
    for i in clb_list:
        if i in l:                
            userclubs.append(i)
    cid = club.objects.get(name=userclubs[0])  

    trans = transaction.objects.filter(club=cid)
    
    if trans:
        flashid = trans.latest('id')
        if flashid:
            if (datetime.now()-flashid.datetime).total_seconds() > 60:
                hide=1
                content['hide']=hide
            ids  = deque()            
            gids = deque()
            fids = deque()
            display = ''
            mem_card_ids = clubstatus.objects.filter(club_id=cid,member__rfidcardno=flashid).select_related("member_id")#member.objects.values('rfidcardno','clubsallowed')   
           
            if mem_card_ids:
               
                for i in mem_card_ids:
                    ids.append(i.member.rfidcardno)

                st = mem_card_ids[0].status
                if st == "":
                    st="Invalid Card"    
                    content['IMAGE_URL'] = conf_settings.IMAGE_URL
                    content['photo'] = mem_card_ids[0].member.photo 
                    name = mem_card_ids[0].member.name+" "+mem_card_ids[0].member.first_name_1+" "+mem_card_ids[0].member.first_name_2
                    content['uname']=""
                    content['dependents']=""
                    content['type']=""
                    content['imagename']=  name +'.jpg'
                    content['expirydate']=""
                    content['uid']=""
                    orgobj = organization.objects.get(id=mem_card_ids[0].member.organization.id)
                    if orgobj.name == 'QP':
                        content['org']=orgobj.name
                    content['status']=st

                else:
                    name = mem_card_ids[0].member.name+" "+mem_card_ids[0].member.first_name_1+" "+mem_card_ids[0].member.first_name_2
                    content['IMAGE_URL'] = conf_settings.IMAGE_URL
                    content['photo'] = mem_card_ids[0].member.photo 
                    content['status']=st
                    content['uname']=name
                    content['dependents'] = family.objects.filter(member_id=mem_card_ids[0].member.id).count()
                    content['type']="Main Member"
                    content['main']=1
                    content['imagename']=  name +'.jpg'
                    content['expirydate']=mem_card_ids[0].member.date_of_expiry
                    content['uid']=mem_card_ids[0].member.member_uid
                    content["dependent"]=mem_card_ids[0].member.No_of_dependents
                    orgobj = organization.objects.get(id=mem_card_ids[0].member.organization.id)
                    if orgobj.name == 'QP':
                        content['org']=orgobj.name
                    
            family_ids = family.objects.filter(rfidcardno=flashid)
            
            if family_ids:
                for i in family_ids:
                    st =''
                    fids.append(i.rfidcardno)
                    # cid = club.objects.get(name=userclubs[0])
                    st_obj = clubstatus.objects.filter(member=i.member.id,club=cid)
                    print st_obj
                    print cid
                    if userclubs[0] in clb_list and st_obj:
                        st=st_obj[0].status
                    
                    if st == "":
                        st="No Access For This Club"    
                        content['IMAGE_URL'] = conf_settings.IMAGE_URL
                        content['photo'] = i.photo 
                        name = i.dapendent_first_name1 +" "+ i.dependent_family_name
                        content['uname']=""
                        content['dependents']=""
                        content['type']=""
                        content['imagename']=  name +'.jpg'
                        content['expirydate']=""
                        content['uid']=""
                        # content['org']=i.member.organization
                        orgobj = organization.objects.get(id=i.member.organization.id)
                        content['status']=st
                        content['org'] = orgobj.name

                    else:
                        if i.status!="Pending-Crossed-Age 21":

                            name = i.dapendent_first_name1 +" "+i.dependent_family_name
                            content['IMAGE_URL'] = conf_settings.IMAGE_URL
                            content['photo'] = i.photo 
                            content['status']=i.member.status
                            content['uname']=name
                            orgobj = organization.objects.get(id=i.member.organization.id)
                            if orgobj.name == 'QP':
                                content['org']=orgobj.name
                            content['type']="Family Member"
                            content['fam']=1
                            content['imagename']=  name +'.jpg'
                            content['main_id']=i.member.member_uid
                            content['expirydate']=i.date_of_expiry
                            content['uid']=i.family_uid
                        else:
                            name = i.dapendent_first_name1 +" "+i.dependent_family_name
                            content['IMAGE_URL'] = conf_settings.IMAGE_URL
                            content['photo'] = i.photo 
                            content['status']=i.status
                            content['uname']=name
                            orgobj = organization.objects.get(id=i.member.organization.id)
                            if orgobj.name == 'QP':
                                content['org']=orgobj.name
                            content['type']="Family Member"
                            content['fam']=1
                            content['imagename']=  name +'.jpg'
                            content['main_id']=i.member.member_uid
                            content['expirydate']=i.date_of_expiry
                            content['uid']=i.family_uid   
            guest_ids = guest.objects.filter(rfidcardno=flashid)

            if guest_ids:                              
                for i in guest_ids:
                    #if userclubs[0] in i.memberid.clubsallowed:
                    gids.append(i.rfidcardno)
                if str(flashid).lower() in gids:            
                    statuss = clubstatus.objects.filter(club_id=cid,member__member_uid = guest_ids[0].memberid)
                    st=guest_ids[0].status
                    #st = statuss[0].status 
                    if st=="":
                        st="Invalid Card"    
                        content['IMAGE_URL'] = conf_settings.IMAGE_URL
                        content['photo'] = statuss[0].member.photo 
                        name = guest_ids[0].name
                        content['uname']=""
                        content['dependents']=""
                        content['type']=""
                        content['imagename']=  name +'.jpg'
                        content['expirydate']=""
                        content['uid']=""
                        # content['org']=statuss[0].member.member.organization
                        #orgobj = organization.objects.get(id=statuss[0].member.memberid.organization.id)
                        content['status'] = st
                        content['org'] = orgobj.name
                    else:
                        name = guest_ids[0].name
                        content['IMAGE_URL'] = conf_settings.IMAGE_URL
                        content['photo'] = guest_ids[0].photo 
                        content['status']=st
                        content['uname']=name
                        content['org']=1
                        content['type']="Guest"
                        content['guest']=1
                        content['imagename']=  name +'.jpg'
                        content['main_id']=guest_ids[0].memberid
                        #content['expirydate']=i.date_of_expiry
                        content['uid']=""
       
            if str(flashid) not in ids and str(flashid) not in fids and str(flashid) not in gids:
                content['IMAGE_URL'] = conf_settings.IMAGE_URL
                content['photo'] =  'People.jpg'
                display = "Unregistered Card"
                content['expirydate']=  ' '
                content['values']=ids
                content['status']=display

    return render_to_response('Receptionist/display.html',content, context_instance=RequestContext(request))

@user_login_required
def members_visit(request):
    msg = ''
    content={}
    content.update(csrf(request))
    user = request.session['user']
    content['username']=user.name
    userclubs=[]
    l = user.clubsallowed
    clubs = []
    clubs_list = club.objects.all()

    for i in clubs:
        if i in l:                
            userclubs.append(i)
    
    li=[]
    clubs = []
    clubs_list = club.objects.all()

    for i in clubs_list:
        clubs.append(i.name)

    for i in clubs:
        if i in l:                
            li.append(i)

    x =  club.objects.filter(name__in=li)
    m = []
    for k in x:
        m.append(k.id)


    cls = clubstatus.objects.filter(club_id__in=m).select_related("member_id")
    n  = deque()
    cl = deque()
    guest_n = deque()
    for b in cls:
        n.append(b.member_id)
        # guest_n.append(b.member.member_uid)
        cl.append(b.club_id)

    my_queryset = member.objects.filter(id__in=n)

    all_family = family.objects.filter(member_id__in=n).exclude(status='Inactive')

    all_guest = guest.objects.all()

    trans1 = transaction.objects.filter(datetime__gte=date.today(),club_id=cl[0])
    
    today_visitors = deque()
    mem_visit = []
    if trans1:  
        for k in my_queryset:
            for i in trans1: 
                if k.rfidcardno == i.rfidcardid:
                    if i not in mem_visit:
                        dic={}
                        mem_visit.append(i)
                        dic['name'] = k.name+" "+k.first_name_1+" "+k.first_name_2
                        dic['uid'] = k.member_uid
                        dic['type'] = "Member"
                        dic['time'] = i.datetime
                        today_visitors.append(dic)
                
        for k in all_family:
            for i in trans1:
                # if i.datetime.date()==datetime.now().date() and i.club_id == cl[0]:
                    if k.rfidcardno== i.rfidcardid:
                        if i not in mem_visit:
                            dic={}
                            mem_visit.append(i)
                            dic['name']=k.dapendent_first_name1+" "+k.dependent_family_name
                            dic['uid']=k.family_uid
                            dic['type']="Dependant"
                            dic['time']=i.datetime
                            today_visitors.append(dic)                
        for k in all_guest:
            for i in trans1:    
                # if i.datetime.date()==datetime.now().date():
                    if k.rfidcardno == i.rfidcardid:
                        if i not in mem_visit:
                            dic={}
                            mem_visit.append(i)
                            dic['name']=k.name
                            dic['type']="Guest"
                            dic['uid']=''
                            dic['time']=i.datetime
                            dic['uid'] = k.memberid
                            today_visitors.append(dic)               
    if len(today_visitors) == 0:
        msg = 'No records found !!!' 
        content['msg']=msg
    content['report_list']=today_visitors    
    return render_to_response('Receptionist/index.html',content,context_instance=RequestContext(request))

@user_login_required
def userlogs(request):
    url = '/userlogs/'    
    msg = ''
    obj_listm={}
    txnew_list=[] 
    content={}
    content.update(csrf(request))
    user = request.session['user']
    content['username']=user.name
    content['url'] = url
    if request.method == "POST":
        fromdate = request.POST["fromdate"]
        todate = request.POST["todate"]
        logtype= request.POST["logs"]        
        year,mnth,day = todate.split("-")
        sdate = date(int(year), int(mnth), int(day))
        difference = timedelta(days=1)
        todate= sdate+difference        
        if logtype == 'login':
            obj_list1 = userlogin.objects.filter(logintime__range=(fromdate, todate))
            for i in obj_list1:
                dic = {}        
                dic['username'] = i.username
                dic['userid'] = i.userid
                dic['time'] = i.logintime
                dic['role'] = i.role                 
                txnew_list.append(dic)
            if len(obj_list1) == 0:
                msg = 'No record found !!!' 
                content['msg']=msg
            content['report_list']=txnew_list   
        if logtype == 'logout':            
            obj_list2 = userlogout.objects.filter(logouttime__range=(fromdate, todate))
            for i in obj_list2:
                dic = {}        
                dic['username'] = i.username
                dic['userid'] = i.userid
                dic['time'] = i.logouttime
                dic['role'] = i.role                 
                txnew_list.append(dic)  
            if len(obj_list2) == 0:
                msg = 'No record found !!!' 
                content['msg']=msg
            content['report_list']=txnew_list
        return render_to_response('Admin/userlogs.html',content,context_instance=RequestContext(request))
    return render_to_response('Admin/userlogs.html',content,context_instance=RequestContext(request))

@user_login_required
def childreenage(request):
    url = '/childreenage/'
    obj_listf=family.objects.all()
    today=date.today()
    difference = timedelta(days=15)
    dif=timedelta(days=21*365.245)
    
    content={}
    obj_list=[]
    content.update(csrf(request))
    user = request.session['user']
    content['username']=user.name

    com_date=today +difference
    for l in obj_listf:
        if l.status=="Active":
            exp_date=l.dob+dif
              
            dic = {}
            age=int((com_date.year-l.dob.year)/1.0+(com_date.month-l.dob.month)/12.0+(com_date.day-l.dob.day)/365.0)
            if age==21 and today<=exp_date: 

               
                dic['name']=l.dapendent_first_name1+" "+l.dependent_family_name
                dic['uid']=l.family_uid
                dic['parent']=l.member.member_uid
                dic['exp_date']=exp_date
                obj_list.append(dic) 
    content['obj_list']=obj_list 

    context_dict = {
            'obj_list': obj_list,
        }
        
    # message = render_to_string('report_temp.html', context_dict)
    # subject = "Dependent Age Expiry Report"
      
    # msg = EmailMultiAlternatives(subject, message, 'asif@techanipr.com', ['asif@techanipr.com'])
    # msg.content_subtype = "html"
    # if len(obj_list) > 0:
    #     msg.send()
    if request.method == "GET":
        if 'export' in request.GET:
            typ=request.GET['type']
            if typ == 'excel':
                filename = "Childreen's Age Expiry Report"
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename='+filename+".xls"
                wb = xlwt.Workbook(encoding='utf-8')
                ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                row_num = 2
                columns = [
                    (u"Staff ID", 6000),
                    (u"Name", 6000),
                    (u"Main Member Id",5000,),
                    (u"Date Of Expiry", 8000),
                    
                ]
                style = xlwt.easyxf('font: bold 1')
                font_style = xlwt.XFStyle()
                font_style.font.bold = True
                ws.write(0,1,filename, font_style)
                for col_num in xrange(len(columns)):
                    ws.write(row_num, col_num, columns[col_num][0], font_style)
                    # set column width
                    ws.col(col_num).width = columns[col_num][1]
                font_style = xlwt.XFStyle()
                font_style.alignment.wrap =-1
                for obj in obj_list:
                    row_num += 1
                    row = [
                        obj['uid'],
                        obj['name'],
                        obj['parent'],
                        str(obj['exp_date'])
                        
                    ]
                    for col_num in xrange(len(row)):
                        ws.write(row_num, col_num, row[col_num], font_style)
                        
                wb.save(response)
                return response
    if len(obj_list) == 0:
        msg = 'No record found !!!' 
        content['msg']=msg
            
        return render_to_response('Steward/children_age_expiry.html',content,context_instance=RequestContext(request))
    return render_to_response('Steward/children_age_expiry.html',content,context_instance=RequestContext(request)) 
  
@user_login_required
def memberslist(request):
    url = '/memberslist/'
    content={}
    content.update(csrf(request))
    user = request.session['user']
    userclubs=[]
    userclubs1=[]
    userclubs1.append('All')
    l = user.clubsallowed
    clb_list=[]
    clubs =club.objects.all()   
    for i in clubs:
        clb_list.append(i.name)
    for i in clb_list:
        if i in l:                
            userclubs.append(i) 
            userclubs1.append(i) 
    content['userclubs']=userclubs1        
    content['username']=user.name
    # obj_listm = member.objects.all().exclude(status='Inactive')
    # obj_listf = family.objects.all().exclude(status='Inactive')
    obj_list = deque()
    list_m=[]
    list_f=[]

    if request.is_ajax():
        result = []
        if 'page' in request.GET:
            query = request.GET.get('page')

            cid = request.GET.get('cid')

            if cid == 'All':
                cids = []
                cid = club.objects.filter(name__in=userclubs)

                for i in cid:
                    cids.append(i.id)

                members = clubstatus.objects.filter(club_id__in=cids).exclude(status='Inactive')
                content['cid'] = 'All'
            else:
                members = clubstatus.objects.filter(club_id=cid).exclude(status='Inactive')
                content['cid'] = cid

            if query is not None:
                page = query
            try:
                for i in members.iterator(): 
                    result.append(i)    
                paginator = Paginator(result, 100)
                result = paginator.page(page)
            except PageNotAnInteger:
                # If page is not an integer, deliver first page.
                result = paginator.page(1)
            except EmptyPage:
                # If page is out of range (e.g. 9999), deliver last page of results.
                result = paginator.page(paginator.num_pages)
            content['obj_list'] = result

            print content

            return render_to_response('Steward/memberlist.html',content,context_instance=RequestContext(request))
    
    if request.method == "POST":
        club_q = request.POST['club']

        if club_q == 'All':
            cids = []
            cid = club.objects.filter(name__in=userclubs)

            for i in cid:
                cids.append(i.id)

            members = clubstatus.objects.filter(club_id__in=cids).exclude(status='Inactive')
            content['cid'] = 'All'

        else:
            cid = club.objects.get(name=club_q)

            members = clubstatus.objects.filter(club_id=cid.id).exclude(status='Inactive')

            content['cid'] = cid.id

        result = []
        page = request.GET.get('page')
        
        try:
            for i in members.iterator(): 
                result.append(i)    
            paginator = Paginator(result, 100)
            result = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            result = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            result = paginator.page(paginator.num_pages)

        # if club_q=='All':
        #     for i in obj_listm:
        #         dic={}
        #         for j in userclubs:
        #             if j in i.clubsallowed:
        #                 if i.status!="Membership-Cancelled":
        #                     if i not in list_m:
        #                         list_m.append(i)
        #                         dic['name']=i.name +" "+i.first_name_1+" "+i.first_name_2
        #                         dic['uid']=i.member_uid
        #                         dic['exp_date']=i.date_of_expiry
        #                         dic['type']=i.organization
        #                         dic['status']=i.status
        #                         clubsss=[]
        #                         for m in userclubs:
        #                             if m in i.clubsallowed:
        #                                 clubsss.append(str(m))
        #                         dic['club']=clubsss
        #                         obj_list.append(dic)
            
        #     for i in obj_listf:
        #         dic={}
        #         for j in userclubs:
        #             if j in i.member.clubsallowed:
        #                 if i.status!="Membership-Cancelled":
        #                     if i not in list_f:
        #                         list_f.append(i)
        #                         dic['name']=i.dapendent_first_name1 +" "+i.dependent_family_name
        #                         dic['uid']=i.family_uid
        #                         dic['exp_date']=i.date_of_expiry
        #                         dic['type']=i.member.organization.name +"-Family"
        #                         dic['status']=i.status
        #                         clubsss=[]
        #                         for m in userclubs:
        #                             if m in i.clubsallowed:
        #                                 clubsss.append(str(m))
        #                         dic['club']=clubsss
        #                         obj_list.append(dic) 
        #     content['obj_list']=obj_list 
        # else:
        # for i in members:
        #     dic={}
        #     if i not in list_m:
        #         list_m.append(i)
        #         dic['name']=i.member.name +" "+i.member.first_name_1+" "+i.member.first_name_2
        #         dic['uid']=i.member.member_uid
        #         dic['exp_date']=i.date_of_expiry
        #         dic['type']=i.member.organization
        #         dic['status']=i.status
        #         dic['club'] = club_q
        #         obj_list.append(dic)
            
        #     for i in obj_listf:
        #         dic={}
        #         for j in userclubs:
        #             if j in i.member.clubsallowed:
        #                 if i.status!="Membership-Cancelled":
        #                     if j == club_q and club_q  in i.member.clubsallowed:
        #                         list_f.append(i)
        #                         dic['name']=i.dapendent_first_name1 +" "+i.dependent_family_name
        #                         dic['uid']=i.family_uid
        #                         dic['exp_date']=i.date_of_expiry
        #                         dic['type']=i.member.organization.name +"-Family"
        #                         dic['status']=i.status
                                
        #                         dic['club']=club_q
        #                         obj_list.append(dic) 
        content['obj_list'] = result
        

        if len(members) == 0:
            msg = 'No record found !!!' 
            content['msg']=msg
                
            return render_to_response('Steward/memberlist.html',content,context_instance=RequestContext(request))
            
    if request.method == "GET":
        if 'export' in request.GET:

            typ = request.GET['type']
            club_q = request.GET['club']
            print club_q
            if club_q == 'All':
                cids = []
                cid = club.objects.filter(name__in=userclubs)

                for i in cid:
                    cids.append(i.id)

                members = clubstatus.objects.filter(club_id__in=cids).exclude(status='Inactive')
                

            else:
                #cid = club.objects.get(id=club_q)

                members = clubstatus.objects.filter(club_id=club_q.id).exclude(status='Inactive')

            
            for i in members:
                dic={}
                
                if i.status!="Membership-Cancelled":
                    if i not in list_m:
                        list_m.append(i)
                        dic['name']=i.member.name +" "+i.member.first_name_1+" "+i.member.first_name_2
                        dic['uid']=i.member.member_uid
                        dic['exp_date']=i.date_of_expiry
                        dic['type']=i.member.organization
                        dic['club']=i.club.name
                        dic['status']=i.member.status
                        obj_list.append(dic)
    
            # for i in obj_listf:
            #     dic={}
            #     for j in userclubs:
            #         if j in i.member.clubsallowed:
            #             if i.status!="Membership-Cancelled":
            #                 if i not in list_f:
            #                     list_f.append(i)
            #                     dic['name']=i.dapendent_first_name1 +" "+i.dependent_family_name
            #                     dic['uid']=i.family_uid
            #                     dic['exp_date']=i.date_of_expiry
            #                     dic['type']=i.member.organization.name +"-Family"
            #                     dic['status']=i.status
            #                     obj_list.append(dic)
                        
            if typ == 'excel':
                filename = "List Of Members"
                fromdate=date.today()
                response = HttpResponse(content_type='application/ms-excel')
                response['Content-Disposition'] = 'attachment; filename='+filename+"("+str(fromdate)+").xls"
                wb = xlwt.Workbook(encoding='utf-8')
                ws = wb.add_sheet("MyModel",{'default_date_format':'dd/mm/yy'})
                row_num = 2
                columns = [
                    (u"Staff Id", 6000),
                    (u"Name", 8000),
                    (u"Club",6000),
                    (u"Status",4000),
                    (u"Date Of Expiry",6000),
                    (u"Type",6000),
                ]
                style = xlwt.easyxf('font: bold 1')
                font_style = xlwt.XFStyle()
                font_style.font.bold = True
                ws.write(0,2, filename, font_style)
                for col_num in xrange(len(columns)):
                    ws.write(row_num, col_num, columns[col_num][0], font_style)
                    # set column width
                    ws.col(col_num).width = columns[col_num][1]
                font_style = xlwt.XFStyle()
                font_style.alignment.wrap =-1
                for obj in obj_list:
                    row_num += 1
                    row = [
                        obj['uid'],
                        obj['name'],
                        obj['club'],
                        obj['status'],
                        str(obj['exp_date']),
                        str(obj['type']),
                        
                   
                    ]
                    for col_num in xrange(len(row)):
                        ws.write(row_num, col_num, row[col_num], font_style)
                        
                wb.save(response)
                return response
            
                # return response    
    return render_to_response('Steward/memberlist.html',content,context_instance=RequestContext(request))

@user_login_required   
def qpaddmember(request):

    url = '/qpaddmember/'
    userid = request.session['user']
    content={}
    content.update(csrf(request))

    data = {}
    if 'emid' in request.GET:
        emid = request.GET['emid']
        mem_obj = member.objects.get(id=emid)
        data['name'] = mem_obj.name
        data['first_name_1'] = mem_obj.first_name_1
        data['first_name_2'] = mem_obj.first_name_2
        data['first_name_3'] = mem_obj.first_name_3
        data['initials'] = mem_obj.initials
        data['member_uid'] = mem_obj.member_uid
        data['residencelocation'] = mem_obj.residencelocation
        data['nationality'] = mem_obj.nationality
        data['office_fax_no'] = mem_obj.office_fax_no
        data['cont_type'] = mem_obj.cont_type
        data['cont_term_reason'] = mem_obj.cont_term_reason
        data['cont_expiry_date'] = mem_obj.cont_expiry_date
        data['No_of_dependents'] = mem_obj.No_of_dependents
        data['associatecompany'] = mem_obj.associatecompany
        data['maritalstatus'] = mem_obj.maritalstatus
        data['mobileno'] = mem_obj.mobileno
        data['gender'] = mem_obj.gender
        data['emailid'] = mem_obj.emailid
        data['dob'] = mem_obj.dob
        data['date_of_joining'] = mem_obj.date_of_joining
        data['date_of_expiry'] = mem_obj.date_of_expiry
        data['rfidcardno'] = mem_obj.rfidcardno
        data['extract_run_date'] = mem_obj.extract_run_date
        data['pos_desc'] = mem_obj.pos_desc
        data['worklocation'] = mem_obj.worklocation
        li=[]
        # l = mem_obj.clubsallowed
       
        # clubs = []
        # clubs_list = club.objects.all()

        # for i in clubs_list:
        #     clubs.append(i.name)

        # for i in clubs:
        #     if i in l:                
        #         li.append(i)
        cls = clubstatus.objects.filter(member_id=mem_obj.id)
        for i in cls:
            li.append(i.club_id)
        # tot_clubs = club.objects.filter(name__in=li)
        data['clubsallowed'] = li
        data['status'] = mem_obj.status
        data['department'] = mem_obj.department
        data['membership_grade'] = mem_obj.membership_grade
        data['membership_category'] = mem_obj.membership_category
        data['organization'] = mem_obj.organization
        # data['employment'] = mem_obj.employment
        data['qpuser'] = mem_obj.qpuser
        data['datetime'] = mem_obj.datetime
        form=MemberForm(initial=data,user=userid)

        content = {'form':form,'mid':emid,'photo':mem_obj.photo,'IMAGE_URL':conf_settings.IMAGE_URL}

        if str(userid.role) == 'Steward':
            return render_to_response('Steward/qpaddmember.html',content, context_instance=RequestContext(request))
        return render_to_response('qpaddmember.html', content,context_instance=RequestContext(request))


    if 'mid' in request.POST:
        emid = request.POST['mid']
        if emid:

            member_form = MemberForm(userid,request.POST)
            if member_form.is_valid():
                clubs1 = member_form.cleaned_data['clubsallowed']
                li=[]
                l = userid.clubsallowed
               
                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in l:                
                        li.append(i)
                uclubs = club.objects.filter(name__in=li)
                # for i in clubs1:
                #     if i not in uclubs:
                #         return HttpResponse('<script type="text/javascript">alert("You are not allowed to do any Operation of other Club Member!");window.close();</script>')
                memberedit = member.objects.get(id=emid)
                if 'Imagefile' in request.FILES:
                    f = request.FILES['Imagefile']
                    #f = open(settings.IMAGE_ROOT,"ListingImages\\Customer-%s.%s" %(cid,flist[1]), "wb")
                    file_name = f.name
                    flist = file_name.split(".")
                    data = f.read()
                    f.close()
                    f = open(conf_settings.IMAGE_ROOT + "%s.%s" %(memberedit.member_uid,flist[1]),"wb")
                    # size = (100,100)
                    # f.thumbnail(size, Image.ANTIALIAS)
                    # f.save(outfile, "JPEG")
                    f.write(data)
                    f.close()
                    imageUrl  = "%s.%s" %(memberedit.member_uid,flist[1])
                    # memberedit.photo =  imageUrl
                member_form = MemberForm(userid,request.POST, instance = memberedit)
                member_form.save()
                mem_obj = member.objects.get(id=emid)
                li=[]
                l = mem_obj.clubsallowed
               
                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in l:                
                        li.append(i)
                tot_clubs = club.objects.filter(name__in=li)
                date = datetime.now()
                for i in tot_clubs:
                    status_obj = clubstatus.objects.filter(member_id=mem_obj.id,club_id=i.id)
                    if not status_obj:
                        # date_of_expiry = "%s-%s-%s" % (date.year+1, date.month, date.day)
                        # status_obj.date_of_expiry = date_of_expiry
                        # status_obj.save()
                        cl_obj = clubstatus(member_id=mem_obj.id,club_id=i.id,status=mem_obj.status)
                        cl_obj.save()
                if 'Imagefile' in request.FILES:
                    f = request.FILES['Imagefile']
                    if f:
                        memobj = member.objects.get(id=emid)
                        memobj.photo = imageUrl
                        memobj.save()

                family_obj = family.objects.filter(member_id=emid)
                for i in family_obj:
                    i.clubsallowed = clubs1
                    i.save()

                mem_obj = member.objects.get(id=emid)
                l = mem_obj.clubsallowed
               
                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in l:                
                        li.append(i)
                new_clubs = club.objects.filter(name__in=li)
                mem_status_obj = clubstatus.objects.filter(member_id=mem_obj.id)
                return HttpResponse('<script type="text/javascript">window.close();window.opener.location.reload(true);</script>')

    if request.method == 'POST':
        if 'personid' in request.POST:
            personid = request.POST["personid"]
            # personid = request.POST["personid"]
            # path = os.getcwd()+'/qpcmms/static/'
            path = os.path.join(os.path.dirname(__file__))
            book=xlrd.open_workbook(path + '/static/Qpdata.xlsx')
            sheet = book.sheet_by_index(0)
            r = sheet.row(0)
            c = sheet.col_values(1)
            data = []
            for i in range(len(c)):
                if(c[i] == personid):
                    r = sheet.row(i)
                    for i in range(len(r)):
                        data.append(r[i].value)
            if personid not in c:
                err_msg = 'Sorry! There is no member with this ID'
                form = MemberForm(user=userid)
                content = {'username':userid.name,'err_msg':err_msg,'form':form}

                return HttpResponse('<script type="text/javascript" >alert("There is no Member with this ID");window.close();</script>')
            name = data[2]
            first_name_1 = data[3]
            first_name_2 = data[4]
            first_name_3 = data[5]
            initials = data[6]
            member_uid = data[1]
            nationality = data[10]
            maritalstatus = data[9]
            mobileno = data[13]
            office_fax_no = data[14]
            cont_type =data[17]
            cont_term_reason = data[18]
            cont_expiry_date = data[19]
            No_of_dependents = data[20]
            gender = data[8]
            
            dob = ''#data[]
            residencelocation = ''
            membership_grade = 'QP Full Membership'
            membership_category = data[15]
            associatecompany = 'QP'
            # date = datetime.now()
            # date_of_joining = "%s-%s-%s" % (date.year, date.month, date.day)
            # date_of_expiry = "%s-%s-%s" % (date.year+1, date.month, date.day)
            user = userid.id
            extract_run_date = data[22]
            pos_desc = data[16]
            worklocation = data[12]
            clubsallowed = 'DRC'
            status = 'Pending'
            department = data[11]
            membership = '1'
            organization = '1'
            employment = '2'
            mem_id = member.objects.filter(member_uid=member_uid).order_by('-id')
            if mem_id:
                if mem_id[0].status != 'Inactive':
                    err_msg = 'Member already Added !!'
                    form = MemberForm(user=userid)
                    content = {'username':userid.name,'err_msg':err_msg,'form':form}
                    return HttpResponse('<script type="text/javascript">alert("Member already Added !!");window.close();</script>')

            form=MemberForm(initial={'name': name, 'first_name_1' : first_name_1, 'first_name_2' : first_name_2, 'first_name_3' : first_name_3,    'initials' : initials,    'office_fax_no' : office_fax_no, 'cont_type' : cont_type, 'cont_term_reason' : cont_term_reason, 'cont_expiry_date' : cont_expiry_date,    'No_of_dependents' : No_of_dependents,    'member_uid': member_uid, 'nationality': nationality, 'dob': dob, 'mobileno': mobileno, 'gender': gender, 'maritalstatus': maritalstatus, 'residencelocation':residencelocation, 'membership_grade': membership_grade, 'membership_category': membership_category, 'associatecompany':associatecompany, 'clubsallowed': clubsallowed, 'status': status, 'employment': employment, 'organization': organization, 'department': department, 'qpuser': user, 'extract_run_date':extract_run_date, 'pos_desc':pos_desc, 'worklocation':worklocation},user=userid)
            content = {'username':userid.name,'form':form}
        else:
            form = MemberForm(userid,request.POST)
            if form.is_valid():
                member_uid = form.cleaned_data['member_uid']
                clubs1 = form.cleaned_data['clubsallowed']
                obj = form.save(commit=False)
                obj.datetime = datetime.now()
                li=[]
                l = userid.clubsallowed
               
                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in l:                
                        li.append(i)
                uclubs = club.objects.filter(name__in=li)
                for i in clubs1:
                    if i not in uclubs:
                        return HttpResponse('<script type="text/javascript">alert("You are not allowed to do any Operation of other Club Member!");window.close();</script>')
                obj = form.save(commit=False)
                if str(userid.role) == 'Supervisor':
                    obj.status = 'Active'
                # obj.user_id = user.id
                if 'Imagefile' in request.FILES:
                    f = request.FILES['Imagefile']
                    file_name = f.name
                    flist = file_name.split(".")
                    data = f.read()
                    f.close()
                    f = open(os.path.join(conf_settings.IMAGE_ROOT, "%s.%s" %(member_uid,flist[1])), "wb")
                    f.write(data)
                    f.close()
                if 'Imagefile' in request.FILES:
                    if f:
                        # memObj = member.objects.latest('id')
                        imageUrl  = "%s.%s" %(member_uid,flist[1])
                        obj.photo =  imageUrl
                if 'Imagefile' not in request.FILES:
                    imageUrl  = 'People.jpg'
                    obj.photo =  imageUrl
                #     # customer.save()
                obj.save()
                memobj = member.objects.filter(qpuser=userid.id).latest('id')
                clubstatus_obj = clubstatus()
                # date = datetime.now()
                # # date_of_joining = "%s-%s-%s" % (date.year, date.month, date.day)
                # date_of_expiry = "%s-%s-%s" % (date.year+1, date.month, date.day)
                # memship = membership()
                clubstatus_obj.member_id = memobj.id
                li=[]
                # l = mem_obj.clubsallowed

                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in memobj.clubsallowed:
                        li.append(i)

                for i in li:
                    c_obj = club.objects.get(name=i)
                    memship = clubstatus(member_id=memobj.id,club_id=c_obj.id,status=memobj.status)

                    memship.save()
                return HttpResponse('<script type="text/javascript">window.close();window.opener.parent.location.href = "/members/";</script>')
    return render_to_response('qpaddmember.html',content, context_instance=RequestContext(request))
 
@user_login_required
def clubslist(request):

    content = {}
    data = {}
    content.update(csrf(request))
    user = request.session['user']

    content['user'] = user

    reason = ''
    cid = ''

    if request.method == 'POST':
        mid = request.POST['mid']
        submit = request.POST['submit']
        mem_obj = member.objects.get(id=mid)
        action = request.POST['action']
        form = SuspensionForm(cid,mid,user,request.POST)
        print form.errors
        if form.is_valid:
            clubs1 = form.cleaned_data['clubsallowed']
            status = form.cleaned_data['status']
            mobj = member.objects.get(id=mid)
            if status == 'Active':
                mobj.status = 'Active'
                mobj.save()

            d1 = form.cleaned_data['fromdate']
            d2 = form.cleaned_data['todate']
            club_id = form.cleaned_data['club']
            li=[]
            l = user.clubsallowed
           
            clubs = []
            clubs_list = club.objects.all()

            for i in clubs_list:
                clubs.append(i.name)

            for i in clubs:
                if i in l:                
                    li.append(i)
            uclubs = club.objects.filter(name__in=li)
            # for i in clubs1:
            #     if i not in uclubs:
            #         return HttpResponse('<script type="text/javascript">alert("You are not allowed to do any Operation of other Club Member!");window.close();</script>')

            form.save()
            if 'renewing' in request.POST:
                if str(user.role) == 'Supervisor':
                    # if submit != 'Reject':
                    renew_obj = renewal()
                    renew_obj.renewalby_id = user.id
                    renew_obj.date_of_renewal = d1
                    renew_obj.date_of_expiry = d2
                    renew_obj.member_id = mem_obj.id
                    renew_obj.club_id = club_id.id
                    renew_obj.save()

            lst = []
            for i in clubs1:
                lst.append(i.name)

            if 'Supervisor' not in str(user.role):
                supervisor = role.objects.get(rolename='Supervisor')
                qpuser_lst = qpuser.objects.filter(role_id=supervisor.id)
                email_lst = []
                user_name = []
                for u in qpuser_lst:
                    if u.role.rolename == 'Supervisor' or u.role.rolename =='supervisor':
                        l = u.clubsallowed
                        clubs = []
                        li = []
                        clubs_list = club.objects.all()

                        for i in clubs_list:
                            clubs.append(i.name)


                        for i in clubs:
                            if i in l:                
                                li.append(i)
                        new_cl = club.objects.filter(name__in=li)
                        for i in new_cl:
                            for j in clubs1:
                                if i.id == j.id:
                                    email_lst.append(u.emailid)
                if status == 'Pending-Suspension':
                    subject = 'New request for Suspension of membership for Member Id :%s'%(mem_obj.member_uid)
                    message = 'Dear Supervisor,\n\n\n'
                    message += 'Please consider suspension request submitted for the Club Member whose details are as follows, \n\n\n'
                    name = mem_obj.name+' '+mem_obj.first_name_1
                    message += 'Member Name: %s \n\n\n '%name
                    message += 'Staff ID:  %s \n\n\n'%mem_obj.member_uid
                    message += 'Club: %s\n \n'%(str(lst))
                    message += 'Click http://localhost:8000/common/?mid=%s to take any action.'%(str(mem_obj.id))
                    from_email = 'venugopal@techanipr.com'
                    # to_list = ['ashok@indiadens.com']
                    # return HttpResponse(message)
                    datatuple = (
                    (subject, message, 'venugopal@techanipr.com', email_lst),
                    )

                    # send_mass_mail(datatuple, fail_silently = True)
                    NotifySupervisor.delay(datatuple)

                if status == 'Pending-Cancel':
                    subject = 'New request for Cancellation of membership for Member Id :%s'%(mem_obj.member_uid)
                    message = 'Dear Supervisor,\n\n\n'
                    message += 'Please consider cancellation request submitted for the Club Member whose details are as follows, \n\n\n'
                    name = mem_obj.name+' '+mem_obj.first_name_1
                    message += 'Member Name: %s \n\n\n '%name
                    message += 'Staff ID:  %s \n\n\n'%mem_obj.member_uid
                    message += 'Club: %s\n \n'%(str(lst))
                    message += 'Click http://localhost:8000/common/?mid=%s to take any action.'%(str(mem_obj.id))
                    from_email = 'venugopal@techanipr.com'
                    # to_list = ['ashok@indiadens.com']
                    # return HttpResponse(message)
                    datatuple = (
                    (subject, message, 'venugopal@techanipr.com', email_lst),
                    )
                    # send_mass_mail(datatuple, fail_silently = True)
                    NotifySupervisor.delay(datatuple)

                if status == 'Pending-Renewal':
                    subject = 'New request for Renewal of membership for Member Id :%s'%(mem_obj.member_uid)
                    message = 'Dear Supervisor,\n\n\n'
                    message += 'Please consider renewal request submitted for the Club Member whose details are as follows, \n\n\n'
                    name = mem_obj.name+' '+mem_obj.first_name_1
                    message += 'Member Name: %s \n\n\n '%name
                    message += 'Staff ID:  %s \n\n\n'%mem_obj.member_uid
                    message += 'Club: %s\n \n'%(str(lst))
                    message += 'Click http://localhost:8000/common/?mid=%s to take any action.'%(str(mem_obj.id))
                    from_email = 'venugopal@techanipr.com'
                    # to_list = ['ashok@indiadens.com']
                    # return HttpResponse(message)
                    datatuple = (
                    (subject, message, 'venugopal@techanipr.com', email_lst),
                    )
                    # send_mass_mail(datatuple, fail_silently = True)
                    NotifySupervisor.delay(datatuple)

                if status == 'Pending-Suspension-Revoke':
                    subject = 'New request for Revoke of membership for Member Id :%s'%(mem_obj.member_uid)
                    message = 'Dear Supervisor,\n\n\n'
                    message += 'Please consider revoke request submitted for the Club Member whose details are as follows, \n\n\n'
                    name = mem_obj.name+' '+mem_obj.first_name_1
                    message += 'Member Name: %s \n\n\n '%name
                    message += 'Staff ID:  %s \n\n\n'%mem_obj.member_uid
                    message += 'Club: %s\n \n'%(str(lst))
                    message += 'Click http://localhost:8000/common/?mid=%s to take any action.'%(str(mem_obj.id))
                    from_email = 'venugopal@techanipr.com'
                    # to_list = ['ashok@indiadens.com']
                    # return HttpResponse(message)
                    datatuple = (
                    (subject, message, 'venugopal@techanipr.com', email_lst),
                    )
                    # send_mass_mail(datatuple, fail_silently = True)
                    NotifySupervisor.delay(datatuple)
                # messages.success(request, 'Hello Qp Club Membership Holders ')


                if status == 'Pending-Cancel-Reactivate':
                    subject = 'New request for Reactivation of membership for Member Id :%s'%(mem_obj.member_uid)
                    message = 'Dear Supervisor,\n\n\n'
                    message += 'Please consider reactivation request submitted for the Club Member whose details are as follows, \n\n\n'
                    name = mem_obj.name+' '+mem_obj.first_name_1
                    message += 'Member Name: %s \n\n\n '%name
                    message += 'Staff ID:  %s \n\n\n'%mem_obj.member_uid
                    message += 'Club: %s\n \n'%(str(lst))
                    message += 'Click http://localhost:8000/common/?mid=%s to take any action.'%(str(mem_obj.id))
                    from_email = 'venugopal@techanipr.com'
                    # to_list = ['ashok@indiadens.com']
                    # return HttpResponse(message)
                    datatuple = (
                    (subject, message, 'venugopal@techanipr.com', email_lst),
                    )
                    # send_mass_mail(datatuple, fail_silently = True)
                    NotifySupervisor.delay(datatuple)
                # messages.success(request, 'Hello Qp Club Membership Holders ')

        li = []
        clubs = club.objects.all()
        sus_obj = suspension.objects.filter(member_id=mem_obj.id).order_by('-id')
        sus_obj = sus_obj[0]
        l = sus_obj.clubsallowed
       
        clubs = []
        clubs_list = club.objects.all()

        for i in clubs_list:
            clubs.append(i.name)

        for i in clubs:
            if i in l:                
                li.append(i)
        new_cl = club.objects.filter(name__in=li)

        set_status = clubstatus.objects.filter(member_id=mem_obj.id)

        if len(set_status) == 1:
            set_status = set_status[0]
            if str(sus_obj.status) == 'Suspension-Revoke':
                # if submit == 'Reject':
                #     set_status.status = sus_obj.status = mem_obj.status = 'Suspended'
                # else:
                set_status.status = mem_obj.status = 'Active'
            elif str(sus_obj.status) == 'Suspended':
                # if submit == 'Reject':
                #     set_status.status = sus_obj.status = 'Active'
                #     mem_obj.status = 'Active'
                # else:
                set_status.status = mem_obj.status = 'Suspended'
            elif str(sus_obj.status) == 'Membership-Cancelled':
                set_status.status =  'Inactive'#mem_obj.status = 'Inactive'

            else:

                set_status.status = mem_obj.status = sus_obj.status
            mem_obj.save()
            sus_obj.save()
            set_status.save()
        else:
            fix_status = fix_status1 = []
            for i in new_cl:

                status_obj = clubstatus.objects.filter(member_id=mem_obj.id,club_id=i.id)
                status_obj = status_obj[0]

                if 'renewing' in request.POST:
                    if str(user.role) == 'Supervisor':
                        # if submit == 'Reject':
                        #     status_obj.status = 'Rejected-Renewal'
                        #     # status_obj.save()
                        # else:
                        status_obj.date_of_expiry = d2

                # if str(sus_obj.status) == 'Suspended':
                #         # if submit == 'Reject':
                #         #     status_obj.status = sus_obj.status = 'Active'
                #         sus_obj.save()
                if str(sus_obj.status) == 'Suspension-Revoke':
                    # if submit == 'Reject':
                    #     status_obj.status = sus_obj.status = 'Suspended'
                    #     sus_obj.save()

                    # else:
                    status_obj.status = 'Active'

                elif str(sus_obj.status) == 'Membership-Cancelled':
                    #cl_obj = clubstatus.objects.filter(member_id=mem_obj.id)
                    # for c in cl_obj:
                    #     c.status = 'InActive'
                    status_obj.status = 'Inactive'
                    # c.save()
                    # mem_obj.status = 'Inactive'
                    mem_obj.save()
                # elif str(sus_obj.status) == 'Pending-Cancel':
                #     cl_obj = clubstatus.objects.filter(member_id=mem_obj.id)
                #     for c in cl_obj:
                #         c.status = 'Pending-Cancel'
                #     c.save()
                #     mem_obj.status = 'Pending-Cancel'
                #     mem_obj.save()

                else:
                    status_obj.status = sus_obj.status
                status_obj.save()

        fix_status = clubstatus.objects.filter(member_id=mem_obj.id)
        if len(fix_status) > 1:
            for i in fix_status:
                fix_status1.append(i.status)

            status = fix_status1[:1]
            status = status[0]
            counter = 0
            for i in fix_status1:
                if i == status:
                    counter = counter+1
            if counter == len(fix_status):
                mem_obj.status = status
                mem_obj.save()



        family_obj = family.objects.filter(member_id=mem_obj.id)
        from datetime import datetime
        today = datetime.now().date()
        if family_obj:

            for i in family_obj:
                if i.age >= 21 and i.relationship != 'W' and not i.date_of_expiry:
                    i.status = 'Pending-Crossed-Age 21'
                else:
                    i.status = mem_obj.status

                if i.relationship == 'H':
                    i.status = mem_obj.status
                
                if i.date_of_expiry:
                    if i.date_of_expiry < today:
                        i.status = 'Pending-Crossed-Age 21'
                i.save()
                
        mem_obj = member.objects.get(id=mid)
        if mem_obj.status != 'Inactive':
            return HttpResponse('<script type="text/javascript">window.close();window.opener.location.reload(true);</script>')
        else:
            return HttpResponse('<script type="text/javascript">window.close();window.opener.location.href = "/members/";</script>')

    if 'mid' in request.GET:
        mid = request.GET['mid']

    if 'c_id' in request.GET:
        cid = request.GET['c_id']

        if cid:
            cobj = club.objects.filter(id=cid)
        else:
            m_clubs = clubstatus.objects.filter(member_id=mid)
            cobj = []
            for i in m_clubs:
                cobj.append(i.club)
    if 'action' in request.GET:
        action = request.GET['action']
    mem_obj = member.objects.get(id=mid)
    li = []
    li2 = []
    if action == 'rev':
        mobj = clubstatus.objects.filter(member_id=mid,status__icontains='Suspen')
        if mobj:
            clubs = []
            clubs_list = club.objects.all()

            for i in clubs_list:
                clubs.append(i.name)

            for i in mobj:
                li2.append(i.club_id)

        for i in mobj:
            if 'Pending-' in i.status:
                reject_visible = 'on'
                content['reject_visible'] = reject_visible
                # if action == 'sus':
                sus_obj = suspension.objects.filter(member_id=mem_obj.id,status='Pending-Suspension-Revoke',club_id=cobj[0].id).order_by('-id')
                if sus_obj:
                    sus_obj = sus_obj[0]
                    frmdate = sus_obj.fromdate
                    l = sus_obj.clubsallowed
                   
                    clubs = []
                    clubs_list = club.objects.all()

                    for i in clubs_list:
                        clubs.append(i.name)

                    for i in clubs:
                        if i in l:                
                            li.append(i)
                    cl = club.objects.filter(name__in=li)

                    if cl[0].id == cobj[0].id:
                        reason = sus_obj.reason
                    if frmdate:
                        frmdate = datetime.strftime(frmdate,'%Y-%m-%d')
                        content['fromdate'] = frmdate
                    todate = sus_obj.todate
                    if todate:
                        todate = datetime.strftime(todate,'%Y-%m-%d')
                        content['todate'] = todate
            # else:
            #     cl = club.objects.filter(id__in=li2)

    if action == 'ren':
        mobj = clubstatus.objects.filter(member_id=mid,club_id=cid)
        
        # for i in mobj:
        #     if 'Pending-' in i.status:
        #         reject_visible = 'on'
        #         content['reject_visible'] = reject_visible
        clubs = []
        clubs_list = club.objects.all()

        for i in clubs_list:
            clubs.append(i.name)

        for i in mobj:
            # if i in mem_obj.clubsallowed:
            li2.append(i.club_id)
            cl = club.objects.filter(id__in=li2)


    if action == 'app' or action == 'act':
        if action == 'app':
            mobj = clubstatus.objects.filter(member_id=mid,status="Pending",club_id=cid)
        else:
            mobj = clubstatus.objects.filter(member_id=mid,club_id=cid)

        m_obj = member.objects.get(id=mid)
        sus_obj = suspension.objects.filter(member_id=mid,status='Pending-Cancel-Reactivate',club_id=cobj[0].id).order_by('-id')
        if sus_obj:
            sus_obj = sus_obj[0]
            reason = sus_obj.reason
        clubs = []
        clubs_list = club.objects.all()

        for i in clubs_list:
            clubs.append(i.name)

        for i in mobj:
            li2.append(i.club_id)
            cl = club.objects.filter(id__in=li2)

        data['status'] = 'Active'
        from datetime import datetime

        frmdate = datetime.strftime(datetime.now(),'%Y-%m-%d')
        content['fromdate'] = frmdate
        if mobj[0].date_of_expiry:
            todate = datetime.strftime(mobj[0].date_of_expiry,'%Y-%m-%d')
            content['todate'] = todate
        if m_obj.organization.name == 'QP':
            content['org'] = m_obj.organization.name
        

    if action == 'sus' or action=='can':
        # sus_form = SuspensionForm()
        li2 = []
        mobj = clubstatus.objects.filter(member_id=mid,club_id=cobj[0].id).exclude(status='Pending')
        if mobj:
            clubs = []
            clubs_list = club.objects.all()

            for i in clubs_list:
                clubs.append(i.name)

            for i in mobj:
                li2.append(i.club_id)

                if 'Pending-' in i.status:
                    reject_visible = 'on'
                    content['reject_visible'] = reject_visible
                    if action == 'sus':
                        sus_obj = suspension.objects.filter(member_id=mem_obj.id,status='Pending-Suspension',club_id=cobj[0].id).order_by('-id')
                        # if i.club_id == cobj[0].id:
                        from datetime import datetime
                        if sus_obj:
                            sus_obj = sus_obj[0]
                            reason = sus_obj.reason
                            frmdate = sus_obj.fromdate
                            if frmdate:
                                frmdate = datetime.strftime(frmdate,'%Y-%m-%d')
                                content['fromdate'] = frmdate
                            todate = sus_obj.todate
                            if todate:
                                todate = datetime.strftime(todate,'%Y-%m-%d')
                                content['todate'] = todate
                        else:
                                cl = club.objects.filter(id__in=li2)

                    if action == 'can':
                        canc_cl = []
                        sus_obj = suspension.objects.filter(member_id=mem_obj.id,status='Pending-Cancel').order_by('-id')
                        if sus_obj:
                            sus_obj = sus_obj[0]
                            reason = sus_obj.reason
                            l = sus_obj.clubsallowed
                           
                            clubs = []
                            clubs_list = club.objects.all()

                            for i in clubs_list:
                                clubs.append(i.name)

                            for i in clubs:
                                if i in l:                
                                    li.append(i)
                            cl = club.objects.filter(name__in=li)
                        else:
                            cl = club.objects.filter(id__in=li2)
                else:
                    cl = club.objects.filter(id__in=li2)
        else:
            clubs = []
            clubs_list = club.objects.all()

            for i in clubs_list:
                clubs.append(i.name)

            for i in clubs:
                if i in mem_obj.clubsallowed:
                    li2.append(i)
                    cl = club.objects.filter(name__in=li2)
    data['member'] = mid
    # data['clubsallowed'] = cobj
    data['doneby'] = user.id
    if action=='sus':
        if str(user.role) == 'Supervisor':
            data['status'] = 'Suspended'
        else:
             data['status'] = 'Pending-Suspension'



    if action == 'rev':
        if str(user.role) == 'Supervisor':
            data['status'] = 'Suspension-Revoke'
        else:
            data['status'] = 'Pending-Suspension-Revoke'

    if action == 'can':
        if str(user.role) == 'Supervisor':
            data['status'] = 'Membership-Cancelled'
        else:
            data['status'] = 'Pending-Cancel'

    if action == 'act':
        if str(user.role) == 'Supervisor':
            data['status'] = 'Active'
        else:
            data['status'] = 'Pending-Cancel-Reactivate'

    if action == 'ren':
        from datetime import datetime
        date = datetime.now()
        fromdate = "%s-%s-%s" % (date.year, date.month, date.day)
        todate = "%s-%s-%s" % (date.year+1, date.month, date.day)
        content['fromdate'] = fromdate
        content['todate'] = todate
        if str(user.role) == 'Supervisor':
            data['status'] = 'Active'
            renew = 'renewal'
            content['renewal'] = renew
            sus_obj = suspension.objects.filter(member_id=mid,status='Pending-Renewal',club_id=cid).order_by('-id')
            reason = sus_obj[0].reason
            content['fromdate'] = datetime.strftime(sus_obj[0].fromdate,'%Y-%m-%d')
            content['todate'] = datetime.strftime(sus_obj[0].todate,'%Y-%m-%d')
        else:
            data['status'] = 'Pending-Renewal'

    if action == 'can':
        data['clubsallowed'] = cobj
        content['cname'] = cobj
        data['club'] = cid
    else:
        data['clubsallowed'] = cobj
        data['club'] = cid
        content['cname'] = cobj[0].name
    if cid:
        sform = SuspensionForm(initial=data,user=user,mid=mid,cid=cid)
    else:
        sform = SuspensionForm(initial=data,user=user,mid=mid,cid=cobj[0].id)
    # sform.fields['clubsallowed'].widget.attrs['hidden'] = True
    content['sform'] = sform
    content['mid'] = mid
    content['action'] = action
    if str(user.role) == 'Supervisor':
        content['reas'] = reason
    content['role'] = str(user.role)

    return render_to_response('clublist.html',content, context_instance=RequestContext(request))

@user_login_required
def download(request):
    if 'mid' in request.GET:

        mid = request.GET['mid']

        m_obj = member.objects.get(id=mid)
        filename = m_obj.attachment 
        content_type = "application/octet-stream"
        response = HttpResponse(filename, content_type=content_type)
        response["Content-Disposition"]= "attachment; filename=attachment"
        return response 


def render_email(template, data=None):
  html = get_template(template)
  d = Context(data)
  html_content = html.render(d)
  return html_content

def SendEMail(subject, body, to):
    from_email = '<venugopal@techanipr.com>'

    if type(to) is str:
      to = [to]

    white_list = []
    for email in to:
      # if email  in [ 'venugopal@techanipr.com',]:
        white_list.append(email)

    if type(to) is not list:
      logging.info("Invalid To Address. To addresses should be in list")
      return False
      
    try:      
      msg = EmailMultiAlternatives(subject, body, from_email, white_list)
      msg.attach_alternative(body, "text/html")
      if white_list:  msg.send()
    except Exception,  e:
      logging.info(str(e))
      return False
  
    return True

def ResetPassword(request):
    content = {}
    if 'emailid' in request.GET:
        emailid = request.GET['emailid']
        if(qpuser.objects.filter(emailid = emailid)):
          uobj = qpuser.objects.filter(emailid = emailid)
          uobj = uobj[0]
          content['emailid'] = uobj.userid
          content['password'] = uobj.password
          html = render_email('PasswordReset.html', content)
          # SendEMail("Password Reset", html, str(userObj1[0].emailid.strip()))
          UserMail.delay(uobj)
          content['success'] = 'Password has been sent to your Mail. Please check your Inbox.'
          return render_to_response('EMail-PasswordReset.html', content, context_instance=RequestContext(request))
        else:
          content['err_msg'] = 'Email not found'
          return render_to_response('EMail-PasswordReset.html', content, context_instance=RequestContext(request))
    else:
        return render_to_response('EMail-PasswordReset.html', content, context_instance=RequestContext(request))

@user_login_required
def userpwd_reset(request):

    content = {}

    if request.method == 'POST':
        if 'email' in request.POST:

            email = request.POST['email']
            uid = request.POST['uid']
            uobj = qpuser.objects.get(id=uid)
            pwd = ''.join(random.choice('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(5))
            uobj.password = pwd

            uobj.save()
            content['emailid'] = uobj.userid
            content['password'] = pwd
            content['first_name'] = uobj.name
            html = render_email('PasswordReset.html', content)
            # SendEMail("Password Reset", html, str(email))
            UserMail.delay(uobj)

            suc_msg = 'Password Has been Sent to User Email'

            content['suc_msg'] = suc_msg

            return HttpResponse('<script type="text/javascript">alert("Password Has been Sent to User Email !");window.close();window.opener.parent.location.href = "/users/";</script>')


    if request.method == 'GET':
        if 'uid' in request.GET:
            uid = request.GET['uid']

            uobj = qpuser.objects.get(id=uid)

            content['email'] = uobj.emailid

            content['uid'] = uobj.id

    return render_to_response('Admin/user_pwd_reset.html', content, context_instance=RequestContext(request))

@user_login_required
def reset_self_pwd(request):
    content = {}

    if request.method == 'POST':
        currentpassword = request.POST['currentpassword']
        newpassword = request.POST['newpassword']
        confirmpassword = request.POST['confirmpassword']
        user = request.session['user']
        if currentpassword != user.password:
            err_msg = 'Password did not match! Please try again'
            content['errmsg'] = err_msg
            return render_to_response('user_selfpwd_reset.html', content, context_instance=RequestContext(request))
        
        if newpassword != confirmpassword:
            err_msg = 'Password did not match! Please try again'
            content['errmsg'] = err_msg
            return render_to_response('user_selfpwd_reset.html', content, context_instance=RequestContext(request))

        userobj = qpuser.objects.get(id=user.id)

        userobj.password = confirmpassword
        userobj.save()
        suc_msg = 'Password Has been Changed Successfully !'
        content['errmsg'] = suc_msg
        return HttpResponse('<script type="text/javascript">alert("Password Has been Changed Successfully !");window.close();window.opener.parent.location.href = "/logout/";</script>')
        # return render_to_response('user_selfpwd_reset.html', content, context_instance=RequestContext(request))


    return render_to_response('user_selfpwd_reset.html', content, context_instance=RequestContext(request))

@user_login_required
def Reject(request):
    if 'mid' in request.GET:
        mid = request.GET['mid']

        mem_obj = member.objects.get(id=mid)

    if 'cid' in request.GET:
        cid = request.GET['cid']

        if cid:
            status_obj = clubstatus.objects.get(member_id=mid,club_id=cid)

            clubs = clubstatus.objects.filter(member_id=mid)

    else:

        status_obj = clubstatus.objects.filter(member_id=mid)

        clubs = clubstatus.objects.filter(member_id=mid)



    if 'action' in request.GET:

        action = request.GET['action']

    if action == 'sus' or action == 'can':

        if action == 'sus':
            status_obj.status = 'Active'
            if len(clubs) == 1:
                mem_obj.status = 'Active'

        if action == 'can':

            cl_obj = clubstatus.objects.filter(member_id=mem_obj.id)

            for c in cl_obj:
                c.status = 'Active'
                c.save()


    if action  == 'app':
        status_obj.status = 'Membership-Rejected'

        if len(clubs) == 1:
            mem_obj.status = 'Membership-Rejected'

    if action  == 'act':
        status_obj.status = 'Inactive'

        # if len(clubs) == 1:
        #     mem_obj.status = 'Inactive'

    if action == 'rev':
        status_obj.status = 'Suspended'

        if len(clubs) == 1:
            mem_obj.status = 'Suspended'


    if action == 'ren':
        status_obj.status = 'Rejected-Renewal'

        if len(clubs) == 1:
            mem_obj.status = 'Rejected-Renewal'


    if action != 'can':
        status_obj.save()

    mem_obj.save()
    fix_status1 = []
    fix_status = clubstatus.objects.filter(member_id=mem_obj.id)
    if len(fix_status) > 1:
        for i in fix_status:
            fix_status1.append(i.status)

        status = fix_status1[:1]
        status = status[0]
        counter = 0
        for i in fix_status1:
            if i == status:
                counter = counter+1
        if counter == len(fix_status):
            mem_obj.status = status
            mem_obj.save()



    family_obj = family.objects.filter(member_id=mem_obj.id)

    if family_obj:
        from datetime import datetime
        today = datetime.now().date()

        for i in family_obj:
            for i in family_obj:
                if i.age >= 21 and i.relationship != 'W' and not i.date_of_expiry:
                    i.status = 'Pending-Crossed-Age 21'
                else:
                    i.status = mem_obj.status

                if i.relationship == 'H':
                    i.status = mem_obj.status
                
                if i.date_of_expiry:
                    if i.date_of_expiry < today:
                        i.status = 'Pending-Crossed-Age 21'
                i.save()

    url = '/common/?mid=%s'%(mid)

    return HttpResponseRedirect(url)

@user_login_required
def family_suspension(request):
    content = {}
    if 'fid' in request.GET:
        fid = request.GET['fid']

        content['fid'] = fid
        # content['reason'] = 'Age is above 21 years.'
    if 'fid' in request.POST:

        fid = request.POST['fid']

        date1 = request.POST['todate']

        reason = request.POST['reason']

        fobj = family.objects.get(id=fid)
        mem_obj = member.objects.get(id=fobj.member_id)

        # if fobj.age >= 21 and (fobj.relationship != 'W' or fobj.relationship != 'H') and (not fobj.date_of_expiry or fobj.date_of_expiry<date.today()):
        #     fobj.status = 'Pending-Crossed-Age 21'
        # else:
        fobj.status = mem_obj.status
        fobj.date_of_expiry = date1

        fobj.save()

        return HttpResponse('<script type="text/javascript">window.close();window.opener.location.reload(true);</script>')

    if 'fid' in request.GET and 'sus' in request.GET:
        fid = request.GET['fid']

        fobj = family.objects.get(id=fid)
        fobj.status = 'Cancelled-Age21'

        fobj.save()

        url = '/familyform/?mid=%s'%(fobj.member_id)
        return HttpResponseRedirect(url)



    return render_to_response('family_suspension.html', content, context_instance=RequestContext(request))

@user_login_required
def addclubs(request):

    user = request.session['user']

    data = {}
    content={}
    if request.method == 'GET':
        if 'mid' in request.GET:

            mid = request.GET['mid']
            mobj = member.objects.get(id = mid)

            # data['clubsallowed'] = club.objects.all()
            data['member'] = mobj
            if str(user.role.rolename) == 'Supervisor':
                data['status'] = 'Active'
            else:
                data['status'] = 'Pending'
            data['doneby'] = user
            sform = AddClubsForm(user=user,mobj=mobj,initial=data)
            # print sform.clubsallowed
            content['mid'] = mid
            content['mobj'] = mobj
            content['sform'] = sform
            content['user'] = user

    if request.method == 'POST':
        mid = request.POST['mid']
        mem_obj = member.objects.get(id=mid)
        form = AddClubsForm(user,mem_obj,request.POST)
        print form.errors
        if form.is_valid:
            clubs1 = form.cleaned_data['clubsallowed']
            status = form.cleaned_data['status']
            lst = []
            for i in clubs1:
                lst.append(i.name)
            clubs = club.objects.filter(name__in=lst)
            mobj = member.objects.get(id=mid)
            if status == 'Active':
                mobj.status = 'Active'
                mobj.save()

            d1 = form.cleaned_data['fromdate']
            d2 = form.cleaned_data['todate']
            club_id = form.cleaned_data['club']

            for i in clubs:
                if d2:
                    mem_club = clubstatus(member_id=mid,club_id=i.id,status=status,date_of_expiry=d2)
                else:
                    mem_club = clubstatus(member_id=mid,club_id=i.id,status=status)

                mem_club.save()
            li=[]
            l = user.clubsallowed
           
            clubs = []
            clubs_list = club.objects.all()

            for i in clubs_list:
                clubs.append(i.name)

            for i in clubs:
                if i in l:                
                    li.append(i)
            uclubs = club.objects.filter(name__in=li)

            form.save()

            if status == 'Pending':
                supervisor = role.objects.get(rolename='Supervisor')
                qpuser_lst = qpuser.objects.filter(role_id=supervisor.id)
                email_lst = []
                for u in qpuser_lst:
                    if u.role.rolename == 'Supervisor' or u.role.rolename =='supervisor':
                        l = u.clubsallowed
                        clubs = []
                        li = []
                        clubs_list = club.objects.all()

                        for i in clubs_list:
                            clubs.append(i.name)


                        for i in clubs:
                            if i in l:                
                                li.append(i)
                        new_cl = club.objects.filter(name__in=li)
                        for i in new_cl:
                            for j in clubs1:
                                if i.id == j.id:
                                    email_lst.append(u.emailid)
                subject = 'New request for membership access for Member Id :%s'%(mobj.member_uid)
                message = 'Dear Supervisor,\n\n\n'
                message += 'Please consider access request submitted for the Club Member whose details are as follows, \n\n\n'
                name = mobj.name+' '+mobj.first_name_1
                message += 'Member Name: %s \n\n\n '%name
                message += 'Staff ID:  %s \n\n\n'%mobj.member_uid
                message += 'Club: %s\n \n'%(str(lst))
                message += 'Click http://localhost:8000/common/?mid=%s to take any action.'%(str(mem_obj.id))
                from_email = 'venugopal@techanipr.com'
                # to_list = ['ashok@indiadens.com']
                # return HttpResponse(message)
                datatuple = (
                (subject, message, 'venugopal@techanipr.com', email_lst),
                )
                # send_mass_mail(datatuple, fail_silently = True)
                NotifySupervisor.delay(datatuple)

    return render_to_response('add_to_club.html',content, context_instance=RequestContext(request))




@user_login_required
def search_members(request):

    user = request.session['user']
    mem_list = []

    new_list = []

    content={}
    content.update(csrf(request))

    if request.method == 'POST':
        search_text = request.POST['search_text']

        print search_text
        if search_text:
            mems = member.objects.filter(Q(name__icontains=search_text)|Q(member_uid__icontains=search_text)).exclude(status='Inactive')[:20]
            # f_mems = family.objects.filter(Q(family_uid__icontains=search_text)).exclude(status='Inactive')[:20]
            # print f_mems
            # if f_mems:
            #     for i in f_mems:
            #         mems.append(i.member)
            # print mems
            if mems:
            #     li=[]
            #     l = user.clubsallowed
                   
            #     clubs = []
            #     clubs_list = club.objects.all()

            #     for i in clubs_list:
            #         clubs.append(i.name)

            #     for i in clubs:
            #         if i in l:                
            #             li.append(i)
            #     for i in mems:
            #         for j in li:
            #             if j in i.clubsallowed:
            #                 mem_list.append(i)
                content['result'] = list(set(mems))

            for i in mems:
                new_list.append(i.member_uid)

        json_stuff = simplejson.dumps({"list_of_jsonstuffs" : new_list})    
        return HttpResponse(json_stuff, content_type ="application/json")


@user_login_required
def view_profile(request):

    content={}
    content.update(csrf(request))

    if request.method == 'POST':
        search_text = request.POST['search_members']
        if search_text:
            mems = member.objects.filter(Q(name__icontains=search_text)|Q(member_uid__icontains=search_text)).exclude(status='Inactive').values('id')

            url = '/common/?mid=%s'%mems[0]['id']

            return HttpResponseRedirect(url)


@user_login_required
def view_profile_guest(request):

    content={}
    content.update(csrf(request))

    if request.method == 'POST':
        search_text = request.POST['search_members']
        if search_text:
            gst = guest.objects.filter(Q(name__icontains=search_text)|Q(emailid__icontains=search_text)|Q(phone_no__icontains=search_text)).values('id')
            if gst:
                url = '/guestEntry/?gid=%s'%gst[0]['id']

                return HttpResponseRedirect(url)
            else:  
                search_msg="No Guest Found With This Detail"  
                content['search_msg']=search_msg
                return render_to_response('Receptionist/guestList.html',content, context_instance=RequestContext(request))
    #return HttpResponseRedirect('/guestList/')

def rfid_post(request):

    if request.method == 'GET':

        if 'rfid' in request.GET and 'cid' in request.GET:

            rfid = request.GET['rfid']
            cid = request.GET['cid']

            tr_obj = transaction(rfidcardid=rfid,club_id=cid,datetime=datetime.now())

            tr_obj.save()
            return HttpResponse('True')

        else:
            return HttpResponse('False')



def get_club(request):

    if request.method == 'GET':
        if 'mac' in request.GET:
            cid = request.GET['mac']

            print cid

            c_id = club.objects.get(ip=cid)

            print c_id

            content = {}

            content['cid'] = c_id.id

        #     json_stuff = simplejson.dumps({"club" : c_id.id})    
        # return HttpResponse(json_stuff, content_type ="application/json")

    return HttpResponse(c_id.id)


@user_login_required
def extend(request):
    content={}
    content.update(csrf(request))

    if request.method == 'POST':
        print "ggahjkaaaaaaaaaaaaatttt"
        #guest_form = GuestForm(request.POST)
        gstid=request.POST['gstid']
        print "hhhhhhhhhuuuuuuuuuuuuurrrrrrrrr" ,gstid
        period=request.POST['period']
        rfidcardno=request.POST['rfidcardno']
        months=int(period)

        guest_obj= guest.objects.get(id=gstid)
        if guest_obj.status=="Active":
            # print guest_obj.status=="Active"
            # exp_date=guest_obj.date_of_expiry+timedelta(int(period))
            # guest_obj.date_of_expiry = exp_date
            sourcedate=guest_obj.date_of_expiry
            month = sourcedate.month - 1 + months
            year = sourcedate.year + month / 12
            month = month % 12 + 1
            day = min(sourcedate.day,calendar.monthrange(year,month)[1])
            exp_date =date(year,month,day-1)
            guest_obj.date_of_expiry = exp_date
            guest_obj.period = period
            guest_obj.rfidcardno = rfidcardno
            #guest_form = GuestForm(request.POST, instance = guest_obj)
            guest_obj.save()
            
        if guest_obj.status=="Inactive":
            #exp_date=date.today()+timedelta(int(period))
            sourcedate=date.today()
            month = sourcedate.month - 1 + months
            year = sourcedate.year + month / 12
            month = month % 12 + 1
            day = min(sourcedate.day,calendar.monthrange(year,month)[1])
            exp_date =date(year,month,day-1)
            guest_obj.date_of_expiry = exp_date
            guest_obj.period = period
            guest_obj.rfidcardno = rfidcardno
            guest_obj.status = "Active"
            #guest_form = GuestForm(request.POST, instance = guest_obj)
            guest_obj.save()
        # from_email = [guest_obj.emailid]

        # # if type(to) is str:
        # #   to = [to]

        # # white_list = []
        # # for email in to:
        # #   # if email  in [ 'venugopal@techanipr.com',]:
        # #     white_list.append(email)

        # # if type(to) is not list:
        # #   logging.info("Invalid To Address. To addresses should be in list")
        # #   return False
        # supervisor_mail=''
        # white_list= '' 
        # try:      
        #   msg = EmailMultiAlternatives(subject, body, from_email, white_list)
        #   msg.attach_alternative(body, "text/html")
        #   if white_list:  msg.send()
        # except Exception,  e:
        #   logging.info(str(e))
        #   return False
      
        # return True    
        return HttpResponse('<script type="text/javascript">window.close();window.opener.parent.location.href = "/guestList/";</script>')
    if request.method == 'GET':
        
        print "ttttttttttwwwwwwwwwwwwwwwwwww"
        gid = request.GET['gid']
        print gid
        rfidcardno=request.GET['rfidcardno']
        guest_obj = guest.objects.get(id=gid)
        print guest_obj.status
        content['expiry'] = guest_obj.date_of_expiry
        content['status'] = guest_obj.status
        content['gid'] = gid
        content['rfidcardno']=rfidcardno
    return render_to_response('Receptionist/extend_guest.html',content, context_instance=RequestContext(request))
    #return HttpResponseRedirect('/guestList/')
          

@user_login_required
def deactivate_guest(request):
    content={}
    content.update(csrf(request))

    if request.method == 'GET':
        print "ggahjkaaaaaaaaaaaaatttt"
        #guest_form = GuestForm(request.POST)
        gstid=request.GET['gstid']
        if gstid:
            guest_obj= guest.objects.get(id=gstid)
            #exp_date=date.today()+timedelta(int(guest_obj.period))
            guest_obj.status = "Inactive"
            guest_obj.rfidcardno = ""
            #guest_form = GuestForm(request.POST, instance = guest_obj)
            guest_obj.save()
                
    return HttpResponseRedirect('/guestList/')  
@user_login_required
def activate_guest(request):
    content={}
    content.update(csrf(request))

    if request.method == 'GET':
        print "ggahjkaaaaaaaaaaaaatttt"
        #guest_form = GuestForm(request.POST)
        gstid=request.GET['gstid']
        if gstid:
            guest_obj= guest.objects.get(id=gstid)
            #exp_date=date.today()+timedelta(int(guest_obj.period))
            guest_obj.status = "Active"
            guest_obj.rfidcardno = request.GET['rfidcardno']
            #guest_form = GuestForm(request.POST, instance = guest_obj)
            guest_obj.save()
                
    return HttpResponseRedirect('/guestList/')        