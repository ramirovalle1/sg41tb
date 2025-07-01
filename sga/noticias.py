from datetime import datetime, timedelta
import json
import os
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from decorators import secure_module
from settings import MEDIA_ROOT
from sga.commonviews import addUserData
from sga.forms import NoticiaForm
from sga.models import Noticia, TIPOS_NOTICIAS

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action=='add':
            f = NoticiaForm(request.POST)
            if f.is_valid():
                noticia = Noticia(titular = f.cleaned_data['titular'],
                                    cuerpo=f.cleaned_data['cuerpo'],
                                    desde=f.cleaned_data['desde'],
                                    hasta=f.cleaned_data['hasta'],
                                    tipo=f.cleaned_data['tipo'],
                                    publica=request.session['persona'])
                noticia.save()
                if "archivo" in request.FILES:
                    if (MEDIA_ROOT + '/' + str(noticia.archivo)) and noticia.archivo:
                            os.remove(MEDIA_ROOT + '/' + str(noticia.archivo))
                    noticia.archivo = request.FILES["archivo"]
                    noticia.save()
                return HttpResponseRedirect("/noticias")
            else:
                return HttpResponseRedirect("/noticias?action=add")

        elif action=='edit':
            noticia = Noticia.objects.get(pk=request.POST['id'])
            f = NoticiaForm(request.POST)
            if f.is_valid():
                noticia.titular = f.cleaned_data['titular']
                noticia.cuerpo = f.cleaned_data['cuerpo']
                noticia.desde = f.cleaned_data['desde']
                noticia.hasta = f.cleaned_data['hasta']
                noticia.tipo = f.cleaned_data['tipo']
                noticia.publica = request.session['persona']
                if "archivo" in request.FILES:
                    if (MEDIA_ROOT + '/' + str(noticia.archivo)) and noticia.archivo:
                            os.remove(MEDIA_ROOT + '/' + str(noticia.archivo))
                    noticia.archivo = request.FILES["archivo"]
                noticia.save()

        elif action=='delete':
            noticia = Noticia.objects.get(pk=request.POST['id'])
            noticia.delete()

        elif action=='addimg':
            try:
                noticia = Noticia.objects.get(pk=request.POST['idnoticia'])
                if "archivo" in request.FILES:
                    if (MEDIA_ROOT + '/' + str(noticia.archivo)) and noticia.archivo:
                            os.remove(MEDIA_ROOT + '/' + str(noticia.archivo))
                    noticia.archivo = request.FILES["archivo"]
                noticia.save()
                return HttpResponse(json.dumps({"result": "ok"}),content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({"result": "bad"}),content_type="application/json")

        return HttpResponseRedirect("/noticias")
    else:
        data = {'title': 'Noticias publicadas'}
        addUserData(request,data)
        if 'action' in request.GET:
            action = request.GET['action']
            if action=='add':
                data['title'] = 'Nueva Noticia'
                data['form'] = NoticiaForm(initial={'desde': datetime.now(), 'hasta': datetime.now() + timedelta(30)})
                return render(request ,"noticias/adicionarbs.html" ,  data)
            elif action=='edit':
                data['title'] = 'Editar Noticia'
                noticia = Noticia.objects.get(pk=request.GET['id'])
                data['form'] = NoticiaForm(instance=noticia)
                data['noticia'] = noticia
                return render(request ,"noticias/editarbs.html" ,  data)
            elif action=='delete':
                data['title'] = 'Eliminar Noticia'
                data['noticia'] = Noticia.objects.get(pk=request.GET['id'])
                return render(request ,"noticias/borrarbs.html" ,  data)
            elif action=='delimg':
                data['title'] = 'Eliminar Imagen'
                noticia = Noticia.objects.get(pk=request.GET['id'])
                if (MEDIA_ROOT + '/' + str(noticia.archivo)) and noticia.archivo:
                            os.remove(MEDIA_ROOT + '/' + str(noticia.archivo))
                noticia.archivo = None
                noticia.save()
                return HttpResponseRedirect("/noticias")
        else:
            noticias = Noticia.objects.all().order_by('-desde','-id')
            paging = Paginator(noticias, 45)
            try:
                if 'page' in request.GET:
                    p = int(request.GET['page'])
                page = paging.page(p)
            except:
                page = paging.page(1)
            data['paging'] = paging
            data['page'] = page

            data['noticias'] = page.object_list
            return render(request ,"noticias/noticiasbs.html" ,  data)
