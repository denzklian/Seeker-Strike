<?php
header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(array('status' => 'error', 'message' => 'Method Not Allowed'));
    exit();
}

$ip = $_SERVER['REMOTE_ADDR'];
if ($ip !== '127.0.0.1' && $ip !== '::1') {
    http_response_code(403);
    echo json_encode(array('status' => 'error', 'message' => 'Unauthorized: Only local operator can clear database.'));
    exit();
}

$csv_file = '../../db/results.csv';
$json_file = '../../db/results.json';
$js_file = '../../db/results.js';

if (file_exists($csv_file)) {
    $f = fopen($csv_file, 'w');
    fclose($f);
}

if (file_exists($json_file)) {
    $f = fopen($json_file, 'w');
    fwrite($f, '[]');
    fclose($f);
}

if (file_exists($js_file)) {
    $f = fopen($js_file, 'w');
    fwrite($f, 'const seeker_results = [];');
    fclose($f);
}

echo json_encode(array('status' => 'success', 'message' => 'Database cleared successfully.'));
