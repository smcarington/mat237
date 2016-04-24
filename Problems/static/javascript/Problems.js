$('document').ready(function() {
    
    // Select all li items whose class begins with "diff". These are the problems.
    // Pass them to autorender
    $('[class^="diff"]').each( function () {
        renderMathInElement( $(this)[0] );
    });

    var curFunHandle;

    $('.ajax-form').change( function() {
        if (curFunHandle) {
            clearTimeout(curFunHandle);
            curFunHandle = null;
        }
        var that = this;
        
        curFunHandle = setTimeout( function() {
            that.submit()}, 1000);
    });
});


