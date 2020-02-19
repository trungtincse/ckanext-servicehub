function requestService(action_url, name, port, form) {
  data = $(form).serialize();
  $($.ajax({
    url: action_url,
    type: 'post',
    data: { url_part: `${name}:${port}/proxy/?${data}` },
    success: function (rs) {
      //whatever you wanna do after the form is successfully submitted
      alert(rs['result']);
    }
  }));
}
function requestCodeService(dom, name) {
  data = dom.val();
  var settings = {
    "url": `http://localhost:5001/execute/${name}`,
    "method": "POST",
    "timeout": 0,
    "data": data,
  };

  $.ajax(settings).done(function (response) {
    if (response["error"] != "")
      alert(response["error"]);
    else {
      callId=response["callId"]
      saveResult(callId);
    }
  });
}


function getResult(callId) {
  var settings = {
    "url": `/call/60fe7d3d-287f-11ea-909d-9f18f0f391fc`,
    "method": "GET",
    "timeout": 0,
  };
  $.ajax(settings).done(function (response) {
    console.log(response);
  });
}
function createCall() {
  var settings = {
    "url": `/call/create/${callId}`,
    "method": "POST",
    "timeout": 0,
  };
  $.ajax(settings).done(function (response) {
    console.log(response);
  });
}
