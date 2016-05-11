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
});
