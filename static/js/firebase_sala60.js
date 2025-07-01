  import { initializeApp } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-app.js";
  import { getStorage, ref, uploadBytes,uploadBytesResumable, getDownloadURL  } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-storage.js";
  import { getFirestore, collection, addDoc ,updateDoc ,query, where, getDoc, getDocs ,doc ,onSnapshot ,orderBy } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-firestore.js"


  import { GuardarMensaje} from "./firebase59.js";







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
  export const url=""
  export let urlarchivo=""
  export let tipoarchivo=""

  const storage=getStorage(app);


   var btncerrarsesion= document.getElementById("btncerrarsesion");
   var btninciarseccion= document.getElementById("btninciarseccion");
   var seccionchatdetail= document.getElementById("chat-detail");



   var idlistaverpersonaasignada=document.getElementById("idlistapersonasasignada");

   var nompersonaasignada=document.getElementById("nombrepersonachat");


   let idpersonasleccionchat="";
   let nombrepersonaseleccionada="";
   let idasginacionseleccionada="";

   let idsoporteatiende="";
   let nomsoporteantiende="";
   let idasignacioncliente="";

   var detallechatsala= document.getElementById("iddetallesalachatsoporte");



   let htmlsala = "";

   let cantidadmensajenoleidos=0;







 function uploadfile(file,nombrearchivo,tipoarchivosub) {

     var idmodalenviararchivo=document.getElementById("idmodalenviar");


     $("#venteenviararchivo").modal({backdrop: 'static', keyboard: false});
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
          urlarchivo=downloadURL;
          tipoarchivo=tipoarchivosub;
          enviarmensajeSoporte();
          $("#venteenviararchivo").modal('hide');
        });
      });

      return urlarchivo;

     // uploadBytes(storageRef,file).then(snapshot =>{
     //     console.log(snapshot)
     // })

 }


  export const GuardarSoporte=(estado,nombre,correo)=>{
      addDoc(collection(db,'soporte'),{estado:estado,nombre:nombre,correo:correo})
  }

  export const getSoporte=(email) => query(collection(db, "soporte"), where("correo", "==",email))

  export const getPersonasAsignadaSoporte=(idsoporte) => query(collection(db, "asignacionsoportepersona"), where("idsoporte", "==",idsoporte),where("finalizado", "==",false))




  export const getMensajeEnviadoSoporte=(idsoporte,idpersona,idasignacionsoporte)=> query(collection(db, "mensaje"),orderBy("fechaparaordenar","asc" ), where("idsoporte", "==",idsoporte),where("idpersona", "==",idpersona),where("idasignacion", "==",idasignacionsoporte))

  function armarmensaje(doc,idpersona,idasignacion) {

       const mesajedata = doc.data();

       htmlsala="";

       if ((idpersona == mesajedata.idpersona) && (idasignacion == mesajedata.idasignacion)) {

            if ((mesajedata.enviosoporte == true) && (idpersona == mesajedata.idpersona) ) {
                if (mesajedata.urlarchivo!=""){

                    if (mesajedata.tipoarchivo==".pdf"){
                        if (mesajedata.leido == true){
                            htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="../../../static/images/chat-img2.jpg" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="'+mesajedata.urlarchivo+'" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' +'<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                        }else{
                            htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="../../../static/images/chat-img2.jpg" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="'+mesajedata.urlarchivo+'" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' +'<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                        }

                    }else{
                         if (mesajedata.leido == true) {
                             htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="../../../static/images/chat-img2.jpg" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                         }else{
                             htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="../../../static/images/chat-img2.jpg" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                         }
                    }

                }else{
                     if (mesajedata.leido == true) {
                         htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="../../../static/images/chat-img2.jpg" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                     }else{
                         htmlsala = '<li class="clearfix admin_chat"> <span class="chat-img"> <img src="../../../static/images/chat-img2.jpg" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <p>' + mesajedata.mensaje + '</p> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion.png"></div> </div> </li>';
                     }
                }

            }else{
                if (mesajedata.urlarchivo!=""){

                    if (mesajedata.tipoarchivo==".pdf"){
                        if (mesajedata.leido == true) {
                            htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                        }else{
                            htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" title="Descargar" target="_blank"> <img src="../../../static/images/descargar32px.png">Descargar Archivo</a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                        }
                    }else{
                          if (mesajedata.leido == true) {
                              htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
                          }else{
                              htmlsala = '<li class="clearfix"> <span class="chat-img"> <img src="../../../static/images/icono.png" alt="" class="mCS_img_loaded"> </span> <div class="chat-body clearfix"> <div ><a href="' + mesajedata.urlarchivo + '" data-fancybox="images" style="border: 0px"><img src="' + mesajedata.urlarchivo + '"  style="max-width: 300px;border: 0px" class="img-thumbnail"/></a> </div> <div class="chat_time">' + mesajedata.fecha + '-' + mesajedata.horapresentar + ' ' + '<img src="../../../static/images/doble-verificacion-1.png"></div> </div> </li>';
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

        detallechatsala.scrollTop=detallechatsala.scrollHeight;

       return htmlsala;

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



  const qasiga = query(collection(db, "asignacionsoportepersona"),where("finalizado", "==",false));
  onSnapshot(qasiga, (querySnapshotasigna) => {


     (async () => {
        idlistaverpersonaasignada.innerHTML ="";
        detallechatsala.innerHTML="";
        querySnapshotasigna.forEach((docsoporasiga) => {



            if (idsoporteatiende == docsoporasiga.data().idsoporte){

                    idlistaverpersonaasignada.innerHTML += '<li  ><a class="personasactivas"  style="cursor: pointer" idasignacioncliente="'+docsoporasiga.id+'" idpersonaselecciona="'+docsoporasiga.data().idpersona+'" idsoporteasig="'+docsoporasiga.data().idsoporte+'"  id="'+docsoporasiga.id+'"  nombrepersonasinada="'+docsoporasiga.data().nombrepersona+'"> <img src="../../../static/images/chatescribir.png" alt="" > <h3 class="clearfix">'+docsoporasiga.data().nombrepersona+'</h3> <p><i class="fa fa-circle text-light-green"></i> online</p> <span class="badge badge-danger" id="badge_'+docsoporasiga.data().idpersona+'" style="margin-top: 10px;font-size: 12px"> '+cantidadmensajenoleidos+' no leido </span> </a> </li>';


                   (async () => {
                       const querySnapchotCantidadMensaje = await getDocs(getMensajeEnviadoSoporte(docsoporasiga.data().idsoporte, docsoporasiga.data().idpersona, docsoporasiga.id));

                        querySnapchotCantidadMensaje.forEach((doccantidadmensajenoleidos) => {
                            if (doccantidadmensajenoleidos.data().leido == false){
                             cantidadmensajenoleidos=cantidadmensajenoleidos+1;
                            }
                        });


                   })().then(function () {
                             $("#badge_"+docsoporasiga.data().idpersona).html(cantidadmensajenoleidos+' no leido');
                         })


                            $(".personasactivas").on("click", function () {
                              let htmsalaaxu='';
                              idasignacioncliente="";
                              var idbtnfinalizarchat=document.getElementById("idbtnfinalizarchat");
                              idbtnfinalizarchat.style.display = "block";
                              seccionchatdetail.style.display = "block";


                              htmlsala="";
                              idasginacionseleccionada=$(this).attr('id');
                              nompersonaasignada.innerText=$(this).attr('nombrepersonasinada');
                              idpersonasleccionchat=$(this).attr('idpersonaselecciona');
                              nombrepersonaseleccionada=$(this).attr('nombrepersonasinada');
                              idasignacioncliente=$(this).attr('idasignacioncliente');



                                (async () => {

                                    const querySnapchotMensajeSoportePersona = await getDocs(getMensajeEnviadoSoporte(docsoporasiga.data().idsoporte, idpersonasleccionchat, idasginacionseleccionada))

                                    if (querySnapchotMensajeSoportePersona.docs.length > 0) {



                                        querySnapchotMensajeSoportePersona.forEach((docsoportepersonamensaje) => {

                                            const docmensarecep = doc(db, "mensaje", docsoportepersonamensaje.id);
                                            // Set de recibido
                                            updateDoc(docmensarecep, {
                                                  leido: true

                                            });

                                            htmsalaaxu += armarmensaje(docsoportepersonamensaje, idpersonasleccionchat, idasignacioncliente);

                                        });
                                    }

                                })().then(function () {

                                     detallechatsala.innerHTML=htmsalaaxu;
                                })


                            });




            }

            cantidadmensajenoleidos=0;

        });

     })()
  });




  function llenarpersonaasignadasoporte(idsoporte) {

      (async () => {
              const querySnapshotPersonAsignada= await getDocs(getPersonasAsignadaSoporte(idsoporte))
                detallechatsala.innerHTML="";
              querySnapshotPersonAsignada.forEach((docpersonaasignada) => {

                         idlistaverpersonaasignada.innerHTML += '<li  ><a class="personasactivas"  style="cursor: pointer" idasignacioncliente="'+docpersonaasignada.id+'" idpersonaselecciona="'+docpersonaasignada.data().idpersona+'" idsoporteasig="'+docpersonaasignada.data().idsoporte+'"  id="'+docpersonaasignada.id+'"  nombrepersonasinada="'+docpersonaasignada.data().nombrepersona+'"> <img src="../../../static/images/chatescribir.png" alt="" > <h3 class="clearfix">'+docpersonaasignada.data().nombrepersona+'</h3> <p><i class="fa fa-circle text-light-green"></i> online</p><span class="badge badge-danger" id="badge_'+docpersonaasignada.data().idpersona+'" style="margin-top: 10px;font-size: 12px"> '+cantidadmensajenoleidos+' no leido</span> </a> </li>';

                         (async () => {
                           const querySnapchotCantidadMensaje = await getDocs(getMensajeEnviadoSoporte(docpersonaasignada.data().idsoporte, docpersonaasignada.data().idpersona, docpersonaasignada.id));

                            querySnapchotCantidadMensaje.forEach((doccantidadmensajenoleidos) => {
                                if (doccantidadmensajenoleidos.data().leido == false){

                                   cantidadmensajenoleidos=cantidadmensajenoleidos+1;

                                }
                            });

                         })().then(function () {
                             $("#badge_"+docpersonaasignada.data().idpersona).html(cantidadmensajenoleidos+' no leido');
                         })

                         $(".personasactivas").on("click", function() {

                              let htmsalaaxu='';
                              idasignacioncliente="";

                              var idbtnfinalizarchat=document.getElementById("idbtnfinalizarchat");
                              idbtnfinalizarchat.style.display = "block";
                              seccionchatdetail.style.display = "block";


                              htmlsala="";
                              idasginacionseleccionada=$(this).attr('id');
                              nompersonaasignada.innerText=$(this).attr('nombrepersonasinada');
                              idpersonasleccionchat=$(this).attr('idpersonaselecciona');
                              nombrepersonaseleccionada=$(this).attr('nombrepersonasinada');
                              idasignacioncliente=$(this).attr('idasignacioncliente');




                              // cargar los mensaje que se han enviado

                              (async () => {



                                  const querySnapchotMensajeSoportePersona=  await getDocs(getMensajeEnviadoSoporte(docpersonaasignada.data().idsoporte,idpersonasleccionchat,idasginacionseleccionada))

                                  if (querySnapchotMensajeSoportePersona.docs.length > 0) {

                                      querySnapchotMensajeSoportePersona.forEach((docsoportepersonamensaje) => {


                                           const docmensarecep = doc(db, "mensaje", docsoportepersonamensaje.id);
                                            // Set de recibido
                                            updateDoc(docmensarecep, {
                                                  leido: true

                                            });


                                         htmsalaaxu+= armarmensaje(docsoportepersonamensaje,idpersonasleccionchat,idasignacioncliente);

                                      });
                                  }

                              })().then(function () {
                                    detallechatsala.innerHTML=htmsalaaxu;
                              })
                         });





              });

              cantidadmensajenoleidos=0;

      })()

  }



  $("#btninciarseccion").click(function() {


     (async () => {
         try {

             const querySnapshot= await getDocs(getSoporte($("#lblcorreo").html()))
             if (parseInt(querySnapshot.docs.length)==0) {
                 await GuardarSoporte(true, $("#nombresporte").html(), $("#lblcorreo").html());
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
                    llenarpersonaasignadasoporte(docsoporte.id);

                  });

             }


         }catch (error) {

              swal("Error", String(error), "error");
         }



      })().then(function () {

             swal("! Inicio Session", "Inicio de Sesión exitoso", "success");
             btncerrarsesion.style.display = "block";
             btninciarseccion.style.display = "none";

            }

     )
  });

   $


  $("#btncerrarsesion").click(function() {


     (async () => {
         try {

             const querySnapshot= await getDocs(getSoporte($("#lblcorreo").html()))
             if (parseInt(querySnapshot.docs.length)==0) {
                 await GuardarSoporte(true, $("#nombresporte").html(), $("#lblcorreo").html());
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

             btncerrarsesion.style.display = "none";
             btninciarseccion.style.display = "block";
             seccionchatdetail.style.display = "none";
             detallechatsala.style.display = "none";
             idlistaverpersonaasignada.style.display = "none";


         }catch (error) {

              swal("Error", String(error), "error");
         }

      })()


  });


  const q = query(collection(db, "mensaje"), orderBy("fechaparaordenar","asc"));
  onSnapshot(q, (querySnapshot) => {

     detallechatsala.innerHTML="";
     let htmsalaaxu2='';
     htmlsala="";
     (async () => {

        querySnapshot.forEach((docsopor) => {


               (async () => {
                       const querySnapchotCantidadMensaje = await getDocs(getMensajeEnviadoSoporte(docsopor.data().idsoporte, docsopor.data().idpersona, docsopor.data().idasignacion));

                        querySnapchotCantidadMensaje.forEach((doccantidadmensajenoleidos) => {
                            if (doccantidadmensajenoleidos.data().leido == false){
                               cantidadmensajenoleidos=cantidadmensajenoleidos+1;

                            }
                        });

                   })().then(function () {
                       $("#badge_"+docsopor.data().idpersona).html(cantidadmensajenoleidos+' no leido');
                       cantidadmensajenoleidos=0;
               });



            (async () => {
                const querySnapchotMensajeSoportePersonarec = await getDocs(getMensajeEnviadoSoporte(docsopor.data().idsoporte, idpersonasleccionchat, idasginacionseleccionada))

                if (querySnapchotMensajeSoportePersonarec.docs.length > 0) {

                    querySnapchotMensajeSoportePersonarec.forEach((docsoportepersonamensajerec) => {


                        const docmensarecepotro = doc(db, "mensaje", docsoportepersonamensajerec.id);
                        // Set de recibido
                        updateDoc(docmensarecepotro, {
                            leido: true

                        });
                    });
                }
            })()

            htmsalaaxu2+=   armarmensaje(docsopor,idpersonasleccionchat,idasignacioncliente);

        });

     })().then(function () {
         detallechatsala.innerHTML=htmsalaaxu2;



     })
  });







   $("#idenviarmensajessoporte").click(function() {

          if ($("#id_messagesoporte").val()!='' ) {
                enviarmensajeSoporte();
          }else{
               swal("Alerta", "Debe ingresar el mensaje", "warning");
          }
   });


    $("#inputSoporteFile01").change(function(){
        var x = document.getElementById("inputSoporteFile01");
        var fileExt = x.value;
        var validExts = new Array(".pdf",".jpg",".jpeg",".png");
        var fileExt1 = fileExt.substring(fileExt.lastIndexOf('.'));
        var nombre= fileExt.substring(fileExt.indexOf(x.files[0].name),fileExt.lastIndexOf('.'));
        if (validExts.indexOf(fileExt1) < 0){
            $("#inputSoporteFile01").val('');
            swal("Error","El formato del archivo solo debe ser pdf,jpg","error");
        }else{
            uploadfile(x.files[0],x.files[0].name,fileExt1);
        }
    });


    $("#idshowfilesoporte").click(function() {

             $('#inputSoporteFile01').click();
    });


    $("#btnfinalizarchat").click(function() {


        (async () => {

                 const docRefasig = doc(db, "asignacionsoportepersona", idasginacionseleccionada);
                  // Set del asignacionsoportepersona
                 updateDoc(docRefasig, {
                      finalizado: true

                 });

                 const docSnapasignacion = await getDoc(docRefasig);
                 idlistaverpersonaasignada.innerHTML='';
                 llenarpersonaasignadasoporte(docSnapasignacion.data().idsoporte);



        })().then(function () {
                $("#id_messagesoporte").val("El soporte asignado finalizo el chat");
                 enviarmensajeSoporte();
                $("#id_messagesoporte").val("");
                detallechatsala.innerHTML="";
                seccionchatdetail.style.display = "none";


        })
    });

    $(window).on('load', function () {

        (async () => {
             try {

                 const querySnapshot= await getDocs(getSoporte($("#lblcorreo").html()))
                 if (parseInt(querySnapshot.docs.length)>0) {

                     querySnapshot.forEach((docsoporte) => {
                        // doc.data() is never undefined for query doc snapshots
                        if(docsoporte.data().estado==true) {
                            /// cargue los chat asignado a el
                            idsoporteatiende = docsoporte.id;
                            nomsoporteantiende = docsoporte.data().nombre;
                            llenarpersonaasignadasoporte(docsoporte.id);
                             swal("! Inicio Session", "Inicio de Sesión exitoso", "success");
                             btncerrarsesion.style.display = "block";
                             btninciarseccion.style.display = "none";

                        }

                      });
                 }

             }catch (error) {

                  swal("Error", String(error), "error");
             }
      })()

    });










