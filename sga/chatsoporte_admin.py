from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from sga.commonviews import addUserData


@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
    else:
        data = {}
        addUserData(request, data)
        if 'action' in request.GET:
            action = request.GET['action']
        else:
            try:

               return render(request ,"chat/salachatsoporte.html" ,  data)

            except Exception as ex:
                 return HttpResponseRedirect("/?info=Error: "+str(ex))

