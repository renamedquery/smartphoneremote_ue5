//SERVER status
var ws_status = new WebSocket("ws://127.0.0.1:9090/status");

setInterval(function(){
  var displayed_status="None";
  var displayed_status_color = 'White';

  switch (ws_status.readyState) {
    case 0:
      displayed_status = "connecting";
     break;
    case 1:
      displayed_status = "connected";
     break;
    case 2:
       displayed_status = "closing";
     break;
    case 3:
        displayed_status = "closed";
      break;
    default:
        displayed_status = "none";
  }
   document.getElementById('server_status').innerHTML = displayed_status;}, 5000);
