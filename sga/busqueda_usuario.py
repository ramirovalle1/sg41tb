import json
from django.http import HttpResponse
from django.shortcuts import render
from django.template import RequestContext
import requests
from settings import IP_SERVIDOR_API_DIRECTORY, NEW_PASSWORD
from sga.commonviews import addUserData, add_usuario_AD
from sga.models import *


def view(request):
    if request.method=='POST':
        action = request.POST['action']
        if action == 'verifica_correo':
            try:
                data = {}
                usuario = request.POST['usuario']
                try:
                    consulta = requests.get(IP_SERVIDOR_API_DIRECTORY + '/api?Identity=' + usuario, timeout=5, verify=False)
                    if consulta.status_code == 200:
                        datos = consulta.json()
                        if 'msg_corto' in datos:
                            if datos['msg_corto'] == 'Usuario NO existe':
                                return HttpResponse(json.dumps({'result': 'bad',
                                                                'message': str(datos['msg_corto']),
                                                                'nousuario': 'ok'}),
                                                    content_type="application/json")
                        elif 'UserPrincipalName' in datos:
                            correousuario = datos['UserPrincipalName']
                            datoconsulta = {"correo" : correousuario}
                            jsondata = json.dumps(datoconsulta)
                            headers = {'content_type':"application/json"}
                            try:
                                consulta_correo_existe = requests.put(IP_SERVIDOR_API_DIRECTORY + '/correo', data=jsondata, headers=headers)
                                if consulta_correo_existe.status_code == 200:
                                    datosexiste = consulta_correo_existe.json()
                                    if "msg_corto" in datosexiste:
                                        if datosexiste['msg_corto'] == 'Usuario NO Existe':
                                            return HttpResponse(json.dumps({'result': 'bad',
                                                                            'message': str(datosexiste['msg_largo']),
                                                                            'nocorreo': 'ok'}),
                                                content_type="application/json")
                                        else:
                                            data['correoexiste'] = correousuario
                                            data['result'] = 'ok'
                            except request.Timeout:
                                print("Error Timeout al consultar correo")
                                return HttpResponse(json.dumps({'result': 'bad', 'message': "Error Timeout al consultar correo"}), content_type="application/json")

                            except requests.ConnectionError:
                                print("Error ConnectionError al consultar correo")
                                return HttpResponse(json.dumps({'result': 'bad', 'message': "Error ConnectionError al consultar correo"}),
                                                    content_type="application/json")
                except requests.Timeout:
                    print("Error Timeout al consultar usuario")
                    return HttpResponse(json.dumps({'result': 'bad', 'message': "Error Timeout al consultar usuario"}),
                                        content_type="application/json")

                except requests.ConnectionError:
                    print("Error ConnectionError al consultar usuario")
                    return HttpResponse(json.dumps({'result': 'bad', 'message': "Error ConnectionError al consultar usuario"}),
                                         content_type="application/json")

                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        if action == 'crear_correo':
            try:
                data = {}
                usuario = request.POST['usuario']
                if Inscripcion.objects.filter(persona__usuario__username=usuario).exists():
                    persona = Inscripcion.objects.filter(persona__usuario__username=usuario).order_by('-id')[:1].get().persona
                    try:
                        print('ingreso addusuario ' + str(request.user))
                        numrep = ''
                        usertipo = "INSCRIPCION"
                        EmailAddress = persona.usuario.username + '@itb.edu.ec'
                        if persona.cedula:
                            if Persona.objects.filter(cedula=persona.cedula).count() > 1:
                                numrep = Persona.objects.filter(cedula=persona.cedula).count()
                        elif persona.pasaporte:
                            if Persona.objects.filter(pasaporte=persona.pasaporte).count() > 1:
                                numrep = Persona.objects.filter(pasaporte=persona.pasaporte).count()

                        UserPrincipalName = persona.usuario.username
                        # EmailAddress = persona.emailinst
                        GivenName = persona.nombres + ' ' + str(numrep)
                        Surname = persona.apellido1 + " " + persona.apellido2
                        datos = {"username": UserPrincipalName,
                                 "AccountPassword": NEW_PASSWORD,
                                 "GivenName": GivenName,
                                 "Surname": Surname,
                                 "Description": usertipo,
                                 "correo": EmailAddress
                        }
                        try:
                            print('creacion de directory para ' + UserPrincipalName)
                            consulta = requests.post(IP_SERVIDOR_API_DIRECTORY + '/create', json.dumps(datos), timeout=30, verify=False)
                            if consulta.status_code == 200:
                                datos = consulta.json()
                                if 'msg_corto' in datos:
                                    if datos['msg_corto'] != 'Usuario NO Creado':
                                        persona.activedirectory = True
                                        persona.save()
                        except Exception as e:
                            print(e)
                            pass

                        # add_usuario_AD(persona)
                        data['result'] = 'ok'
                    except Exception as e:
                        print('eroror excep adduser ' + str(e))
                else:
                    return HttpResponse(json.dumps({'result': 'bad',
                                                    'message': 'No se encontro el registro de la persona con el usuario ' + usuario}),
                                        content_type="application/json")
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        if action == 'consultaxgrupo':
            try:
                data = {}
                listfaltacorreo = []
                print('total de inscip: ', InscripcionGrupo.objects.filter(grupo=request.POST['idgrupo'], activo=True).count())
                for inscg in InscripcionGrupo.objects.filter(grupo=request.POST['idgrupo'], activo=True):
                    persona = inscg.inscripcion.persona
                    usuario = persona.usuario.username
                    # try:
                    #     print('antes de solicitar a la api de usuario')
                    #     consulta = requests.get(IP_SERVIDOR_API_DIRECTORY + '/api?Identity=' + usuario)
                    #     print('entra api consulta usuario')
                    #     if consulta.status_code == 200:
                    #         datos = consulta.json()
                    #         if 'UserPrincipalName' in datos:
                    #             correousuario = datos['UserPrincipalName']
                    if persona.emailinst:
                        correousuario = persona.emailinst
                        datoconsulta = {"correo": correousuario}
                        jsondata = json.dumps(datoconsulta)
                        headers = {'content_type': "application/json"}
                        try:
                            print('antes de solicitar a la api de correo')
                            consulta_correo_existe = requests.put(IP_SERVIDOR_API_DIRECTORY + '/correo', data=jsondata, headers=headers)
                            print('entra api consulta correo')
                            if consulta_correo_existe.status_code == 200:
                                datosexiste = consulta_correo_existe.json()
                                if "msg_corto" in datosexiste:
                                    if datosexiste['msg_corto'] == 'Usuario NO Existe':
                                        # listfaltacorreo.append({'nombre': datos['DisplayName'] if datos['DisplayName'] else '',
                                        #                         'usuario': datos['SamAccountName'] if datos['SamAccountName'] else '',
                                        #                         'correo': correousuario})
                                        listfaltacorreo.append({'nombre': persona.nombre_completo(),
                                                                'usuario': usuario,
                                                                'correo': correousuario})
                        except requests.Timeout:
                            print("Error Timeout al consultar correo")
                            return HttpResponse(json.dumps({'result': 'bad', 'message': "Error Timeout al consultar correo"}),
                                                content_type="application/json")
                        except requests.ConnectionError:
                            print("Error ConnectionError al consultar correo")
                            return HttpResponse(json.dumps({'result': 'bad', 'message': "Error ConnectionError al consultar correo"}),
                                                content_type="application/json")
                if len(listfaltacorreo) > 0:
                    data['listfaltacorreo'] = listfaltacorreo
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        if action == 'crear_correo_x_grupo':
            try:
                data = {}
                arreglo = json.loads(request.POST['listausuariosincorreo'])
                for a in arreglo:
                    usuario = a['usuario']
                    if Inscripcion.objects.filter(persona__usuario__username=usuario).exists():
                        persona = Inscripcion.objects.filter(persona__usuario__username=usuario).order_by('-id')[:1].get().persona
                        try:
                            print('ingreso addusuario ' + str(request.user))
                            numrep = ''
                            usertipo = "INSCRIPCION"
                            EmailAddress = persona.usuario.username + '@itb.edu.ec'
                            if persona.cedula:
                                if Persona.objects.filter(cedula=persona.cedula).count() > 1:
                                    numrep = Persona.objects.filter(cedula=persona.cedula).count()
                            elif persona.pasaporte:
                                if Persona.objects.filter(pasaporte=persona.pasaporte).count() > 1:
                                    numrep = Persona.objects.filter(pasaporte=persona.pasaporte).count()

                            UserPrincipalName = persona.usuario.username
                            # EmailAddress = persona.emailinst
                            GivenName = persona.nombres + ' ' + str(numrep)
                            Surname = persona.apellido1 + " " + persona.apellido2
                            datos = {"username": UserPrincipalName,
                                     "AccountPassword": NEW_PASSWORD,
                                     "GivenName": GivenName,
                                     "Surname": Surname,
                                     "Description": usertipo,
                                     "correo": EmailAddress
                            }
                            try:
                                print('creacion de directory para ' + UserPrincipalName)
                                consulta = requests.post(IP_SERVIDOR_API_DIRECTORY + '/create', json.dumps(datos),
                                                         timeout=7, verify=False)
                                if consulta.status_code == 200:
                                    datos = consulta.json()
                                    if 'msg_corto' in datos:
                                        if datos['msg_corto'] != 'Usuario NO Creado':
                                            persona.activedirectory = True
                                            persona.save()
                            except Exception as e:
                                print(e)
                                pass
                            # add_usuario_AD(persona)
                            data['result'] = 'ok'
                        except Exception as e:
                            print('eroror excep adduser ' + str(e))
                    else:
                        print('no se encontro la inscripcion del usuario '+ usuario)
                data['result'] = 'ok'
                return HttpResponse(json.dumps(data), content_type="application/json")
            except Exception as e:
                return HttpResponse(json.dumps({'result': 'bad', 'message': str(e)}), content_type="application/json")


        data = {'title': ''}
        addUserData(request,data)

    else:
        if 'action' in request.GET:
            action = request.GET['action']
            if action == 'buscaxnombre':
                try:
                    m = request.GET['model']
                    q = request.GET['q'].upper()
                    if ':' in m:
                        sp = m.split(':')
                        model = eval(sp[0])
                        query = model.flexbox_query(q)
                        query = query.filter(
                            eval(sp[1].replace('[uid]', str(request.session['persona'].id)))).distinct()
                    else:
                        model = eval(request.GET['model'])
                        query = model.flexbox_query(q)

                    data = {"results": [{"id": x.id, "name": x.flexbox_repr() + ' usuario: ' + x.persona.usuario.username} for x in query]}
                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    data = {"results": str(ex)}
                    return HttpResponse(json.dumps(data),content_type="application/json")

            elif action == 'buscaxgrupo':
                try:
                    m = request.GET['model']
                    q = request.GET['q'].upper()
                    if ':' in m:
                        sp = m.split(':')
                        model = eval(sp[0])
                        query = model.flexbox_query(q)
                        query = query.filter(
                            eval(sp[1].replace('[uid]', str(request.session['carrera'].id)))).distinct()
                    else:
                        model = eval(request.GET['model'])
                        query = model.flexbox_query(q)

                    data = {"results": [{"id": x.id, "name": x.flexbox_repr()} for x in query]}

                    return HttpResponse(json.dumps(data),content_type="application/json")
                except Exception as ex:
                    data = {"results": str(ex)}
                    return HttpResponse(json.dumps(data),content_type="application/json")

        data = {'title': 'Busqueda por usuario'}
        addUserData(request, data)



        return render(request ,"busqueda_usuario/busqueda_usuario.html" ,  data)

