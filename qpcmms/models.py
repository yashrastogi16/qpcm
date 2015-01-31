from django.db import models
import os
from django.contrib import admin
from django.utils import timezone
from datetime import datetime


STATUS_CHOICES = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Suspended', 'Suspended'),
        ('Pending', 'Pending'),
        ('Pending-Cancel', 'Pending-Cancel'),
        ('Membership-Cancelled', 'Membership-Cancelled'),
        ('Pending-Suspension', 'Pending-Suspension'),
        ('Membership-Suspended','Membership-Suspended'),
        # ('Family_Member-Pending-Suspension', 'Family_Member-Pending-Suspension'),
        # ('Family_Member-Suspended','Family_Member-Suspended'),
        ('Pending-Crossed-Age 21', 'Pending-Crossed-Age 21'),
        ('Cancelled-Age21','Cancelled-Age21'),
        ('Pending-Suspension-Revoke','Pending-Suspension-Revoke'),
        ('Pending-Cancel-Reactivate','Pending-Cancel-Reactivate'),
        ('Suspension-Revoke','Suspension-Revoke'),
        ('Pending-Renewal', 'Pending-Renewal'),
        ('Rejected-Renewal', 'Rejected-Renewal'),
        ('Y', 'Yes'),
        ('N', 'No'),
        ('None', 'None'),
    ) 
MARITAL_CHOICES = (
        ('S', 'Single'),
        ('M', 'Married'),        
    ) 
    
PERIOD_CHOICES = (
        ('1', 'One Month'),
        ('2', 'Two Months'),
        ('3', 'Three Months'),
        
    )     
RELATIONSHIP = (
        ('D', 'Daughter'),
        ('S', 'Son'),        
        ('W', 'Wife'),        
        ('M', 'Mother'),        
        ('F', 'Father'),
        ('H', 'Husband'),        
    )
    
GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),        
    ) 
    
MEMBERSHIP_TYPE = (
        ('QP Full Membership', 'QP Full Membership'),
        ('QP Temporary Membership/House Guest', 'QP Temporary Membership/House Guest'),        
        ('Associate Membership', 'Associate Membership'),        
        ('Non-Associate Membership', 'Non-Associate Membership'),        
        ('Corporate Membership', 'Corporate Membership'),        
        ('Golf-ELS-Non-QP', 'Golf-ELS-Non-QP'),        
    )

MEMBERSHIP_CATEGORY = (
        ('E', 'Junior Post Employee'),
        ('S', 'Senior Post Employee'),      
    )

class club(models.Model):
    
    name = models.CharField(max_length=128)
    ip = models.CharField(max_length=128,null=True,blank=True)
    # members = models.ManyToManyField(member) #through='Membership', through_fields=('group', 'person'))
    # status = models.CharField(max_length=50, choices=STATUS_CHOICES,blank=True,null=True) 
    class Admin:
        pass
    def __str__(self):
        return '%s' %(self.name)

class member(models.Model):
    name = models.CharField(max_length=40, null=True,blank=True)
    first_name_1 = models.CharField(max_length=40, null=True,blank=True)
    first_name_2 = models.CharField(max_length=40, null=True,blank=True)
    first_name_3 = models.CharField(max_length=40, null=True,blank=True)
    initials = models.CharField(max_length=40, null=True,blank=True)
    member_uid = models.CharField(max_length=40, null=True,blank=True)
    nationality = models.CharField(max_length=30, null=True,blank=True)
    dob = models.DateField(null=True,blank=True)
    mobileno = models.CharField(max_length=30, null=True,blank=True)
    photo = models.CharField(max_length=255L, null=True,blank=True)
    office_fax_no = models.CharField(max_length=30, null=True,blank=True)
    cont_type = models.CharField(max_length=30, null=True,blank=True)
    cont_term_reason = models.CharField(max_length=30, null=True,blank=True)
    cont_expiry_date = models.CharField(max_length=30, null=True,blank=True)
    No_of_dependents = models.CharField(max_length=30, null=True,blank=True)
    extract_run_date = models.CharField(max_length=30, null=True,blank=True)
    pos_desc = models.CharField(max_length=100, null=True,blank=True)
    attachment = models.FileField(null=True,blank=True,upload_to=os.path.join(os.path.dirname(__file__))+'/static/qpmedia/')
    worklocation = models.CharField(max_length=50, null=True,blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES,blank=True)
    maritalstatus = models.CharField(max_length=10, choices=MARITAL_CHOICES, null=True,blank=True)
    residencelocation = models.CharField(max_length=40, null=True,blank=True)   
    rfidcardno = models.CharField(max_length=30, null=True,blank=True)
    membership_grade = models.CharField(max_length = 50, choices = MEMBERSHIP_TYPE, null=True,blank=True)
    membership_category = models.CharField(max_length = 50, choices = MEMBERSHIP_CATEGORY, null=True,blank=True)   
    associatecompany = models.ForeignKey('associatecompany', null = True,blank=True)    
    date_of_joining = models.DateField(null=True,blank=True)
    date_of_expiry = models.DateField(null=True,blank=True)        
    # clubsallowed  = models.ManyToManyField('club')
    clubsallowed  = models.CharField(max_length=400) 
    emailid = models.EmailField(null=True,blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES,blank=True,null=True,default='Pending')
    # employment = models.ForeignKey('employment')
    organization = models.ForeignKey('organization',blank=True,null=True)
    department = models.CharField(max_length=100,blank=True,null=True)  
    # department = models.ForeignKey('department')
    qpuser = models.ForeignKey('qpuser')
    datetime = models.DateTimeField(blank=True,null=True)
    class Admin:
        pass
    def __str__(self):
        return '%s' %(self.name)
  
        
class clubstatus(models.Model):
    member = models.ForeignKey('member')
    club = models.ForeignKey('club') 
    status = models.CharField(max_length=40, choices=STATUS_CHOICES,blank=True)
    date_of_expiry = models.DateField(null=True,blank=True)

    class Admin:
        pass
    def __str__(self):
        return '%s''--''%s' %(self.member, self.club)


class qpuser(models.Model):
    name = models.CharField(max_length=40,blank=True)
    userid = models.CharField(max_length=40,blank=True)
    password = models.CharField(max_length=30,blank=True)
    residencelocation = models.CharField(max_length=40,blank=True)  
    clubsallowed  = models.CharField(max_length=400,blank=True)    
    emailid = models.EmailField(null = False,blank=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES,blank=True)
    role = models.ForeignKey('role')
    datetime = models.DateTimeField(auto_now=True)
    officephone = models.CharField(max_length=30,blank=True)
    mobileno = models.CharField(max_length=30,blank=True)
    class Admin:
        pass
    def __str__(self):
        return '%s' %(self.name)
        
        
# class employment(models.Model):    
#     worklocation = models.CharField(max_length=30)
#     officephone = models.CharField(max_length=30)
#     position = models.CharField(max_length=1000)
#     staffid = models.CharField(max_length=40)
#     personallevel = models.CharField(max_length=30)
#     department = models.CharField(max_length=30,blank=True,null=True)  
#     status = models.CharField(max_length=40, choices=STATUS_CHOICES)
#     class Admin:
#         pass
#     def __str__(self):
#         return '%s' %(self.staffid)

class organization(models.Model):
    name = models.CharField(max_length=30)    
    status = models.CharField(max_length=40, choices=STATUS_CHOICES)
    class Admin:
        pass
    def __str__(self):
        return '%s' %(self.name)

      
class associatecompany(models.Model):
    name = models.CharField(max_length=30)    
    status = models.CharField(max_length=40, choices=STATUS_CHOICES)
    class Admin:
        pass
    def __str__(self):
        return '%s' %(self.name)



class family(models.Model):    
    dapendent_first_name1 = models.CharField(max_length=40, null=True,blank=True)
    dependent_family_name = models.CharField(max_length=40, null=True,blank=True)
    dependent_sequence = models.CharField(max_length=40, null=True,blank=True)
    family_uid = models.CharField(max_length=40, null=True,blank=True)    
    relationship = models.CharField(max_length=10,choices=RELATIONSHIP)
    photo = models.CharField(max_length=255L, null=True,blank=True)  
    age = models.PositiveSmallIntegerField(null=True,blank=True)
    dob = models.DateField(null=True,blank=True)        
    date_of_joining = models.DateField(null=True,blank=True)
    date_of_expiry = models.DateField(null=True,blank=True)    
    rfidcardno=models.CharField(max_length=64, null=True,blank=True)
    contact_no = models.CharField(max_length=30, null=True,blank=True)    
    clubsallowed  = models.CharField(max_length=400, null=True,blank=True)
    emailid = models.EmailField(null=True,blank=True)
    nationality = models.CharField(max_length=30, null=True,blank=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES)
    # organization = models.ForeignKey('organization')
    member = models.ForeignKey('member')
    datetime = models.DateTimeField(blank=True,null=True)
    class Admin:
        pass
    def __str__(self):
        return '%s''--''%s' %(self.family_uid, self.dapendent_first_name1)
               
class role(models.Model):
    rolename = models.CharField(max_length=30)        
    status = models.CharField(max_length=40, choices=STATUS_CHOICES)
    class Admin:
        pass
    def __str__(self):
        return '%s' %(self.rolename)
        
class suspension(models.Model):
    fromdate = models.DateField(max_length=30,blank=True,null=True)
    todate = models.DateField(max_length=30,blank=True,null=True)
    reason = models.TextField(max_length=100,blank=True,null=True)        
    member = models.ForeignKey('member')
    doneby = models.ForeignKey('qpuser')
    club = models.ForeignKey('club',blank=True,null=True)
    family_member = models.ForeignKey('family',blank=True,null=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES)
    datetime = models.DateTimeField(auto_now=True)
    clubsallowed  = models.CharField(max_length=400)
    class Admin:
        pass
    def __str__(self):
        return '%s' %(self.fromdate)
        
class renewal(models.Model):
    date_of_renewal = models.DateField(max_length=30,blank=True,null=True)
    date_of_expiry = models.DateField(max_length=30,blank=True,null=True)   
    status = models.CharField(max_length=40, choices=STATUS_CHOICES)
    member = models.ForeignKey('member')
    club = models.ForeignKey('club')
    renewalby = models.ForeignKey('qpuser')
    datetime = models.DateTimeField(auto_now=True)
    class Admin:
        pass
    def __str__(self):
        return '%s' %(self.date_of_renewal)
 
class guest(models.Model):
    name = models.CharField(max_length = 30,blank=True)
    # guest_uid = models.CharField(max_length=40,blank=True)
    gender = models.CharField(max_length = 10, choices = GENDER_CHOICES,blank=True)
    dob = models.DateField(blank=True,null=True)    
    # relationship = models.CharField(max_length = 20,choices=RELATIONSHIP,blank=True)
    phone_no = models.CharField(max_length = 20,blank=True)
    rfidcardno = models.CharField(max_length=30,blank=True)
    clubsallowed  = models.CharField(max_length=400,blank=True)    
    emailid = models.EmailField(null = True,blank=True)
    residencelocation = models.CharField(max_length=40,blank=True)
    photo = models.CharField(max_length=255L, null=True,blank=True)
    nationality = models.CharField(max_length=30,blank=True)
    memberid = models.CharField(max_length=30,blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES,blank=True)
    period=models.CharField(max_length=30, choices=PERIOD_CHOICES)
    date_of_expiry=models.DateField(max_length=30,null=True,blank=True)
    datetime = models.DateTimeField(auto_now=True,blank=True)
    
    class Admin:
        pass
    def __str__(self):
        return '%s,%s' %(self.name,self.memberid)

               
class transaction(models.Model):
    rfidcardid = models.CharField(max_length=30)
    datetime = models.DateTimeField()  
    club = models.ForeignKey('club')  
    class Admin:
        pass
    def __str__(self):
        return '%s' %(self.rfidcardid)

class userlogin(models.Model):
    username = models.CharField(max_length=30)
    userid = models.CharField(max_length=30)
    role = models.ForeignKey('role')
    logintime  = models.DateTimeField()         
    class Admin:
        pass
    def __str__(self):
        return '%s' %(self.username)
        
class userlogout(models.Model):
    username = models.CharField(max_length=30)
    userid = models.CharField(max_length=30)
    role = models.ForeignKey('role')    
    logouttime  = models.DateTimeField()          
    class Admin:
        pass
    def __str__(self):
        return '%s' %(self.username)