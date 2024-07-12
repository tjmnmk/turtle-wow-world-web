chat_max_top = 0;
chat_current_top = 0;
chat_enable_rd = true;
vis_counter = 0;
down = true;
message_id = -1;
chat_enable_rd = true;

var vis = (function(){
    var stateKey, eventKey, keys = {
        hidden: "visibilitychange",
        webkitHidden: "webkitvisibilitychange",
        mozHidden: "mozvisibilitychange",
        msHidden: "msvisibilitychange"
    };
    for (stateKey in keys) {
        if (stateKey in document) {
            eventKey = keys[stateKey];
            break;
        }
    }
    return function(c) {
        if (c) document.addEventListener(eventKey, c);
        return !document[stateKey];
    }
})();

$.fn.selectRange = function(start, end) {
    if(!end) end = start;
    return this.each(function() {
        if (this.setSelectionRange) {
            this.focus();
            this.setSelectionRange(start, end);
        } else if (this.createTextRange) {
            var range = this.createTextRange();
            range.collapse(true);
            range.moveEnd('character', end);
            range.moveStart('character', start);
            range.select();
        }
    });
};

function sleep(milliseconds) {
  var start = new Date().getTime();
  for (var i = 0; i < 1e7; i++) {
    if ((new Date().getTime() - start) > milliseconds){
      break;
    }
  }
}

(function($) {
    $.fn.getCursorPosition = function() {
        var input = this.get(0);
        if (!input) return; // No (input) element found
        if ('selectionStart' in input) {
            // Standard-compliant browsers
            return input.selectionStart;
        } else if (document.selection) {
            // IE
            input.focus();
            var sel = document.selection.createRange();
            var selLen = document.selection.createRange().text.length;
            sel.moveStart('character', -input.value.length);
            return sel.text.length - selLen;
        }
    }
})(jQuery);

function ChatUpdate() {
	vis_counter_cap = 0;

	if(!vis()) {
		if(vis_counter == vis_counter_cap) {
			vis_counter = 0;
		}
		else {
			vis_counter++;
			return;
		}
	}

	$.ajax({
		type: "GET",
		url: "update2.php",
		async: true,
        data: {message_id: message_id},
		dataType: "json",
		success: function(data) {
			if(data.messages) {
				$('#obsah').append(data.messages);
				// scroll down if was scrolled
                $('#obsah').scrollTop($('#obsah')[0].scrollHeight);
			}
            message_id = data.client_message_id;
		}
	})
}

// chat_enabled_rd
