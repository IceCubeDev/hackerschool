var map,						// The google map instance
	 geodecoder,			// Instance of the geodecoder
	 myCenter,				// The starting point on the map
	 infoWindows = [],	// Information window
	 results = [];			// List of markers being displayed on the map

// Initialize google maps	 
function initialize() {
	// Set the center on Sofia
	myCenter = new google.maps.LatLng(42.7,  23.3333333);
	
	// Set map center, zoom and type
	var mapOptions = {
   	center: myCenter,
      zoom: 14,
      mapTypeId: google.maps.MapTypeId.ROADMAP
  	};
  	
  	// Create the map
  	map = new google.maps.Map(document.getElementById("map_canvas"), mapOptions);
  	
	// Create the geodecoder
	geocoder = new google.maps.Geocoder();
	
	infoWindow = new google.maps.InfoWindow();
	
	document.getElementById('keyword').onkeyup = function(e) {
      if (!e) var e = window.event;
      if (e.keyCode != 13) return;
      document.getElementById('keyword').blur();
      searchRestNear(document.getElementById('keyword').value);
   }
   
   document.getElementById('search-button').onclick = function() {
		searchRestNear(document.getElementById('keyword').value);
   }
	//searchRestNear("Яворов, ул. Цар Иван Асен II 66");
}



// Generates a list of all establishments within a 300 meter radius of a
// given address
function searchRestNear(address) {
	// First clear previous markers
	clearMarkers();
	// Find the address location and search for nearby establishments
	geocoder.geocode( { 'address': address}, function(results, status) {
   	if (status == google.maps.GeocoderStatus.OK) {
   		findByLocation(results[0].geometry.location);
   	}
	});
}

function findByLocation(coords) {
	// Clear all markers from the map
	//clearMarkers();	
	
	downloadUrl("download_info.php?coord=" + coords.toUrlValue(), function(data){
		var xml = data.responseXML;
   	var markers = xml.documentElement.getElementsByTagName("marker");
      
   	// Iterate through the results
   	for (var i = 0; i < markers.length; i++) {
     		// Get information
      	var id  = markers[i].getAttribute("id");
      	var name = markers[i].getAttribute("name");
      	var address = markers[i].getAttribute("address");
      	var type = markers[i].getAttribute("type");
      	var point = new google.maps.LatLng(
             parseFloat(markers[i].getAttribute("lat")),
             parseFloat(markers[i].getAttribute("lng")));
      	var icon = "images/number_" + (i + 1) +".png";
      	var description = markers[i].getAttribute("description");
         
         results.push(new google.maps.Marker({
    			position: point,
    			map: map,
    			icon: icon,
    			type: type,
    			title: name
  	  		}));
  	  		
			infoWindows.push(new google.maps.InfoWindow({
				content: description
			}));  	  		
  	  		
  	  		google.maps.event.addListener(results[i], 'click', showInfo(results[i], i));
     		addResult(results[i], i);
  	  	}
	});
}

function addResult(result, i) {
    var result_table = document.getElementById('results');
    var tr = document.createElement('tr');
    tr.style.backgroundColor = (i% 2 == 0 ? '#F0F0F0' : '#FFFFFF');
    tr.onclick = function() {
      	google.maps.event.trigger(results[i], 'click');
    };

    var iconTd = document.createElement('td');
    var nameTd = document.createElement('td');
    var icon = document.createElement('img');
    icon.src = 'images/number_' + (i+1) + '.png';
    icon.setAttribute('class', 'placeIcon');
    icon.setAttribute('className', 'placeIcon');
    var name = document.createTextNode(result.title);
    iconTd.appendChild(icon);
    nameTd.appendChild(name);
    tr.appendChild(iconTd);
    tr.appendChild(nameTd);
    result_table.appendChild(tr);
}

// Show information about an establishment
function showInfo(marker, i) {
	return function() {
		map.panTo(marker.position);
		infoWindows[i].open(map, marker);
	}
}

// Remove all markers from the map
function clearMarkers() {
	for (i = 0; i < results.length; i ++) {
		results[i].setMap(null);
	}
	results.splice(1, results.length);
}

// Request information from URL
function downloadUrl(url,callback) {
 var request = window.ActiveXObject ?
     new ActiveXObject('Microsoft.XMLHTTP') :
     new XMLHttpRequest;

 request.onreadystatechange = function() {
   if (request.readyState == 4) {
     request.onreadystatechange = doNothing;
     callback(request, request.status);
   }
 };

 request.open('GET', url, true);
 request.send(null);
}

function doNothing() {}

// Set the initialization function
google.maps.event.addDomListener(window, 'load', initialize);