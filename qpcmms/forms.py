from django import forms
from django.forms import ModelForm,PasswordInput
from models import *
from django.db.models import Q
from collections import deque

CLUB_CHOICES = (
        ('DRC', 'Dhukhan Recreation Club'),
        ('JRC', 'Jinan Recreation Club'),
        ('DWS', 'Dhukhan Water Sports Club'),
        ('DGC', 'Dhukhan Golf Club'),
        ('DFC', 'Dhukhan Fitness Club'),
        ('ASRC', 'Al-Shaheen Recreation Club'),
        ('MGC', 'Mesaieed Golf Club'),
        ('AC', 'Alghazal Club'),
        ('BC', 'Beach Club'),       
    )

class MemberForm(ModelForm):
    # clubs = forms.MultipleChoiceField(choices=club.objects.all(), required=False, widget=forms.CheckboxSelectMultiple)
    attachment = forms.FileField(label='Attachment', help_text='max. 4 MB',required=False)
    class Meta:
        model = member

    # Representing the many to many related field in member
    clubsallowed = forms.ModelMultipleChoiceField(queryset=club.objects.all())

    def __init__ (self, user,*args, **kwargs):

        self.user = user
        super(MemberForm, self).__init__(*args, **kwargs)
        self.fields["clubsallowed"].widget = forms.widgets.CheckboxSelectMultiple()
        self.fields["clubsallowed"].help_text = ""
        if hasattr(user, 'clubsallowed'):
                userclubs = []
                # member_obj = clubstatus.objects.filter(member_id=mid)

                # for i in member_obj:
                #     print i.club.name
                # l2 = member_obj.clubsallowed
                l = user.clubsallowed
                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in l:                
                        userclubs.append(i)
                self.fields["clubsallowed"].queryset = club.objects.filter(name__in=userclubs)

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput,required=False)
    # clubsallowed = forms.MultipleChoiceField(choices=CLUB_CHOICES, required=True, widget=forms.CheckboxSelectMultiple(), label='Clubs Allowed')
    class Meta:
        model = qpuser

    clubsallowed = forms.ModelMultipleChoiceField(queryset=club.objects.all())

    def __init__ (self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields["clubsallowed"].widget = forms.widgets.CheckboxSelectMultiple()
        self.fields["clubsallowed"].help_text = ""
        self.fields["clubsallowed"].queryset = club.objects.all()
        self.fields['role'].queryset = role.objects.all().exclude(rolename__icontains='Admin')
        
class FamilyForm(ModelForm): 
    # clubsallowed = forms.MultipleChoiceField(choices=CLUB_CHOICES, required=True, widget=forms.CheckboxSelectMultiple(), label='Clubs Allowed')
    # family_uid = forms.CharField(widget = forms.TextInput(attrs={'readonly':'readonly'}))    
    class Meta:
        model = family

    clubsallowed = forms.ModelMultipleChoiceField(queryset=club.objects.all())

    def __init__ (self, user,*args, **kwargs):

        self.user = user
        super(FamilyForm, self).__init__(*args, **kwargs)
        self.fields["clubsallowed"].widget = forms.widgets.CheckboxSelectMultiple()
        self.fields["clubsallowed"].help_text = ""
        # print user.clubsallowed
        userclubs = []
        l = user.clubsallowed
        clubs = []
        clubs_list = club.objects.all()

        for i in clubs_list:
            clubs.append(i.name)

        for i in clubs:
            if i in l:                
                userclubs.append(i)
        # print userclubs
        self.fields["clubsallowed"].queryset = club.objects.filter(name__in=userclubs)

        
class AssociateCompanyForm(ModelForm):    
    class Meta:
        model = associatecompany

class ClubForm(ModelForm):    
    class Meta:
        model = club
        
        
class OrganizationForm(ModelForm):
    class Meta:
        model = organization
        
class RoleForm(ModelForm):
    class Meta:
        model = role
        
class SuspensionForm(ModelForm):
    class Meta:
        model = suspension

    clubsallowed = forms.ModelMultipleChoiceField(queryset=club.objects.all())

    def __init__ (self, user,mid,cid,*args, **kwargs):
        self.user = user
        super(SuspensionForm, self).__init__(*args, **kwargs)
        self.fields["clubsallowed"].widget = forms.widgets.CheckboxSelectMultiple()
        self.fields["clubsallowed"].help_text = ""
        if hasattr(user, 'clubsallowed'):
                userclubs = []
                userclubs1 = []
                member_obj = clubstatus.objects.filter(member_id=mid)

                for i in member_obj:
                    userclubs1.append(i.club.name)

                l = user.clubsallowed
                clubs = []
                clubs_list = club.objects.all()

                for i in clubs_list:
                    clubs.append(i.name)

                for i in clubs:
                    if i in l:                
                        userclubs.append(i)
                common = filter(lambda x:x in userclubs,userclubs1)

                self.fields["clubsallowed"].queryset = club.objects.filter(id=cid)
        
class RenewalForm(ModelForm):
    class Meta:
        model = renewal
        
class TransactionForm(ModelForm):
    class Meta:
        model = transaction
        
class GuestForm(ModelForm):
    # clubsallowed = forms.MultipleChoiceField(choices=CLUB_CHOICES, required=True, widget=forms.CheckboxSelectMultiple(), label='Clubs Allowed')
    class Meta:
        model = guest

    clubsallowed = forms.ModelMultipleChoiceField(queryset=club.objects.all())

    def __init__ (self,*args, **kwargs):
        super(GuestForm, self).__init__(*args, **kwargs)
        self.fields["clubsallowed"].widget = forms.widgets.CheckboxSelectMultiple()
        self.fields["clubsallowed"].help_text = ""
        self.fields["clubsallowed"].queryset = club.objects.all()


class AddClubsForm(ModelForm):
    class Meta:
        model = suspension

    clubsallowed = forms.ModelMultipleChoiceField(queryset=club.objects.all())

    def __init__ (self, user,mobj,*args, **kwargs):

        self.user = user
        super(AddClubsForm, self).__init__(*args, **kwargs)
        self.fields["clubsallowed"].widget = forms.widgets.CheckboxSelectMultiple()
        self.fields["clubsallowed"].help_text = "Check these boxes to allow member to access"
        userclubs = deque()
        member_obj = clubstatus.objects.filter(member_id=mobj.id).values('club_id')
        li = deque()
        for i in member_obj:
            li.append(i['club_id'])
            
        # l = user.clubsallowed
        # clubs = []
        # clubs_list = club.objects.all()

        # for i in clubs_list:
        #     clubs.append(i.name)

        # for i in clubs:
        #     if i in l:                
        #         userclubs.append(i)
        self.fields["clubsallowed"].queryset = club.objects.filter(~Q(id__in=li))
        
