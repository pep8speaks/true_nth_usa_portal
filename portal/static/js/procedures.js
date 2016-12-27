$.fn.extend({
    // Special type of select question - passes two values - the answer from
    // the select plus an associated date from a separate input
    eventInput: function(settings) {
        $(this).on("click", function() {

            // First disable button to prevent double-clicks
            $(this).attr('disabled', true);

            var selectVal = $(this).attr('data-name');
            var selectDate = $(this).attr('data-date');
            // Only continue if both values are filled in
            if (selectVal !== undefined && selectDate !== undefined) {

                // Submit the data
                var procArray = {};
                var selectFriendly = $("#tnthproc option:selected").text();
                var procID = [{ "code": selectVal, "display": selectFriendly,
                    system: "http://snomed.info/sct" }];
                procArray["resourceType"] = "Procedure";
                procArray["subject"] = {"reference": "Patient/" + subjectId };
                procArray["code"] = {"coding": procID};
                procArray["performedDateTime"] = selectDate;
                tnthAjax.postProc(subjectId,procArray);

                // Update the procedure list - we animate opacity to retain the
                // width and height so lower content doesn't go up and down
                $("#userProcedures").animate({opacity: 0}, function() {
                    $(this).html(eventLoading).css('opacity',1);
                    // Clear the inputs
                    $("select[id^='tnthproc']").val('');
                    $("input[id^='tnthproc-value']").val('');
                    $("input[id^='tnthproc-date']").val('');
                    $("#procDay").val("");
                    $("#procMonth").val("");
                    $("#procYear").val("");
                    // Clear submit button
                    $("button[id^='tnthproc-submit']").addClass('disabled').attr({
                        "data-name": "",
                        "data-date": "",
                        "data-date-read": ""
                    });
                    // Set a one second delay before getting updated list. Mostly to give user sense of progress/make it
                    // more obvious when the updated list loads
                    setTimeout(function(){
                        tnthAjax.getProc(subjectId,true);
                    },1000);

                });
            }

            return false;
        });
    }
}); // $.fn.extend({

var eventLoading = '<div style="margin: 1em" id="eventListLoad"><i class="fa fa-spinner fa-spin fa-2x loading-message"></i></div>';
var procDateReg =  /(0[1-9]|1\d|2\d|3[01])/;
var procYearReg = /(19|20)\d{2}/;

$(document).ready(function() {

    // Options for datepicker - prevent future dates, no default
    $('.event-element .input-group.date').each(function(){
        $(this).datepicker({
            format: 'dd/mm/yyyy',
            endDate: "0d",
            startDate: "-10y",
            autoclose: true,
            forceParse: false
        });
    });

    // Trigger eventInput on submit button
    $("button[id^='tnthproc-submit']").eventInput();

    // Add/remove disabled from submit button

    function checkSubmit(btnId) {

        if ($(btnId).attr("data-name") != "" && $(btnId).attr("data-date-read") != "") {
            // We trigger the click here. The button is actually hidden so user doesn't interact with it
            // TODO - Remove the button completely and store the updated values elsewhere
            $(btnId).removeClass('disabled').removeAttr('disabled').trigger("click");
        } else {
            $(btnId).addClass('disabled').attr('disabled',true);
        };
    };

    function isLeapYear(year)
    {
      return ((year % 4 == 0) && (year % 100 != 0)) || (year % 400 == 0);
    };

    function checkDate() {
        var d = $("#procDay").val(), m = $("#procMonth").val(), y = $("#procYear").val();
        if (!isNaN(parseInt(d))) {
            if (parseInt(d) > 0 && parseInt(d) < 10) d = "0" + d;
        };

        var dTest = procDateReg.test(d);
        var mTest = (m != "");
        var yTest = procYearReg.test(y);
        var errorText = "The procedure date must be valid and in required format.";
        var dgField = $("#procDateGroup");
        var deField = $("#procDateErrorContainer");
        var errorColor = "#a94442";
        var validColor = "#777";

        if (dTest && mTest && yTest) {

            if (parseInt(m) === 2) { //month of February
                if (isLeapYear(parseInt(y))) {
                    if (parseInt(d) > 29)  {
                        deField.text(errorText).css("color", errorColor);
                        return false;
                    };
                } else {
                    if (parseInt(d) > 28) {
                        dgField.addClass("has-error");
                        deField.text(errorText).css("color", errorColor);
                        return false;
                    };
                };
                deField.text("").css("color", validColor);
                return true;
            } else {
                deField.text("").css("color", validColor)
                return true;
            };

        } else {
            errorText = "";
            if ((d != "") && (y != "") && (m != "")) {
                if (!dTest) errorText += "Procedure day is not valid.";
                if (!mTest) errorText += (errorText != "" ? "<br/>": "")  +  "Procedure month is not valid.";
                if (!yTest) errorText += (errorText != "" ? "<br/>": "") + "Procedure year is not valid.";
                deField.html(errorText).css("color", errorColor);
            };
            return false;
        };
    };

    function setDate() {
        var passedDate = dateFields.map(function(fn) {
            fd = $("#" + fn);
            if (fd.attr("type") == "text") return fd.val();
            else return fd.find("option:selected").val();
        }).join("/");
        //console.log("passedDate: " + passedDate);
        $("button[id^='tnthproc-submit']").attr('data-date-read',passedDate);
        dateFormatted = tnthDates.swap_mm_dd(passedDate);
        //console.log("formatted date: " + dateFormatted);
        $("button[id^='tnthproc-submit']").attr('data-date',dateFormatted);
        checkSubmit("button[id^='tnthproc-submit']");

    };


    // Update submit button when select changes
    $("select[id^='tnthproc']").on('change', function() {
        $("button[id^='tnthproc-submit']").attr("data-name", $(this).val());
        checkSubmit("button[id^='tnthproc-submit']");
    });
    // Update submit button when text input changes (single option)
    //datepicker field
    $("input[id^='tnthproc-value']").on('change', function() {
        $("button[id^='tnthproc-submit']").attr("data-name", $(this).val());
        checkSubmit("button[id^='tnthproc-submit']");
    });

    // When date changes, update submit button w/ both mm/dd/yyyy and yyyy-mm-dd
    var dateFields = ["procDay", "procMonth", "procYear"];

    dateFields.forEach(function(fn) {
        var triggerEvent = $("#" + fn).attr("type") == "text" ? "blur": "change";
        $("#" + fn).on(triggerEvent, function() {
            var isValid = checkDate();
            //console.log("isValid: " +  isValid)
            if (isValid) {
                setDate();
            };
        });
    });

    $("input[id^='tnthproc-date']").on('change', function( event ) {
        var passedDate = $(this).val(); // eg "11/20/2016"
        //passedDate = tnthDates.swap_mm_dd(passedDate);
        //$("button[id^='tnthproc-submit']").attr('data-date-read',passedDate);
        var dateFormatted;
        // Change dates to YYYY-MM-DD
        //and make sure date is in dd/mm/yyyy format before reformat
        if (passedDate && passedDate != '' && /^(0[1-9]|[12][0-9]|3[01])[\/](0[1-9]|1[012])[\/]\d{4}$/.test(passedDate)) {
            $("button[id^='tnthproc-submit']").attr('data-date-read',passedDate);
            dateFormatted = tnthDates.swap_mm_dd(passedDate);
            console.log("formatted date: " + dateFormatted);
            $("button[id^='tnthproc-submit']").attr('data-date',dateFormatted);
            checkSubmit("button[id^='tnthproc-submit']");
        }

    });

    /*** Delete functions ***/
    $('body').on('click', '.cancel-delete', function() {
        $(this).parents("div.popover").prev('a.confirm-delete').trigger('click');
    });
    // Need to attach delete functionality to body b/c section gets reloaded
    $("body").on('click', ".btn-delete", function() {
        var procId = $(this).parents('tr').attr('data-id');
        // Remove from list
        $(this).parents('tr').fadeOut('slow', function(){
            $(this).remove();
            // If there's no events left, add status msg back in
            if ($('#eventListtnthproc tr').length == 0) {
                $("body").find("#userProcedures").html("<p id='noEvents' style='margin: 0.5em 0 0 1em'><em>You haven't entered any treatments yet.</em></p>").animate({opacity: 1});
            }
        });
        // Post delete to server
        tnthAjax.deleteProc(procId);
        return false;
    });

});
