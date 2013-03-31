$(document).ready(function() {

	$('select').change(function() {
    	var id = $(this).find("option:selected").attr("id");

  		switch (id){
    		case "play":
    			$('<div id="bet_field"> <label> Bet </label> <input type="number"> </div>').appendTo('#do_action')
    		case "draw":
    		case "fold":
    			$("#bet_field").remove();


      	break;
  	}
	}).trigger('change');
	/*
	(function poll(){
    	setTimeout(function(){
        	$.ajax({ url: String(window.location.pathname), success: function(data){
            	console.log("Polling!");
        	}, complete: poll, timeout: 500,type: "GET"});
    	}, 500);
	})();


    channel = new goog.appengine.Channel('{{ token }}');
    socket = channel.open();
    
    socket.onopen = onOpened;
    socket.onmessage = onMessage;
    socket.onerror = onError;
    socket.onclose = onClose;
    */
})
