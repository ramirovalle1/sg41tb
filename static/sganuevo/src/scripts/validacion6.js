


function cambiarTab(tab, div) {
         $("#tabpanelpostucacion a").removeClass('active');
         $("#tabpanelcontenido div").removeClass('active');
         $('#' + tab).addClass('tab-pane fade show active');
         $('#' + div).addClass('tab-pane fade show active');
}



function limpiarInformacion() {
    $("#cmbidentificacion").val(0);
    $('#cmbidentificacion').trigger('change.select2');
    $("#cmbsexo").val(0);
    $('#cmbsexo').trigger('change.select2');
    $("#cmbprovincianacimientodatoscontacto").val(0);
    $('#cmbprovincianacimientodatoscontacto').trigger('change.select2');
    $("#txtnombres").val("");
    $("#txtapellidopaterno").val("");
    $("#txtapellidomaterno").val("");
     $("#cmbprovincianacimientodatoscontacto").val(0);
    $('#cmbprovincianacimientodatoscontacto').trigger('change.select2');



}


function limpiar() {

         $("#helpcmbidentificacion").html("");
         $("#helptxtidentificacion").html("");
         $("#helptxtnombres").html("");
         $("#helptxtapellidopaterno").html("");
         $("#helptxtapellidomaterno").html("");
         $("#helptxtemail").html("");
         $("#helptxtemailalternativo").html("");
         $("#helpcmbtipodiscapacidad").html("");
         $("#helptxtporcentajediscapacidad").html("");
         $("#helpcmbprovincianacimientodatoscontacto").html("");
         $("#helpcmbciudadnacimientocontacto").html("");
         $("#helpcmbparroquianacimientocontacto").html("");
         $("#helpdtbfechanacimiento").html("");
         $("#helpcmbtiposangre").html("");
         $("#helpcmbestadocivil").html("");
         $("#helpcmbsexo").html("");
         $("#helptxttelefonodomicilio").html("");
         $("#helptxttelefonocelular").html("");
         $("#txttelefonodomicilio").unmask();


     }


     function limpiarEditar() {

         $("#helpcmbidentificacionedit").html("");
         $("#helptxtidentificacionedit").html("");
         $("#helptxtnombresedit").html("");
         $("#helptxtapellidopaternoedit").html("");
         $("#helptxtapellidomaternoedit").html("");
         $("#helptxtemailedit").html("");
         $("#helptxtemailalternativoedit").html("");
         $("#helpcmbtipodiscapacidadedit").html("");
         $("#helptxtporcentajediscapacidadedit").html("");
         $("#helpcmbprovincianacimientodatoscontactoedit").html("");
         $("#helpcmbciudadnacimientocontactoedit").html("");
         $("#helpcmbparroquianacimientocontactoedit").html("");
         $("#helpdtbfechanacimientoedit").html("");
         $("#helpcmbtiposangreedit").html("");
         $("#helpcmbestadociviledit").html("");
         $("#helpcmbsexoedit").html("");
         $("#helptxttelefonodomicilioedit").html("");
         $("#helptxttelefonocelularedit").html("");
         $("#txttelefonodomicilioedit").unmask();
         $("#txttelefonodomicilioedit").unmask();


     }


function validarCedula(numerocedula, val) {

         if (val == 2) {
             return 0;
         } else {
             var cad = numerocedula;
             var total = 0;
             var longitud = cad.length;
             var longcheck = longitud - 1;

             if (cad !== "" && longitud === 10) {
                 for (i = 0; i < longcheck; i++) {
                     if (i % 2 === 0) {
                         var aux = cad.charAt(i) * 2;
                         if (aux > 9) aux -= 9;
                         total += aux;
                     } else {
                         total += parseInt(cad.charAt(i)); // parseInt o concatenará en lugar de sumar
                     }
                 }

                 total = total % 10 ? 10 - total % 10 : 0;
                 if (cad.charAt(longitud - 1) == total) {
                     return 0;
                 } else {
                     return 1;
                 }
             }
         }

     }


var myarea = [ '02', '03', '06', '04', '05', '07' ];

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


 soloNumeros = function (e) {
         var key = window.Event ? e.which : e.keyCode
         return (key >= 48 && key <= 57)
     }

 soloNumeros2 = function (evt) {
     var nav4 = window.Event ? true : false;
     var key = nav4 ? evt.which : evt.keyCode;
     return (key <= 13 || key == 46 || (key >= 38 && key <= 57));

 }



function validarDatos() {


         /****** Datos Personales *////
         if ($("#cmbidentificacion").val() == 0) {
             $("#helpcmbidentificacion").html("Seleccionar el Tipo Identificación");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }
         if ($("#txtidentificacion").val() == "") {
             $("#helptxtidentificacion").html("Debe Ingresar la Identificación");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if (validarCedula($("#txtidentificacion").val(), $("#cmbidentificacion").val()) != 0) {
             $("#helptxtidentificacion").html("Número de Cédula Incorrecta");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

          if ($("#cmbsexo").val() == 0) {
             $("#helpcmbsexo").html("Seleccionar el sexo");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }




         if ($("#txtnombres").val() == "") {
             $("#helptxtnombres").html("Debe Ingresar los nombres");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }
         if ($("#txtapellidopaterno").val() == "") {
             $("#helptxtapellidopaterno").html("Debe Ingresar los apellidos paternos");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#txtapellidomaterno").val() == "") {
             $("#helptxtapellidomaterno").html("Debe Ingresar los apellidos maternos");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }


          if ($("#cmbprovincianacimientodatoscontacto").val() == 0) {
             $("#helpcmbprovincianacimientodatoscontacto").html("Seleccionar la provincia de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#dtbfechanacimiento").val() == "") {
             $("#helpdtbfechanacimiento").html("Debe Ingresar la fecha de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#cmbciudadnacimientocontacto").val() == 0) {
             $("#helpcmbciudadnacimientocontacto").html("Seleccionar la ciudad de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#cmbparroquianacimientocontacto").val() == 0) {
             $("#helpcmbparroquianacimientocontacto").html("Seleccionar la parroquia de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }




         // if ($("#cmbtiposangre").val() == 0) {
         //     $("#helpcmbtiposangre").html("Seleccionar el tipo de sangre");
         //     cambiarTab('base-tab1', 'datospersonales');
         //     return 1;
         // }
         //
         // if ($("#cmbestadocivil").val() == 0) {
         //     $("#helpcmbestadocivil").html("Seleccionar el estado civil");
         //     cambiarTab('base-tab1', 'datospersonales');
         //     return 1;
         // }



         /****** Datos Domicilio Contacto *////

        if ($("#txtemail").val() == "") {
             $("#helptxtemail").html("Debe Ingresar el email");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

          if (validarEmail($("#txtemail").val())!=0) {
            $("#helptxtemail").html("Formato del Correo Incorrecto");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
          }




         // if ($("#txtemailalternativo").val() == "") {
         //     $("#helptxtemailalternativo").html("Debe Ingresar el email alternativo");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         // if (validarEmail($("#txtemailalternativo").val())!=0) {
         //    $("#helptxtemailalternativo").html("Formato del Correo Incorrecto");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         //  }



         // if ($("#txttelefonodomicilio").val() == "") {
         //     $("#helptxttelefonodomicilio").html("Debe Ingresar el nùmero de telèfono");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         //
         //
         // if (myarea.includes($("#txttelefonodomicilio").val().substr(0,2))==false) {
         //     $("#helptxttelefonodomicilio").html("No existe el código de área para el número de domicilio");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         // if ( parseInt($("#txttelefonodomicilio").val().length) != parseInt("9")) {
         //     $("#helptxttelefonodomicilio").html("El número telèfono debe contener 9 números");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         //
         //
         // $("#txttelefonodomicilio").mask("(00)-0000000");
         //
         // if ($("#txttelefonocelular").val() == "") {
         //     $("#helptxttelefonocelular").html("Debe Ingresar el nùmero de celular");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         // if ( parseInt($("#txttelefonocelular").val().length) != parseInt("10")) {
         //     $("#helptxttelefonocelular").html("El número celular debe contener 10 números");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         //
         //
         // if ( parseInt($("#txttelefonocelular").val().substr(0,1)) != parseInt("0")) {
         //     $("#helptxttelefonocelular").html("El número celular esta incorrecto");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }





         if (document.getElementById("chkdiscapacidad").checked == true) {

             if ($("#cmbtipodiscapacidad").val() == 0) {
                 $("#helpcmbtipodiscapacidad").html("Debe Ingresar el tipo discapacidad");
                 cambiarTab('base-tab3', 'datodiscapacidad');
                 return 1;
             }

             if ($("#txtporcentajediscapacidad").val() == "0" || $("#txtporcentajediscapacidad").val() == "") {
                 $("#helptxtporcentajediscapacidad").html("El porcentaje de discapacidad debe ser mayor a 0");
                 cambiarTab('base-tab3', 'datodiscapacidad');
                 return 1;
             }


         }










        return 0;

     }




function validarDatosEditar() {


         /****** Datos Personales *////
         if ($("#cmbidentificacionedit").val() == 0) {
             $("#helpcmbidentificacionedit").html("Seleccionar el Tipo Identificación");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }
         if ($("#txtidentificacionedit").val() == "") {
             $("#helptxtidentificacionedit").html("Debe Ingresar la Identificación");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if (validarCedula($("#txtidentificacionedit").val(), $("#cmbidentificacionedit").val()) != 0) {
             $("#helptxtidentificacionedit").html("Número de Cédula Incorrecta");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

          if ($("#cmbsexoedit").val() == 0) {
             $("#helpcmbsexoedit").html("Seleccionar el sexo");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }




         if ($("#txtnombresedit").val() == "") {
             $("#helptxtnombresedit").html("Debe Ingresar los nombres");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }
         if ($("#txtapellidopaternoedit").val() == "") {
             $("#helptxtapellidopaternoedit").html("Debe Ingresar los apellidos paternos");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#txtapellidomaterno").val() == "") {
             $("#helptxtapellidomaterno").html("Debe Ingresar los apellidos maternos");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }


          if ($("#cmbprovincianacimientodatoscontacto").val() == 0) {
             $("#helpcmbprovincianacimientodatoscontacto").html("Seleccionar la provincia de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#dtbfechanacimientoedit").val() == "") {
             $("#helpdtbfechanacimientoedit").html("Debe Ingresar la fecha de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#cmbciudadnacimientocontactoedit").val() == 0) {
             $("#helpcmbciudadnacimientocontactoedit").html("Seleccionar la ciudad de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#cmbparroquianacimientocontactoedit").val() == 0) {
             $("#helpcmbparroquianacimientocontactoedit").html("Seleccionar la parroquia de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }




         // if ($("#cmbtiposangre").val() == 0) {
         //     $("#helpcmbtiposangre").html("Seleccionar el tipo de sangre");
         //     cambiarTab('base-tab1', 'datospersonales');
         //     return 1;
         // }
         //
         // if ($("#cmbestadocivil").val() == 0) {
         //     $("#helpcmbestadocivil").html("Seleccionar el estado civil");
         //     cambiarTab('base-tab1', 'datospersonales');
         //     return 1;
         // }



         /****** Datos Domicilio Contacto *////

        if ($("#txtemailedit").val() == "") {
             $("#helptxtemailedit").html("Debe Ingresar el email");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

          if (validarEmail($("#txtemailedit").val())!=0) {
            $("#helptxtemailedit").html("Formato del Correo Incorrecto");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
          }




         // if ($("#txtemailalternativo").val() == "") {
         //     $("#helptxtemailalternativo").html("Debe Ingresar el email alternativo");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         // if (validarEmail($("#txtemailalternativo").val())!=0) {
         //    $("#helptxtemailalternativo").html("Formato del Correo Incorrecto");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         //  }



         // if ($("#txttelefonodomicilio").val() == "") {
         //     $("#helptxttelefonodomicilio").html("Debe Ingresar el nùmero de telèfono");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         //
         //
         // if (myarea.includes($("#txttelefonodomicilio").val().substr(0,2))==false) {
         //     $("#helptxttelefonodomicilio").html("No existe el código de área para el número de domicilio");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         // if ( parseInt($("#txttelefonodomicilio").val().length) != parseInt("9")) {
         //     $("#helptxttelefonodomicilio").html("El número telèfono debe contener 9 números");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         //
         //
         // $("#txttelefonodomicilio").mask("(00)-0000000");
         //
         // if ($("#txttelefonocelular").val() == "") {
         //     $("#helptxttelefonocelular").html("Debe Ingresar el nùmero de celular");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         // if ( parseInt($("#txttelefonocelular").val().length) != parseInt("10")) {
         //     $("#helptxttelefonocelular").html("El número celular debe contener 10 números");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }
         //
         //
         //
         // if ( parseInt($("#txttelefonocelular").val().substr(0,1)) != parseInt("0")) {
         //     $("#helptxttelefonocelular").html("El número celular esta incorrecto");
         //     cambiarTab('base-tab2', 'datoscontactos');
         //     return 1;
         // }





         if (document.getElementById("chkdiscapacidadedit").checked == true) {

             if ($("#cmbtipodiscapacidadedit").val() == 0) {
                 $("#helpcmbtipodiscapacidadedit").html("Debe Ingresar el tipo discapacidad");
                 cambiarTab('base-tab3', 'datodiscapacidad');
                 return 1;
             }

             if ($("#txtporcentajediscapacidadedit").val() == "0" || $("#txtporcentajediscapacidadedit").val() == "") {
                 $("#helptxtporcentajediscapacidadedit").html("El porcentaje de discapacidad debe ser mayor a 0");
                 cambiarTab('base-tab3', 'datodiscapacidad');
                 return 1;
             }


         }










        return 0;

     }


function validarDatosEditar2(validaedicion) {


        $("#txttelefonodomicilioedit").unmask();

        $("#txttelefonocelularedit").unmask();

         /****** Datos Personales *////
         if ($("#cmbidentificacionedit").val() == 0) {
             $("#helpcmbidentificacionedit").html("Seleccionar el Tipo Identificación");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }
         if ($("#txtidentificacionedit").val() == "") {
             $("#helptxtidentificacionedit").html("Debe Ingresar la Identificación");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if (validarCedula($("#txtidentificacionedit").val(), $("#cmbidentificacionedit").val()) != 0) {
             $("#helptxtidentificacionedit").html("Número de Cédula Incorrecta");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

          if ($("#cmbsexoedit").val() == 0) {
             $("#helpcmbsexoedit").html("Seleccionar el sexo");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }




         if ($("#txtnombresedit").val() == "") {
             $("#helptxtnombresedit").html("Debe Ingresar los nombres");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }
         if ($("#txtapellidopaternoedit").val() == "") {
             $("#helptxtapellidopaternoedit").html("Debe Ingresar los apellidos paternos");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#txtapellidomaterno").val() == "") {
             $("#helptxtapellidomaterno").html("Debe Ingresar los apellidos maternos");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }


          if ($("#cmbprovincianacimientodatoscontacto").val() == 0) {
             $("#helpcmbprovincianacimientodatoscontacto").html("Seleccionar la provincia de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#dtbfechanacimientoedit").val() == "") {
             $("#helpdtbfechanacimientoedit").html("Debe Ingresar la fecha de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#cmbciudadnacimientocontactoedit").val() == 0) {
             $("#helpcmbciudadnacimientocontactoedit").html("Seleccionar la ciudad de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#cmbparroquianacimientocontactoedit").val() == 0) {
             $("#helpcmbparroquianacimientocontactoedit").html("Seleccionar la parroquia de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }


         if( parseInt(validaedicion) == 1) {

             if ($("#cmbtiposangreedit").val() == 0) {
                 $("#helpcmbtiposangreedit").html("Seleccionar el tipo de sangre");
                 cambiarTab('base-tab1', 'datospersonales');
                 return 1;
             }

             if ($("#cmbestadociviledit").val() == 0) {
                 $("#helpcmbestadociviledit").html("Seleccionar el estado civil");
                 cambiarTab('base-tab1', 'datospersonales');
                 return 1;
             }

         }




         /****** Datos Domicilio Contacto *////

        if ($("#txtemailedit").val() == "") {
             $("#helptxtemailedit").html("Debe Ingresar el email");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

          if (validarEmail($("#txtemailedit").val())!=0) {
            $("#helptxtemailedit").html("Formato del Correo Incorrecto");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
          }


        if( parseInt(validaedicion) == 1) {

            if ($("#txtemailalternativo").val() == "") {
                $("#helptxtemailalternativo").html("Debe Ingresar el email alternativo");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }

            if (validarEmail($("#txtemailalternativo").val()) != 0) {
                $("#helptxtemailalternativo").html("Formato del Correo Incorrecto");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }


            if ($("#txttelefonodomicilioedit").val() == "") {
                $("#helptxttelefonodomicilioedit").html("Debe Ingresar el nùmero de telèfono");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }


            if (myarea.includes($("#txttelefonodomicilioedit").val().substr(0, 2)) == false) {
                $("#helptxttelefonodomicilioedit").html("No existe el código de área para el número de domicilio");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }

            if (parseInt($("#txttelefonodomicilioedit").val().length) != parseInt("9")) {
                $("#helptxttelefonodomicilioedit").html("El número telèfono debe contener 9 números");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }


            $("#txttelefonodomicilioedit").mask("(00)-0000000");

            if ($("#txttelefonocelularedit").val() == "") {
                $("#helptxttelefonocelularedit").html("Debe Ingresar el nùmero de celular");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }

            if (parseInt($("#txttelefonocelularedit").val().length) != parseInt("10")) {
                $("#helptxttelefonocelularedit").html("El número celular debe contener 10 números");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }


            if (parseInt($("#txttelefonocelularedit").val().substr(0, 1)) != parseInt("0")) {
                $("#helptxttelefonocelularedit").html("El número celular esta incorrecto");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }
        }





         if (document.getElementById("chkdiscapacidadedit").checked == true) {

             if ($("#cmbtipodiscapacidadedit").val() == 0) {
                 $("#helpcmbtipodiscapacidadedit").html("Debe Ingresar el tipo discapacidad");
                 cambiarTab('base-tab3', 'datodiscapacidad');
                 return 1;
             }

             if ($("#txtporcentajediscapacidadedit").val() == "0" || $("#txtporcentajediscapacidadedit").val() == "") {
                 $("#helptxtporcentajediscapacidadedit").html("El porcentaje de discapacidad debe ser mayor a 0");
                 cambiarTab('base-tab3', 'datodiscapacidad');
                 return 1;
             }


         }










        return 0;

     }



     function limpiarperfilarPerfil() {

         $("#helpcmbidentificacionperfil").html("");
         $("#helptxtidentificacionperfil").html("");
         $("#helptxtnombresperfil").html("");
         $("#helptxtapellidopaternoperfil").html("");
         $("#helptxtapellidomaternoperfil").html("");
         $("#helptxtemailperfil").html("");
         $("#helptxtemailalternativoperfil").html("");
         $("#helpcmbtipodiscapacidadperfil").html("");
         $("#helptxtporcentajediscapacidadperfil").html("");
         $("#helpcmbprovincianacimientoperfil").html("");
         $("#helpcmbciudadnacimientocontactoperfil").html("");
         $("#helpcmbparroquianacimientocontactoperfil").html("");
         $("#helpdtbfechanacimientoperfil").html("");
         $("#helpcmbtiposangreperfil").html("");
         $("#helpcmbestadocivilperfil").html("");
         $("#helpcmbsexoperfil").html("");
         $("#helptxttelefonodomicilioperfil").html("");
         $("#helptxttelefonocelularperfil").html("");
         $("#txttelefonodomicilioperfil").unmask();
         $("#txttelefonodomicilioperfil").unmask();


     }



     function validarDatosperfilarPerfil(validaedicion) {


        $("#txttelefonodomicilioperfil").unmask();

        $("#txttelefonocelularperfil").unmask();

         /****** Datos Personales *////
         if ($("#cmbidentificacionperfil").val() == 0) {
             $("#helpcmbidentificacionperfil").html("Seleccionar el Tipo Identificación");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }
         if ($("#txtidentificacionperfil").val() == "") {
             $("#helptxtidentificacionperfil").html("Debe Ingresar la Identificación");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if (validarCedula($("#txtidentificacionperfil").val(), $("#cmbidentificacionperfil").val()) != 0) {
             $("#helptxtidentificacionperfil").html("Número de Cédula Incorrecta");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

          if ($("#cmbsexoperfil").val() == 0) {
             $("#helpcmbsexoperfil").html("Seleccionar el sexo");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }




         if ($("#txtnombresperfil").val() == "") {
             $("#helptxtnombresperfil").html("Debe Ingresar los nombres");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }
         if ($("#txtapellidopaternoperfil").val() == "") {
             $("#helptxtapellidopaternoperfil").html("Debe Ingresar los apellidos paternos");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#txtapellidomaterno").val() == "") {
             $("#helptxtapellidomaterno").html("Debe Ingresar los apellidos maternos");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }


          if ($("#cmbprovincianacimientodatosperfil").val() == 0) {
             $("#helpcmbprovincianacimientoperfil").html("Seleccionar la provincia de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#dtbfechanacimientoperfil").val() == "") {
             $("#helpdtbfechanacimientoperfil").html("Debe Ingresar la fecha de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#cmbciudadnacimientocontactoperfil").val() == 0) {
             $("#helpcmbciudadnacimientocontactoperfil").html("Seleccionar la ciudad de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#cmbparroquianacimientocontactoperfil").val() == 0) {
             $("#helpcmbparroquianacimientocontactoperfil").html("Seleccionar la parroquia de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }


         if( parseInt(validaedicion) == 1) {

             if ($("#cmbtiposangreperfil").val() == 0) {
                 $("#helpcmbtiposangreperfil").html("Seleccionar el tipo de sangre");
                 cambiarTab('base-tab1', 'datospersonales');
                 return 1;
             }

             if ($("#cmbestadocivilperfil").val() == 0) {
                 $("#helpcmbestadocivilperfil").html("Seleccionar el estado civil");
                 cambiarTab('base-tab1', 'datospersonales');
                 return 1;
             }

         }




         /****** Datos Domicilio Contacto *////

        if ($("#txtemailperfil").val() == "") {
             $("#helptxtemailperfil").html("Debe Ingresar el email");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

          if (validarEmail($("#txtemailperfil").val())!=0) {
            $("#helptxtemailperfil").html("Formato del Correo Incorrecto");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
          }


        if( parseInt(validaedicion) == 1) {

            if ($("#txtemailalternativo").val() == "") {
                $("#helptxtemailalternativo").html("Debe Ingresar el email alternativo");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }

            if (validarEmail($("#txtemailalternativo").val()) != 0) {
                $("#helptxtemailalternativo").html("Formato del Correo Incorrecto");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }


            if ($("#txttelefonodomicilioperfil").val() == "") {
                $("#helptxttelefonodomicilioperfil").html("Debe Ingresar el nùmero de telèfono");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }


            if (myarea.includes($("#txttelefonodomicilioperfil").val().substr(0, 2)) == false) {
                $("#helptxttelefonodomicilioperfil").html("No existe el código de área para el número de domicilio");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }

            if (parseInt($("#txttelefonodomicilioperfil").val().length) != parseInt("9")) {
                $("#helptxttelefonodomicilioperfil").html("El número telèfono debe contener 9 números");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }


            $("#txttelefonodomicilioperfil").mask("(00)-0000000");

            if ($("#txttelefonocelularperfil").val() == "") {
                $("#helptxttelefonocelularperfil").html("Debe Ingresar el nùmero de celular");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }

            if (parseInt($("#txttelefonocelularperfil").val().length) != parseInt("10")) {
                $("#helptxttelefonocelularperfil").html("El número celular debe contener 10 números");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }


            if (parseInt($("#txttelefonocelularperfil").val().substr(0, 1)) != parseInt("0")) {
                $("#helptxttelefonocelularperfil").html("El número celular esta incorrecto");
                cambiarTab('base-tab2', 'datoscontactos');
                return 1;
            }
        }





         if (document.getElementById("chkdiscapacidadperfil").checked == true) {

             if ($("#cmbtipodiscapacidadperfil").val() == 0) {
                 $("#helpcmbtipodiscapacidadperfil").html("Debe Ingresar el tipo discapacidad");
                 cambiarTab('base-tab3', 'datodiscapacidad');
                 return 1;
             }

             if ($("#txtporcentajediscapacidadperfil").val() == "0" || $("#txtporcentajediscapacidadperfil").val() == "") {
                 $("#helptxtporcentajediscapacidadperfil").html("El porcentaje de discapacidad debe ser mayor a 0");
                 cambiarTab('base-tab3', 'datodiscapacidad');
                 return 1;
             }


         }










        return 0;

     }
