
function DetalleRecurso(action, ids, id) {
    $.get("{{ request.path }}", {'action': action, 'ids': ids, 'id': id}, function (data) {
        if (data.result === 'ok') {
            $.unblockUI();
            $(".paneltitle").html(data.title);
            $(".panelbodyRecurso").html(data.html);
            $(".detalleRecurso").modal({backdrop: 'static', width: '1000px'}).modal('show');
            $(".detalleRecurso").modal("show").off('shown.bs.modal').on('shown.bs.modal', function () {
                $(".cerrarrecurso_modal").off('click').on('click', function () {
                    $(this).closest('.modal').modal('hide');
                });
            });
        }
    }, 'json');
}