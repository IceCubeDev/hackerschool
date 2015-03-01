<?php

/**
 * @package Google Maps
 */
/*
Plugin Name: GMaps
Plugin URI: http://localhost/
Description: Used to embed google maps in posts.
Version: 1.0.0
Author: Ivan Dortulov
Author URI: https://github.com/IceCubeDev
License: GPLv2 or later
Text Domain: gmaps
*/

function gmaps_func( $atts ){
	return "<iframe
  				width=\"800\"
  				height=\"480\"
  				frameborder=\"0\" 
  				style=\"border:0\"
  				src=\"/wp-content/plugins/google_maps/_inc/search.html\"></iframe>";
}
add_shortcode( 'map', 'gmaps_func' );

?>