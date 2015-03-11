<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
<div id="search_box">
	<form action="#" method="get"> 
	<label>Търси по:</label>                            
			<select name="fields">
				<option value="ekatte">По ЕКАТТЕ</option>
				<option value="name" selected="selected">По населено място</option>
				<option value="oblast_name">Област</option>
				<option value="obstina_name">Община</option>
				<option value="kmetstvo_name">Кметство</option>
			</select>                            
		<input type="text" name="searching" value="" id="searching" size="40">                            
		<input type="submit" name="search" value="Търси">                            
		<input type="submit" name="load_all" value="Зареди всички"> 
	</form>
</div>
<?php
$servername = "localhost";
$database = "ekatte";
$username = "root";
$password = "******";

// Create connection
$conn = new mysqli($servername, $username, $password, $database);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

mysqli_set_charset($conn, "utf8");

$query = "SELECT 
			* 
		  FROM 
			ekatte AS _ekatte
		  LEFT JOIN oblast AS _oblast 
			ON _ekatte.oblast = _oblast.oblast
		  LEFT JOIN obshtina AS _obshtina 
			ON _ekatte.obshtina = _obshtina.obshtina
		  LEFT JOIN kmetstvo AS _kmetstvo 
			ON _ekatte.kmetstvo = _kmetstvo.kmetstvo ";

if (isset($_GET['sort'])) {
	if ($_GET['sort'] == "ekatte") {
		$query .= "ORDER BY _ekatte.ekatte ASC";
	}
	else if ($_GET['sort'] == "grs") {
		$query .= "ORDER BY _ekatte.grad_selo ASC";
	}
	else if ($_GET['sort'] == "naseleno_mqsto") {
		$query .= "ORDER BY _ekatte.grad_selo ASC";
	}
	else if ($_GET['sort'] == "oblast_name") {
		$query .= "ORDER BY _oblast.oname ASC";
	}
	else if ($_GET['sort'] == "obshtina_name") {
		$query .= "ORDER BY _obshtina.obname ASC";
	}
	else if ($_GET['sort'] == "kmetsvto_name") {
		$query .= "ORDER BY _kmetstvo.kname ASC";
	}
}			
			
if (isset($_GET['search']) && isset($_GET['fields']) && isset($_GET['searching']) &&
    !empty($_GET['fields']) && !empty($_GET['searching'])) {
	$search_type = $_GET['fields'];
	$search_criteria = $_GET['searching'];
	$url = "ekatte.php?search=Търси&fields=".$search_type."&searching=".$search_criteria;
	
	if ($search_type == "name") {
		$query .= "WHERE _ekatte.naseleno_mqsto LIKE '%".mysqli_real_escape_string($conn, $_GET['searching'])."'";
	} else if ($search_type == "ekatte") {
		$query .= "WHERE _ekatte.ekatte LIKE '%".mysqli_real_escape_string($conn, $_GET['searching'])."'";
	} else if ($search_type == "oblast_name") {
		$query .= "WHERE _oblast.oname LIKE '%".mysqli_real_escape_string($conn, $_GET['searching'])."'";
	} else if ($search_type == "obshtina_name") {
		$query .= "WHERE _oblast.obname LIKE '%".mysqli_real_escape_string($conn, $_GET['searching'])."'";
	} else if ($search_type == "kmetstvo_name") {
		$query .= "WHERE _kmetstvo.kname LIKE '%".mysqli_real_escape_string($conn, $_GET['searching'])."' ";
	}
	
	if (isset($_GET['sort'])) {
		if ($_GET['sort'] == "ekatte") {
			$query .= "ORDER BY _ekatte.ekatte DESC";
		}
		else if ($_GET['sort'] == "grs") {
			$query .= "ORDER BY _ekatte.grad_selo DESC";
		}
		else if ($_GET['sort'] == "naseleno_mqsto") {
			$query .= "ORDER BY _ekatte.grad_selo DESC";
		}
		else if ($_GET['sort'] == "oblast_name") {
			$query .= "ORDER BY _oblast.oname DESC";
		}
		else if ($_GET['sort'] == "obshtina_name") {
			$query .= "ORDER BY _obshtina.obname DESC";
		}
		else if ($_GET['sort'] == "kmetsvto_name") {
			$query .= "ORDER BY _kmetstvo.kname DESC";
		}
	}
	
	$result = $conn->query($query);
	print_results($result, $url);
} else if (isset($_GET['load_all'])) {
	$url = "ekatte.php?load_all=Зареди+всички";
	$result = $conn->query($query);
	print_results($result, $url);
}
mysqli_close($conn);

function print_results($result, $url) {	
?>
<table id="result_table">
	<thead>
        <tr>
			<th><a href="<?php echo $url."&sort=ekatte";?>">ЕКАТТЕ</a></th>
			<th><a href="<?php echo $url."&sort=grs";?>">Гр./с</a></th>
            <th><a href="<?php echo $url."&sort=name";?>">Населено място</a></th>
            <th><a href="<?php echo $url."&sort=oblast_name";?>">Област</a></th>
            <th><a href="<?php echo $url."&sort=obshtina_name";?>">Община</a></th>
            <th><a href="<?php echo $url."&sort=kmetsvto_name";?>">Кметство</a></th>
        </tr>
		
<?php		
	if ($result->num_rows > 0) {
		// output data of each row
		while($row = $result->fetch_assoc()) {
			echo "<tr>";
			echo "<td>".$row["ekatte"]."</td>";
			echo "<td>".$row["grad_selo"]."</td>";
			echo "<td>".$row["naseleno_mqsto"]."</td>";
			echo "<td>".$row["oname"]."</td>";
			echo "<td>".$row["obname"]."</td>";
			echo "<td>".$row["kname"]."</td>";
			echo "</tr>";
		}
	} else {
		echo "0 results";
	}
?>
	</thead>
</table>
<?php
}
?>
</body>
</html>