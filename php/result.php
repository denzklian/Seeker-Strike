<?php
header('Content-Type: text/html');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('Method Not Allowed');
}

$ok_status = isset($_POST['Status']) ? substr($_POST['Status'], 0, 32) : 'failed';
$lat = isset($_POST['Lat']) ? substr($_POST['Lat'], 0, 32) : 'N/A';
$lon = isset($_POST['Lon']) ? substr($_POST['Lon'], 0, 32) : 'N/A';
$acc = isset($_POST['Acc']) ? substr($_POST['Acc'], 0, 32) : 'N/A';
$alt = isset($_POST['Alt']) ? substr($_POST['Alt'], 0, 32) : 'N/A';
$dir = isset($_POST['Dir']) ? substr($_POST['Dir'], 0, 32) : 'N/A';
$spd = isset($_POST['Spd']) ? substr($_POST['Spd'], 0, 32) : 'N/A';

$raw_sid = isset($_POST['Sid']) ? $_POST['Sid'] : 'unknown';
$sid = preg_replace('/[^a-zA-Z0-9_\-]/', '', substr($raw_sid, 0, 64));

$data = array(
    'status' => $ok_status,
    'lat' => $lat,
    'lon' => $lon,
    'acc' => $acc,
    'alt' => $alt,
    'dir' => $dir,
    'spd' => $spd,
    'sid' => $sid
);

$json_data = json_encode($data);
$f = fopen('../../logs/' . $sid . '.gps.json', 'w+');
fwrite($f, $json_data);
fclose($f);
