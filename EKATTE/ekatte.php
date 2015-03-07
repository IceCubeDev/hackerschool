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
		<input type="text" name="searching" value="София" id="searching" size="40">                            
		<input type="submit" name="search" value="Търси">                            
		<input type="submit" name="load_all" value="Зареди всички"> 
	</form>
</div>
<table id="result_table">
	<thead>
        <tr>
			<th><a href="#&sort=ekatte">ЕКАТТЕ</a></th>
			<th><a href="#&sort=grs">Гр./с</a></th>
            <th><a href="#&sort=name">Населено място</a></th>
            <th><a href="#&sort=obstina_name">Област</a></th>
            <th><a href="#&sort=obstina_name">Община</a></th>
            <th><a href="#&sort=kmetstvo_name">Кметство</a></th>
        </tr>
<?php
$servername = "localhost";
$database = "ekatte";
$username = "root";
$password = "089860";

// Create connection
$conn = new mysqli($servername, $username, $password, $database);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

mysqli_set_charset($conn, "utf8");

if (isset($_GET['search']) && isset($_GET['searching']) && isset($_GET['fields'])) {
	$search_type = $_GET['fields'];
	$search_criteria = $_GET['searching'];
	
	$query = "SELECT * FROM ekatte AS _ekatte
			  LEFT JOIN oblast AS _oblast ON _ekatte.oblast = _oblast.oblast
			  LEFT JOIN obshtina AS _obshtina ON _ekatte.obshtina = _obshtina.obshtina
			  LEFT JOIN kmetstvo AS _kmetstvo ON _ekatte.kmetstvo = _kmetstvo.kmetstvo ";
	
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
			$query .= "ORDER BY _ekatte.ekatte";
		}
	}
	
	$result = $conn->query($query);
		
	if ($result->num_rows > 0) {
		// output data of each row
		while($row = $result->fetch_assoc()) {
			echo "<tr>";
			echo "<td>".$row["id"]."</td>";
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
}

mysqli_close($conn);
?>
	</thead>
</table>
</body>
</html>