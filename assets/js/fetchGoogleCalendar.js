/* https://kb.zensoft.hu/javascript-to-display-a-public-google-calendar-as-a-list-on-your-website/
* This solution makes use of "simple access" to google, providing only an API Key.
* This way we can only get access to public calendars. To access a private calendar,
* we would need to use OAuth 2.0 access.
*
* "Simple" vs. "Authorized" access: https://developers.google.com/api-client-library/javascript/features/authentication
* Examples of "simple" vs OAuth 2.0 access: https://developers.google.com/api-client-library/javascript/samples/samples#authorizing-and-making-authorized-requests
*
* We will make use of "Option 1: Load the API discovery document, then assemble the request."
* as described in https://developers.google.com/api-client-library/javascript/start/start-js

Example:
<script src="https://cdn.jsdelivr.net/npm/moment@2/moment.min.js"></script>
<script src="https://apis.google.com/js/api.js"></script>
<script src="{{ '/assets/js/fetchGoogleCalendar.js' | relative_url }}"></script>

<script>
  var maxResults = 2;  // for fetchGoogleCalendarEvents() in fetchGoogleCalendar.js

  // fetchGoogleCalendarEvents() in fetchGoogleCalendar.js will call show(items) after success.
  function show(items) {
    var calendarRows = ['<table class="wellness-calendar"><tbody>'];
    items.forEach(function (entry) {
      var startsAt = moment(entry.start.dateTime).format("L") + ' ' + moment(entry.start.dateTime).format("LT");
      var endsAt = moment(entry.end.dateTime).format("LT");
      calendarRows.push(`<tr><td>${startsAt} - ${endsAt}</td><td>${entry.summary}</td></tr>`);
    });
    calendarRows.push('</tbody></table>');
    $('#wellness-calendar').html(calendarRows.join(""));
  }

  // Loads the JavaScript client library and invokes `start` afterwards.
  gapi.load('client', fetchGoogleCalendarEvents);
</script>
*/

function fetchGoogleCalendarEvents() {
  /*
  * To use this function, 
  * * Include "https://cdn.jsdelivr.net/npm/moment@2/moment.min.js" and "https://apis.google.com/js/api.js".
  * * predefine an int var maxResults and function show(items).
  * * call gapi.load('client', fetchGoogleCalendarEvents);
  * See example at the top.
  */
  // The "Calendar ID" from your calendar settings page, "Calendar Integration" secion:
  var calendarId = 'ekol7ulqm14nv155angut2rlfo@group.calendar.google.com';

  // 1. Create a project using google's wizzard: https://console.developers.google.com/start/api?id=calendar
  // 2. Create credentials:
  //    a) Go to https://console.cloud.google.com/apis/credentials
  //    b) Create Credentials / API key
  //    c) Since your key will be called from any of your users' browsers, set "Application restrictions" to "None",
  //       leave "Website restrictions" blank; you may optionally set "API restrictions" to "Google Calendar API"
  var apiKey = 'AIzaSyBq6TTVUkWGCs0vmGh1XlIuGn0w5dCtbsA';
  // You can get a list of time zones from here: http://www.timezoneconverter.com/cgi-bin/zonehelp
  // var userTimeZone = "Europe/Budapest";
  // var userTimeZone = gapi.client.calendar.events.list;

  // Initializes the client with the API key and the Translate API.
  gapi.client.init({
    'apiKey': apiKey,
    // Discovery docs docs: https://developers.google.com/api-client-library/javascript/features/discovery
    'discoveryDocs': ['https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest'],
  }).then(function () {
    // Use Google's "apis-explorer" for research: https://developers.google.com/apis-explorer/#s/calendar/v3/
    // Events: list API docs: https://developers.google.com/calendar/v3/reference/events/list
    return gapi.client.calendar.events.list({
      'calendarId': calendarId,
      'singleEvents': true,
      'timeMin': (new Date()).toISOString(), //gathers only events not happened yet
      'maxResults': maxResults,
      'orderBy': 'startTime'
    });
  }).then(function (response) {
    if (response.result.items) {
      show(response.result.items);
    }
  }, function (reason) {
    console.log('Error: ' + reason.result.error.message);
  });
};