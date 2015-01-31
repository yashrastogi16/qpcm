from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = patterns('qpcmms.views',
    # Examples:
    # url(r'^$', 'qpcm.views.home', name='home'),
    # url(r'^qpcm/', include('qpcm.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^index/', 'index'),
    url(r'^members/', 'members'),
    url(r'^users/', 'users'),
    url(r'^common/', 'common'),
    url(r'^membershipform/', 'membershipform'),
    url(r'^reports/', 'reports'),
    url(r'^settings/', 'settings'),
    # url(r'^memberinfo/', 'memberinfo'),
    url('^$', 'login'),
    url(r'^login/', 'login'),
    url(r'^logout/', 'logout'),
    url(r'^userform/', 'userform'),
    # url(r'^bulkupload/', 'bulkupload'),
    url(r'^familyform/', 'familyform'),
    url(r'^search/', 'search'),
    url(r'^newmemberreport/', 'newmembershipreport'),
    url(r'^suspensionreport/', 'suspensionreport'),
    url(r'^cancellationreport/', 'cancellationreport'),
    url(r'^attendancereport/', 'attendancereport'),
    url(r'^nearrenewal/', 'nearrenewal'),
    url(r'^guestEntry/', 'guestEntry'),
    url(r'^employmentform/', 'employmentform'),
    url(r'^organizationform/', 'organizationform'),
    url(r'^companyform/', 'companyform'),
    url(r'^companies/', 'companies'),
    url(r'^company-delete/', 'company_delete'),
    url(r'^printcard/', 'print_card'),
    url(r'^display/', 'display'),
    url(r'^today-visitors/', 'members_visit'),
    url(r'^userlogs/', 'userlogs'),
    url(r'^memberslist/', 'memberslist'),
    url(r'^Childrenage/', 'childreenage'),
	url(r'^qpaddmember/', 'qpaddmember'),
    url(r'^clubslist/', 'clubslist'),
    url(r'^download/', 'download'),
    url(r'^resetpwd/','ResetPassword'),
    url(r'^suspensionrevokereport/', 'suspensionrevokereport'),
    url(r'^dependents/', 'dependents'),
    url(r'^renewalreport/', 'renewalreport'),
    url(r'^guestList/','guestList'),
    url(r'^clubs/','clubs'),
    url(r'^clubform/','clubform'),
    url(r'^club-delete/', 'club_delete'),
    url(r'^reset_userpwd/', 'userpwd_reset'),
    url(r'^reset_self_pwd/', 'reset_self_pwd'),
    url(r'^reject/', 'Reject'),
    url(r'^family_suspension/', 'family_suspension'),
    url(r'^addclubs/', 'addclubs'),
    url(r'^search_members/', 'search_members'),
    url(r'^view_profile/', 'view_profile'),
    url(r'^rfid_post/', 'rfid_post'),
    url(r'^get_club/', 'get_club'),
    url(r'^extend/', 'extend'),
    url(r'^deactivate_guest/','deactivate_guest'),
    url(r'^activate_guest/','activate_guest'),
    url(r'^view_profile_guest/', 'view_profile_guest'),
)#+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

