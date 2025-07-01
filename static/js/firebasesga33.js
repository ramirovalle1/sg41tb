  // Import the functions you need from the SDKs you need
  import { initializeApp } from "https://www.gstatic.com/firebasejs/9.15.0/firebase-app.js";

  import { idpersonalogin } from "./conexion_firebasesga33.js"


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


  export const GuardarSoporte=(estado,nombre,correo,sexo)=>{
      addDoc(collection(db,'soporte'),{estado:estado,nombre:nombre,correo:correo,sexo:sexo})
  }

  export const GuardarAsignacionSoportePersona=(idsoporte,nombresoporte,idpersona,nombrepersona,fechaasigancion,estado,finalizado)=>{
    addDoc(collection(db,'asignacionsoportepersona'),{idsoporte:idsoporte,nombresoporte:nombresoporte,idpersona:idpersona,nombrepersona:nombrepersona,fechaasigancion:fechaasigancion,estado:estado,finalizado:finalizado})
  }


  export const getSoporte=(email) => query(collection(db, "soporte"), where("correo", "==",email))

  export const getSoporteActivo=()=>  query(collection(db, "soporte"),where("estado", "==",true))

  export const getSoportePersonaFecha=(fechasignacion,idpersona)=>  query(collection(db, "asignacionsoportepersona"),where("fechaasigancion", "==",fechasignacion),where("idpersona", "==",idpersona))

  export const getSoportePersonaFechaOtro=(fechasignacion,idpersona)=>  query(collection(db, "asignacionsoportepersona"),where("fechaasigancion", "==",fechasignacion),where("idpersona", "==",idpersona),where("finalizado", "==",false))

  export const getSoportePersonaFechaSoporte=(idpersona)=>  query(collection(db, "asignacionsoportepersona"),where("idpersona", "==",idpersona),where("finalizado", "==",false))

  export const getPersona=(email) => query(collection(db, "persona"), where("correo", "==",email))

  export const getMensajeporPersona=(idpersonalogin,idasignacionsoporte) => query(collection(db, "mensaje"),orderBy("fechaparaordenar","asc" ), where("idpersona", "==",idpersonalogin),where("idasignacion", "==",idasignacionsoporte))

  export const getMensajeEnviadoSoporte=(idsoporte,idpersona,idasignacionsoporte)=> query(collection(db, "mensaje"),orderBy("fechaparaordenar","asc" ), where("idsoporte", "==",idsoporte),where("idpersona", "==",idpersona),where("idasignacion", "==",idasignacionsoporte))

  export const getMensajeEnviadoSoporteNoLeidos=(idsoporte)=> query(collection(db, "mensaje"),orderBy("fechaparaordenar","asc" ), where("idsoporte", "==",idsoporte),where("enviopersona", "==",true),where("leido", "==",false))

  export const getMensajeEnviadoPersonaNoLeidos=(idpersona,idasignacionsoporte)=> query(collection(db, "mensaje"),orderBy("fechaparaordenar","asc" ), where("idpersona", "==",idpersona),where("idasignacion", "==",idasignacionsoporte),where("enviosoporte", "==",true),where("leido", "==",false))

  export const getPersonasAsignadaSoporte=(idsoporte) => query(collection(db, "asignacionsoportepersona"), where("idsoporte", "==",idsoporte),where("finalizado", "==",false))

  export const getPersonasAsignadaSoportePersona=(idsoporte,idpersona) => query(collection(db, "asignacionsoportepersona"), where("idsoporte", "==",idsoporte),where("idpersona", "==",idpersona),where("finalizado", "==",false))

   export const getMensajeEnviadoPersonaNoLeidosSalida=(idpersona,idasignacionsoporte)=> query(collection(db, "mensaje"),orderBy("fechaparaordenar","asc" ), where("idpersona", "==",idpersona),where("idasignacion", "==",idasignacionsoporte),where("leido", "==",false))


  function salirpersona() {
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

                            $("#cierre_session_chat").modal({backdrop: 'static', keyboard: false});
                            $('#content-session_chat').html('<div class="loading" style="border: 0px solid #ccc;padding: 0 1rem;margin: 1rem;top:30%"><img src="../ube/static/imagen/loader.gif"/><br/> Cerrando el chat espere un momento...</div>');



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

                                            salirpersona();

                                        })

                                    })

                                });
                            }else{

                               salirpersona();
                            }
                    })()

                }else{
                    salirpersona();

                }
            })
        }else{
             salirpersona();
        }



    });