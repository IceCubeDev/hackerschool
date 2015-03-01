<?php

define("POST_CLASS", "post 	  ");
define("IMAGE_CLASS", "listing_image_img");
define("LISTING_CLASS", "listing_info");

function find_restaurant_near($lat, $lng) {
    $con = @ mysqli_connect('localhost', 'root', '089860');
    if (!$con) echo "Unable to connect: ".mysqli_error($con);
    
    $db = mysqli_select_db($con, 'wordpress');
    if (!$db) echo "Unable to select database: ".mysqli_error($con);
    
    $query = sprintf("SELECT *,  ( 3959 * acos( cos( radians('%s') ) * cos( radians( lat ) ) * cos( radians( lng ) - radians('%s') ) + sin( radians('%s') ) * sin( radians( lat ) ) ) ) AS distance
				  FROM `markers`
				  HAVING distance < '%s'
              ORDER BY distance LIMIT 0, 20",
              $lat, $lng, $lat, 0.8);
    //$query = "SELECT * FROM markers";
    $result = $con->query($query);
    if (!$result) echo mysql_error();
    
    $doc = new DOMDocument('1.0', 'utf-8');
    $node = $doc->createElement("markers");
    $parnode = $doc->appendChild($node);

    
    while (@$row = mysqli_fetch_array($result)) {
        // ADD TO XML DOCUMENT NODE
        $node = $doc->createElement("marker");
        $newnode = $parnode->appendChild($node);
        
        $newnode->setAttribute("id", $row['id']);
        $newnode->setAttribute("name", $row['name']);
        $newnode->setAttribute("address", $row['address']);
        $newnode->setAttribute("lat", $row['lat']);
        $newnode->setAttribute("lng", $row['lng']);
        $newnode->setAttribute("type", 'restaurant');
        $newnode->setAttribute("description", $row['description']);
    }
    
    mysqli_close($con);
    return $doc->saveXML();
}

function download_info($url_base) {
	// Create DOM from URL
	$html = new DOMDocument();
	@$html->loadHTMLFile($url_base);
	//$html->loadHTML($url);

	// Find all article blocks
	$items = array();
	$entry = array();

	$divs = $html->getElementsByTagName('div');
	for ($i = 0; $i < $divs->length; $i ++) {
		$div = $divs->item($i);
		
		if ($div->hasAttribute('class')) {
			// This is the start of a post
			if ($div->getAttribute('class') == POST_CLASS) {
				$post = $div->getElementsByTagName('div');
				
				for ($j = 0; $j < $post->length; $j ++) {
					$elem = $post->item($j);
					
					if ($elem->hasAttribute('class')) {
						if ($elem->getAttribute('class') == IMAGE_CLASS) {
							$image_link = $elem->getAttribute('style');
							$start = strpos($image_link, "(") + 1;
							$end = strpos($image_link, ")");
							$image_link = substr($image_link, $start, $end - $start);
							$entry["image"] = $image_link;
							//echo "<img src=\"".$image_link."\"><br>\n";
						}
						else if ($elem->getAttribute('class') == LISTING_CLASS) {
							$link = $elem->getElementsByTagName('a')->item(0);
							$entry["title"] = $link->getAttribute('title');
							$entry["link"] = $link->getAttribute('href');
							$entry["address"] = get_inner_html($elem->getElementsByTagName('b')->item(0));
							//echo $link->getAttribute('title');
							
							extract_info($entry["link"], $entry);
						}
					}
				}
				
				array_push($items, $entry);
                
                // Create directory structure
                mkdir($_SERVER['DOCUMENT_ROOT']."/restaurants/".$entry["id"]);
                mkdir($_SERVER['DOCUMENT_ROOT']."/restaurants/".$entry["id"]."/gallery");
                mkdir($_SERVER['DOCUMENT_ROOT']."/restaurants/".$entry["id"]."/gallery/thumb");
                mkdir($_SERVER['DOCUMENT_ROOT']."/restaurants/".$entry["id"]."/gallery/big");
                
                // Download images
                foreach ($entry['gallery'] as $image) {
                    //save_image($image['small'], "/restaurants/".$entry["id"]."/gallery/thumb".substr($image['small'], strrpos($image['small'], "/"), strlen($image['small'])));
                    //save_image($image['big'], "/restaurants/".$entry["id"]."/gallery/big".substr($image['big'], strrpos($image['big'], "/"), strlen($image['big'])));
                }
                
                $path = $_SERVER['DOCUMENT_ROOT']."/restaurants/".$entry["id"]."/".$entry["id"].".html";
                echo $path."<br>";
                $info_file = fopen($path, "w");
                if (!$info_file) echo "Unable to open file for writing: ".$info_file."<br>";
                $content = "<img src=\"".$entry["image"]."\" style=\"float:left;\"><div id=\"description\">".$entry["desc"]."</div>";
                fwrite($info_file, $content);
                fclose($info_file);
                
				//echo "</div><br>\n";
			}
		}
	}
	
	return $items;
}

function get_inner_html( $node ) { 
    $innerHTML= ''; 
    $children = $node->childNodes; 
    foreach ($children as $child) { 
        $innerHTML .= $child->ownerDocument->saveXML( $child ); 
    } 

    return $innerHTML; 
} 

function extract_info($url, &$entry) {
	// Extract restaurant information
	$url = substr($url, 0, strlen($url) - 1);
    $url= substr($url, 0, strrpos($url, "/"));
    $id = substr($url, strrpos($url, "/") + 1, strlen($url));

    // Get entry id
    $entry["id"] = $id;
    
	$html = new DOMDocument();
	@$html->loadHTMLFile($url);
	$body = $html->getElementsByTagName('body');
	$body->item(0)->setAttribute("onload", "show_desc()");
	
	@$html->loadHTML($html->saveHTML());
	$content = $html->getElementsByTagName('div');
	
	for ($i = 0; $i < $content->length; $i ++) {
		$item = $content->item($i);
		
		if ($item->hasAttribute('class')) {
			if ($item->getAttribute('class') == 'rest_options_left') {
				$scripts = $item->getElementsByTagName('script');
				
				for ($j = 0; $j < $scripts->length; $j ++) {
					$script = get_inner_html($scripts->item($j));
					
					if (strstr($script, 'function show_desc()')) {
						$desc = substr($script, strpos($script, "else"), strlen($script));
						$start = strpos($desc, ".html(") + 7;
						$end = strpos($desc, ");");
						$desc = substr($desc, $start, $end - $start);
						$entry["desc"] = $desc;
					}
				}
				
				$spans = $item->getElementsByTagName('span');
				for ($j = 0; $j < $spans->length; $j ++) {
					$span = $spans->item($j);
					if ($span->getAttribute('itemprop') == "average") {
						$entry["score"] = get_inner_html($span);
						break;
					}
				}
			}
			if ($item->getAttribute('class') == 'rest_options_right') {
				$map = $item->getElementsByTagName("img");
                
                if ($map->length == 3) {
                    //echo $map->length."<br>\n";
                    $map = $map->item(2)->getAttribute('src');
                    $start = strrpos($map, "label:") + 9;
                    $end = strrpos($map, "&");
                    $coords = substr($map, $start, $end - $start);
                    $entry["lat"] = floatval(substr($coords, 0, strpos($coords, ",")));
                    $entry["lgn"] = floatval(substr($coords, strpos($coords, ",") + 1, strlen($coords)));
                    echo $entry["lat"].",".$entry["lgn"];
                }
				
				$address = get_inner_html($item->getElementsByTagName("span")->item(2));
				$entry["address"] = $address;
			}
		}
	}
	
	// Extract menu information
	@$html->loadHTMLFile($url."/menu");
	$menu = $html->getElementById('middleMain');
	$items = $menu->getElementsByTagName('div');
	
	$menu = array();
	$item = array();
	for ($i = 0; $i < $items->length; $i ++) {
		if ($items->item($i)->getAttribute('class') == 'menu_item') {
			$menu_item = $items->item($i);
			
			// Get item image
			$image = $menu_item->getElementsByTagName('div')->item(0)->getElementsByTagName('img');
			if ($image->length > 0) {
				$image = $image->item(0)->getAttribute('src');
				$item["image"] = $image;
			}
			
			// Get the item title and description
			$desc = $menu_item->getElementsByTagName('div')->item(1)->getElementsByTagName('a');
			$item["name"] = get_inner_html($desc->item(0));
			$desc = $menu_item->getElementsByTagName('div')->item(1)->getElementsByTagName('i');
			$item["desc"] = get_inner_html($desc->item(0));
			
			// Get item options
			$item["opt"] = get_inner_html($menu_item->getElementsByTagName('div')->item(3));
			
			array_push($menu, $item);
		}
	}
	
	$entry["menu"] = $menu;
	
	$slideshow = array();
	$image = array();
	// Extract restaurant gallery
	@$html->loadHTMLFile($url."/photos");
	$galery = $html->getElementById('middle');
	$divs = $galery->getElementsByTagName('div');
	for ($i = 0; $i < $divs->length; $i ++) {
		$div = $divs->item($i);
		
		if ($div->getAttribute('class') == 'gallery') {
			$photos = $div->getElementsByTagName('div');
			
			for ($j = 0; $j < $photos->length; $j ++) {
				$image_link = $photos->item($j)->getAttribute('style');
				$start = strpos($image_link, "(") + 1;
				$end = strpos($image_link, ")");
				$thumb = substr($image_link, $start, $end - $start);
				$big = str_replace("thumb", "big", $thumb);
				$image['small'] = $thumb;
				$image['big'] = $big;
				array_push($slideshow, $image);
			}
		}
	}

	$entry["gallery"] = $slideshow;
}

function save_image($inPath,$outPath) { 
    //Download images from remote server
    $in=    fopen($inPath, "rb");
    $out=   fopen($_SERVER['DOCUMENT_ROOT'].$outPath, "wb");
    while ($chunk = fread($in,8192))
    {
        fwrite($out, $chunk, 8192);
    }
    fclose($in);
    fclose($out);
}

function insertInDB($restaurants) {
    $con = @mysql_connect('localhost', 'root', '089860');
    $db = @mysql_select_db('wordpress');
    
    $query = "INSERT INTO markers\n";
    $query .= "  (id,  name, address, lat, lng, description, type)\n";
    $query .= "VALUES\n";
    foreach ($restaurants as $rest) {
        $query .= sprintf(" ('%d', '%s', '%s', '%F', '%F', '%s', '%s'),",
                $rest["id"],
                mysql_real_escape_string($rest["title"]),
                mysql_real_escape_string($rest["address"]),
                $rest['lat'],
                $rest['lgn'],
                mysql_real_escape_string($rest["desc"]),
                "restaurant");  
    }
    $query = substr($query, 0, strlen($query) - 1);
    $query .= ";";
    //echo $query."<br>";
    $result = mysql_query($query);
    if (!$result) echo mysql_error();

    mysql_close($con);
}

/*for ($i = 3; $i < 8; $i ++) {
	$restaurants = download_info("http://sofia.zavedenia.com/restorant_9/".$i);
	insertInDB($restaurants);
}*/

if (isset($_GET['coord'])) {
	header("Content-type: text/xml");
	$lat = substr($_GET['coord'], 0, strpos($_GET['coord'], ','));
	$lgn = substr($_GET['coord'], strpos($_GET['coord'], ',') + 1, strlen($_GET['coord']));
	echo find_restaurant_near($lat, $lgn);
}
?>