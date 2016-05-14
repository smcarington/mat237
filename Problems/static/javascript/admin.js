$('document').ready(function() {
    // Poll administration 
    $('[id^="check"]').click( function() {
        var question = $(this).attr('id').split('_')[1];
        var live     = $(this).is(':checked');
        $.post('/make_live/', {question: question, live: live}, 
            function(data) {
                $response = $("#response_"+question);
                $response.html(data['response']);
                setTimeout( function() {$response.html('')}, 2000);
        }, "json");
    });

    // When a button is clicked (that is, the start/stop/reset buttons), determine 
    // the appropriate action and send the server the appropriate response
    $('button').click( function() {
        [action, pk] = $(this).attr('id').split('_');
        $.post('/live_question/', {action: action, questionpk: pk},
            function(data) {
                if (action=='endall') {
                    $('[id^="response"]').html(data['response']);
                    setTimeout( function() {$('[id^="response"]').html('')}, 2000);
                } else {
                    $response = $("#response_"+pk);
                    $response.html(data['response']);
                    setTimeout( function() {$response.html('')}, 2000);
                }
            }, "json");
    });
});
