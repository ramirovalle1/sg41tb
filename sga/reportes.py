import json
import os
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
import unicodedata
from django.utils.encoding import force_str
from decorators import secure_module
from settings import JR_JAVA_COMMAND, DATABASES, JR_DB_TYPE, SITE_ROOT, JR_USEROUTPUT_FOLDER, JR_RUN, MEDIA_URL
from sga.commonviews import addUserData, ip_client_address
from sga.models import *
from bib.models import *
import subprocess

def tipoParametro(tipo):
    if tipo==1:
        return "string"
    elif tipo==2:
        return "integer"
    elif tipo==3:
        return "double"
    elif tipo==4:
        return "boolean"
    elif tipo==5:
        return "integer"
    elif tipo==6:
        return "string"
    elif tipo==7:
        return "string".upper()
    return "string"

def fixParametro(tipo, valor):
    if tipo==6:
        # FECHA
        fm = valor.index("-")
        sm = valor.index("-", fm+1)
        d = valor[:fm]
        m = valor[fm+1:sm]
        y = valor[sm+1:]
        return y+"-"+m+"-"+d
    return valor



def transform(parametro, request):
    return "%s=%s:%s"%(parametro.nombre, tipoParametro(parametro.tipo), fixParametro(parametro.tipo, request.GET[parametro.nombre]))

def elimina_tildes(cadena):
    s = ''.join((c for c in unicodedata.normalize('NFD',str(cadena)) if unicodedata.category(c) != 'Mn'))
    return s

def transform_jasperstarter(parametro, request):
    if parametro.tipo == 1 or parametro.tipo == 7:
        return "%s='%s'" % (parametro.nombre, fixParametro(parametro.tipo, elimina_tildes(request.GET[parametro.nombre])))
    else:
        return '%s=%s' % (parametro.nombre, fixParametro(parametro.tipo, request.GET[parametro.nombre]))

@login_required(redirect_field_name='ret', login_url='/login')
@secure_module
def view(request):
    if 'action' in request.GET:
        action = request.GET['action']
        if action=='data':
            try:
                m = request.GET['model']
                q = request.GET['q'].upper()
                if ':' in m:
                    sp = m.split(':')
                    model = eval(sp[0])
                    query = model.flexbox_query(q)
                    query = query.filter(eval(sp[1].replace('[uid]',str(request.session['persona'].id)))).distinct()
                else:
                    model = eval(request.GET['model'])
                    query = model.flexbox_query(q)

                data = {"results": [{"id": x.id, "name": x.flexbox_repr() } for x in query]}
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as ex:
                data = {"results": str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")
        if action=='dataadm':
            try:
                m = request.GET['model']
                q = request.GET['q'].upper()
                if ':' in m:
                    sp = m.split(':')
                    model = eval(sp[0])
                    query = model.flexbox_queryadm(q)
                    query = query.filter(eval(sp[1].replace('[uid]',str(request.session['persona'].id)))).distinct()
                else:
                    model = eval(request.GET['model'])
                    query = model.flexbox_queryadm(q)

                data = {"results": [{"id": x.id, "name": x.flexbox_repr() } for x in query]}
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as ex:
                data = {"results": str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")
        if action=='databiblio':
            try:
                m = request.GET['model']
                q = request.GET['q'].upper()
                if ':' in m:
                    sp = m.split(':')
                    model = eval(sp[0])
                    query = model.flexbox_query_2(q)
                    for n in range(1,len(sp)):
                        query = eval('query.filter(%s)'%(sp[n]))
                else:
                    model = eval(request.GET['model'])
                    query = model.flexbox_query_2(q)

                data = {"results": [{"id": x.id, "name": x.flexbox_repr(), "alias": x.flexbox_alias() } for x in query]}
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as ex:
                data = {"results": str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")

        if action=='databiblio2':
            try:
                m = request.GET['model']
                q = request.GET['q'].upper()
                if ':' in m:
                    sp = m.split(':')
                    model = eval(sp[0])
                    query = model.flexbox_query_2(q)
                    for n in range(1,len(sp)):
                        query = eval('query.filter(%s)'%(sp[n]))
                else:
                    model = eval(request.GET['model'])
                    query = model.flexbox_query_2(q)

                data = {"results": [{"id": x.id, "name": x.flexbox_repr2(), "alias": x.flexbox_alias() } for x in query]}
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as ex:
                data = {"results": str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")


        if action=='datafilt':
            try:
                m = request.GET['model']
                q = request.GET['q'].upper()
                if ':' in m:
                    sp = m.split(':')
                    model = eval(sp[0])
                    query = model.flexbox_query(q)
                    for n in range(1,len(sp)):
                        query = eval('query.filter(%s)'%(sp[n]))
                else:
                    model = eval(request.GET['model'])
                    query = model.flexbox_query(q)

                data = {"results": [{"id": x.id, "name": x.flexbox_repr(),  "alias": x.flexbox_alias() } for x in query]}
                return HttpResponse(json.dumps(data),content_type="application/json")
            except Exception as ex:
                data = {"results": str(ex)}
                return HttpResponse(json.dumps(data),content_type="application/json")
        elif action=='run':
            # Ejecutar Reporte
            try:
                if 'n' in request.GET:
                    reporte = Reporte.objects.get(nombre=request.GET['n'])
                else:
                    reporte = Reporte.objects.get(pk=request.GET['rid'])
                tipo = request.GET['rt']
                output_folder = os.path.join(JR_USEROUTPUT_FOLDER,elimina_tildes(request.user.username))
                if 'ruta' in request.GET:
                    output_folder = os.path.join(SITE_ROOT, 'media', request.GET['ruta'])
                try:
                    os.makedirs(output_folder)
                except :
                    # return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                    pass

                d = datetime.now()
                pdfname = reporte.nombre+d.strftime('%Y%m%d_%H%M%S')

                runjrcommand = [JR_JAVA_COMMAND,'-jar',
                                os.path.join(JR_RUN, 'jasperstarter.jar'),
                                 'pr', reporte.archivo.file.name,
                                 '--jdbc-dir', JR_RUN,
                                 '-f', tipo,
                                 '-t', 'postgres',
                                 '-H', DATABASES['default']['HOST'],
                                 '-n', DATABASES['default']['NAME'],
                                 '-u', DATABASES['default']['USER'],
                                 '-p', DATABASES['default']['PASSWORD'],
                                 '-o', output_folder + os.sep + pdfname]
                parametros = reporte.parametros()
                paramlist = [ transform_jasperstarter(p, request) for p in parametros ]
                if paramlist:
                    runjrcommand.append('-P')
                    for parm in paramlist:
                        runjrcommand.append(parm)
                try:
                    mensaje = ''
                    for m in runjrcommand:
                        mensaje += ' ' + m

                    runjr = subprocess.call(mensaje, shell=True)



                except Exception as ex:
                    print(('error reporte' + str(ex)))
                    return HttpResponse(json.dumps({"result":"bad"}),content_type="application/json")
                sp = os.path.split(reporte.archivo.file.name)
                #Obtain client ip address
                client_address = ip_client_address(request)

                # Log de EDICION PROCESO
                LogEntry.objects.log_action(
                    user_id         = request.user.pk,
                    content_type_id = ContentType.objects.get_for_model(reporte).pk,
                    object_id       = reporte.id,
                    object_repr     = force_str(reporte),
                    action_flag     = ADDITION,
                    change_message  = 'Reporte Ejecutado (' + client_address + ')' )
                if 'direct' in request.GET:
                    return HttpResponseRedirect("/".join([MEDIA_URL,'documentos','userreports',elimina_tildes(request.user.username), pdfname+"."+tipo]))
                if 'ruta' in request.GET:
                    return HttpResponse(json.dumps({'result':'ok', 'reportfile': "/".join([MEDIA_URL, request.GET['ruta'], pdfname+"."+tipo])}), content_type="application/json")

                return HttpResponse(json.dumps({'result':'ok', 'reportfile': "/".join([MEDIA_URL,'documentos','userreports',request.user.username, pdfname+"."+tipo]) }),content_type="application/json")
            # ///////////////////////////////////////////////////////////////////////////////////////////////
            # /////////////////////////////////////////////////////////////////////////////////
            except Exception as e:
                print(('error reporte' + str(e)))
                if 'direct' in request.GET:
                    return HttpResponseRedirect("/?error=3")
                return HttpResponse(json.dumps({'result':'bad'}),content_type="application/json")
                # pass

        return HttpResponseRedirect('/reportes')
    else:
        data = {'title': 'Reportes'}
        addUserData(request,data)

        categorias = []
        for categoria in CategoriaReporte.objects.all().order_by('nombre'):
            reportes_categoria = Reporte.objects.filter(categoria=categoria,grupos__in=request.user.groups.all()).order_by('nombre').distinct()
            if reportes_categoria.count()>0:
                categorias.append({'nombre':categoria.nombre, 'reportes':reportes_categoria})
        data['categorias'] = categorias
        print(categorias)
        return render(request ,"reportes/reportesbs.html" ,  data)