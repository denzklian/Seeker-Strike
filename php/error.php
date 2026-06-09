<?php
header('Content-Type: text/html');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('Method Not Allowed');
}

$err_status = isset($_POST['Status']) ? substr($_POST['Status'], 0, 32) : 'failed';
$err_text = isset($_POST['Error']) ? substr($_POST['Error'], 0, 512) : 'Unknown error';

$raw_sid = isset($_POST['Sid']) ? $_POST['Sid'] : 'unknown';
$sid = preg_replace('/[^a-zA-Z0-9_\-]/', '', substr($raw_sid, 0, 64));

$data = array(
    'status' => $err_status,
    'error' => $err_text,
    'sid' => $sid
);

$f = fopen('../../logs/' . $sid . '.gps.json', 'w+');
$json_data = json_encode($data);
fwrite($f, $json_data);
fclose($f);
