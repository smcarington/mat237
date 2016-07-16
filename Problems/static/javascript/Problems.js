$(document).ready(function() {

    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
            return cookieValue;
    }
    var csrftoken = getCookie('csrftoken'); 

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
        }
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
    
    // Select all li items whose class begins with "diff". These are the problems.
    // Pass them to autorender
    $('[class^="diff"]').each( function () {
        renderMathInElement( $(this)[0] );
    });

    var curFunHandle;

    $('.ajax-form').change( function() {
        use = $('#user').val()
        que = $('#question').val()
        att = $('#attempted').is(':checked');
        sol = $('#solved').is(':checked');
        dif = $('#difficulty').val();

        if (parseInt(dif) > 10) {
            $('#difficulty').val('10');
            dif = '10'
        } else if (parseInt(dif)<1) {
            $('#difficulty').val('1');
            dif = '1'
        }
        
        if (curFunHandle) {
            clearTimeout(curFunHandle);
            curFunHandle = null;
        }
        
        curFunHandle = setTimeout( function() {
            $.post('/update_status/', {attempted: att, solved: sol, difficulty: dif, user: use, question:que}, 
                function(data, status) {
                    $response = $("#response");
                    $response.html(data['response']);
                    setTimeout( function() {$response.html('') }, 2000);
            }, "json")
        },1000);
    });

    // adds a datepicker jquery ui element to dates
    //$('#id_expires').datepicker()
    //$('#id_live').datepicker()
    jQuery('#id_expires').datetimepicker(
            { format:'Y-m-d H:i',
            });
    jQuery('#id_live').datetimepicker(
            { format:'Y-m-d H:i',
            });
    

    // gets old announcements and inserts them into the page
    $('#get_old').click( function() {
        $.get('/get_old_announcements/', {}, function(data) {
            $('.old-ann').html(data);
        });
    });

    // On Problem set page, deal with ability to print questions and solutions.
    // First, nice JS for "all" checkboxes. Unnecessary but nice.
    $("[id$='-all']").click( function() {
        qs=$(this).attr('id').split('')[0]
        $("[name^='"+qs+"-']").prop("checked", $(this).is(":checked"));
    });

    // Cannot include solution without text
    $("[name^='s-']").click( function() {
        var thisNum = $(this).attr('name').split('-')[1];
        $("[name='q-"+thisNum+"']").prop("checked",true);
    });

    // Now deal with the button press. Harvest the selected questions and send this list
    // to the server
    $('#pdflatex').click(function () {
        // Check to see if the 'all' buttons have been pushed
        var ps     = $('#problem-set').val();
        var allbox = {"q": false, "a": false};
        var qbox   = [];
        if ($("#q-all").is(":checked")) {
            allbox["q"] = true;
        }
        if ($("#s-all").is(":checked")) {
            allbox["s"] = true;
        }

        $("[name^='q-']").each( function () {
            if ($(this).is(":checked")) {
                var thisNum = $(this).attr('name').split('-')[1];
                sol = $("[name='s-"+thisNum+"'").is(":checked");

                qbox.push({"number": thisNum, "sol":sol});
            }
        });

        $.post("/pdflatex/", JSON.stringify({"all": allbox, "questions": qbox, "problem_set": ps}), 
                function(data) {
                    $response = $("#response");
                    $response.html(data['response']);
                    setTimeout( function() {$response.html('') }, 2000);
                },
        "json");
    });

    $('span.choice-remove').click( function() {
        data_id = $(this).attr('data-id');
        $('[data-id='+data_id+']').remove();
        $('form').submit();
    });


    if ($("#id_q_type option:selected").text() != "Multiple Choice") {
        $("#id_mc_choices").prop("disabled", true);
    }

    $("#id_q_type").change( function() {
        if ($(this).find("option:selected").text() == 'Multiple Choice') {
            $("#id_mc_choices").prop('disabled', false);
        } else {
            $("#id_mc_choices").prop('disabled', true);
        }
    });
});
