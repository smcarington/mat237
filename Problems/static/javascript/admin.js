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
        // Highlight the appropriate div so it is easy to see
        if (action == 'start') {
            color = "#c2c2c2";
        } else if (action == 'stop') {
            color = "transparent"
        }
        $(".div-"+pk).css("background-color", color);
    });

    // Opens choices option in poll administration
    $("[id^='open']").click( function () {
        qpk = $(this).attr('id').split('-')[1];
        $target = $("#"+qpk+"-choices");
        if ($target.is(":visible") ) {
            $target.hide(300);
        } else {
            $target.show(300);
        }
    });

    // Helper function for swapping two elements
    function swapDiv(element, order) {
        if (order == "up") { 
            element.parent().insertBefore(element, element.previousSibling);
        } else if (order == "down") {
            element.parentNode.insertBefore(element.nextSibling, element);
        }
    }

    // Listener for moving arrows.
    $("[id^='arrow']").click( function() {
        [pre, action, pk] = $(this).attr('id').split('-');
        // Find the appropriate div. It is the grandparent, not great grandparent
        $thisDiv = $(this).parents("#global-"+pk)
        if (action == "up") {
            $thisDiv.insertBefore($thisDiv.prev("[id^='global']"));
        } else if (action == "down") {
            $thisDiv.next("[id^='global']").insertBefore($thisDiv);
        }
        $.post('/change_question_order/', {action:action, pk:pk},
        "json");
    });

    // Check to see how many votes have been cast
    function voteCheck() {
        $.get('/query_live/', 
            function(data) {
                [pk, state] = data['state'].split('-');
                if (state == 'True') {
                    $("#votes-"+pk).html("Total Votes: "+data['numVotes']);
                } else if (state == 'False') {
                    $("#votes-"+pk).html('');
                }
            }, 
        "json");
        setTimeout(voteCheck, 5000);
    }
    // Start the method to check if votes have been cast
    setTimeout(voteCheck, 5000);
});
