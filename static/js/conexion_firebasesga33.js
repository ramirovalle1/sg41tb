
    import { initializeApp } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-app.js";
    import { app, GuardarPersona, getPersona, GuardarMensaje, getSoporteActivo ,getRandomIntInclusive ,GuardarAsignacionSoportePersona ,getSoportePersonaFecha ,getSoportePersonaFechaOtro,getMensajeporPersona, getSoportePersonaFechaSoporte, getSoporte, GuardarSoporte, getPersonasAsignadaSoporte, getMensajeEnviadoSoporte, getPersonasAsignadaSoportePersona,getMensajeEnviadoSoporteNoLeidos, getMensajeEnviadoPersonaNoLeidos   } from "./firebasesga33.js"
    import { getAuth, signInAnonymously, onAuthStateChanged  } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-auth.js"
    import { getFirestore, getDocs, doc, updateDoc, query, collection, orderBy, onSnapshot, where, getDoc } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-firestore.js"
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
  const db = getFirestore(appsto);


    var idsalachat= document.getElementById("collapseOne");
    var iddivregistro= document.getElementById("idregistrochat");
    var idcargachat= document.getElementById("idcargachat");
    var detallechatinicio= document.getElementById("detallechat");
    var idmenuchat= document.getElementById("idmenuchat");

    var idconver= document.getElementById("idinciarcon");
    var testmensaje= document.getElementById("testmensaje");
    var idinciarconsoporte= document.getElementById("idinciarconsoporte");
    var detallechatsalasoporte= document.getElementById("detallechatsoporte");
    var idlistaverpersonaasignada=document.getElementById("idlistapersonasasignada");
    var seccionchatdetail= document.getElementById("collapseOnesoporte");

    var nompersonaasignada=document.getElementById("nombrepersonachat");

    export var idpersonalogin="";
    export var idasignacionclientemod="";
    var idsoporteatiende="";
    var nomsoporteantiende="";
    var nombrepersonalogin="";
    let urlarchivousuario="";
    let tipoarchivousuario="";
    var sexosoporteatiende="";


    let idasignacioncliente="";

    let cantidadmensajenoleidos=0;
    let cantidadtotalmensajenoleidos=0;
    let cantidadtotalmensajenoleidospersona=0;


    let idpersonasleccionchat="";
    let nombrepersonaseleccionada="";
    let idasginacionseleccionada="";

    let htmlsala = "";

    let urlarchivo=""
    let tipoarchivo=""
    let sexoSoporte = "";

    const storage=getStorage(appsto);

    function uploadfileUsuario(file,nombrearchivo,tipoarchivosub) {

     var idmodalenviararchivo=document.getElementById("idmodalenviarusuario");


     $("#venteenviararchivousuario").modal({backdrop: 'static', keyboard: false});
     const storageRef=ref(storage,'archivochats/'+nombrearchivo)
     const uploadTask = uploadBytesResumable(storageRef, file);
     uploadTask.on('state_changed',
     (snapshot) => {
        // Observe state change events such as progress, pause, and resume
        // Get task progress, including the number of bytes uploaded and the total number of bytes to be uploaded
        const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;




        idmodalenviararchivo.innerHTML='<div class="animated-progress progress-green"><span data-progress="'+progress+'"></span></div> ';

        $(".animated-progress span").each(function () {
              $(this).animate(
                {
                  width: progress + "%",
                },
                1000
              );
              $(this).text(progress + "%");
         });

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
          enviarmensaje(2);
          $("#venteenviararchivousuario").modal('hide');
        });
      });

      return urlarchivousuario;

     // uploadBytes(storageRef,file).then(snapshot =>{
     //     console.log(snapshot)
     // })

    }


    function uploadfileUsuarioSoporte(file,nombrearchivo,tipoarchivosub) {

     var idmodalenviararchivo=document.getElementById("idmodalenviarusuario");


     $("#venteenviararchivousuario").modal({backdrop: 'static', keyboard: false});
     const storageRef=ref(storage,'archivochats/'+nombrearchivo)
     const uploadTask = uploadBytesResumable(storageRef, file);
     uploadTask.on('state_changed',
     (snapshot) => {
        // Observe state change events such as progress, pause, and resume
        // Get task progress, including the number of bytes uploaded and the total number of bytes to be uploaded
        const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;




        idmodalenviararchivo.innerHTML='<div class="animated-progress progress-green"><span data-progress="'+progress+'"></span></div> ';

        $(".animated-progress span").each(function () {
              $(this).animate(
                {
                  width: progress + "%",
                },
                1000
              );
              $(this).text(progress + "%");
         });

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
          urlarchivo=downloadURL;
          tipoarchivo=tipoarchivosub;
          enviarmensajeSoporte();
          $("#venteenviararchivousuario").modal('hide');
        });
      });

      return urlarchivousuario;

     // uploadBytes(storageRef,file).then(snapshot =>{
     //     console.log(snapshot)
     // })

    }








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

                                             var de = document.getElementById("chatsgaonlie");
                                             de.style.display = "none";
                                             var d = document.getElementById("divwhatpsga");
                                             d.style.display="block"
                                             d.className = " whatsapp";
                                             var btninciaconve= document.getElementById("inciarconver");
                                             var iddivregistro= document.getElementById("idregistrochat");
                                             var alertamensajepersonap= document.getElementById("divalerta");
                                             btninciaconve.style.display = "block";
                                             iddivregistro.style.display = "none";
                                             alertamensajepersonap.style.display = "block";
                                             $('.modal-backdrop').remove();//eliminamos el backdrop del modal

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

        $("#helpnombre").html("");
        $("#helpemail").html("");
    }

    function validarRegistro() {

        if ($("#txtnombre").val() == "") {
             $("#helpnombre").html("Debe Ingresar el nombre");
             return 1;
        }

        if ($("#txtcorreo").val() == "") {
             $("#helpemail").html("Debe Ingresar el email");
             return 1;
        }

        if (validarEmail($("#txtcorreo").val())!=0) {
            $("#helpemail").html("Formato del Correo Incorrecto");
             return 1;
        }
        return 0;
    }

    function verificarconversacion(email) {


        var cantidadsoporteac=0;
        idasignacionclientemod="";
        idcargachat.style.display = "block";
        (async () => {


               const querySnapshot= await getDocs(getPersona(email))
               const querySnapshotSoporte=  await getDocs(getSoporteActivo())

               cantidadsoporteac=parseInt(querySnapshotSoporte.docs.length);

               if (cantidadsoporteac>0) {
                      if (parseInt(querySnapshot.docs.length)>0){
                    //buscar a la persona que se logoneo
                           const querySnapshotdata= await getDocs(getPersona(email))
                           querySnapshotdata.forEach((doc) =>{
                               idpersonalogin=doc.id;
                               nombrepersonalogin=doc.data().nombre;

                           })

                      }
                      // buscar si la persona que esta enviando el mensaje ya tiene asignado un soporte

                     const querySnapshotFechasignacionnuevo=  await getDocs(getSoportePersonaFechaSoporte(idpersonalogin));
                     querySnapshotFechasignacionnuevo.forEach((docasing) => {
                           if (docasing.data().finalizado==false) {
                               idasignacionclientemod = docasing.id;
                           }

                     })




               }else{

                    swal("Alerta", "Gracias por contactarnos. De momento no se encuentra ningún soporte conectado.", "warning");
                    idsalachat.style.display = "none";
                    var btninciaconveincio= document.getElementById("inciarconver");
                    btninciaconveincio.style.display = "block";
               }


        })().then(function () {

            if (idasignacionclientemod!=""){
                idconver.style.display = "none";
                verificaciontienechatabierto($("#txtnombre").val(),$("#txtcorreo").val());
            }else{
                idconver.style.display = "block";
                idcargachat.style.display = "none";

            }
        })
    }

    function verificaciontienechatabierto(nombre,email) {

         var listasoporteactivo=[];
         var cantidadsoporteac=0;
         var idindexsoporte=0;
         let html = "";
         idcargachat.style.display = "block";
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
                                 sexoSoporte==listasoporteactivo[idindexsoporte-1].sexo;



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


                                     //buscar las anterioes asignaciones y ponerla como finalizada
                                     const querySnapshotAsignacionSoportePersona=  await getDocs(getPersonasAsignadaSoportePersona(idsoporteatiende,idpersonalogin));
                                      querySnapshotAsignacionSoportePersona.forEach((docasingsopersona) => {
                                            const docRefasigoPersona= doc(db, "asignacionsoportepersona", docasingsopersona.id);
                                            // Set del asignacionsoportepersona
                                            (async () => {
                                                await updateDoc(docRefasigoPersona, {
                                                    "finalizado": true,


                                                });
                                            })()

                                      });

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

                                     html += '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded">  </span> <div class="chat-body clearfix"> <p>Hola, estás hablando con ' + listasoporteactivo[idindexsoporte-1].nombresoporte + ' . ¿En qué te puedo ayudar?</p> <div class="chat_time">' + fecha() + '-' + horapresentar() + '</div> </div> </li>';

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
                                var btninciaconveincio= document.getElementById("inciarconver");
                                btninciaconveincio.style.display = "block";



                            }



                      })().then(function () {
              idcargachat.style.display = "none";
                detallechatinicio.innerHTML=html;
         })


    }

    function mensajenoleidopersona (idpersonalogin,idasignacionpersonasoporte) {
        cantidadtotalmensajenoleidospersona=0;



        (async () => {

              const querySnapchotCantidadMensajeSoporte = await getDocs(getMensajeEnviadoPersonaNoLeidos(idpersonalogin,idasignacionpersonasoporte));

              querySnapchotCantidadMensajeSoporte.forEach((doccantidadmensajenoleidossoporte) => {


                  if (doccantidadmensajenoleidossoporte.data().leido == false) {
                      cantidadtotalmensajenoleidospersona = cantidadtotalmensajenoleidospersona + 1;

                  }
              });



        })().then(function () {
            if (document.getElementById("mensajenoleidopersona") !== null) {
                document.getElementById("mensajenoleidopersona").innerHTML = cantidadtotalmensajenoleidospersona;
                document.getElementById("mensajepersonanoleidos").innerHTML = cantidadtotalmensajenoleidospersona+" "+"mensaje(s) no leidos";
                cantidadtotalmensajenoleidospersona=0;
            }
        })




   }



    $("#divwhatpsga").click(function () {



        var d = document.getElementById("chatsgaonlie");
        d.style.display = "block";
        var x = document.getElementById("divwhatpsga");
        var f = document.getElementById("divalerta");
        x.style.display = "none";
        f.style.display = "none";
        idsalachat.style.display = "none";
        leermensajepersona();
        verificarconversacion($("#txtcorreo").val());
        idconver.style.display = "none";

    });



	$("#btnenviar").click(function() {



        limpiarDatos();
	    if (validarRegistro()==0) {

            const auth = getAuth(app);
            const nombre = $("#txtnombre").val();
            const email = $("#txtcorreo").val();


            idcargachat.style.display = "block";
            iddivregistro.style.display = "none";

              signInAnonymously(auth)
                  .then(() => {
                        verificaciontienechatabierto(nombre,email);

                  })
                  .catch((error) => {
                    const errorCode = error.code;
                    const errorMessage = error.message;
                    swal("Error",errorMessage , "error");
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





     $("#inputGroupFile01usuariioSoporte").change(function(){

        var x = document.getElementById("inputGroupFile01usuariioSoporte");
        var fileExt = x.value;
        var validExts = new Array(".pdf",".jpg",".jpeg",".png");
        var fileExt1 = fileExt.substring(fileExt.lastIndexOf('.'));
        var nombre= fileExt.substring(fileExt.indexOf(x.files[0].name),fileExt.lastIndexOf('.'));
        if (validExts.indexOf(fileExt1) < 0){
            $("#inputGroupFile01usuariioSoporte").val('');
            swal("Error","El formato del archivo solo debe ser pdf,jpg","error");
        }else{
            uploadfileUsuarioSoporte(x.files[0],x.files[0].name,fileExt1);
        }


     });

     $("#idshowfilesusuariosoporte").click(function() {
        $('#inputGroupFile01usuariioSoporte').click();
    });





   function armarmensaje(doc,idpersona,idasignacion,sexo) {

       const mesajedata = doc.data();

        var sexosopor="";

       if (parseInt(sexo)==1){
            sexosopor="../../../static/images/chat-img1.jpg"
       }else{
            sexosopor="../../../static/images/chat-img2.jpg"
       }




       htmlsala="";

       if ((idpersona == mesajedata.idpersona) && (idasignacion == mesajedata.idasignacion)) {

            if ((mesajedata.enviosoporte == true) && (idpersona == mesajedata.idpersona) ) {
                if (mesajedata.urlarchivo!=""){

                    if (mesajedata.tipoarchivo==".pdf"){
                        if (mesajedata.leido == true){
                            htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="'+mesajedata.urlarchivo+'" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' +'<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                        }else{
                            htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="'+mesajedata.urlarchivo+'" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' +'<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                        }

                    }else{
                         if (mesajedata.leido == true) {
                             htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                         }else{
                             htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                         }
                    }

                }else{
                     if (mesajedata.leido == true) {
                         htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                     }else{
                         htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                     }
                }

            }else{
                if (mesajedata.urlarchivo!=""){

                    if (mesajedata.tipoarchivo==".pdf"){
                        if (mesajedata.leido == true) {
                            htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                        }else{
                            htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                        }
                    }else{
                          if (mesajedata.leido == true) {
                              htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                          }else{
                              htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                          }
                    }

                }else{
                     if (mesajedata.leido == true) {
                         htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                     }else{
                         htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                     }
                }

            }
       }



        detallechatinicio.scrollTop=detallechatinicio.scrollHeight;
        detallechatsalasoporte.scrollTop=detallechatsalasoporte.scrollHeight;


       return htmlsala;

  }


   function mensajenoleidosoporte (idsoporteatiende) {
        cantidadtotalmensajenoleidos=0;


        (async () => {

              const querySnapchotCantidadMensajeSoporte = await getDocs(getMensajeEnviadoSoporteNoLeidos(idsoporteatiende));

              querySnapchotCantidadMensajeSoporte.forEach((doccantidadmensajenoleidossoporte) => {


                  if (doccantidadmensajenoleidossoporte.data().leido == false) {
                      cantidadtotalmensajenoleidos = cantidadtotalmensajenoleidos + 1;

                  }
              });



        })().then(function () {
            if (document.getElementById("testmensaje") !== null) {
                document.getElementById("testmensaje").innerHTML = cantidadtotalmensajenoleidos + ' Chat no leido'
                cantidadtotalmensajenoleidos=0;
            }
        })




   }

   function actualizarmensajenoleidopersona(idpersonalogin,idasignacionpersonasoporte) {

        (async () => {

              const querySnapchotCantidadMensajeSoporte = await getDocs(getMensajeEnviadoPersonaNoLeidos(idpersonalogin,idasignacionpersonasoporte));

              querySnapchotCantidadMensajeSoporte.forEach((doccantidadmensajenoleidossoporte) => {


                  if (doccantidadmensajenoleidossoporte.data().leido == false) {
                      const docRef = doc(db, "mensaje", doccantidadmensajenoleidossoporte.id);
                          // Set del soporte
                          updateDoc(docRef, {
                              leido: true

                          });

                  }
              });

        })()

    }

   function leermensajepersona() {

       (async () => {
                     const querySnapshotpersona= await getDocs(getPersona($("#txtcorreo").val()))

                     if (parseInt(querySnapshotpersona.docs.length) > 0) {
                         //buscar a la persona que se logoneo
                         const querySnapshotpersona = await getDocs(getPersona($("#txtcorreo").val()))
                         querySnapshotpersona.forEach((doc) => {
                             idpersonalogin = doc.id;
                             nombrepersonalogin = doc.data().nombre;
                             (async () => {
                                    const quersigancionpersonaactiva = await getDocs(getSoportePersonaFechaSoporte(idpersonalogin));
                                    quersigancionpersonaactiva.forEach((doc) => {
                                        actualizarmensajenoleidopersona(idpersonalogin,doc.id);
                                    });
                             })()

                         })

                     }
         })()

   }

   function leermesnajespersonasoporte(tipoperfil,docsoportepersonamensajerec,idasipersona,asignacionpersonasoportselec) {

       if (tipoperfil==1){ /* persona */

                 if ( (idasipersona==docsoportepersonamensajerec.data().idasignacion) && (docsoportepersonamensajerec.data().enviosoporte==true) && (docsoportepersonamensajerec.data().leido == false)) {
                     // Set de recibido
                      const docRef = doc(db, "mensaje", docsoportepersonamensajerec.id);
                          // Set del soporte
                          updateDoc(docRef, {
                              leido: true

                          });
                 }



       }else{

           if ( (asignacionpersonasoportselec==docsoportepersonamensajerec.data().idasignacion) && (docsoportepersonamensajerec.data().enviopersona==true) && (docsoportepersonamensajerec.data().leido == false)) {
                     // Set de recibido
                      const docRef = doc(db, "mensaje", docsoportepersonamensajerec.id);
                          // Set del soporte
                          updateDoc(docRef, {
                              leido: true

                          });
                 }
       }



   }



   const qasiga = query(collection(db, "asignacionsoportepersona"));
   onSnapshot(qasiga, (querySnapshotasigna) => {



     (async () => {


        querySnapshotasigna.docChanges().forEach((docsoporasiga) => {

             detallechatsalasoporte.innerHTML="";
             idlistaverpersonaasignada.innerHTML="";

             cantidadtotalmensajenoleidos=0;
             mensajenoleidosoporte(idsoporteatiende);
             consultarmensajepersona();




            if (docsoporasiga.type === "added" ) {

                if (idsoporteatiende == docsoporasiga.doc.data().idsoporte) {



                    llenarpersonaasignadasoporte(idsoporteatiende,2,sexosoporteatiende);




                }
            }

        });

     })()
  });


    const q = query(collection(db, "mensaje"), orderBy("fechaparaordenar","asc"));
    onSnapshot(q,(querySnapshot) => {

          cantidadtotalmensajenoleidos=0;



          if (querySnapshot.docs.length > 0) {

              /* leer los mensajes no leido del soporte */



              (async () => {

                  querySnapshot.docChanges().forEach((docsopor) => {


                     if ((docsopor.type === "added" || docsopor.type === "modified" ) ) {


                         mensajenoleidosoporte(idsoporteatiende);
                         consultarmensajepersona();



                         (async () => {

                             const docRefverfi = doc(db, "soporte", docsopor.doc.data().idsoporte);
                             const docSnap = await getDoc(docRefverfi);

                             if (docSnap.exists()) {

                                  sexoSoporte=docSnap.data().sexo;
                             }


                             const querySnapchotCantidadMensaje = await getDocs(getMensajeEnviadoSoporte(docsopor.doc.data().idsoporte, docsopor.doc.data().idpersona, docsopor.doc.data().idasignacion));

                             querySnapchotCantidadMensaje.forEach((doccantidadmensajenoleidos) => {
                                 if (doccantidadmensajenoleidos.data().leido == false && doccantidadmensajenoleidos.data().enviopersona == true) {
                                     cantidadmensajenoleidos = cantidadmensajenoleidos + 1;

                                 }
                             });

                         })().then(function () {
                             $("#badge_" + docsopor.doc.data().idpersona).html(cantidadmensajenoleidos + ' no leido');
                             cantidadmensajenoleidos = 0;
                         });

                         let html="";

                         (async () => {

                             let querySnapchotMensajeSoportePersonarec;
                             if (idpersonalogin != "" && idasignacionclientemod != "") {

                                querySnapchotMensajeSoportePersonarec = await getDocs(getMensajeEnviadoSoporte(docsopor.doc.data().idsoporte, idpersonalogin, idasignacionclientemod))

                             }else{
                                 querySnapchotMensajeSoportePersonarec = await getDocs(getMensajeEnviadoSoporte(docsopor.doc.data().idsoporte, idpersonasleccionchat, idasginacionseleccionada))
                             }


                             if (querySnapchotMensajeSoportePersonarec.docs.length > 0) {

                                 querySnapchotMensajeSoportePersonarec.forEach((docsoportepersonamensajerec) => {



                                 if (idpersonalogin != "" && idasignacionclientemod != "") {

                                        if (document.getElementsByClassName('chat_window')[0].style.height!="69px"){
                                             leermesnajespersonasoporte(1,docsoportepersonamensajerec,idasignacionclientemod,idasginacionseleccionada);
                                        }

                                        html += armarmensaje(docsoportepersonamensajerec, idpersonalogin, idasignacionclientemod,sexoSoporte);
                                 } else {

                                        leermesnajespersonasoporte(2,docsoportepersonamensajerec,idpersonasleccionchat,idasignacionclientemod,idasginacionseleccionada);

                                        html += armarmensaje(docsoportepersonamensajerec, idpersonasleccionchat,idasignacionclientemod,sexoSoporte);
                                 }

                                 });
                             }
                         })().then(function () {

                             detallechatinicio.innerHTML=html;
                             detallechatsalasoporte.innerHTML=html
                         })
                     }
                  });

              })()


          }

      });

    /* fin escuchador de llega de mensajes */



    /* chat del sorpote */

    function armarmensajeotro(doc,idpersona,idasignacion,sexo) {

       const mesajedata = doc.data();

       var sexosopor="";

       if (parseInt(sexo)==1){
            sexosopor="../../../static/images/chat-img1.jpg"
       }else{
            sexosopor="../../../static/images/chat-img2.jpg"
       }


       htmlsala="";

       if ((idpersona == mesajedata.idpersona) && (idasignacion == mesajedata.idasignacion)) {

            if ((mesajedata.enviosoporte == true) && (idpersona == mesajedata.idpersona) ) {
                if (mesajedata.urlarchivo!=""){

                    if (mesajedata.tipoarchivo==".pdf"){
                        if (mesajedata.leido == true){
                            htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="'+mesajedata.urlarchivo+'" title="Descargar" target="_blank"> <img src="../../../images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' +'<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                        }else{
                            htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="'+mesajedata.urlarchivo+'" title="Descargar" target="_blank"> <img src="../../../images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' +'<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                        }

                    }else{
                         if (mesajedata.leido == true) {
                             htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                         }else{
                             htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                         }
                    }

                }else{
                     if (mesajedata.leido == true) {
                         htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                     }else{
                         htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                     }
                }

            }else{
                if (mesajedata.urlarchivo!=""){

                    if (mesajedata.tipoarchivo==".pdf"){
                        if (mesajedata.leido == true) {
                            htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                        }else{
                            htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                        }
                    }else{
                          if (mesajedata.leido == true) {
                              htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                          }else{
                              htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                          }
                    }

                }else{
                     if (mesajedata.leido == true) {
                         htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                     }else{
                         htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                     }
                }

            }
       }

        detallechatsalasoporte.scrollTop=detallechatsalasoporte.scrollHeight;

       return htmlsala;

    }



    function llenarpersonaasignadasoporte(idsoporte,tipo,sexo) {
      idlistaverpersonaasignada.innerHTML="";
      cantidadtotalmensajenoleidos=0;
      (async () => {
              const querySnapshotPersonAsignada= await getDocs(getPersonasAsignadaSoporte(idsoporte))
                detallechatsalasoporte.innerHTML="";
              querySnapshotPersonAsignada.forEach((docpersonaasignada) => {


                          idlistaverpersonaasignada.innerHTML += '<li><a class="personasactivas"  style="cursor: pointer" idasignacioncliente="' + docpersonaasignada.id + '" idpersonaselecciona="' + docpersonaasignada.data().idpersona + '" idsoporteasig="' + docpersonaasignada.data().idsoporte + '"  id="' + docpersonaasignada.id + '"  nombrepersonasinada="' + docpersonaasignada.data().nombrepersona + '"><div class="row-fluid"> <div class="span2"><img src="../../../static/images/comentario.png" alt="" > </div><div class="span10"><h4 class="clearfix">' + docpersonaasignada.data().nombrepersona + '</h4><p><p class="badge badge-warning" id="badge_' + docpersonaasignada.data().idpersona + '"> ' + cantidadmensajenoleidos + ' no leido</p></div></div> </a> </li>';


                          (async () => {
                              const querySnapchotCantidadMensaje = await getDocs(getMensajeEnviadoSoporte(docpersonaasignada.data().idsoporte, docpersonaasignada.data().idpersona, docpersonaasignada.id));

                              querySnapchotCantidadMensaje.forEach((doccantidadmensajenoleidos) => {
                                  if (doccantidadmensajenoleidos.data().leido == false) {

                                      cantidadmensajenoleidos = cantidadmensajenoleidos + 1;

                                  }
                              });

                          })().then(function () {
                              $("#badge_" + docpersonaasignada.data().idpersona).html(cantidadmensajenoleidos + ' no leido');
                              cantidadmensajenoleidos = 0;
                          })

                          $(".personasactivas").on("click", function () {


                              let htmsalaaxu = '';
                              idasignacioncliente = "";

                              // var idbtnfinalizarchat=document.getElementById("idbtnfinalizarchat");
                              // idbtnfinalizarchat.style.display = "block";
                              seccionchatdetail.style.display = "block";
                              idmenuchat.style.display = "block";


                              htmlsala = "";
                              idasginacionseleccionada = $(this).attr('id');
                              nompersonaasignada.innerText = $(this).attr('nombrepersonasinada');
                              idpersonasleccionchat = $(this).attr('idpersonaselecciona');
                              nombrepersonaseleccionada = $(this).attr('nombrepersonasinada');
                              idasignacioncliente = $(this).attr('idasignacioncliente');
                              idasignacionclientemod = $(this).attr('idasignacioncliente');




                              // cargar los mensaje que se han enviado

                              (async () => {


                                  const querySnapchotMensajeSoportePersona = await getDocs(getMensajeEnviadoSoporte(docpersonaasignada.data().idsoporte, idpersonasleccionchat, idasginacionseleccionada))

                                  if (querySnapchotMensajeSoportePersona.docs.length > 0) {

                                      querySnapchotMensajeSoportePersona.forEach((docsoportepersonamensaje) => {


                                          const docmensarecep = doc(db, "mensaje", docsoportepersonamensaje.id);
                                          // Set de recibido
                                          updateDoc(docmensarecep, {
                                              leido: true

                                          });

                                          htmsalaaxu += armarmensajeotro(docsoportepersonamensaje, idpersonasleccionchat, idasignacioncliente,sexo);

                                      });
                                  }

                              })().then(function () {
                                  detallechatsalasoporte.innerHTML = htmsalaaxu;

                              })
                          });


              });

              cantidadmensajenoleidos=0;

      })().then(function () {
          if (tipo==1) {
              swal("! Inicio Session", "Inicio de Sesión exitoso", "success");

              mensajenoleidosoporte(idsoporteatiende);
              idinciarconsoporte.style.display = "none";

          }

      })

  }


    function llenarpersonaasignadasoportebusqueda(idsoporte,nombrebusqueda,sexo) {

      var re = new RegExp(nombrebusqueda, 'gi');


      idlistaverpersonaasignada.innerHTML="";
      (async () => {
              const querySnapshotPersonAsignada= await getDocs(getPersonasAsignadaSoporte(idsoporte))
                detallechatsalasoporte.innerHTML="";
              querySnapshotPersonAsignada.forEach((docpersonaasignada) => {

                  if (nombrebusqueda!="") {
                      if (docpersonaasignada.data().nombrepersona.match(re)) {
                          idlistaverpersonaasignada.innerHTML += '<li><a class="personasactivas"  style="cursor: pointer" idasignacioncliente="' + docpersonaasignada.id + '" idpersonaselecciona="' + docpersonaasignada.data().idpersona + '" idsoporteasig="' + docpersonaasignada.data().idsoporte + '"  id="' + docpersonaasignada.id + '"  nombrepersonasinada="' + docpersonaasignada.data().nombrepersona + '"><div class="row-fluid"> <div class="span2"><img src="../../../static/images/comentario.png" alt="" > </div><div class="span10"><h4 class="clearfix">' + docpersonaasignada.data().nombrepersona + '</h4><p><p class="badge badge-warning" id="badge_' + docpersonaasignada.data().idpersona + '"> ' + cantidadmensajenoleidos + ' no leido</p></div></div> </a> </li>';

                          (async () => {
                              const querySnapchotCantidadMensaje = await getDocs(getMensajeEnviadoSoporte(docpersonaasignada.data().idsoporte, docpersonaasignada.data().idpersona, docpersonaasignada.id));

                              querySnapchotCantidadMensaje.forEach((doccantidadmensajenoleidos) => {
                                  if (doccantidadmensajenoleidos.data().leido == false) {

                                      cantidadmensajenoleidos = cantidadmensajenoleidos + 1;

                                  }
                              });

                          })().then(function () {
                              $("#badge_" + docpersonaasignada.data().idpersona).html(cantidadmensajenoleidos + ' no leido');
                              cantidadmensajenoleidos = 0;
                          })

                          $(".personasactivas").on("click", function () {


                              let htmsalaaxu = '';
                              idasignacioncliente = "";

                              // var idbtnfinalizarchat=document.getElementById("idbtnfinalizarchat");
                              // idbtnfinalizarchat.style.display = "block";
                              seccionchatdetail.style.display = "block";
                              idmenuchat.style.display = "block";


                              htmlsala = "";
                              idasginacionseleccionada = $(this).attr('id');
                              nompersonaasignada.innerText = $(this).attr('nombrepersonasinada');
                              idpersonasleccionchat = $(this).attr('idpersonaselecciona');
                              nombrepersonaseleccionada = $(this).attr('nombrepersonasinada');
                              idasignacioncliente = $(this).attr('idasignacioncliente');
                              idasignacionclientemod = $(this).attr('idasignacioncliente');




                              // cargar los mensaje que se han enviado

                              (async () => {


                                  const querySnapchotMensajeSoportePersona = await getDocs(getMensajeEnviadoSoporte(docpersonaasignada.data().idsoporte, idpersonasleccionchat, idasginacionseleccionada))

                                  if (querySnapchotMensajeSoportePersona.docs.length > 0) {

                                      querySnapchotMensajeSoportePersona.forEach((docsoportepersonamensaje) => {


                                          const docmensarecep = doc(db, "mensaje", docsoportepersonamensaje.id);
                                          // Set de recibido
                                          updateDoc(docmensarecep, {
                                              leido: true

                                          });


                                          htmsalaaxu += armarmensajeotro(docsoportepersonamensaje, idpersonasleccionchat, idasignacioncliente,sexo);

                                      });
                                  }

                              })().then(function () {
                                  detallechatsalasoporte.innerHTML = htmsalaaxu;
                                  mensajenoleidosoporte(idsoporteatiende);
                              })
                          });


                      }
                  }else{

                      idlistaverpersonaasignada.innerHTML += '<li><a class="personasactivas"  style="cursor: pointer" idasignacioncliente="' + docpersonaasignada.id + '" idpersonaselecciona="' + docpersonaasignada.data().idpersona + '" idsoporteasig="' + docpersonaasignada.data().idsoporte + '"  id="' + docpersonaasignada.id + '"  nombrepersonasinada="' + docpersonaasignada.data().nombrepersona + '"><div class="row-fluid"> <div class="span2"><img src="../../../static/images/comentario.png" alt="" > </div><div class="span10"><h4 class="clearfix">' + docpersonaasignada.data().nombrepersona + '</h4><p><p class="badge badge-warning" id="badge_' + docpersonaasignada.data().idpersona + '"> ' + cantidadmensajenoleidos + ' no leido</p></div></div> </a> </li>';

                          (async () => {
                              const querySnapchotCantidadMensaje = await getDocs(getMensajeEnviadoSoporte(docpersonaasignada.data().idsoporte, docpersonaasignada.data().idpersona, docpersonaasignada.id));

                              querySnapchotCantidadMensaje.forEach((doccantidadmensajenoleidos) => {
                                  if (doccantidadmensajenoleidos.data().leido == false) {

                                      cantidadmensajenoleidos = cantidadmensajenoleidos + 1;

                                  }
                              });

                          })().then(function () {
                              $("#badge_" + docpersonaasignada.data().idpersona).html(cantidadmensajenoleidos + ' no leido');
                          })

                          $(".personasactivas").on("click", function () {


                              let htmsalaaxu = '';
                              idasignacioncliente = "";

                              // var idbtnfinalizarchat=document.getElementById("idbtnfinalizarchat");
                              // idbtnfinalizarchat.style.display = "block";
                              seccionchatdetail.style.display = "block";
                              idmenuchat.style.display = "block";


                              htmlsala = "";
                              idasginacionseleccionada = $(this).attr('id');
                              nompersonaasignada.innerText = $(this).attr('nombrepersonasinada');
                              idpersonasleccionchat = $(this).attr('idpersonaselecciona');
                              nombrepersonaseleccionada = $(this).attr('nombrepersonasinada');
                              idasignacioncliente = $(this).attr('idasignacioncliente');
                              idasignacionclientemod = $(this).attr('idasignacioncliente');


                              // cargar los mensaje que se han enviado

                              (async () => {


                                  const querySnapchotMensajeSoportePersona = await getDocs(getMensajeEnviadoSoporte(docpersonaasignada.data().idsoporte, idpersonasleccionchat, idasginacionseleccionada))

                                  if (querySnapchotMensajeSoportePersona.docs.length > 0) {

                                      querySnapchotMensajeSoportePersona.forEach((docsoportepersonamensaje) => {


                                          const docmensarecep = doc(db, "mensaje", docsoportepersonamensaje.id);
                                          // Set de recibido
                                          updateDoc(docmensarecep, {
                                              leido: true

                                          });


                                          htmsalaaxu += armarmensajeotro(docsoportepersonamensaje, idpersonasleccionchat, idasignacioncliente,sexo);

                                      });
                                  }

                              })().then(function () {
                                  detallechatsalasoporte.innerHTML = htmsalaaxu;
                              })
                          });


                  }

              });

              cantidadmensajenoleidos=0;

      })().then(function () {
          regresarchatactivo();

      })

  }

    function  enviarmensajeSoporte(){


                var f = new Date();
                var fechastr = f.getDate() + "/" + (f.getMonth() + 1) + "/" + f.getFullYear();
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

                var hora = hor + ":" + min + ":" + segu;
                var horapresentar = hor + ":" + min;


                (async () => {



                    GuardarMensaje(false,fechastr,hora,horapresentar,idpersonasleccionchat,idsoporteatiende,nombrepersonaseleccionada,nomsoporteantiende,$("#id_messagesoporte").val(),true,false,idasignacioncliente,urlarchivo,tipoarchivo);


                })().then(function () {
                     $("#id_messagesoporte").val("");
                       urlarchivo="";
                       tipoarchivo="";

                })

   }






     $("#chatsporte").click(function () {



         var d = document.getElementById("chatsgaonliesoporte");
         d.style.display = "block";

         var x = document.getElementById("chatasignadosoporte");
         x.style.display = "block";

         cantidadtotalmensajenoleidos=0;

        //verificar si tiene la sesion abierta o cerrada
        (async () => {
            const querySnapshotverificacion = await getDocs(getSoporte($("#lblcorreosoporte").html()))
             if (parseInt(querySnapshotverificacion.docs.length)>0) {
                 querySnapshotverificacion.forEach((docsoporteverificacion) => {
                     // doc.data() is never undefined for query doc snapshots
                     const docRefverfi = doc(db, "soporte", docsoporteverificacion.id);
                     (async () => {
                        const docSnap = await getDoc(docRefverfi);
                        if (docSnap.exists()) {
                              idsoporteatiende= docSnap.id;
                              nomsoporteantiende=docSnap.data().nombre;
                              sexosoporteatiende=docSnap.data().sexo;


                              if (docSnap.data().estado){
                                  llenarpersonaasignadasoporte(docsoporteverificacion.id,1,sexosoporteatiende);
                              }else{
                                  idinciarconsoporte.style.display = "block";
                              }
                        }
                     })().then(function () {
                           mensajenoleidosoporte(idsoporteatiende);
                     })

                 });
             }else{
                idinciarconsoporte.style.display="block";
             }

        })()

     });


     $("#btninciarseccion").click(function() {


         (async () => {
             try {

                 const querySnapshot= await getDocs(getSoporte($("#lblcorreosoporte").html()))
                 if (parseInt(querySnapshot.docs.length)==0) {
                     await GuardarSoporte(true, $("#nombresporte").html(), $("#lblcorreosoporte").html(),parseInt($("#generosorporte").html()));
                 }else{

                      querySnapshot.forEach((docsoporte) => {
                        // doc.data() is never undefined for query doc snapshots
                        const docRef = doc(db, "soporte", docsoporte.id);
                          // Set del soporte
                          updateDoc(docRef, {
                              estado: true

                          });
                         /// cargue los chat asignado a el
                        idsoporteatiende= docsoporte.id;
                        nomsoporteantiende=docsoporte.data().nombre;
                        sexoSoporte=docsoporte.data().sexo;

                        llenarpersonaasignadasoporte(docsoporte.id,1,sexoSoporte);

                        mensajenoleidosoporte(docsoporte.id);

                      });

                 }


             }catch (error) {

                  swal("Error", String(error), "error");
             }



          })()


      });


     $("#idenviarmensajessoporte").click(function() {

        if ($("#id_messagesoporte").val()!='' ) {
                enviarmensajeSoporte();
          }else{
               swal("Alerta", "Debe ingresar el mensaje", "warning");
          }
     });


     $("#buscarpersona").click(function () {
        let nombreText = $("#txtbusqueda").val().toUpperCase();
        llenarpersonaasignadasoportebusqueda(idsoporteatiende,nombreText,sexoSoporte);

     });

     function regresarchatactivo() {
        $("#id_messagesoporte").val("");
        idasginacionseleccionada=0;
        nompersonaasignada.innerText="";
        idpersonasleccionchat="";
        nombrepersonaseleccionada="";
        idasignacioncliente="";
        idasignacionclientemod="";
        detallechatsalasoporte.innerHTML="";
        seccionchatdetail.style.display = "none";
        idmenuchat.style.display = "none";
     }

     $("#regresarchat").click(function () {

       regresarchatactivo();

     });


     $("#btnfinalizarchat").click(function() {


        (async () => {

                 const docRefasig = doc(db, "asignacionsoportepersona", idasginacionseleccionada);
                  // Set del asignacionsoportepersona
                 updateDoc(docRefasig, {
                      finalizado: true

                 });
                 idlistaverpersonaasignada.innerHTML="";
                 const docSnapasignacion = await getDoc(docRefasig);

                 llenarpersonaasignadasoporte(docSnapasignacion.data().idsoporte,2,1);



        })().then(function () {
                $("#id_messagesoporte").val("El soporte asignado finalizo el chat");
                 enviarmensajeSoporte();
                 regresarchatactivo();


        })
     });


     $("#btncerrarsesion").click(function() {


         (async () => {
             try {

                 const querySnapshot= await getDocs(getSoporte($("#lblcorreosoporte").html()))
                 if (parseInt(querySnapshot.docs.length)==0) {
                     await GuardarSoporte(true, $("#nombresporte").html(), $("#lblcorreosoporte").html(),parseInt($("#generosorporte").html()));
                 }else{

                      querySnapshot.forEach((docsoporte) => {
                        // doc.data() is never undefined for query doc snapshots
                        const docRef = doc(db, "soporte", docsoporte.id);
                          // Set del soporte
                          updateDoc(docRef, {
                              estado: false

                          });
                      });




                 }
                 swal("! Cerrando Sesión", " Sesión cerrada con exitoso", "success");

                 var df = document.getElementById("chatsgaonliesoporte");
                 df.style.display = "none";
                 var xf = document.getElementById("chatasignadosoporte");
                 xf.style.display = "none";



                 idlistaverpersonaasignada.innerHTML ="";

                 regresarchatactivo();


             }catch (error) {

                  swal("Error", String(error), "error");
             }

          })()


     });


     function consultarmensajepersona() {
         (async () => {
                     const querySnapshotpersona= await getDocs(getPersona($("#txtcorreo").val()))

                     if (parseInt(querySnapshotpersona.docs.length) > 0) {
                         //buscar a la persona que se logoneo
                         const querySnapshotpersona = await getDocs(getPersona($("#txtcorreo").val()))
                         querySnapshotpersona.forEach((doc) => {
                             idpersonalogin = doc.id;
                             nombrepersonalogin = doc.data().nombre;
                             (async () => {
                                    const quersigancionpersonaactiva = await getDocs(getSoportePersonaFechaSoporte(idpersonalogin));
                                    quersigancionpersonaactiva.forEach((doc) => {
                                        mensajenoleidopersona(idpersonalogin,doc.id);
                                    });
                             })()

                         })

                     }
         })()
     }


     $("#minbtn").click(function(){

                var barraenviomensaje= document.getElementById("barraenviomensaje");
                var alertamensajepersona= document.getElementById("divalerta");
                var alertamensajepersonacabecera= document.getElementById("mensajepersonanoleidos");

                alertamensajepersona.style.display = "none";

                if (document.getElementsByClassName('chat_window')[0].style.height=="69px"){
                    barraenviomensaje.style.display = "block";
                    alertamensajepersonacabecera.style.display = "none";
                    leermensajepersona();
                    document.getElementsByClassName('chat_window')[0].style.top="400px";
                    document.getElementsByClassName('chat_window')[0].style.height = "80%";

                }else {
                    barraenviomensaje.style.display = "none";
                    alertamensajepersonacabecera.style.display = "block";
                    document.getElementsByClassName('chat_window')[0].style.height = "69px";
                    document.getElementsByClassName('chat_window')[0].style.top = "88%";

                }

     });


     $(window).on('load', function () {

        (async () => {
             try {

                 const querySnapshot= await getDocs(getSoporte($("#lblcorreosoporte").html()))
                 if (parseInt(querySnapshot.docs.length)>0) {
                         querySnapshot.forEach((docsoporteverificacion) => {
                             // doc.data() is never undefined for query doc snapshots
                             const docRefverfi = doc(db, "soporte", docsoporteverificacion.id);
                             (async () => {
                                const docSnap = await getDoc(docRefverfi);
                                if (docSnap.exists()) {
                                      idsoporteatiende= docSnap.id;
                                      nomsoporteantiende=docSnap.data().nombre;
                                      sexoSoporte=docSnap.data().sexo;
                                      sexosoporteatiende=docSnap.data().sexo;
                                }
                             })().then(function () {
                                   mensajenoleidosoporte(idsoporteatiende);
                             })

                         });
                 }
                 consultarmensajepersona();



             }catch (error) {
                  console.log( String(error));

                  //swal("Error", String(error), "error");
             }
        })()

     });



