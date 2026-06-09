<?php
header('Content-Type: text/html');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('Method Not Allowed');
}

$raw_sid = isset($_POST['Sid']) ? $_POST['Sid'] : 'unknown';
$sid = preg_replace('/[^a-zA-Z0-9_\-]/', '', substr($raw_sid, 0, 64));

$ptf = isset($_POST['Ptf']) ? substr($_POST['Ptf'], 0, 256) : 'N/A';
$brw = isset($_POST['Brw']) ? substr($_POST['Brw'], 0, 128) : 'N/A';
$cc = isset($_POST['Cc']) ? substr($_POST['Cc'], 0, 64) : 'N/A';
$ram = isset($_POST['Ram']) ? substr($_POST['Ram'], 0, 64) : 'N/A';
$ven = isset($_POST['Ven']) ? substr($_POST['Ven'], 0, 256) : 'N/A';
$ren = isset($_POST['Ren']) ? substr($_POST['Ren'], 0, 256) : 'N/A';
$ht = isset($_POST['Ht']) ? substr($_POST['Ht'], 0, 16) : '0';
$wd = isset($_POST['Wd']) ? substr($_POST['Wd'], 0, 16) : '0';
$os = isset($_POST['Os']) ? substr($_POST['Os'], 0, 256) : 'N/A';
$brand = isset($_POST['Brand']) ? substr($_POST['Brand'], 0, 128) : 'Not Available';
$model = isset($_POST['Model']) ? substr($_POST['Model'], 0, 128) : 'Not Available';

function getUserIP()
{
    if (isset($_SERVER["HTTP_CF_CONNECTING_IP"])) {
        $_SERVER['REMOTE_ADDR'] = $_SERVER["HTTP_CF_CONNECTING_IP"];
        $_SERVER['HTTP_CLIENT_IP'] = $_SERVER["HTTP_CF_CONNECTING_IP"];
    }
    $client  = @$_SERVER['HTTP_CLIENT_IP'];
    $forward = @$_SERVER['HTTP_X_FORWARDED_FOR'];
    $real_ip = @$_SERVER['HTTP_X_REAL_IP'];
    $remote  = $_SERVER['REMOTE_ADDR'];

    if (filter_var($client, FILTER_VALIDATE_IP)) {
        return $client;
    }
    if ($forward) {
        $forward_first = explode(',', $forward)[0];
        $forward_ip = trim($forward_first);
        if (filter_var($forward_ip, FILTER_VALIDATE_IP)) {
            return $forward_ip;
        }
    }
    if (filter_var($real_ip, FILTER_VALIDATE_IP)) {
        return $real_ip;
    }
    return $remote;
}

$ip = getUserIP();

$data = array(
    'platform' => $ptf,
    'browser' => $brw,
    'cores' => $cc,
    'ram' => $ram,
    'vendor' => $ven,
    'render' => $ren,
    'ip' => $ip,
    'ht' => $ht,
    'wd' => $wd,
    'os' => $os,
    'brand' => $brand,
    'model' => $model,
    'sid' => $sid
);

$json_data = json_encode($data);
$f = fopen('../../logs/' . $sid . '.info.json', 'w+');
fwrite($f, $json_data);
fclose($f);
