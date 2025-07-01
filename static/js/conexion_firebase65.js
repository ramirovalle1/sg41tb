
    import { initializeApp } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-app.js";
    import { app, GuardarPersona, getPersona, GuardarMensaje, getSoporteActivo ,getRandomIntInclusive ,GuardarAsignacionSoportePersona ,getSoportePersonaFecha ,getSoportePersonaFechaOtro,getMensajeporPersona } from "./firebase65.js"
    import { getAuth, signInAnonymously, onAuthStateChanged  } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-auth.js"
    import { getDocs} from "https://www.gstatic.com/firebasejs/9.15.0/firebase-firestore.js"
    import { getStorage, ref, uploadBytes,uploadBytesResumable, getDownloadURL  } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-storage.js";


const firebaseConfig = {
  apiKey: "AIzaSyBPl4B7VkQM1MJkaXe1c0SiIiUZnrbSS-E",
  authDomain: "chatitbaok.firebaseapp.com",
  projectId: "chatitbaok",
  storageBucket: "chatitbaok.appspot.com",
  messagingSenderId: "979742280545",
  appId: "1:979742280545:web:44a509f5d62c1697511320",
  measurementId: "G-W9JZZ6MHQ2"
};



  // Initialize Firebase
  export const appsto = initializeApp(firebaseConfig);


    var idsalachat= document.getElementById("collapseOnelogin");
    var iddivregistro= document.getElementById("idregistrochat");
    var idcargachat= document.getElementById("idcargachat");
    var detallechatinicio= document.getElementById("detallechatlogin");
    export var idpersonalogin="";
    export var idasignacionclientemod="";
    var idsoporteatiende="";
    var nomsoporteantiende="";
    var sexosoporteatiende="";
    var nombrepersonalogin="";
    let urlarchivousuario="";
    let tipoarchivousuario="";

    const storage=getStorage(appsto);

    function uploadfileUsuario(file,nombrearchivo,tipoarchivosub) {

     var idmodalenviararchivo=document.getElementById("idmodalenviarusuario");



     $("#venteenviararchivousuariologin").modal({backdrop: 'static', keyboard: false});

     const storageRef=ref(storage,'archivochats/'+nombrearchivo)
     const uploadTask = uploadBytesResumable(storageRef, file);
     uploadTask.on('state_changed',
     (snapshot) => {
        // Observe state change events such as progress, pause, and resume
        // Get task progress, including the number of bytes uploaded and the total number of bytes to be uploaded
        const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;

        idmodalenviararchivo.innerHTML=' <div class="progress" style=" height: 35px;width: '+progress+'%; border: 1px solid #428bca; border-radius: 5px;background-color: #e6f3fa;margin-bottom: 15px;"> <div class="progress-bar" > <span class="progress-bar-text">'+progress+'%</span> </div> </div>';

        console.log('Upload is ' + progress + '% done');
        switch (snapshot.state) {
          case 'paused':
            console.log('Upload is paused');
            break;
          case 'running':
            console.log('Upload is running');
            break;
        }
      },
      (error) => {
        // Handle unsuccessful uploads
      },
      () => {
        // Handle successful uploads on complete
        // For instance, get the download URL: https://firebasestorage.googleapis.com/...
        getDownloadURL(uploadTask.snapshot.ref).then((downloadURL) => {
          console.log('File available at', downloadURL);
          urlarchivousuario=downloadURL;
          tipoarchivousuario=tipoarchivosub;
             $("#venteenviararchivousuariologin").modal('hide');

          enviarmensaje(2);

        });
      });

      return urlarchivousuario;

     // uploadBytes(storageRef,file).then(snapshot =>{
     //     console.log(snapshot)
     // })

    }


    // tipo envio indicar quien es la persona que envia el mensaje 1 para el soporte y 2 para el estudiante

    export function  enviarmensaje(tipoenvio){



                var f = new Date();
                var fechastr = f.getDate() + "/" + (f.getMonth() + 1) + "/" + f.getFullYear();
                var hor = 0;
                var min = 0;
                var segu = 0;
                var tienasignacionhoy=0;
                let puedeenviar=1;

                if (f.getHours() <= 9) {
                    hor = "0" + f.getHours();
                } else {
                    hor = f.getHours();
                }

                if (f.getMinutes() <= 9) {
                    min = "0" + f.getMinutes();
                } else {
                    min = f.getMinutes();
                }

                if (f.getSeconds() <= 9) {
                    segu = "0" + f.getSeconds();
                } else {
                    segu = f.getSeconds();
                }

                var hora = hor + ":" + min + ":" + segu;
                var horapresentar = hor + ":" + min;



                 //preguntar si estan algun personal de soporte
                (async () => {

                    const querySnapshotFechasignacion1=  await getDocs(getSoportePersonaFecha(fechastr,idpersonalogin))


                    querySnapshotFechasignacion1.forEach((docasing) => {



                        // alert(docasing.data().finalizado==true)
                        if (docasing.data().finalizado==false) {
                            /// tiene que volver a logonearse
                            idsoporteatiende = docasing.data().idsoporte;
                            nomsoporteantiende = docasing.data().nombresoporte;
                            idasignacionclientemod = docasing.id;
                            puedeenviar = 0;


                        }


                    })

                })().then(function () {




                    if (puedeenviar==0){

                        if (tipoenvio==1){
                            GuardarMensaje(false,fechastr,hora,horapresentar,idpersonalogin,idsoporteatiende,nombrepersonalogin,nomsoporteantiende,$("#id_message").val(),true,false,idasignacionclientemod,urlarchivousuario,tipoarchivousuario);
                        }else{
                            GuardarMensaje(false,fechastr,hora,horapresentar,idpersonalogin,idsoporteatiende,nombrepersonalogin,nomsoporteantiende,$("#id_message").val(),false,true,idasignacionclientemod,urlarchivousuario,tipoarchivousuario);
                        }
                        $("#id_message").val("");
                        urlarchivousuario="";
                        tipoarchivousuario="";

                    }else{
                        let cantidadsoporteacaux=0;

                        (async () => {

                            const querySnapshotSoporte=  await getDocs(getSoporteActivo())
                            cantidadsoporteacaux=parseInt(querySnapshotSoporte.docs.length);

                        })().then(function () {

                                if (cantidadsoporteacaux>0) {

                                    swal({
                                        title: 'El Soporte ha finalizado el chat para inicar otro chat es necesario volver a conectar para asigarle un soporte?',
                                        type: 'warning',
                                        showCancelButton: true,
                                        confirmButtonText: 'Si,Deseo salir!',
                                        cancelButtonText: 'Cancel',
                                        confirmButtonClass: 'btn btn-success margin-5',
                                        cancelButtonClass: 'btn btn-danger margin-5',
                                        buttonsStyling: false,
                                        allowOutsideClick: false,

                                    }).then(function (isConfirm) {


                                        if (isConfirm['dismiss'] != 'cancel' && isConfirm['dismiss'] != 'esc') {

                                            idsoporteatiende = "";
                                            idasignacionclientemod = "";
                                            location.href = '/';
                                            detallechatinicio.innerHTML = "";
                                            $("#id_message").val("");
                                            urlarchivousuario="";
                                            tipoarchivousuario="";

                                        }
                                    })
                                }

                            })

                    }

                })




    }





    function fecha(){

        var f = new Date();
        var fechastr = f.getDate() + "/" + (f.getMonth() + 1) + "/" + f.getFullYear();
        return fechastr;

    }


    function horapresentar(){

        var f = new Date();
        var hor = 0;
        var min = 0;
        var segu = 0;

        if (f.getHours() <= 9) {
            hor = "0" + f.getHours();
        } else {
            hor = f.getHours();
        }

        if (f.getMinutes() <= 9) {
            min = "0" + f.getMinutes();
        } else {
            min = f.getMinutes();
        }

        if (f.getSeconds() <= 9) {
            segu = "0" + f.getSeconds();
        } else {
            segu = f.getSeconds();
        }

        var horapresentar = hor + ":" + min;

        return horapresentar;

    }




    function validarEmail(correo) {
         if(correo){
          if (/^(([^<>()[\]\.,;:\s@\"]+(\.[^<>()[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$/i.test(correo)){
             return 0;
          }else{
            return 1;
          }
         }else{
             return 0;
         }
    }

    function limpiarDatos() {

        $("#helpnombrelogin").html("");
        $("#helpemaillogin").html("");
    }

    function validarRegistro() {

        if ($("#txtnombrelogin").val() == "") {
             $("#helpnombrelogin").html("Debe Ingresar el nombre");
             return 1;
        }

        if ($("#txtcorreologin").val() == "") {
             $("#helpemaillogin").html("Debe Ingresar el email");
             return 1;
        }

        if (validarEmail($("#txtcorreologin").val())!=0) {
            $("#helpemaillogin").html("Formato del Correo Incorrecto");
             return 1;
        }
        return 0;
    }




	$("#btnenviar").click(function() {



        limpiarDatos();
	    if (validarRegistro()==0) {

            $.post("/validacorreoinstitucional", {
                 email:$("#txtcorreologin").val()
            }, function (data) {
                if (data.result == 'bad') {
                   $("#helpemaillogin").html(data.message);

                }else{

                    const auth = getAuth(app);
                    const nombre = $("#txtnombrelogin").val();
                    const email = $("#txtcorreologin").val();
                    var listasoporteactivo=[];
                    var cantidadsoporteac=0;
                    var idindexsoporte=0;
                    let html = "";

                    idcargachat.style.display = "block";
                    iddivregistro.style.display = "none";

                      signInAnonymously(auth)
                          .then(() => {
                              (async () => {

                                    idpersonalogin="";
                                    nombrepersonalogin="";
                                    idsoporteatiende="";
                                    nomsoporteantiende="";
                                    idasignacionclientemod="";
                                    const querySnapshotSoporte=  await getDocs(getSoporteActivo())

                                    cantidadsoporteac=parseInt(querySnapshotSoporte.docs.length);


                                    if (cantidadsoporteac>0) {

                                         const querySnapshot= await getDocs(getPersona(email))

                                         if (parseInt(querySnapshot.docs.length)==0){
                                                   GuardarPersona(nombre,email);
                                                    const querySnapshotdata= await getDocs(getPersona(email))
                                                    querySnapshotdata.forEach((doc) =>{
                                                       idpersonalogin=doc.id;
                                                       nombrepersonalogin=doc.data().nombre;

                                                    })
                                         }else{
                                            //    buscar a la persona que se logoneo
                                                   const querySnapshotdata= await getDocs(getPersona(email))
                                                    querySnapshotdata.forEach((doc) =>{
                                                       idpersonalogin=doc.id;
                                                       nombrepersonalogin=doc.data().nombre;

                                                    })

                                         }


                                         querySnapshotSoporte.forEach((doc) => {
                                              listasoporteactivo.push({"idsoporte":doc.id,"nombresoporte":doc.data().nombre,"sexo":doc.data().sexo});

                                         });

                                         idindexsoporte=getRandomIntInclusive(1,cantidadsoporteac);

                                         idsoporteatiende=listasoporteactivo[idindexsoporte-1].idsoporte;
                                         nomsoporteantiende =listasoporteactivo[idindexsoporte-1].nombresoporte;
                                         sexosoporteatiende =listasoporteactivo[idindexsoporte-1].sexo;


                                         var sexosopor="";

                                         if (parseInt(sexosoporteatiende)==1){
                                                sexosopor="../../../static/images/chat-img1.jpg"
                                         }else{
                                                sexosopor="../../../static/images/chat-img2.jpg"
                                         }



                                         // buscar si la persona que esta enviando el mensaje ya tiene asignado un soporte
                                         var f = new Date();
                                         var fechastr = f.getDate() + "/" + (f.getMonth() + 1) + "/" + f.getFullYear();

                                         var tienasignacionhoy=0;


                                         const querySnapshotFechasignacion=  await getDocs(getSoportePersonaFechaOtro(fechastr,idpersonalogin));
                                         tienasignacionhoy=parseInt(querySnapshotFechasignacion.docs.length);

                                         querySnapshotFechasignacion.forEach((docasing) => {

                                            idasignacionclientemod=docasing.id;


                                            if (docasing.data().finalizado==true){
                                                /// tiene que volver a logonearse
                                                tienasignacionhoy=0;
                                            }
                                         })



                                         if (tienasignacionhoy==0) {


                                             GuardarAsignacionSoportePersona(idsoporteatiende, nomsoporteantiende, idpersonalogin, nombrepersonalogin, fecha(),true,false)

                                             const querySnapshotFechasignacionnuevo=  await getDocs(getSoportePersonaFecha(fechastr,idpersonalogin));
                                             tienasignacionhoy=parseInt(querySnapshotFechasignacionnuevo.docs.length);

                                             querySnapshotFechasignacionnuevo.forEach((docasing) => {
                                                   if (docasing.data().finalizado==false) {
                                                       idasignacionclientemod = docasing.id;
                                                   }

                                             })

                                             $("#id_message").val('Hola, estás hablando con ' + listasoporteactivo[idindexsoporte-1].nombresoporte + ' . ¿En qué te puedo ayudar?');

                                             enviarmensaje(1);

                                             html += '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>Hola, estás hablando con ' + listasoporteactivo[idindexsoporte-1].nombresoporte + ' . ¿En qué te puedo ayudar?</p> <div class="chat_time">' + fecha() + '-' + horapresentar() + '</div> </div> </li>';


                                             detallechatinicio.innerHTML=html;


                                             idsalachat.style.display = "block";


                                         }else{
                                              (async () => {


                                                      const querySnapshotCargarMensaje = await getDocs(getMensajeporPersona(idpersonalogin, idasignacionclientemod));

                                                      querySnapshotCargarMensaje.forEach((docasingcar) => {


                                                          const mesajedatalo = docasingcar.data();

                                                                if ((mesajedatalo.enviosoporte == true) && (idpersonalogin == mesajedatalo.idpersona) && (idasignacionclientemod == mesajedatalo.idasignacion)  ) {

                                                                    if (mesajedatalo.urlarchivo!=""){

                                                                        if (mesajedatalo.tipoarchivo==".pdf"){
                                                                             if (mesajedatalo.leido == true) {
                                                                                 html += '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix" > <div style="border: 0" ><a href="' + mesajedatalo.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                                                                             }else{

                                                                             }   html += '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix" > <div style="border: 0" ><a href="' + mesajedatalo.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                                                                        }else{
                                                                            if (mesajedatalo.leido == true) {
                                                                                 html += '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix" > <div style="border: 0"><a href="'+mesajedatalo.urlarchivo+'" data-fancybox="images" style="max-width: 300px;border: 0px" class="img-thumbnail"><img src="'+mesajedatalo.urlarchivo+'"   style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                                                                            }else{
                                                                                 html += '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix" > <div style="border: 0"><a href="'+mesajedatalo.urlarchivo+'" data-fancybox="images" style="max-width: 300px;border: 0px" class="img-thumbnail"><img src="'+mesajedatalo.urlarchivo+'"   style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                                                                            }

                                                                        }

                                                                    }else{
                                                                         if (mesajedatalo.leido == true) {
                                                                             html += '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedatalo.mensaje + '</p> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                                                                         }else{
                                                                             html += '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedatalo.mensaje + '</p> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                                                                         }
                                                                    }

                                                                } else {
                                                                    if ((idpersonalogin == mesajedatalo.idpersona) && (idasignacionclientemod == mesajedatalo.idasignacion)) {

                                                                         if (mesajedatalo.urlarchivo!=""){

                                                                             if (mesajedatalo.tipoarchivo==".pdf"){
                                                                                 if (mesajedatalo.leido == true) {
                                                                                     html += '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix" > <div style="border: 0"><a href="' + mesajedatalo.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                                                                                 }else{
                                                                                     html += '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix" > <div style="border: 0"><a href="' + mesajedatalo.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                                                                                 }
                                                                             }else{
                                                                                if (mesajedatalo.leido == true) {
                                                                                    html += '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix" > <div style="border: 0"><a href="' + mesajedatalo.urlarchivo + '" data-fancybox="images" style="max-width: 300px;border: 0px" class="img-thumbnail"><img src="' + mesajedatalo.urlarchivo + '"   style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                                                                                }else{
                                                                                    html += '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix" > <div style="border: 0"><a href="' + mesajedatalo.urlarchivo + '" data-fancybox="images" style="max-width: 300px;border: 0px" class="img-thumbnail"><img src="' + mesajedatalo.urlarchivo + '"   style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                                                                                }
                                                                             }

                                                                         }else{
                                                                             if (mesajedatalo.leido == true) {
                                                                                 html += '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedatalo.mensaje + '</p> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                                                                             }else{
                                                                                 html += '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedatalo.mensaje + '</p> <div class="chat_time">' + mesajedatalo.fecha + '-' + mesajedatalo.horapresentar + ' '+'<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                                                                             }
                                                                         }


                                                                    }
                                                                }

                                                      })

                                              })().then(function () {

                                                    detallechatinicio.innerHTML=html;
                                                    idsalachat.style.display = "block";

                                              })




                                         }



                                    }else{

                                          swal("Alerta", "Gracias por contactarnos. De momento no se encuentra ningún soporte conectado.", "warning");
                                          // html += '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="../ube/static/vendors/images/chat-img2.jpg" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>Gracias por contactarnos. De momento no se encuentra ningún soporte conectado.</p> <div class="chat_time">' + fecha() + '-' + horapresentar() + '</div> </div> </li>';
                                          //
                                          // detallechatinicio.innerHTML=html;

                                        idsalachat.style.display = "none";
                                        $("#txtnombre").val("");
                                        $("#txtcorreo").val("");
                                        var btninciaconveincio= document.getElementById("inciarconver");
                                        btninciaconveincio.style.display = "block";



                                    }



                              })().then(function () {
                                  idcargachat.style.display = "none";
                                    detallechatinicio.innerHTML=html;
                              })

                          })
                          .catch((error) => {
                            const errorCode = error.code;
                            const errorMessage = error.message;
                            swal("Error",errorMessage , "error");
                          });

                }
             }, 'json').fail(function() {
                    $("#helpemaillogin").html("Error de conexi&oacute;n vuelva a intentarlo");
            });



        }


    });

    $("#idenviarmensajes").click(function() {


          if ($("#id_message").val()!='' ) {

                enviarmensaje(2);
          }else{
               swal("Alerta", "Debe ingresar el mensaje", "warning");
          }
    });


     $("#inputGroupFile01usuariio").change(function(){

        var x = document.getElementById("inputGroupFile01usuariio");
        var fileExt = x.value;
        var validExts = new Array(".pdf",".jpg",".jpeg",".png");
        var fileExt1 = fileExt.substring(fileExt.lastIndexOf('.'));
        var nombre= fileExt.substring(fileExt.indexOf(x.files[0].name),fileExt.lastIndexOf('.'));
        if (validExts.indexOf(fileExt1) < 0){
            $("#inputGroupFile01usuariio").val('');
            swal("Error","El formato del archivo solo debe ser pdf,jpg","error");
        }else{
           uploadfileUsuario(x.files[0],x.files[0].name,fileExt1);

        }
    });


    $("#idshowfilesusuario").click(function() {

             $('#inputGroupFile01usuariio').click();
    });





