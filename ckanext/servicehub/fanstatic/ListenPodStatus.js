// const evtSource = new EventSource("http://192.168.1.102:8001/api/v1/watch/namespaces/default/events?watch=true");
// evtSource.onmessage = function(event) {
//   const newElement = document.createElement("li");
//   const eventList = document.getElementById("list");
//
//   newElement.innerHTML = "message: " + event.data;
//   eventList.appendChild(newElement);
// }