$(document).ready(function() {
     // $('.formdynamics').off('click.conectar_modaldynamics').bind('click.conectar_modaldynamics', conectar_modaldynamics);
    $('.formdynamics').bind('click.conectar_modaldynamics', conectar_modaldynamics);
    $('.confirmacionmodal').bind('click.conectar_confirmacion', conectar_confirmacion);
    $('.viewhtml').bind('click.conectar_modaldynamics', conectar_modaldynamics);
    $('.eliminacionmodal').bind('click.conectar_modaldynamics', conectar_modaldynamics);

    cerrar_viewhtml = function () {
        $("#viewhtml").modal("hide");
    };

    tipo_formulario = function (elemento) {
                if (elemento.attr('formtype') == 'form-vertical') {
                    elemento.find(".control-label").css({'float': 'none'});
                    elemento.find(".label-text").css({'text-align': 'left'});
                    elemento.find(".control-label").each(function () {
                        var contenedor = parseFloat($(this).parent().css('width')) - 5;
                        $(this).css({'width': contenedor.toString() + 'px'});
                    });
                    elemento.find(".control").each(function () {
                        var contenedor = parseFloat($(this).parent().css('width')) - 5;
                        $(this).css({'width': contenedor.toString() + 'px'});
                    });
                } else {
                    elemento.find(".control-label").css({'float': 'left'});
                    elemento.find(".label-text").css({'text-align': 'right'});
                    if (elemento.hasClass('form-modal')) {
                        elemento.find(".control-group").each(function () {
                            var contenedor = parseFloat($(this).parent().width());
                            var porciento = (parseFloat($(this).width()) / 100);
                            var tam = parseInt(contenedor * porciento);
                            $(this).css({'width': tam});
                        });
                    }
                    elemento.find(".control-label").each(function () {
                        if ($(this).attr('labelwidth')) {
                            $(this).css({'width': $(this).attr('labelwidth')});
                        } else {
                            $(this).css({'width': '150px'});
                        }
                    });
                    elemento.find(".control").each(function () {
                        var contenedor = $(this).parent().width();
                        var label = parseFloat($(this).parent().find('.control-label').width());
                        $(this).css({'width': ((contenedor - label) - 20).toString() + 'px'});
                    });
                }
                elemento.find(".select2").css({'width': '100%'});
            };
});


function abrirnotificacionmodal(texto, titulo = '', habilitarcerrar = true, obligatoria = false, icono = "fa fa-warning", coloricono = "goldenrod", tamanomodal = '600') {
    if (titulo.length > 0) {
        $(".titulonotificacionmodal").html(titulo);
    }
    if (habilitarcerrar) {
        $('.notificacionmodal').find(".modal-footer").show();
    } else {
        $('.notificacionmodal').find(".modal-footer").hide();
    }
    $("#icononotificacion").addClass(icono);
    document.getElementById('icononotificacion').style.color = coloricono;
    $(".cuerponotificacionmodal").html(texto);
    if (obligatoria) {
        datamodal = {'backdrop': 'static', keyboard: false, 'width': tamanomodal}
    } else {
        datamodal = {'backdrop': 'static', 'width': tamanomodal}
    }
    $('.notificacionmodal').modal(datamodal).modal('show');
    $(".cerrarnotificacionmodal").on('click', cerrarnotificacionmodal);
}

function cerrarnotificacionmodal() {
    $(".notificacionmodal").modal("hide");
}
function conectar_modaldynamics() {
    var href = $(this).attr('nhref');
    $.ajax({
        type: "GET",
        url: href,
        success: function (data) {
            // $.unblockUI();
            if (data.search('"' + 'ajaxformdynamics' + '"') >= 0) {
                $(".ajaxformdynamics").html(data);
                $('.ajaxformdynamics').modal({backdrop: 'static', 'width': '800'}).modal('show');
            } else {
                if (data.search('"' + 'ajaxconfirmaciondinamicbs' + '"') >= 0) {
                    $("#viewhtml").html(data);
                    $('#viewhtml').modal({'width': '650'}).modal('show');
                    $('.cerrarviewhtml').bind('click.cerrar_viewhtml', cerrar_viewhtml);
                } else {
                    if (data.search('"' + 'ajaxdeletedinamicbs' + '"') >= 0) {
                        $("#eliminacionmodal").html(data);
                        $('#eliminacionmodal').modal({'width': '650'}).modal('show');
                    } else {
                        abrirnotificacionmodal('Error de conexión.');
                    }
                }
            }
        },
        error: function () {
            $.unblockUI();
            abrirnotificacionmodal('Error de conexión.');
        },
        dataType: "html"
    });
}

function showWaiting(titulo, mensaje, close) {
    var panel = $("#waitpanel");
    $("#waitpaneltitle").html(titulo);
    $("#waitpanelbody").html(mensaje);
    if (!close) {
        panel.modal({keyboard: false, backdrop: 'static'});
    }
    panel.modal("show");
}

function hideWaiting() {
    $("#waitpanel").modal("hide");
}

function conectar_confirmacion() {
    var href = $(this).attr('nhref');
    $.ajax({
        type: "GET",
        url: href,
        success: function (data) {
            $.unblockUI();
            if (data.search('"' + 'ajaxconfirmaciondinamicbs' + '"') >= 0) {
                $("#confirmacionmodal").html(data);
                $('#confirmacionmodal').modal({'width': '650'}).modal('show');
            } else {
                abrirnotificacionmodal('Error de conexión.');
            }
        },
        error: function () {
            $.unblockUI();
            abrirnotificacionmodal('Error de conexión.');
        },
        dataType: "html"
    });
}
