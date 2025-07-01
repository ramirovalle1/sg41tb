# -*- coding: latin-1 -*-
from datetime import datetime
from decimal import Decimal
import json
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.query_utils import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from decorators import secure_module
from sga.commonviews import addUserData
from sga.forms import ReintegrarRetiroForm
from sga.models import RetiradoMatricula, DetalleRetiradoMatricula,NewsTiket

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        if 'action' in request.POST:
            action = request.POST['action']
            if action== 'add':
                try:
                    news = NewsTiket(
                            hdnoticia = request.POST['tit'],
                            bdynoticia = request.POST['prf'],
                            noticiasitio= 1,
                            horanoticia=datetime.now(),
                            estadonoticia=0
                            )
                    news.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action=='edit':
                try:
                    news=NewsTiket.objects.get(pk=request.POST['id'])
                    news.hdnoticia = request.POST['tit']
                    news.bdynoticia = request.POST['prf']
                    news.horanoticia = datetime.now()
                    news.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action=='act':
                try:
                    news=NewsTiket.objects.get(pk=request.POST['id'])
                    if(news.estadonoticia):
                        news.estadonoticia=0
                    else:
                        news.estadonoticia=1
                    news.save()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")

            elif action=='dell':
                try:
                    news=NewsTiket.objects.get(pk=request.POST['id'])
                    news.delete()
                    return HttpResponse(json.dumps({"result":"ok"}),content_type="application/json")
                except:
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
    else:
        data = {'title': 'Retirados de Matriculas'}
        addUserData(request,data)
        try:
            if 'action' in request.GET:
                action = request.GET['action']
                if action == 'add':
                    data={}
                    data['detalle'] = DetalleRetiradoMatricula.objects.filter(retirado__id=request.GET['id'])
                    return render(request ,"atencioncliente/newstiket.html" ,  data)

            search = None
            if 's' in request.GET:
                search = request.GET['s']

            if search:
                ss = search.split(' ')
                while '' in ss:
                    ss.remove('')
                if len(ss)==1:
                    newstikets = NewsTiket.objects.filter(Q(hdnoticia__icontains=search) | Q(bdynoticia__icontains=search)).order_by('horanoticia')
                else:
                    newstikets = NewsTiket.objects.filter(Q(hdnoticia__icontains=ss[0]) & Q(bdynoticia__icontains=ss[1])).order_by( 'horanoticia')
            else:
                newstikets = NewsTiket.objects.all().order_by('horanoticia')


            paging = Paginator(newstikets, 50)
            p = 1
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)

            data['paging'] = paging
            data['page'] = page
            data['search'] = search if search else ""
            data['newstikets'] = page.object_list
            return render(request ,"atencioncliente/newstiket.html" ,  data)
        except Exception as ex:
            return HttpResponse("/newstiket")
