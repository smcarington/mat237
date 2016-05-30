$(document).ready(function() {
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
        preData = $(this).attr('id').split('_');
        action  = preData[0];
        pk      = preData[1];
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
                // When resetting a question, we must replace the choice pk's. In this instance only, the
                // response item contains a pk map whose keys are the old pk's, and whose values are the new pk's
                if (action=='reset') {
                    pkMap = data['pkMap'];
                    $("#"+pk+"-choices>ol>li>p>small").each( function() {
                        // Determine the old pk, which is the field for the new pk
                        idString = $(this).attr('id').split('-');
                        newIDString = pkMap[idString[0]]+"-votes";
                        $(this).attr('id', newIDString);
                        $(this).html("(0 votes)");
                    });
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
        preData = $(this).attr('id').split('-');
        pre    = preData[0];
        action = preData[1];
        pk     = preData[2];
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
                preData = data['state'].split('-');
                pk      = preData[0];
                state   = preData[1];
                delete data['state']
                if (state == 'True') {
                    $("#votes-"+pk).html("Total Votes: "+data['numVotes']);
                    delete data['numVotes'];
                    Object.keys(data).forEach(function (key) {
                        $("#"+key).html("("+data[key]+" votes)");
                    });
                } else if (state == 'False') {
                    $("#votes-"+pk).html('');
                }
            }, 
        "json");
        setTimeout(voteCheck, 2000);
    }
    // Start the method to check if votes have been cast
    setTimeout(voteCheck, 2000);
});
