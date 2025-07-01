/*! 
 * jQuery Steps v1.1.0 - 09/04/2014
 * Copyright (c) 2014 Rafael Staib (http://www.jquery-steps.com)
 * Licensed under MIT http://www.opensource.org/licenses/MIT
 */
;(function ($, undefined)
{
$.fn.extend({
    _aria: function (name, value)
    {
        return this.attr("aria-" + name, value);
    },

    _removeAria: function (name)
    {
        return this.removeAttr("aria-" + name);
    },

    _enableAria: function (enable)
    {
        return (enable == null || enable) ? 
            this.removeClass("disabled")._aria("disabled", "false") : 
            this.addClass("disabled")._aria("disabled", "true");
    },

    _showAria: function (show)
    {
        return (show == null || show) ? 
            this.show()._aria("hidden", "false") : 
            this.hide()._aria("hidden", "true");
    },

    _selectAria: function (select)
    {
        return (select == null || select) ? 
            this.addClass("current")._aria("selected", "true") : 
            this.removeClass("current")._aria("selected", "false");
    },

    _id: function (id)
    {
        return (id) ? this.attr("id", id) : this.attr("id");
    }
});

if (!String.prototype.format)
{
    String.prototype.format = function()
    {
        var args = (arguments.length === 1 && $.isArray(arguments[0])) ? arguments[0] : arguments;
        var formattedString = this;
        for (var i = 0; i < args.length; i++)
        {
            var pattern = new RegExp("\\{" + i + "\\}", "gm");
            formattedString = formattedString.replace(pattern, args[i]);
        }
        return formattedString;
    };
}

/**
 * A global unique id count.
 *
 * @static
 * @private
 * @property _uniqueId
 * @type Integer
 **/
var _uniqueId = 0;

/**
 * The plugin prefix for cookies.
 *
 * @final
 * @private
 * @property _cookiePrefix
 * @type String
 **/
var _cookiePrefix = "jQu3ry_5teps_St@te_";

/**
 * Suffix for the unique tab id.
 *
 * @final
 * @private
 * @property _tabSuffix
 * @type String
 * @since 0.9.7
 **/
var _tabSuffix = "-t-";

/**
 * Suffix for the unique tabpanel id.
 *
 * @final
 * @private
 * @property _tabpanelSuffix
 * @type String
 * @since 0.9.7
 **/
var _tabpanelSuffix = "-p-";

/**
 * Suffix for the unique title id.
 *
 * @final
 * @private
 * @property _titleSuffix
 * @type String
 * @since 0.9.7
 **/
var _titleSuffix = "-h-";

/**
 * An error message for an "index out of range" error.
 *
 * @final
 * @private
 * @property _indexOutOfRangeErrorMessage
 * @type String
 **/
var _indexOutOfRangeErrorMessage = "Index out of range.";

/**
 * An error message for an "missing corresponding element" error.
 *
 * @final
 * @private
 * @property _missingCorrespondingElementErrorMessage
 * @type String
 **/
var _missingCorrespondingElementErrorMessage = "One or more corresponding step {0} are missing.";

/**
 * Adds a step to the cache.
 *
 * @static
 * @private
 * @method addStepToCache
 * @param wizard {Object} A jQuery wizard object
 * @param step {Object} The step object to add
 **/
function addStepToCache(wizard, step)
{
    getSteps(wizard).push(step);
}

function analyzeData(wizard, options, state)
{
    var stepTitles = wizard.children(options.headerTag),
        stepContents = wizard.children(options.bodyTag);

    // Validate content
    if (stepTitles.length > stepContents.length)
    {
        throwError(_missingCorrespondingElementErrorMessage, "contents");
    }
    else if (stepTitles.length < stepContents.length)
    {
        throwError(_missingCorrespondingElementErrorMessage, "titles");
    }
        
    var startIndex = options.startIndex;

    state.stepCount = stepTitles.length;

    // Tries to load the saved state (step position)
    if (options.saveState && $.cookie)
    {
        var savedState = $.cookie(_cookiePrefix + getUniqueId(wizard));
        // Sets the saved position to the start index if not undefined or out of range 
        var savedIndex = parseInt(savedState, 0);
        if (!isNaN(savedIndex) && savedIndex < state.stepCount)
        {
            startIndex = savedIndex;
        }
    }

    state.currentIndex = startIndex;

    stepTitles.each(function (index)
    {
        var item = $(this), // item == header
            content = stepContents.eq(index),
            modeData = content.data("mode"),
            mode = (modeData == null) ? contentMode.html : getValidEnumValue(contentMode,
                (/^\s*$/.test(modeData) || isNaN(modeData)) ? modeData : parseInt(modeData, 0)),
            contentUrl = (mode === contentMode.html || content.data("url") === undefined) ?
                "" : content.data("url"),
            contentLoaded = (mode !== contentMode.html && content.data("loaded") === "1"),
            step = $.extend({}, stepModel, {
                title: item.html(),
                content: (mode === contentMode.html) ? content.html() : "",
                contentUrl: contentUrl,
                contentMode: mode,
                contentLoaded: contentLoaded
            });

        addStepToCache(wizard, step);
    });
}

/**
 * Triggers the onCanceled event.
 *
 * @static
 * @private
 * @method cancel
 * @param wizard {Object} The jQuery wizard object
 **/
function cancel(wizard)
{
    wizard.triggerHandler("canceled");
}

function decreaseCurrentIndexBy(state, decreaseBy)
{
    return state.currentIndex - decreaseBy;
}

/**
 * Removes the control functionality completely and transforms the current state to the initial HTML structure.
 *
 * @static
 * @private
 * @method destroy
 * @param wizard {Object} A jQuery wizard object
 **/
function destroy(wizard, options)
{
    var eventNamespace = getEventNamespace(wizard);

    // Remove virtual data objects from the wizard
    wizard.unbind(eventNamespace).removeData("uid").removeData("options")
        .removeData("state").removeData("steps").removeData("eventNamespace")
        .find(".actions a").unbind(eventNamespace);

    // Remove attributes and CSS classes from the wizard
    wizard.removeClass(options.clearFixCssClass + " vertical");

    var contents = wizard.find(".content > *");

    // Remove virtual data objects from panels and their titles
    contents.removeData("loaded").removeData("mode").removeData("url");

    // Remove attributes, CSS classes and reset inline styles on all panels and their titles
    contents.removeAttr("id").removeAttr("role").removeAttr("tabindex")
        .removeAttr("class").removeAttr("style")._removeAria("labelledby")
        ._removeAria("hidden");

    // Empty panels if the mode is set to 'async' or 'iframe'
    wizard.find(".content > [data-mode='async'],.content > [data-mode='iframe']").empty();

    var wizardSubstitute = $("<{0} class=\"{1}\"></{0}>".format(wizard.get(0).tagName, wizard.attr("class")));

    var wizardId = wizard._id();
    if (wizardId != null && wizardId !== "")
    {
        wizardSubstitute._id(wizardId);
    }

    wizardSubstitute.html(wizard.find(".content").html());
    wizard.after(wizardSubstitute);
    wizard.remove();

    return wizardSubstitute;
}

/**
 * Triggers the onFinishing and onFinished event.
 *
 * @static
 * @private
 * @method finishStep
 * @param wizard {Object} The jQuery wizard object
 * @param state {Object} The state container of the current wizard
 **/
function finishStep(wizard, state)
{
    var currentStep = wizard.find(".steps li").eq(state.currentIndex);

    if (wizard.triggerHandler("finishing", [state.currentIndex]))
    {
        currentStep.addClass("done").removeClass("error");
        wizard.triggerHandler("finished", [state.currentIndex]);
    }
    else
    {
        currentStep.addClass("error");
    }
}

/**
 * Gets or creates if not exist an unique event namespace for the given wizard instance.
 *
 * @static
 * @private
 * @method getEventNamespace
 * @param wizard {Object} A jQuery wizard object
 * @return {String} Returns the unique event namespace for the given wizard
 */
function getEventNamespace(wizard)
{
    var eventNamespace = wizard.data("eventNamespace");

    if (eventNamespace == null)
    {
        eventNamespace = "." + getUniqueId(wizard);
        wizard.data("eventNamespace", eventNamespace);
    }

    return eventNamespace;
}

function getStepAnchor(wizard, index)
{
    var uniqueId = getUniqueId(wizard);

    return wizard.find("#" + uniqueId + _tabSuffix + index);
}

function getStepPanel(wizard, index)
{
    var uniqueId = getUniqueId(wizard);

    return wizard.find("#" + uniqueId + _tabpanelSuffix + index);
}

function getStepTitle(wizard, index)
{
    var uniqueId = getUniqueId(wizard);

    return wizard.find("#" + uniqueId + _titleSuffix + index);
}

function getOptions(wizard)
{
    return wizard.data("options");
}

function getState(wizard)
{
    return wizard.data("state");
}

function getSteps(wizard)
{
    return wizard.data("steps");
}

/**
 * Gets a specific step object by index.
 *
 * @static
 * @private
 * @method getStep
 * @param index {Integer} An integer that belongs to the position of a step
 * @return {Object} A specific step object
 **/
function getStep(wizard, index)
{
    var steps = getSteps(wizard);

    if (index < 0 || index >= steps.length)
    {
        throwError(_indexOutOfRangeErrorMessage);
    }

    return steps[index];
}

/**
 * Gets or creates if not exist an unique id from the given wizard instance.
 *
 * @static
 * @private
 * @method getUniqueId
 * @param wizard {Object} A jQuery wizard object
 * @return {String} Returns the unique id for the given wizard
 */
function getUniqueId(wizard)
{
    var uniqueId = wizard.data("uid");

    if (uniqueId == null)
    {
        uniqueId = wizard._id();
        if (uniqueId == null)
        {
            uniqueId = "steps-uid-".concat(_uniqueId);
            wizard._id(uniqueId);
        }

        _uniqueId++;
        wizard.data("uid", uniqueId);
    }

    return uniqueId;
}

/**
 * Gets a valid enum value by checking a specific enum key or value.
 * 
 * @static
 * @private
 * @method getValidEnumValue
 * @param enumType {Object} Type of enum
 * @param keyOrValue {Object} Key as `String` or value as `Integer` to check for
 */
function getValidEnumValue(enumType, keyOrValue)
{
    validateArgument("enumType", enumType);
    validateArgument("keyOrValue", keyOrValue);

    // Is key
    if (typeof keyOrValue === "string")
    {
        var value = enumType[keyOrValue];
        if (value === undefined)
        {
            throwError("The enum key '{0}' does not exist.", keyOrValue);
        }

        return value;
    }
    // Is value
    else if (typeof keyOrValue === "number")
    {
        for (var key in enumType)
        {
            if (enumType[key] === keyOrValue)
            {
                return keyOrValue;
            }
        }

        throwError("Invalid enum value '{0}'.", keyOrValue);
    }
    // Type is not supported
    else
    {
        throwError("Invalid key or value type.");
    }
}

/**
 * Routes to the next step.
 *
 * @static
 * @private
 * @method goToNextStep
 * @param wizard {Object} The jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 * @return {Boolean} Indicates whether the action executed
 **/
function goToNextStep(wizard, options, state)
{
    return paginationClick(wizard, options, state, increaseCurrentIndexBy(state, 1));
}

/**
 * Routes to the previous step.
 *
 * @static
 * @private
 * @method goToPreviousStep
 * @param wizard {Object} The jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 * @return {Boolean} Indicates whether the action executed
 **/
function goToPreviousStep(wizard, options, state)
{
    return paginationClick(wizard, options, state, decreaseCurrentIndexBy(state, 1));
}

/**
 * Routes to a specific step by a given index.
 *
 * @static
 * @private
 * @method goToStep
 * @param wizard {Object} The jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 * @param index {Integer} The position (zero-based) to route to
 * @return {Boolean} Indicates whether the action succeeded or failed
 **/
function goToStep(wizard, options, state, index)
{
    if (index < 0 || index >= state.stepCount)
    {
        throwError(_indexOutOfRangeErrorMessage);
    }

    if (options.forceMoveForward && index < state.currentIndex)
    {
        return;
    }

    var oldIndex = state.currentIndex;
    if (wizard.triggerHandler("stepChanging", [state.currentIndex, index]))
    {
        // Save new state
        state.currentIndex = index;
        saveCurrentStateToCookie(wizard, options, state);

        // Change visualisation
        refreshStepNavigation(wizard, options, state, oldIndex);
        refreshPagination(wizard, options, state);
        loadAsyncContent(wizard, options, state);
        startTransitionEffect(wizard, options, state, index, oldIndex, function()
        {
            wizard.triggerHandler("stepChanged", [index, oldIndex]);
        });
    }
    else
    {
        wizard.find(".steps li").eq(oldIndex).addClass("error");
    }

    return true;
}

function increaseCurrentIndexBy(state, increaseBy)
{
    return state.currentIndex + increaseBy;
}

/**
 * Initializes the component.
 *
 * @static
 * @private
 * @method initialize
 * @param options {Object} The component settings
 **/
function initialize(options)
{
    /*jshint -W040 */
    var opts = $.extend(true, {}, defaults, options);

    return this.each(function ()
    {
        var wizard = $(this);
        var state = {
            currentIndex: opts.startIndex,
            currentStep: null,
            stepCount: 0,
            transitionElement: null
        };

        // Create data container
        wizard.data("options", opts);
        wizard.data("state", state);
        wizard.data("steps", []);

        analyzeData(wizard, opts, state);
        render(wizard, opts, state);
        registerEvents(wizard, opts);

        // Trigger focus
        if (opts.autoFocus && _uniqueId === 0)
        {
            getStepAnchor(wizard, opts.startIndex).focus();
        }

        wizard.triggerHandler("init", [opts.startIndex]);
    });
}

/**
 * Inserts a new step to a specific position.
 *
 * @static
 * @private
 * @method insertStep
 * @param wizard {Object} The jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 * @param index {Integer} The position (zero-based) to add
 * @param step {Object} The step object to add
 * @example
 *     $("#wizard").steps().insert(0, {
 *         title: "Title",
 *         content: "", // optional
 *         contentMode: "async", // optional
 *         contentUrl: "/Content/Step/1" // optional
 *     });
 * @chainable
 **/
function insertStep(wizard, options, state, index, step)
{
    if (index < 0 || index > state.stepCount)
    {
        throwError(_indexOutOfRangeErrorMessage);
    }

    // TODO: Validate step object

    // Change data
    step = $.extend({}, stepModel, step);
    insertStepToCache(wizard, index, step);
    if (state.currentIndex !== state.stepCount && state.currentIndex >= index)
    {
        state.currentIndex++;
        saveCurrentStateToCookie(wizard, options, state);
    }
    state.stepCount++;

    var contentContainer = wizard.find(".content"),
        header = $("<{0}>{1}</{0}>".format(options.headerTag, step.title)),
        body = $("<{0}></{0}>".format(options.bodyTag));

    if (step.contentMode == null || step.contentMode === contentMode.html)
    {
        body.html(step.content);
    }

    if (index === 0)
    {
        contentContainer.prepend(body).prepend(header);
    }
    else
    {
        getStepPanel(wizard, (index - 1)).after(body).after(header);
    }

    renderBody(wizard, state, body, index);
    renderTitle(wizard, options, state, header, index);
    refreshSteps(wizard, options, state, index);
    if (index === state.currentIndex)
    {
        refreshStepNavigation(wizard, options, state);
    }
    refreshPagination(wizard, options, state);

    return wizard;
}

/**
 * Inserts a step object to the cache at a specific position.
 *
 * @static
 * @private
 * @method insertStepToCache
 * @param wizard {Object} A jQuery wizard object
 * @param index {Integer} The position (zero-based) to add
 * @param step {Object} The step object to add
 **/
function insertStepToCache(wizard, index, step)
{
    getSteps(wizard).splice(index, 0, step);
}

/**
 * Handles the keyup DOM event for pagination.
 *
 * @static
 * @private
 * @event keyup
 * @param event {Object} An event object
 */
function keyUpHandler(event)
{
    var wizard = $(this),
        options = getOptions(wizard),
        state = getState(wizard);

    if (options.suppressPaginationOnFocus && wizard.find(":focus").is(":input"))
    {
        event.preventDefault();
        return false;
    }

    var keyCodes = { left: 37, right: 39 };
    if (event.keyCode === keyCodes.left)
    {
        event.preventDefault();
        goToPreviousStep(wizard, options, state);
    }
    else if (event.keyCode === keyCodes.right)
    {
        event.preventDefault();
        goToNextStep(wizard, options, state);
    }
}

/**
 * Loads and includes async content.
 *
 * @static
 * @private
 * @method loadAsyncContent
 * @param wizard {Object} A jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 */
function loadAsyncContent(wizard, options, state)
{
    if (state.stepCount > 0)
    {
        var currentIndex = state.currentIndex,
            currentStep = getStep(wizard, currentIndex);

        if (!options.enableContentCache || !currentStep.contentLoaded)
        {
            switch (getValidEnumValue(contentMode, currentStep.contentMode))
            {
                case contentMode.iframe:
                    wizard.find(".content > .body").eq(state.currentIndex).empty()
                        .html("<iframe src=\"" + currentStep.contentUrl + "\" frameborder=\"0\" scrolling=\"no\" />")
                        .data("loaded", "1");
                    break;

                case contentMode.async:
                    var currentStepContent = getStepPanel(wizard, currentIndex)._aria("busy", "true")
                        .empty().append(renderTemplate(options.loadingTemplate, { text: options.labels.loading }));

                    $.ajax({ url: currentStep.contentUrl, cache: false }).done(function (data)
                    {
                        currentStepContent.empty().html(data)._aria("busy", "false").data("loaded", "1");
                        wizard.triggerHandler("contentLoaded", [currentIndex]);
                    });
                    break;
            }
        }
    }
}

/**
 * Fires the action next or previous click event.
 *
 * @static
 * @private
 * @method paginationClick
 * @param wizard {Object} The jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 * @param index {Integer} The position (zero-based) to route to
 * @return {Boolean} Indicates whether the event fired successfully or not
 **/
function paginationClick(wizard, options, state, index)
{
    var oldIndex = state.currentIndex;

    if (index >= 0 && index < state.stepCount && !(options.forceMoveForward && index < state.currentIndex))
    {
        var anchor = getStepAnchor(wizard, index),
            parent = anchor.parent(),
            isDisabled = parent.hasClass("disabled");

        // Enable the step to make the anchor clickable!
        parent._enableAria();
        anchor.click();

        // An error occured
        if (oldIndex === state.currentIndex && isDisabled)
        {
            // Disable the step again if current index has not changed; prevents click action.
            parent._enableAria(false);
            return false;
        }

        return true;
    }

    return false;
}

/**
 * Fires when a pagination click happens.
 *
 * @static
 * @private
 * @event click
 * @param event {Object} An event object
 */
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
function cambiarTab(tab, div) {
         $("#tabpanelpostucacion a").removeClass('active');
         $("#tabpanelcontenido div").removeClass('active');
         $('#' + tab).addClass('tab-pane fade show active');
         $('#' + div).addClass('tab-pane fade show active');
     }

function calcularEdad(fecha) {
        var hoy = new Date();
        var cumpleanos = new Date(fecha);
        var edad = hoy.getFullYear() - cumpleanos.getFullYear();
        var m = hoy.getMonth() - cumpleanos.getMonth();

        if (m < 0 || (m === 0 && hoy.getDate() < cumpleanos.getDate())) {
            edad--;
        }

        return edad;
}


function limpiar() {

         $("#helpcmbidentificacion").html("");
         $("#helptxtidentificacion").html("");
         $("#helptxtnombres").html("");
         $("#helptxtapellidopaterno").html("");
         $("#helptxtapellidomaterno").html("");
         $("#helptxtemail").html("");
         $("#helptxtconfiremail").html("");
         $("#helptxtemailalternativo").html("");
         $("#helptxttipodiscapacidad").html("");
         $("#helptxtporcentajediscapacidad").html("");
         $("#helpcmbprovincianacimiento").html("");
         $("#helpcmbciudadnacimiento").html("");
         $("#helpdtbfechanacimiento").html("");
         $("#helpcmbtiposangre").html("");
         $("#helpcmbestadocivil").html("");
         $("#helpcmbsexo").html("");
         $("#helptxtdireccion").html("");
         $("#helptxtnumerocasa").html("");
         $("#helptxttelefonodomicilio").html("");
         $("#helptxttelefonocelular").html("");
         $("#helpcmbprovincianacimientodatoscontacto").html("");
         $("#helpcmbciudadnacimientocontacto").html("");
         $("#helpcmbparroquianacimientocontacto").html("");
         $("#helpcmbprovinciaresidenciadatoscontacto").html("");
         $("#helpcmbciudadresidentecontacto").html("");
         $("#helpparroquiaresidentecontacto").html("");
         $("#helpcmbtipovivienda").html("");
         $("#helpcmbvivienda").html("");
         $("#helptxtnumerodormitorios").html("");
         $("#helpserviciobasico").html("");
         $("#helpcmtipodesector").html("");
         $("#helptextfacebook").html("");
         $("#helptexttwitter").html("");
         $("#helptexttiktok").html("");
         $("#helptextinstagram").html("");
         $("#txttelefonodomicilio").unmask();

         /****** Datos Academicos *////
         $("#helpcmbprovinciaestudio").html("");
         $("#helpcmbciudadestudio").html("");
         $("#helpcmbtipoinstitucion").html("");
         $("#helptxttitulobachiller").html("");
         $("#helptxtnotagraduacion").html("");
         $("#helptxtanograduacion").html("");
         $("#helpcmbcarrerainteresuno").html("");
         $("#helpcmbmodalidad").html("");

         /***** datos de Referencia *//////
         $("#helptxtnombresreferenciauno").html("");
         $("#helpcmbparentescouno").html("");
         $("#helptxttelefonodomiciliorefuno").html("");
         $("#helptxttelefonocelularrefuno").html("");
         $("#helptxtnombresreferenciados").html("");
         $("#helpcmbparentescodos").html("");
         $("#helptxttelefonodomiciliorefdos").html("");
         $("#helptxttelefonocelularrefdos").html("");
         $("#helptxtnombresreferenciatres").html("");
         $("#helpcmbparentescotres").html("");
         $("#helptxttelefonodomicilioreftres").html("");
         $("#helptxttelefonocelularreftres").html("");
         $("#helparchivocrosqui").html("");
         $("#txttelefonodomiciliorefuno").unmask();
         $("#txttelefonodomiciliorefdos").unmask();
         $("#txttelefonodomicilioreftres").unmask();

         /*** documentacion */
          $("#helparchivoarchivocedula").html("");
          $("#helparchivoactagrado").html("");
          $("#helparchivotitulobachiller").html("");
          $("#helparchivofoto").html("");
          $("#helparchivoplanillaserviciobasico").html("");
          $("#helparchivodiscapacidad").html("");

     }




var myarea = [ '02', '03', '06', '04', '05', '07' ];

function validarDatos() {


         /****** Datos Personales *////
         if ($("#cmbidetificacion").val() == 0) {
             $("#helpcmbidentificacion").html("Seleccionar el Tipo Identificación");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }
         if ($("#txtidentificacion").val() == "") {
             $("#helptxtidentificacion").html("Debe Ingresar la Identificación");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }
         if ($("#cmtipodesector").val() == 0) {
             $("#helpcmtipodesector").html("Seleccionar el Tipo de Sector");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }


         if (validarCedula($("#txtidentificacion").val(), $("#cmbidetificacion").val()) != 0) {
             $("#helptxtidentificacion").html("Número de Cédula Incorrecta");
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
         if ($("#txtemail").val() == "") {
             $("#helptxtemail").html("Debe Ingresar el email");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

          if (validarEmail($("#txtemail").val())!=0) {
            $("#helptxtemail").html("Formato del Correo Incorrecto");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
          }

         if ($("#txtconfiremail").val() == "") {
             $("#helptxtconfiremail").html("Debe Ingresar el email de confirmación");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }




          if (validarEmail($("#txtconfiremail").val())!=0) {
            $("#helptxtconfiremail").html("Formato del Correo Incorrecto");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
          }


          if ($("#txtemail").val() != $("#txtconfiremail").val()){
             $("#helptxtconfiremail").html("El email y el email de confirmación deben ser iguales");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
          }



         if ($("#txtemailalternativo").val() == "") {
             $("#helptxtemailalternativo").html("Debe Ingresar el email alternativo");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if (validarEmail($("#txtemailalternativo").val())!=0) {
            $("#helptxtemailalternativo").html("Formato del Correo Incorrecto");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
          }



         if (document.getElementById("chkdiscapacidad").checked == true) {

             if ($("#txttipodiscapacidad").val() == "") {
                 $("#helptxttipodiscapacidad").html("Debe Ingresar el tipo discapacidad");
                 cambiarTab('base-tab1', 'datospersonales');
                 return 1;
             }

             if ($("#txtporcentajediscapacidad").val() == "0" || $("#txtporcentajediscapacidad").val() == "") {
                 $("#helptxtporcentajediscapacidad").html("El porcentaje de discapacidad debe ser mayor a 0");
                 cambiarTab('base-tab1', 'datospersonales');
                 return 1;
             }


         }

         if ($("#cmbprovincianacimiento").val() == 0) {
             $("#helpcmbprovincianacimiento").html("Seleccionar la provincia de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#cmbciudadnacimiento").val() == 0) {
             $("#helpcmbciudadnacimiento").html("Seleccionar la ciudad de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#dtbfechanacimiento").val() == "") {
             $("#helpdtbfechanacimiento").html("Debe Ingresar la fecha de nacimiento");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }



         if (calcularEdad($("#dtbfechanacimiento").val())<16){
                $("#helpdtbfechanacimiento").html("No es Mayor de 16 años");
                cambiarTab('base-tab1', 'datospersonales');
                return 1;
         }



         if ($("#cmbtiposangre").val() == 0) {
             $("#helpcmbtiposangre").html("Seleccionar el tipo de sangre");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#cmbestadocivil").val() == 0) {
             $("#helpcmbestadocivil").html("Seleccionar el estado civil");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         if ($("#cmbsexo").val() == 0) {
             $("#helpcmbsexo").html("Seleccionar el sexo");
             cambiarTab('base-tab1', 'datospersonales');
             return 1;
         }

         /****** Datos Domicilio Contacto *////

         if ($("#txtdireccion").val() == "") {
             $("#helptxtdireccion").html("Debe Ingresar la Calle-Direcciòn");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#txtnumerocasa").val() == "") {
             $("#helptxtnumerocasa").html("Debe Ingresar la nùmero de casa");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#txttelefonodomicilio").val() == "") {
             $("#helptxttelefonodomicilio").html("Debe Ingresar el nùmero de telèfono");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }



         if (myarea.includes($("#txttelefonodomicilio").val().substr(0,2))==false) {
             $("#helptxttelefonodomicilio").html("No existe el código de area para el número de domicilio");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ( parseInt($("#txttelefonodomicilio").val().length) != parseInt("9")) {
             $("#helptxttelefonodomicilio").html("El número telèfono debe contener 9 números");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }



         $("#txttelefonodomicilio").mask("(00)-0000000");

         if ($("#txttelefonocelular").val() == "") {
             $("#helptxttelefonocelular").html("Debe Ingresar el nùmero de celular");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ( parseInt($("#txttelefonocelular").val().length) != parseInt("10")) {
             $("#helptxttelefonocelular").html("El número celular debe contener 10 números");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }



         if ( parseInt($("#txttelefonocelular").val().substr(0,1)) != parseInt("0")) {
             $("#helptxttelefonocelular").html("El número celular esta incorecto");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }


         if ($("#cmbprovincianacimientodatoscontacto").val() == "0") {
             $("#helpcmbprovincianacimientodatoscontacto").html("Debe seleccionar la provincia");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#cmbciudadnacimientocontacto").val() == "0") {
             $("#helpcmbciudadnacimientocontacto").html("Debe seleccionar la ciudad");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#cmbparroquianacimientocontacto").val() == "0") {
             $("#helpcmbparroquianacimientocontacto").html("Debe seleccionar la parroquia");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }


         if ($("#cmbprovinciaresidenciadatoscontacto").val() == "0") {
             $("#helpcmbprovinciaresidenciadatoscontacto").html("Debe seleccionar la provincia residencia");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#cmbciudadresidentecontacto").val() == "0") {
             $("#helpcmbciudadresidentecontacto").html("Debe seleccionar la ciudad de residencia");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#cmbparroquiaresidentecontacto").val() == "0") {
             $("#helpparroquiaresidentecontacto").html("Debe seleccionar la parroquia de residencia");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#cmbciudadresidentecontacto").val() != 100) {
             $("#helpcmbciudadresidentecontacto").html("La solicitud de postulación son para personas que residen en Guayaquil");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#cmbtipovivienda").val() == "0") {
             $("#helpcmbtipovivienda").html("Debe seleccionar el tipo de vivienda");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#cmbvivienda").val() == "0") {
             $("#helpcmbvivienda").html("Debe seleccionar la vivienda");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#txtnumerodormitorios").val() == "") {
             $("#helptxtnumerodormitorios").html("Debe Ingresar la nùmero de dormitorio");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if (document.getElementById("chkaguapotable").checked == false && document.getElementById("chkalcantarillado").checked == false &&
             document.getElementById("chkenergiaelectrica").checked == false && document.getElementById("chktelefono").checked == false
             && document.getElementById("chkinternet").checked == false && document.getElementById("chktvpagada").checked == false) {

             $("#helpserviciobasico").html("Debe seleccionar al menos un servicio bàsico");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;

         }

         if ($("#textfacebook").val() == "") {

             $("#helptextfacebook").html("Debe Ingresar la cuenta de Facebook");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#texttwitter").val() == "") {

             $("#helptexttwitter").html("Debe Ingresar la cuenta de Twitter");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

         if ($("#textinstagram").val() == "") {

             $("#helptextinstagram").html("Debe Ingresar la cuenta de Instragam");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }

          if ($("#texttiktok").val() == "") {

             $("#helptexttiktok").html("Debe Ingresar la cuenta de TikTok");
             cambiarTab('base-tab2', 'datoscontactos');
             return 1;
         }


         /****** Datos Academicos *////

         if ($("#cmbprovinciaestudio").val() == "0") {
             $("#helpcmbprovinciaestudio").html("Debe seleccionar la provincia");
             cambiarTab('base-tab3', 'datosacademicos');
             return 1;
         }

         if ($("#cmbciudadestudio").val() == "0") {
             $("#helpcmbciudadestudio").html("Debe seleccionar la ciudad");
             cambiarTab('base-tab3', 'datosacademicos');
             return 1;
         }

         if ($("#cmbtipoinstitucion").val() == "0") {
             $("#helpcmbtipoinstitucion").html("Debe seleccionar el tipo de institución");
             cambiarTab('base-tab3', 'datosacademicos');
             return 1;
         }



         if ($("#txttitulobachiller").val() == "") {
             $("#helptxttitulobachiller").html("Debe ingresar titulo de bachiller");
             cambiarTab('base-tab3', 'datosacademicos');
             return 1;
         }

         if ($("#txtnotagraduacion").val() == "") {
             $("#helptxtnotagraduacion").html("Debe ingresar la nota de graduación");
             cambiarTab('base-tab3', 'datosacademicos');
             return 1;
         }


         if (parseFloat($("#txtnotagraduacion").val()) < parseFloat("7.80")) {
             $("#helptxtnotagraduacion").html("La nota de graduación debe ser mayor a 7.80 para la postulación a la beca");
             cambiarTab('base-tab3', 'datosacademicos');
             return 1;
         }

         if ($("#txtanograduacion").val() == "") {
             $("#helptxtanograduacion").html("Debe ingresar el año de graduación");
             cambiarTab('base-tab3', 'datosacademicos');
             return 1;
         }



         if ($("#cmbmodalidad").val() == "0") {
             $("#helpcmbmodalidad").html("Debe seleccionar la modalidad");
             cambiarTab('base-tab3', 'datosacademicos');
             return 1;
         }


         if ($("#cmbcarrerainteresuno").val() == "0") {
             $("#helpcmbcarrerainteresuno").html("Debe seleccionar la carrera de Interes Uno");
             cambiarTab('base-tab3', 'datosacademicos');
             return 1;
         }


         if ($("#txtnombresreferenciauno").val() == "") {
             $("#helptxtnombresreferenciauno").html("Debe ingresar los nombres y apellidos de la referencia 1");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ($("#cmbparentescouno").val() == "0") {
             $("#helpcmbparentescouno").html("Debe seleccionar el parentesco de la referencia 1");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ($("#txttelefonodomiciliorefuno").val() == "") {
             $("#helptxttelefonodomiciliorefuno").html("Debe ingresar el teléfono convencional de la referencia 1");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if (myarea.includes($("#txttelefonodomiciliorefuno").val().substr(0,2))==false) {
             $("#helptxttelefonodomiciliorefuno").html("No existe el código de area para el teléfono convencional de la referencia 1");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ( parseInt($("#txttelefonodomiciliorefuno").val().length) != parseInt("9")) {
             $("#helptxttelefonodomiciliorefuno").html("El número telèfono convencional de la referencia 1 debe contener 9 números");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         $("#txttelefonodomiciliorefuno").mask("(00)-0000000");

         if ($("#txttelefonocelularrefuno").val() == "") {
             $("#helptxttelefonocelularrefuno").html("Debe ingresar el teléfono celular de la referencia 1");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ( parseInt($("#txttelefonocelularrefuno").val().length) != parseInt("10")) {
             $("#helptxttelefonocelularrefuno").html("El número celular de la referencia 1 debe contener 10 números");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }



         if ( parseInt($("#txttelefonocelularrefuno").val().substr(0,1)) != parseInt("0")) {
             $("#helptxttelefonocelularrefuno").html("El número celular de la referencia 1 está incorecto");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }


          $("#collapseOne").removeClass('collapse ');
          $("#collapseTwo").addClass('collapse show');

         if ($("#txtnombresreferenciados").val() == "") {
             $("#helptxtnombresreferenciados").html("Debe ingresar los nombres y apellidos de la referencia 2");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ($("#cmbparentescodos").val() == "0") {
             $("#helpcmbparentescodos").html("Debe seleccionar el parentesco de la referencia 2");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ($("#txttelefonodomiciliorefdos").val() == "") {
             $("#helptxttelefonodomiciliorefdos").html("Debe ingresar el teléfono convencional de la referencia 2");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if (myarea.includes($("#txttelefonodomiciliorefdos").val().substr(0,2))==false) {
             $("#helptxttelefonodomiciliorefdos").html("No existe el código de area para el teléfono convencional de la referencia 2");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ( parseInt($("#txttelefonodomiciliorefdos").val().length) != parseInt("9")) {
             $("#helptxttelefonodomiciliorefdos").html("El número telèfono convencional de la referencia 2 debe contener 9 números");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         $("#txttelefonodomiciliorefdos").mask("(00)-0000000");

         if ($("#txttelefonocelularrefdos").val() == "") {
             $("#helptxttelefonocelularrefdos").html("Debe ingresar el teléfono celular de la referencia 2");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ( parseInt($("#txttelefonocelularrefdos").val().length) != parseInt("10")) {
             $("#helptxttelefonocelularrefdos").html("El número celular de la referencia 2 debe contener 10 números");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }



         if ( parseInt($("#txttelefonocelularrefdos").val().substr(0,1)) != parseInt("0")) {
             $("#helptxttelefonocelularrefdos").html("El número celular de la referencia 2 está incorecto");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         $("#collapseOne").addClass('collapse');
         $("#collapseTwo").addClass('collapse');
         $("#collapseThree").addClass('collapse show');

         if ($("#txtnombresreferenciatres").val() == "") {
             $("#helptxtnombresreferenciatres").html("Debe ingresar los nombres y apellidos de la referencia 3");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ($("#cmbparentescotres").val() == "0") {
             $("#helpcmbparentescotres").html("Debe seleccionar el parentesco de la referencia 3");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ($("#txttelefonodomicilioreftres").val() == "") {
             $("#helptxttelefonodomicilioreftres").html("Debe ingresar el teléfono convencional de la referencia 3");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if (myarea.includes($("#txttelefonodomicilioreftres").val().substr(0,2))==false) {
             $("#helptxttelefonodomicilioreftres").html("No existe el código de area para el teléfono convencional de la referencia 3");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ( parseInt($("#txttelefonodomicilioreftres").val().length) != parseInt("9")) {
             $("#helptxttelefonodomicilioreftres").html("El número telèfono convencional de la referencia 3 debe contener 9 números");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         $("#txttelefonodomicilioreftres").mask("(00)-0000000");

         if ($("#txttelefonocelularreftres").val() == "") {
             $("#helptxttelefonocelularreftres").html("Debe ingresar el teléfono celular de la referencia 3");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ( parseInt($("#txttelefonocelularreftres").val().length) != parseInt("10")) {
             $("#helptxttelefonocelularreftres").html("El número celular de la referencia 3 debe contener 10 números");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }



         if ( parseInt($("#txttelefonocelularreftres").val().substr(0,1)) != parseInt("0")) {
             $("#helptxttelefonocelularreftres").html("El número celular de la referencia 3 está incorecto");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

         if ($("#archivocrosqui").val() == "") {
              //$("#helparchivocrosqui").html("Debe adjuntar el croquis de su vivienda");
              swal("Alerta","Debe adjuntar el croquis de su vivienda","warning");
             cambiarTab('base-tab4', 'datoreferenciapersonal');
             return 1;
         }

          if ($("#archivocedula").val() == "") {
              //$("#helparchivoarchivocedula").html("Debe adjuntar el cédula y papeleta de votación");
              swal("Alerta","Debe adjuntar el cédula y papeleta de votación","warning");
             cambiarTab('base-tab5', 'datodocumentacion');
             return 1;
          }



          if ($("#archivoactagrado").val() == "") {
              //$("#helparchivoactagrado").html("Debe adjuntar el acta de grado");
              swal("Alerta","Debe adjuntar el acta de grado","warning");
             cambiarTab('base-tab5', 'datodocumentacion');
             return 1;
          }

          if ($("#archivotitulobachiller").val() == "") {
              //$("#helparchivotitulobachiller").html("Debe adjuntar el título de bachiller");
             swal("Alerta","Debe adjuntar el título de bachiller","warning");
             cambiarTab('base-tab5', 'datodocumentacion');
             return 1;
          }



          if ($("#archivofoto").val() == "") {
              //$("#helparchivofoto").html("Debe adjuntar la foto tamaño carnet");
              swal("Alerta","Debe adjuntar la foto tamaño carnet","warning");
              cambiarTab('base-tab5', 'datodocumentacion');
             return 1;
          }

          if ($("#archivoplanillaserviciobasico").val() == "") {
             // $("#helparchivoplanillaserviciobasico").html("Debe adjuntar la planilla de servicios básicos");
              swal("Alerta","Debe adjuntar la planilla de servicios básicos","warning");
              cambiarTab('base-tab5', 'datodocumentacion');
             return 1;
          }



         return 0;

     }

function limpiarDatosSituacionLaboral() {

          $("#helpcmbformatrabajo").html("");
          $("#helptxtnombreempresa").html("");
          $("#helptxtdireccionempresa").html("");
          $("#helptxtnombreempresaanterior").html("");
          $("#helptxtdireccionempresaanterior").html("");
          $("#helptxtcedidaporquien").html("");
          $("#helptxtespecifiquetipoviviendasituacion").html("");
          $("#helptxtnumeroinqulinos").html("");
          $("#helptxtnumerodormitoriossituacion").html("");
          $("#helpcmbviviendasituacion").html("");
          $("#helpcmbtipoviviendasituacion").html("");
          $("#helptxtvalorarriendo").html("");
          $("#helptxttelefonoempresa").html("");
          $("#helptxttelefonoempresaanterior").html("");
          $("#txttelefonoempresa").unmask();
          $("#txttelefonoempresaanterior").unmask();



     }
function validaDatosSituacionLaboral(){

     if (document.getElementById("sitrabaja").checked) {
         if ($("#cmbformatrabajo").val() == 0) {
             $("#helpcmbformatrabajo").html("Debe seleccionar la forma de trabajo");
             return 1;
         }

          if ($("#txtnombreempresa").val() == "") {
             $("#helptxtnombreempresa").html("Debe Ingresar el nombre de la empresa");
             return 1;
          }

          if ($("#txtdireccionempresa").val() == "") {
                 $("#helptxtdireccionempresa").html("Debe Ingresar la dirección de la empresa");
                 return 1;
          }

          if ($("#txttelefonoempresa").val() != "") {


                 if (myarea.includes($("#txttelefonoempresa").val().substr(0,2))==false) {
                     $("#helptxttelefonoempresa").html("No existe el código de area para el número de la empresa");
                     return 1;
                 }

                 if ( parseInt($("#txttelefonoempresa").val().length) != parseInt("9")) {
                     $("#helptxttelefonoempresa").html("El número telèfono debe contener 9 números");
                     return 1;
                 }




          }


     }

     $("#txttelefonoempresa").mask("(00)-0000000");


     if (document.getElementById("sitrabajoanterirmente").checked) {

          if ($("#txtnombreempresaanterior").val() == "") {
             $("#helptxtnombreempresaanterior").html("Debe Ingresar el nombre de la empresa");
             return 1;
          }

          if ($("#txtdireccionempresaanterior").val() == "") {
                 $("#helptxtdireccionempresaanterior").html("Debe Ingresar la dirección de la empresa");
                 return 1;
          }

          if ($("#txttelefonoempresaanterior").val() != "") {


                 if (myarea.includes($("#txttelefonoempresaanterior").val().substr(0,2))==false) {
                     $("#helptxttelefonoempresaanterior").html("No existe el código de area para el número de la empresa anterior");
                     return 1;
                 }

                 if ( parseInt($("#txttelefonoempresaanterior").val().length) != parseInt("9")) {
                     $("#helptxttelefonoempresaanterior").html("El número telèfono debe contener 9 números");
                     return 1;
                 }





          }


     }

     $("#txttelefonoempresaanterior").mask("(00)-0000000");

     if ($("#cmbviviendasituacion").val()==0){
          $("#helpcmbviviendasituacion").html("Debe seleccionar la vivienda");
             return 1;
     }


     if ($("#cmbviviendasituacion").val()==3){
         if ($("#txtcedidaporquien").val() == "") {
             $("#helptxtcedidaporquien").html("Debe Ingresar la especificación por quien fue cedida");
             return 1;
         }
     }

     if ($("#cmbviviendasituacion").val()==2){
         if ($("#txtvalorarriendo").val() == "") {
             $("#helptxtvalorarriendo").html("Debe Ingresar el valor del arriendo");
             return 1;
         }
     }

     if ($("#cmbtipoviviendasituacion").val()==0){
          $("#helpcmbtipoviviendasituacion").html("Debe seleccionar el tipo vivienda");
             return 1;

     }

     if ($("#cmbtipoviviendasituacion").val()==7){

         if ($("#txtespecifiquetipoviviendasituacion").val() == "") {

             $("#helptxtespecifiquetipoviviendasituacion").html("Debe Ingresar la especificación del tipo de vivienda");
             return 1;
         }

     }



     if (document.getElementById("sitieneinquilino").checked) {

         if ($("#txtnumeroinqulinos").val() ==0) {

             $("#helptxtnumeroinqulinos").html("el número de inqulinos debe ser mayor a 0");
             return 1;
         }

     }

     if ($("#txtnumerodormitoriossituacion").val() =="") {
             $("#helptxtnumerodormitoriossituacion").html("debe ingresar el número de dormitorios");
             return 1;
     }

    return 0;

}

function limpiarvalidaDatosEconimicos() {
     $("#helpcmbquiencubregatos").html("");
     $("#helptxtquienpagagastos").html("");
     $("#helptxtdescrpcionenfermedad").html("");
     $("#helpcmbquientienenfermedad").html("");
}
function validaDatosEconimicos(){



     if ($("#cmbquiencubregatos").val()==0){
          $("#helpcmbquiencubregatos").html("Debe seleccionar quien cubre los gastos");
             return 1;
     }


     if ($("#cmbquiencubregatos").val()==7){
         if ($("#txtquienpagagastos").val() == "") {
             $("#helptxtquienpagagastos").html("Debe Ingresar la especificación de quien cubre los gastos");
             return 1;
         }
     }

     if ($("#totingre").val() == 0 && $("#totegre").val() == 0 ){
            swal("Error","Debe Ingresar la tabla de Resumen de Ingresos y Egresos","error");
            return 1;
     }


     if (document.getElementById("sienfermedagrupofamiliar").checked) {

         if ($("#txtdescrpcionenfermedad").val() =="") {
             $("#helptxtdescrpcionenfermedad").html("Debe ingresar la descripcion de la enfermedad");
             return 1;
         }

         if ($("#cmbquientienenfermedad").val() ==0) {
             $("#helpcmbquientienenfermedad").html("Debe seleccionar quien padece la enfermedad");
             return 1;
         }

     }


    return 0;

}




function paginationClickHandler(event)
{
    event.preventDefault();

    var anchor = $(this),
        wizard = anchor.parent().parent().parent().parent(),
        options = getOptions(wizard),
        state = getState(wizard),
        href = anchor.attr("href");

    switch (href.substring(href.lastIndexOf("#") + 1)) {
        case "cancel":
            cancel(wizard);
            break;

        case "finish":

               //limpiarvalidaDatosEconimicos();
           // if (validaDatosEconimicos()==0) {
             //   llenartablaIngresosEgresos();
               finishStep(wizard, state);



           // }


            break;

        case "next":
           limpiar();

           if (validarDatos()==0) {


            goToNextStep(wizard, options, state);
            document.getElementById('#next').style.display = 'none';
            document.getElementById('#next2').style.display = 'block';
            document.getElementById('#previous').style.display = 'block';
            document.getElementById('#previous2').style.display = 'none';
            document.getElementById('#previous3').style.display = 'none';
            document.getElementById('#previous4').style.display = 'none';


           }

            break;

        case "next2":
            if (document.getElementById('idtablafamiliares').rows.length>0) {

                goToNextStep(wizard, options, state);
                document.getElementById('#next').style.display = 'none';
                document.getElementById('#next2').style.display = 'none';
                document.getElementById('#next4').style.display = 'none';
                document.getElementById('#next3').style.display = 'block';
                document.getElementById('#previous').style.display = 'none';
                document.getElementById('#previous2').style.display = 'block';
                document.getElementById('#previous3').style.display = 'none';
                document.getElementById('#previous4').style.display = 'none';
            }else{
              swal("Alerta","Debe ingresar por lo menos un dato familiar","warning");
            }

            break;

        case "next3":
            limpiarDatosSituacionLaboral();
            if (validaDatosSituacionLaboral()==0) {
                goToNextStep(wizard, options, state);
                document.getElementById('#next').style.display = 'none';
                document.getElementById('#next2').style.display = 'none';
                document.getElementById('#next3').style.display = 'none';
                document.getElementById('#next4').style.display = 'block';
                document.getElementById('#previous').style.display = 'none';
                document.getElementById('#previous2').style.display = 'none';
                document.getElementById('#previous3').style.display = 'block';
                document.getElementById('#previous4').style.display = 'none';
            }

            break;

        case "next4":
            limpiarvalidaDatosEconimicos();
            if (validaDatosEconimicos()==0) {
                goToNextStep(wizard, options, state);
                finishStep(wizard, state);
                document.getElementById('#next').style.display = 'none';
                document.getElementById('#next2').style.display = 'none';
                document.getElementById('#next3').style.display = 'none';
                document.getElementById('#next4').style.display = 'none';
                document.getElementById('#previous').style.display = 'none';
                document.getElementById('#previous2').style.display = 'none';
                document.getElementById('#previous3').style.display = 'none';
                document.getElementById('#previous4').style.display = 'block';
            }

            break;

        case "previous":
            goToPreviousStep(wizard, options, state);
            document.getElementById('#next').style.display = 'block';
            document.getElementById('#next2').style.display = 'none';
            document.getElementById('#next3').style.display = 'none';
            document.getElementById('#next4').style.display = 'none';
            document.getElementById('#previous').style.display = 'none';
            document.getElementById('#previous2').style.display = 'none';
            document.getElementById('#previous3').style.display = 'none';
            document.getElementById('#previous4').style.display = 'none';

            break;

        case "previous2":
            goToPreviousStep(wizard, options, state);
            document.getElementById('#next').style.display = 'none';
            document.getElementById('#next2').style.display = 'block';
            document.getElementById('#next3').style.display = 'none';
            document.getElementById('#next4').style.display = 'none';
            document.getElementById('#previous').style.display = 'block';
            document.getElementById('#previous2').style.display = 'none';
            document.getElementById('#previous3').style.display = 'none';
            document.getElementById('#previous4').style.display = 'none';

            break;

        case "previous3":
            goToPreviousStep(wizard, options, state);
            document.getElementById('#next').style.display = 'none';
            document.getElementById('#next2').style.display = 'none';
            document.getElementById('#next4').style.display = 'none';
            document.getElementById('#next3').style.display = 'block';
            document.getElementById('#previous').style.display = 'none';
            document.getElementById('#previous2').style.display = 'block';
            document.getElementById('#previous3').style.display = 'none';
            document.getElementById('#previous4').style.display = 'none';

            break;

        case "previous4":
            goToPreviousStep(wizard, options, state);
            document.getElementById('#next').style.display = 'none';
            document.getElementById('#next2').style.display = 'none';
            document.getElementById('#next4').style.display = 'block';
            document.getElementById('#next3').style.display = 'none';

            document.getElementById('#previous').style.display = 'none';
            document.getElementById('#previous2').style.display = 'none';
            document.getElementById('#previous3').style.display = 'block';
            document.getElementById('#previous4').style.display = 'none';

            break;
    }
}

/**
 * Refreshs the visualization state for the entire pagination.
 *
 * @static
 * @private
 * @method refreshPagination
 * @param wizard {Object} A jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 */
function refreshPagination(wizard, options, state)
{
    if (options.enablePagination)
    {
        var finish = wizard.find(".actions a[href$='#finish']").parent(),
            next = wizard.find(".actions a[href$='#next']").parent();

        if (!options.forceMoveForward)
        {
            var previous = wizard.find(".actions a[href$='#previous']").parent();
            previous._enableAria(state.currentIndex > 0);
        }

        if (options.enableFinishButton && options.showFinishButtonAlways)
        {
            finish._enableAria(state.stepCount > 0);
            next._enableAria(state.stepCount > 1 && state.stepCount > (state.currentIndex + 1));
        }
        else
        {
            finish._showAria(options.enableFinishButton && state.stepCount === (state.currentIndex + 1));
            next._showAria(state.stepCount === 0 || state.stepCount > (state.currentIndex + 1)).
                _enableAria(state.stepCount > (state.currentIndex + 1) || !options.enableFinishButton);
        }
    }
}

/**
 * Refreshs the visualization state for the step navigation (tabs).
 *
 * @static
 * @private
 * @method refreshStepNavigation
 * @param wizard {Object} A jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 * @param [oldIndex] {Integer} The index of the prior step
 */
function refreshStepNavigation(wizard, options, state, oldIndex)
{
    var currentOrNewStepAnchor = getStepAnchor(wizard, state.currentIndex),
        currentInfo = $("<span class=\"current-info audible\">" + options.labels.current + " </span>"),
        stepTitles = wizard.find(".content > .title");

    if (oldIndex != null)
    {
        var oldStepAnchor = getStepAnchor(wizard, oldIndex);
        oldStepAnchor.parent().addClass("done").removeClass("error")._selectAria(false);
        stepTitles.eq(oldIndex).removeClass("current").next(".body").removeClass("current");
        currentInfo = oldStepAnchor.find(".current-info");
        currentOrNewStepAnchor.focus();
    }

    currentOrNewStepAnchor.prepend(currentInfo).parent()._selectAria().removeClass("done")._enableAria();
    stepTitles.eq(state.currentIndex).addClass("current").next(".body").addClass("current");
}

/**
 * Refreshes step buttons and their related titles beyond a certain position.
 *
 * @static
 * @private
 * @method refreshSteps
 * @param wizard {Object} A jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 * @param index {Integer} The start point for refreshing ids
 */
function refreshSteps(wizard, options, state, index)
{
    var uniqueId = getUniqueId(wizard);

    for (var i = index; i < state.stepCount; i++)
    {
        var uniqueStepId = uniqueId + _tabSuffix + i,
            uniqueBodyId = uniqueId + _tabpanelSuffix + i,
            uniqueHeaderId = uniqueId + _titleSuffix + i,
            title = wizard.find(".title").eq(i)._id(uniqueHeaderId);

        wizard.find(".steps a").eq(i)._id(uniqueStepId)
            ._aria("controls", uniqueBodyId).attr("href", "#" + uniqueHeaderId)
            .html(renderTemplate(options.titleTemplate, { index: i + 1, title: title.html() }));
        wizard.find(".body").eq(i)._id(uniqueBodyId)
            ._aria("labelledby", uniqueHeaderId);
    }
}

function registerEvents(wizard, options)
{
    var eventNamespace = getEventNamespace(wizard);

    wizard.bind("canceled" + eventNamespace, options.onCanceled);
    wizard.bind("contentLoaded" + eventNamespace, options.onContentLoaded);
    wizard.bind("finishing" + eventNamespace, options.onFinishing);
    wizard.bind("finished" + eventNamespace, options.onFinished);
    wizard.bind("init" + eventNamespace, options.onInit);
    wizard.bind("stepChanging" + eventNamespace, options.onStepChanging);
    wizard.bind("stepChanged" + eventNamespace, options.onStepChanged);

    if (options.enableKeyNavigation)
    {
        wizard.bind("keyup" + eventNamespace, keyUpHandler);
    }

    wizard.find(".actions a").bind("click" + eventNamespace, paginationClickHandler);
}

/**
 * Removes a specific step by an given index.
 *
 * @static
 * @private
 * @method removeStep
 * @param wizard {Object} A jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 * @param index {Integer} The position (zero-based) of the step to remove
 * @return Indecates whether the item is removed.
 **/
function removeStep(wizard, options, state, index)
{
    // Index out of range and try deleting current item will return false.
    if (index < 0 || index >= state.stepCount || state.currentIndex === index)
    {
        return false;
    }

    // Change data
    removeStepFromCache(wizard, index);
    if (state.currentIndex > index)
    {
        state.currentIndex--;
        saveCurrentStateToCookie(wizard, options, state);
    }
    state.stepCount--;

    getStepTitle(wizard, index).remove();
    getStepPanel(wizard, index).remove();
    getStepAnchor(wizard, index).parent().remove();

    // Set the "first" class to the new first step button 
    if (index === 0)
    {
        wizard.find(".steps li").first().addClass("first");
    }

    // Set the "last" class to the new last step button 
    if (index === state.stepCount)
    {
        wizard.find(".steps li").eq(index).addClass("last");
    }

    refreshSteps(wizard, options, state, index);
    refreshPagination(wizard, options, state);

    return true;
}

function removeStepFromCache(wizard, index)
{
    getSteps(wizard).splice(index, 1);
}

/**
 * Transforms the base html structure to a more sensible html structure.
 *
 * @static
 * @private
 * @method render
 * @param wizard {Object} A jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 **/
function render(wizard, options, state)
{
    // Create a content wrapper and copy HTML from the intial wizard structure
    var wrapperTemplate = "<{0} class=\"{1}\">{2}</{0}>",
        orientation = getValidEnumValue(stepsOrientation, options.stepsOrientation),
        verticalCssClass = (orientation === stepsOrientation.vertical) ? " vertical" : "",
        contentWrapper = $(wrapperTemplate.format(options.contentContainerTag, "content " + options.clearFixCssClass, wizard.html())),
        stepsWrapper = $(wrapperTemplate.format(options.stepsContainerTag, "steps " + options.clearFixCssClass, "<ul role=\"tablist\"></ul>")),
        stepTitles = contentWrapper.children(options.headerTag),
        stepContents = contentWrapper.children(options.bodyTag);

    // Transform the wizard wrapper and remove the inner HTML
    wizard.attr("role", "application").empty().append(stepsWrapper).append(contentWrapper)
        .addClass(options.cssClass + " " + options.clearFixCssClass + verticalCssClass);

    // Add WIA-ARIA support
    stepContents.each(function (index)
    {
        renderBody(wizard, state, $(this), index);
    });

    stepTitles.each(function (index)
    {
        renderTitle(wizard, options, state, $(this), index);
    });

    refreshStepNavigation(wizard, options, state);
    renderPagination(wizard, options, state);
}

/**
 * Transforms the body to a proper tabpanel.
 *
 * @static
 * @private
 * @method renderBody
 * @param wizard {Object} A jQuery wizard object
 * @param body {Object} A jQuery body object
 * @param index {Integer} The position of the body
 */
function renderBody(wizard, state, body, index)
{
    var uniqueId = getUniqueId(wizard),
        uniqueBodyId = uniqueId + _tabpanelSuffix + index,
        uniqueHeaderId = uniqueId + _titleSuffix + index;

    body._id(uniqueBodyId).attr("role", "tabpanel")._aria("labelledby", uniqueHeaderId)
        .addClass("body")._showAria(state.currentIndex === index);
}

/**
 * Renders a pagination if enabled.
 *
 * @static
 * @private
 * @method renderPagination
 * @param wizard {Object} A jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 */
function renderPagination(wizard, options, state)
{
    if (options.enablePagination)
    {
        var pagination = "<{0} class=\"actions {1}\"><ul role=\"menu\" aria-label=\"{2}\">{3}</ul></{0}>",
            buttonTemplate = "<li><a id=\"#{0}\" class='btn ' href=\"#{0}\" role=\"menuitem\">{1}</a></li>",
            buttonTemplate2 = "<li><a id=\"#{0}\" class='btn ' href=\"#{0}\" role=\"menuitem\">{1}</a></li>",
            buttonTemplate3 = "<li><a id=\"#{0}\" class='btn ' href=\"#{0}\" role=\"menuitem\">{1}</a></li>",
            buttons = "";



        if (!options.forceMoveForward)
        {
            buttons += buttonTemplate.format("previous", options.labels.previous);
            buttons += buttonTemplate.format("previous2", options.labels.previous);
            buttons += buttonTemplate.format("previous3", options.labels.previous);
            buttons += buttonTemplate.format("previous4", options.labels.previous);
        }

        buttons += buttonTemplate.format("next", options.labels.next);
        buttons += buttonTemplate2.format("next2", options.labels.next);
        buttons += buttonTemplate3.format("next3", options.labels.next);
        buttons += buttonTemplate3.format("next4", options.labels.next);

        if (options.enableFinishButton)
        {
            buttons += buttonTemplate.format("finish", options.labels.finish);
        }

        if (options.enableCancelButton)
        {
            buttons += buttonTemplate.format("cancel", options.labels.cancel);
        }

        wizard.append(pagination.format(options.actionContainerTag, options.clearFixCssClass,
            options.labels.pagination, buttons));

        refreshPagination(wizard, options, state);
        loadAsyncContent(wizard, options, state);
    }
}

/**
 * Renders a template and replaces all placeholder.
 *
 * @static
 * @private
 * @method renderTemplate
 * @param template {String} A template
 * @param substitutes {Object} A list of substitute
 * @return {String} The rendered template
 */
function renderTemplate(template, substitutes)
{
    var matches = template.match(/#([a-z]*)#/gi);

    for (var i = 0; i < matches.length; i++)
    {
        var match = matches[i], 
            key = match.substring(1, match.length - 1);

        if (substitutes[key] === undefined)
        {
            throwError("The key '{0}' does not exist in the substitute collection!", key);
        }

        template = template.replace(match, substitutes[key]);
    }

    return template;
}

/**
 * Transforms the title to a step item button.
 *
 * @static
 * @private
 * @method renderTitle
 * @param wizard {Object} A jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 * @param header {Object} A jQuery header object
 * @param index {Integer} The position of the header
 */
function renderTitle(wizard, options, state, header, index)
{
    var uniqueId = getUniqueId(wizard),
        uniqueStepId = uniqueId + _tabSuffix + index,
        uniqueBodyId = uniqueId + _tabpanelSuffix + index,
        uniqueHeaderId = uniqueId + _titleSuffix + index,
        stepCollection = wizard.find(".steps > ul"),
        title = renderTemplate(options.titleTemplate, {
            index: index + 1,
            title: header.html()
        }),
        stepItem = $("<li role=\"tab\"><a id=\"" + uniqueStepId + "\" href=\"#" + uniqueHeaderId + 
            "\" aria-controls=\"" + uniqueBodyId + "\">" + title + "</a></li>");
        
    stepItem._enableAria(options.enableAllSteps || state.currentIndex > index);

    if (state.currentIndex > index)
    {
        stepItem.addClass("done");
    }

    header._id(uniqueHeaderId).attr("tabindex", "-1").addClass("title");

    if (index === 0)
    {
        stepCollection.prepend(stepItem);
    }
    else
    {
        stepCollection.find("li").eq(index - 1).after(stepItem);
    }

    // Set the "first" class to the new first step button
    if (index === 0)
    {
        stepCollection.find("li").removeClass("first").eq(index).addClass("first");
    }

    // Set the "last" class to the new last step button
    if (index === (state.stepCount - 1))
    {
        stepCollection.find("li").removeClass("last").eq(index).addClass("last");
    }

    // Register click event
    stepItem.children("a").bind("click" + getEventNamespace(wizard), stepClickHandler);
}

/**
 * Saves the current state to a cookie.
 *
 * @static
 * @private
 * @method saveCurrentStateToCookie
 * @param wizard {Object} A jQuery wizard object
 * @param options {Object} Settings of the current wizard
 * @param state {Object} The state container of the current wizard
 */
function saveCurrentStateToCookie(wizard, options, state)
{
    if (options.saveState && $.cookie)
    {
        $.cookie(_cookiePrefix + getUniqueId(wizard), state.currentIndex);
    }
}

function startTransitionEffect(wizard, options, state, index, oldIndex, doneCallback)
{
    var stepContents = wizard.find(".content > .body"),
        effect = getValidEnumValue(transitionEffect, options.transitionEffect),
        effectSpeed = options.transitionEffectSpeed,
        newStep = stepContents.eq(index),
        currentStep = stepContents.eq(oldIndex);

    switch (effect)
    {
        case transitionEffect.fade:
        case transitionEffect.slide:
            var hide = (effect === transitionEffect.fade) ? "fadeOut" : "slideUp",
                show = (effect === transitionEffect.fade) ? "fadeIn" : "slideDown";

            state.transitionElement = newStep;
            currentStep[hide](effectSpeed, function ()
            {
                var wizard = $(this)._showAria(false).parent().parent(),
                    state = getState(wizard);

                if (state.transitionElement)
                {
                    state.transitionElement[show](effectSpeed, function ()
                    {
                        $(this)._showAria();
                    }).promise().done(doneCallback);
                    state.transitionElement = null;
                }
            });
            break;

        case transitionEffect.slideLeft:
            var outerWidth = currentStep.outerWidth(true),
                posFadeOut = (index > oldIndex) ? -(outerWidth) : outerWidth,
                posFadeIn = (index > oldIndex) ? outerWidth : -(outerWidth);

            $.when(currentStep.animate({ left: posFadeOut }, effectSpeed, 
                    function () { $(this)._showAria(false); }),
                newStep.css("left", posFadeIn + "px")._showAria()
                    .animate({ left: 0 }, effectSpeed)).done(doneCallback);
            break;

        default:
            $.when(currentStep._showAria(false), newStep._showAria())
                .done(doneCallback);
            break;
    }
}

/**
 * Fires when a step click happens.
 *
 * @static
 * @private
 * @event click
 * @param event {Object} An event object
 */
function stepClickHandler(event)
{
    event.preventDefault();

    var anchor = $(this),
        wizard = anchor.parent().parent().parent().parent(),
        options = getOptions(wizard),
        state = getState(wizard),
        oldIndex = state.currentIndex;

    if (anchor.parent().is(":not(.disabled):not(.current)"))
    {
        var href = anchor.attr("href"),
            position = parseInt(href.substring(href.lastIndexOf("-") + 1), 0);

        goToStep(wizard, options, state, position);
    }

    // If nothing has changed
    if (oldIndex === state.currentIndex)
    {
        getStepAnchor(wizard, oldIndex).focus();
        return false;
    }
}

function throwError(message)
{
    if (arguments.length > 1)
    {
        message = message.format(Array.prototype.slice.call(arguments, 1));
    }

    throw new Error(message);
}

/**
 * Checks an argument for null or undefined and throws an error if one check applies.
 *
 * @static
 * @private
 * @method validateArgument
 * @param argumentName {String} The name of the given argument
 * @param argumentValue {Object} The argument itself
 */
function validateArgument(argumentName, argumentValue)
{
    if (argumentValue == null)
    {
        throwError("The argument '{0}' is null or undefined.", argumentName);
    }
}

/**
 * Represents a jQuery wizard plugin.
 *
 * @class steps
 * @constructor
 * @param [method={}] The name of the method as `String` or an JSON object for initialization
 * @param [params=]* {Array} Additional arguments for a method call
 * @chainable
 **/
$.fn.steps = function (method)
{
    if ($.fn.steps[method])
    {
        return $.fn.steps[method].apply(this, Array.prototype.slice.call(arguments, 1));
    }
    else if (typeof method === "object" || !method)
    {
        return initialize.apply(this, arguments);
    }
    else
    {
        $.error("Method " + method + " does not exist on jQuery.steps");
    }
};

/**
 * Adds a new step.
 *
 * @method add
 * @param step {Object} The step object to add
 * @chainable
 **/
$.fn.steps.add = function (step)
{
    var state = getState(this);
    return insertStep(this, getOptions(this), state, state.stepCount, step);
};

/**
 * Removes the control functionality completely and transforms the current state to the initial HTML structure.
 *
 * @method destroy
 * @chainable
 **/
$.fn.steps.destroy = function ()
{
    return destroy(this, getOptions(this));
};

/**
 * Triggers the onFinishing and onFinished event.
 *
 * @method finish
 **/
$.fn.steps.finish = function ()
{
    finishStep(this, getState(this));
};

/**
 * Gets the current step index.
 *
 * @method getCurrentIndex
 * @return {Integer} The actual step index (zero-based)
 * @for steps
 **/
$.fn.steps.getCurrentIndex = function ()
{
    return getState(this).currentIndex;
};

/**
 * Gets the current step object.
 *
 * @method getCurrentStep
 * @return {Object} The actual step object
 **/
$.fn.steps.getCurrentStep = function ()
{
    return getStep(this, getState(this).currentIndex);
};

/**
 * Gets a specific step object by index.
 *
 * @method getStep
 * @param index {Integer} An integer that belongs to the position of a step
 * @return {Object} A specific step object
 **/
$.fn.steps.getStep = function (index)
{
    return getStep(this, index);
};

/**
 * Inserts a new step to a specific position.
 *
 * @method insert
 * @param index {Integer} The position (zero-based) to add
 * @param step {Object} The step object to add
 * @example
 *     $("#wizard").steps().insert(0, {
 *         title: "Title",
 *         content: "", // optional
 *         contentMode: "async", // optional
 *         contentUrl: "/Content/Step/1" // optional
 *     });
 * @chainable
 **/
$.fn.steps.insert = function (index, step)
{
    return insertStep(this, getOptions(this), getState(this), index, step);
};

/**
 * Routes to the next step.
 *
 * @method next
 * @return {Boolean} Indicates whether the action executed
 **/
$.fn.steps.next = function ()
{
    return goToNextStep(this, getOptions(this), getState(this));
};

/**
 * Routes to the previous step.
 *
 * @method previous
 * @return {Boolean} Indicates whether the action executed
 **/
$.fn.steps.previous = function ()
{
    return goToPreviousStep(this, getOptions(this), getState(this));
};

/**
 * Removes a specific step by an given index.
 *
 * @method remove
 * @param index {Integer} The position (zero-based) of the step to remove
 * @return Indecates whether the item is removed.
 **/
$.fn.steps.remove = function (index)
{
    return removeStep(this, getOptions(this), getState(this), index);
};

/**
 * Sets a specific step object by index.
 *
 * @method setStep
 * @param index {Integer} An integer that belongs to the position of a step
 * @param step {Object} The step object to change
 **/
$.fn.steps.setStep = function (index, step)
{
    throw new Error("Not yet implemented!");
};

/**
 * Skips an certain amount of steps.
 *
 * @method skip
 * @param count {Integer} The amount of steps that should be skipped
 * @return {Boolean} Indicates whether the action executed
 **/
$.fn.steps.skip = function (count)
{
    throw new Error("Not yet implemented!");
};

/**
 * An enum represents the different content types of a step and their loading mechanisms.
 *
 * @class contentMode
 * @for steps
 **/
var contentMode = $.fn.steps.contentMode = {
    /**
     * HTML embedded content
     *
     * @readOnly
     * @property html
     * @type Integer
     * @for contentMode
     **/
    html: 0,

    /**
     * IFrame embedded content
     *
     * @readOnly
     * @property iframe
     * @type Integer
     * @for contentMode
     **/
    iframe: 1,

    /**
     * Async embedded content
     *
     * @readOnly
     * @property async
     * @type Integer
     * @for contentMode
     **/
    async: 2
};

/**
 * An enum represents the orientation of the steps navigation.
 *
 * @class stepsOrientation
 * @for steps
 **/
var stepsOrientation = $.fn.steps.stepsOrientation = {
    /**
     * Horizontal orientation
     *
     * @readOnly
     * @property horizontal
     * @type Integer
     * @for stepsOrientation
     **/
    horizontal: 0,

    /**
     * Vertical orientation
     *
     * @readOnly
     * @property vertical
     * @type Integer
     * @for stepsOrientation
     **/
    vertical: 1
};

/**
 * An enum that represents the various transition animations.
 *
 * @class transitionEffect
 * @for steps
 **/
var transitionEffect = $.fn.steps.transitionEffect = {
    /**
     * No transition animation
     *
     * @readOnly
     * @property none
     * @type Integer
     * @for transitionEffect
     **/
    none: 0,

    /**
     * Fade in transition
     *
     * @readOnly
     * @property fade
     * @type Integer
     * @for transitionEffect
     **/
    fade: 1,

    /**
     * Slide up transition
     *
     * @readOnly
     * @property slide
     * @type Integer
     * @for transitionEffect
     **/
    slide: 2,

    /**
     * Slide left transition
     *
     * @readOnly
     * @property slideLeft
     * @type Integer
     * @for transitionEffect
     **/
    slideLeft: 3
};

var stepModel = $.fn.steps.stepModel = {
    title: "",
    content: "",
    contentUrl: "",
    contentMode: contentMode.html,
    contentLoaded: false
};

/**
 * An object that represents the default settings.
 * There are two possibities to override the sub-properties.
 * Either by doing it generally (global) or on initialization.
 *
 * @static
 * @class defaults
 * @for steps
 * @example
 *   // Global approach
 *   $.steps.defaults.headerTag = "h3";
 * @example
 *   // Initialization approach
 *   $("#wizard").steps({ headerTag: "h3" });
 **/
var defaults = $.fn.steps.defaults = {
    /**
     * The header tag is used to find the step button text within the declared wizard area.
     *
     * @property headerTag
     * @type String
     * @default "h1"
     * @for defaults
     **/
    headerTag: "h1",

    /**
     * The body tag is used to find the step content within the declared wizard area.
     *
     * @property bodyTag
     * @type String
     * @default "div"
     * @for defaults
     **/
    bodyTag: "div",

    /**
     * The content container tag which will be used to wrap all step contents.
     *
     * @property contentContainerTag
     * @type String
     * @default "div"
     * @for defaults
     **/
    contentContainerTag: "div",

    /**
     * The action container tag which will be used to wrap the pagination navigation.
     *
     * @property actionContainerTag
     * @type String
     * @default "div"
     * @for defaults
     **/
    actionContainerTag: "div",

    /**
     * The steps container tag which will be used to wrap the steps navigation.
     *
     * @property stepsContainerTag
     * @type String
     * @default "div"
     * @for defaults
     **/
    stepsContainerTag: "div",

    /**
     * The css class which will be added to the outer component wrapper.
     *
     * @property cssClass
     * @type String
     * @default "wizard"
     * @for defaults
     * @example
     *     <div class="wizard">
     *         ...
     *     </div>
     **/
    cssClass: "wizard",

    /**
     * The css class which will be used for floating scenarios.
     *
     * @property clearFixCssClass
     * @type String
     * @default "clearfix"
     * @for defaults
     **/
    clearFixCssClass: "clearfix",

    /**
     * Determines whether the steps are vertically or horizontally oriented.
     *
     * @property stepsOrientation
     * @type stepsOrientation
     * @default horizontal
     * @for defaults
     * @since 1.0.0
     **/
    stepsOrientation: stepsOrientation.horizontal,

    /*
     * Tempplates
     */

    /**
     * The title template which will be used to create a step button.
     *
     * @property titleTemplate
     * @type String
     * @default "<span class=\"number\">#index#.</span> #title#"
     * @for defaults
     **/
    titleTemplate: "<span class=\"number\">#index#.</span> #title#",

    /**
     * The loading template which will be used to create the loading animation.
     *
     * @property loadingTemplate
     * @type String
     * @default "<span class=\"spinner\"></span> #text#"
     * @for defaults
     **/
    loadingTemplate: "<span class=\"spinner\"></span> #text#",

    /*
     * Behaviour
     */

    /**
     * Sets the focus to the first wizard instance in order to enable the key navigation from the begining if `true`. 
     *
     * @property autoFocus
     * @type Boolean
     * @default false
     * @for defaults
     * @since 0.9.4
     **/
    autoFocus: false,

    /**
     * Enables all steps from the begining if `true` (all steps are clickable).
     *
     * @property enableAllSteps
     * @type Boolean
     * @default false
     * @for defaults
     **/
    enableAllSteps: false,

    /**
     * Enables keyboard navigation if `true` (arrow left and arrow right).
     *
     * @property enableKeyNavigation
     * @type Boolean
     * @default true
     * @for defaults
     **/
    enableKeyNavigation: true,

    /**
     * Enables pagination if `true`.
     *
     * @property enablePagination
     * @type Boolean
     * @default true
     * @for defaults
     **/
    enablePagination: true,

    /**
     * Suppresses pagination if a form field is focused.
     *
     * @property suppressPaginationOnFocus
     * @type Boolean
     * @default true
     * @for defaults
     **/
    suppressPaginationOnFocus: true,

    /**
     * Enables cache for async loaded or iframe embedded content.
     *
     * @property enableContentCache
     * @type Boolean
     * @default true
     * @for defaults
     **/
    enableContentCache: true,

    /**
     * Shows the cancel button if enabled.
     *
     * @property enableCancelButton
     * @type Boolean
     * @default false
     * @for defaults
     **/
    enableCancelButton: false,

    /**
     * Shows the finish button if enabled.
     *
     * @property enableFinishButton
     * @type Boolean
     * @default true
     * @for defaults
     **/
    enableFinishButton: true,

    /**
     * Not yet implemented.
     *
     * @property preloadContent
     * @type Boolean
     * @default false
     * @for defaults
     **/
    preloadContent: false,

    /**
     * Shows the finish button always (on each step; right beside the next button) if `true`. 
     * Otherwise the next button will be replaced by the finish button if the last step becomes active.
     *
     * @property showFinishButtonAlways
     * @type Boolean
     * @default false
     * @for defaults
     **/
    showFinishButtonAlways: false,

    /**
     * Prevents jumping to a previous step.
     *
     * @property forceMoveForward
     * @type Boolean
     * @default false
     * @for defaults
     **/
    forceMoveForward: false,

    /**
     * Saves the current state (step position) to a cookie.
     * By coming next time the last active step becomes activated.
     *
     * @property saveState
     * @type Boolean
     * @default false
     * @for defaults
     **/
    saveState: false,

    /**
     * The position to start on (zero-based).
     *
     * @property startIndex
     * @type Integer
     * @default 0
     * @for defaults
     **/
    startIndex: 0,

    /*
     * Animation Effect Configuration
     */

    /**
     * The animation effect which will be used for step transitions.
     *
     * @property transitionEffect
     * @type transitionEffect
     * @default none
     * @for defaults
     **/
    transitionEffect: transitionEffect.none,

    /**
     * Animation speed for step transitions (in milliseconds).
     *
     * @property transitionEffectSpeed
     * @type Integer
     * @default 200
     * @for defaults
     **/
    transitionEffectSpeed: 200,

    /*
     * Events
     */

    /**
     * Fires before the step changes and can be used to prevent step changing by returning `false`. 
     * Very useful for form validation. 
     *
     * @property onStepChanging
     * @type Event
     * @default function (event, currentIndex, newIndex) { return true; }
     * @for defaults
     **/
    onStepChanging: function (event, currentIndex, newIndex) { return true; },

    /**
     * Fires after the step has change. 
     *
     * @property onStepChanged
     * @type Event
     * @default function (event, currentIndex, priorIndex) { }
     * @for defaults
     **/
    onStepChanged: function (event, currentIndex, priorIndex) { },

    /**
     * Fires after cancelation. 
     *
     * @property onCanceled
     * @type Event
     * @default function (event) { }
     * @for defaults
     **/
    onCanceled: function (event) { },

    /**
     * Fires before finishing and can be used to prevent completion by returning `false`. 
     * Very useful for form validation. 
     *
     * @property onFinishing
     * @type Event
     * @default function (event, currentIndex) { return true; }
     * @for defaults
     **/
    onFinishing: function (event, currentIndex) { return true; },

    /**
     * Fires after completion. 
     *
     * @property onFinished
     * @type Event
     * @default function (event, currentIndex) { }
     * @for defaults
     **/
    onFinished: function (event, currentIndex) { },

    /**
     * Fires after async content is loaded. 
     *
     * @property onContentLoaded
     * @type Event
     * @default function (event, index) { }
     * @for defaults
     **/
    onContentLoaded: function (event, currentIndex) { },

    /**
     * Fires when the wizard is initialized. 
     *
     * @property onInit
     * @type Event
     * @default function (event) { }
     * @for defaults
     **/
    onInit: function (event, currentIndex) { },

    /**
     * Contains all labels. 
     *
     * @property labels
     * @type Object
     * @for defaults
     **/
    labels: {
        /**
         * Label for the cancel button.
         *
         * @property cancel
         * @type String
         * @default "Cancel"
         * @for defaults
         **/
        cancel: "Cancel",

        /**
         * This label is important for accessability reasons.
         * Indicates which step is activated.
         *
         * @property current
         * @type String
         * @default "current step:"
         * @for defaults
         **/
        current: "current step:",

        /**
         * This label is important for accessability reasons and describes the kind of navigation.
         *
         * @property pagination
         * @type String
         * @default "Pagination"
         * @for defaults
         * @since 0.9.7
         **/
        pagination: "Pagination",

        /**
         * Label for the finish button.
         *
         * @property finish
         * @type String
         * @default "Finish"
         * @for defaults
         **/
        finish: "Finish",

        /**
         * Label for the next button.
         *
         * @property next
         * @type String
         * @default "Next"
         * @for defaults
         **/
        next: "Next",

        /**
         * Label for the previous button.
         *
         * @property previous
         * @type String
         * @default "Previous"
         * @for defaults
         **/
        previous: "Previous",

        /**
         * Label for the loading animation.
         *
         * @property loading
         * @type String
         * @default "Loading ..."
         * @for defaults
         **/
        loading: "Loading ..."
    }
};
})(jQuery);