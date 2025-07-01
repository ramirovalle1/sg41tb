  // Import the functions you need from the SDKs you need
  import { initializeApp } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-app.js";

  import { idpersonalogin, idasignacionclientemod } from "./conexion_firebase65.js"

  import { getFirestore, collection, addDoc,  query, where, getDoc  ,onSnapshot ,orderBy  ,doc ,updateDoc ,getDocs, serverTimestamp  } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-firestore.js"


  // TODO: Add SDKs for Firebase products that you want to use
  // https://firebase.google.com/docs/web/setup#available-libraries

  // Your web app's Firebase configuration
  // For Firebase JS SDK v7.20.0 and later, measurementId is optional
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
  export const app = initializeApp(firebaseConfig);
  const db = getFirestore(app);
  var detallechat= document.getElementById("detallechatlogin");
  var f = new Date();
  let htmlsalalogin = "";



   function scroll_to_bottom(){
         if ( document.getElementById( "detallechatlogin" )) {
             var objDiv = document.getElementById("detallechatlogin");
             objDiv.scrollTop = objDiv.scrollHeight;
         }
   }



  export function getRandomIntInclusive(min, max) {
      min = Math.ceil(min);
      max = Math.floor(max);
      return Math.floor(Math.random() * (max - min + 1) + min);
  }


  export const GuardarMensaje=(estado,fecha,hora,horapresentar,idpersona,idsoporte,nombrepersona,nombresporte,mensaje,enviosoporte,enviopersona,idasignacion,urlarchvio,tipoarchivo)=>{
    addDoc(collection(db,'mensaje'),{estado:estado,fecha:fecha,hora:hora,horapresentar:horapresentar,idpersona:idpersona,idsoporte:idsoporte,
    nombrepersona:nombrepersona,nombresporte:nombresporte,mensaje:mensaje,enviosoporte:enviosoporte,enviopersona:enviopersona,fechaparaordenar:serverTimestamp(),idasignacion: idasignacion,urlarchivo:urlarchvio,tipoarchivo:tipoarchivo,leido:false})
  }

  export const GuardarPersona=(nombre,email)=>{
    addDoc(collection(db,'persona'),{correo:email,estado:true,nombre:nombre})
  }




  export const GuardarAsignacionSoportePersona=(idsoporte,nombresoporte,idpersona,nombrepersona,fechaasigancion,estado,finalizado)=>{
    addDoc(collection(db,'asignacionsoportepersona'),{idsoporte:idsoporte,nombresoporte:nombresoporte,idpersona:idpersona,nombrepersona:nombrepersona,fechaasigancion:fechaasigancion,estado:estado,finalizado:finalizado})
  }



  export const getSoporteActivo=()=>  query(collection(db, "soporte"),where("estado", "==",true))

  export const getSoportePersonaFecha=(fechasignacion,idpersona)=>  query(collection(db, "asignacionsoportepersona"),where("fechaasigancion", "==",fechasignacion),where("idpersona", "==",idpersona))

  export const getSoportePersonaFechaOtro=(fechasignacion,idpersona)=>  query(collection(db, "asignacionsoportepersona"),where("fechaasigancion", "==",fechasignacion),where("idpersona", "==",idpersona),where("finalizado", "==",false))

  export const getPersona=(email) => query(collection(db, "persona"), where("correo", "==",email))

  export const getMensajeporPersona=(idpersonalogin,idasignacionsoporte) => query(collection(db, "mensaje"),orderBy("fechaparaordenar","asc" ), where("idpersona", "==",idpersonalogin),where("idasignacion", "==",idasignacionsoporte))

  export const getMensajeEnviadoSoporte=(idsoporte,idpersona,idasignacionsoporte)=> query(collection(db, "mensaje"),orderBy("fechaparaordenar","asc" ), where("idsoporte", "==",idsoporte),where("idpersona", "==",idpersona),where("idasignacion", "==",idasignacionsoporte))

  export const getSoportePersonaFechaSoporte=(idpersona)=>  query(collection(db, "asignacionsoportepersona"),where("idpersona", "==",idpersona),where("finalizado", "==",false))

  export const getMensajeEnviadoPersonaNoLeidos=(idpersona,idasignacionsoporte)=> query(collection(db, "mensaje"),orderBy("fechaparaordenar","asc" ), where("idpersona", "==",idpersona),where("idasignacion", "==",idasignacionsoporte),where("enviosoporte", "==",true),where("leido", "==",false))

  export const getMensajeEnviadoPersonaNoLeidosSalida=(idpersona,idasignacionsoporte)=> query(collection(db, "mensaje"),orderBy("fechaparaordenar","asc" ), where("idpersona", "==",idpersona),where("idasignacion", "==",idasignacionsoporte),where("leido", "==",false))


  function salirpersonalogin() {

        var df = document.getElementById("chatsgaonlie");
            df.style.display = "none";


        var d = document.getElementById("divwhatp");
        d.className = " whatsapp";
      d.style.display="block"



        var btninciaconve= document.getElementById("inciarconver");
        var iddivregistro= document.getElementById("idregistrochat");
        var idcollapseOne= document.getElementById("collapseOnelogin");
         $("#txtnombrelogin").val("");
         $("#txtcorreologin").val("");

          var detallechatlogin= document.getElementById("detallechatlogin");
         detallechatlogin.innerHTML="";
         btninciaconve.style.display = "block";
         iddivregistro.style.display = "none";
         idcollapseOne.style.display = "none";

         $('.modal-backdrop').remove();//eliminamos el backdrop del modal
  }


  function leermesnajespersonalogin(docsoportepersonamensajerec,idasipersona) {

         if ( (idasipersona==docsoportepersonamensajerec.data().idasignacion) && (docsoportepersonamensajerec.data().enviosoporte==true) && (docsoportepersonamensajerec.data().leido == false)) {
             // Set de recibido
              const docRef = doc(db, "mensaje", docsoportepersonamensajerec.id);
                  // Set del soporte
                  updateDoc(docRef, {
                      leido: true

                  });
         }

  }



  function armarmensajelogin(docme,idpersona,idasignacion,sexo) {

       const mesajedata = docme.data();


       var sexosopor="";

       if (parseInt(sexo)==1){
            sexosopor="../../../static/images/chat-img1.jpg"
       }else{
            sexosopor="../../../static/images/chat-img2.jpg"
       }




       htmlsalalogin="";

       if ((idpersona == mesajedata.idpersona) && (idasignacion == mesajedata.idasignacion)) {

            if ((mesajedata.enviosoporte == true) && (idpersona == mesajedata.idpersona) ) {
                if (mesajedata.urlarchivo!=""){

                    if (mesajedata.tipoarchivo==".pdf"){
                        if (mesajedata.leido == true){
                            htmlsalalogin = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="'+mesajedata.urlarchivo+'" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' +'<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                        }else{
                            htmlsalalogin = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="'+mesajedata.urlarchivo+'" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' +'<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                        }

                    }else{
                         if (mesajedata.leido == true) {
                             htmlsalalogin = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                         }else{
                             htmlsalalogin = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                         }
                    }

                }else{
                     if (mesajedata.leido == true) {
                         htmlsalalogin = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                     }else{
                         htmlsalalogin = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="'+sexosopor+'" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                     }
                }

            }else{
                if (mesajedata.urlarchivo!=""){

                    if (mesajedata.tipoarchivo==".pdf"){
                        if (mesajedata.leido == true) {
                            htmlsalalogin = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                        }else{
                            htmlsalalogin = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                        }
                    }else{
                          if (mesajedata.leido == true) {
                              htmlsalalogin = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                          }else{
                              htmlsalalogin = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                          }
                    }

                }else{
                     if (mesajedata.leido == true) {
                         htmlsalalogin = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                     }else{
                         htmlsalalogin = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                     }
                }

            }
       }



        detallechat.scrollTop=detallechat.scrollHeight;

       return htmlsalalogin;

  }





  const q = query(collection(db, "mensaje"), orderBy("fechaparaordenar","asc"));
  onSnapshot(q, (querySnapshot) => {



      let html = "";
      let idsexosoporte="";

      if (querySnapshot.docs.length > 0) {

             querySnapshot.docChanges().forEach((docmensaje) => {



                 if ((docmensaje.type === "added" || docmensaje.type === "modified" ) ) {


                    (async () => {

                         const docRefsoporte = doc(db, "soporte", docmensaje.doc.data().idsoporte);
                         const docSnapsoporte = await getDoc(docRefsoporte);

                         if (docSnapsoporte.exists()) {
                             idsexosoporte=docSnapsoporte.data().sexo;

                         }



                        var querySnapchotMensajelogin = await getDocs(getMensajeEnviadoSoporte(docmensaje.doc.data().idsoporte, idpersonalogin, idasignacionclientemod))

                        if (querySnapchotMensajelogin.docs.length > 0) {
                            querySnapchotMensajelogin.forEach((docsoportepersonamensajerec) => {

                                if (document.getElementsByClassName('chat_window')[0].style.height!="69px"){
                                       leermesnajespersonalogin(docsoportepersonamensajerec,idasignacionclientemod);
                                }

                                html += armarmensajelogin(docsoportepersonamensajerec, idpersonalogin, idasignacionclientemod,idsexosoporte);
                            });
                        }

                    })().then(function () {
                        if ( document.getElementById( "detallechatlogin" )) {
                             detallechat.innerHTML=html;
                        }
                    })

                }




            });



      }

  });



 function actualizarmensajenoleidopersonalogin (idpersonalogin,idasignacionpersonasoporte) {

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



  function leermensajepersonalogin() {

       (async () => {
                     const querySnapshotpersona= await getDocs(getPersona($("#txtcorreologin").val()))

                     if (parseInt(querySnapshotpersona.docs.length) > 0) {
                         //buscar a la persona que se logoneo
                         querySnapshotpersona.forEach((docpersonalogin) => {



                             (async () => {
                                    const quersigancionpersonaactiva = await getDocs(getSoportePersonaFechaSoporte(docpersonalogin.id));
                                    quersigancionpersonaactiva.forEach((doc) => {
                                        actualizarmensajenoleidopersonalogin(docpersonalogin.id,doc.id);
                                    });
                             })()

                         })

                     }
         })()

  }




 $("#minbtnlogin").click(function(){

                var barraenviomensaje= document.getElementById("barraenviomensaje");
                if (document.getElementsByClassName('chat_window')[0].style.height=="69px"){

                    leermensajepersonalogin();
                    barraenviomensaje.style.display = "block";//
                    document.getElementsByClassName('chat_window')[0].style.top="400px";
                    document.getElementsByClassName('chat_window')[0].style.height = "80%";

                }else {

                    barraenviomensaje.style.display = "none";
                    document.getElementsByClassName('chat_window')[0].style.height = "69px";
                    document.getElementsByClassName('chat_window')[0].style.top = "88%";

                }

     });





 $("#btncerrar").click(function() {


        if(idpersonalogin!="") {

            swal({
                title: 'Está seguro que desea salir del Chat?',
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

                    (async () => {




                            const querySnapshotFechasignacionsalir=  await getDocs(getSoportePersonaFechaSoporte(idpersonalogin))

                            if (querySnapshotFechasignacionsalir.docs.length > 0) {



                                querySnapshotFechasignacionsalir.forEach((docasingsalir) => {

                                    const docRefasigotrosalirsga = doc(db, "asignacionsoportepersona", docasingsalir.id);
                                    // Set del asignacionsoportepersona


                                    (async () => {
                                        await updateDoc(docRefasigotrosalirsga, {
                                            "finalizado": true


                                        });
                                    })().then(function () {
                                        /// poner como leidos todos los mensajes de las asignaciones
                                        (async () => {


                                            const querySnapchotMensajeNoLeidoPersona = await getDocs(getMensajeEnviadoPersonaNoLeidosSalida(idpersonalogin,docasingsalir.id));

                                            querySnapchotMensajeNoLeidoPersona.forEach((docmensajenoleidopersona) => {

                                                if (docmensajenoleidopersona.data().leido == false) {


                                                    const docRef = doc(db, "mensaje", docmensajenoleidopersona.id);
                                                    // Set del soporte
                                                    updateDoc(docRef, {
                                                        leido: true
                                                    });


                                                }
                                            });
                                        })().then(function () {

                                            salirpersonalogin();

                                        })

                                    })

                                });
                            }else{

                               salirpersonalogin();
                            }
                    })()


                }
            })
        }else{

             salirpersonalogin();
        }



    });




